import asyncio
import aiohttp
import aiofiles
import json
from pathlib import Path
from urllib.parse import urlparse
import random

# Configuration
BASE_HOST = "http://localhost:3000"
ROOT_ENDPOINT = "/api/2014" # Crawler seed (starting point)
OUTPUT_DIR = Path("data/rules/dnd_5e_data")
CONCURRENCY_LIMIT = 10 # Concurrency limit



# 全局状态
visited_urls = set()
queue = asyncio.Queue()

def extract_links_recursively(data):
    """递归提取 JSON 中的所有 API 链接"""
    links = []
    if isinstance(data, dict):
        for key, value in data.items():
            if isinstance(value, str) and value.startswith("/api/2014"):
                links.append(value)
            elif isinstance(value, (dict, list)):
                links.extend(extract_links_recursively(value))
    elif isinstance(data, list):
        for item in data:
            links.extend(extract_links_recursively(item))
    return links

def url_to_filepath(url):
    """Convert API URL to local file path"""
    clean_path = url.replace("/api/2014", "").strip("/")
    if not clean_path:
        return OUTPUT_DIR / "root.json"
    return OUTPUT_DIR / f"{clean_path}.json"

async def worker(session):
    try:
        while True:
            # 1. Get task
            url = await queue.get()
            
            try:
                if url in visited_urls:
                    continue # Note: continue here will also trigger task_done in finally
                
                full_url = BASE_HOST + url
                
                # --- Retry logic ---
                max_retries = 5
                for attempt in range(max_retries):
                    try:
                        async with session.get(full_url) as response:
                            
                            # A. Success
                            if response.status == 200:
                                data = await response.json()
                                visited_urls.add(url)
                                
                                # Save
                                file_path = url_to_filepath(url)
                                file_path.parent.mkdir(parents=True, exist_ok=True)
                                async with aiofiles.open(file_path, 'w', encoding='utf-8') as f:
                                    await f.write(json.dumps(data, indent=2, ensure_ascii=False))
                                
                                # Discover new links
                                new_links = extract_links_recursively(data)
                                for link in new_links:
                                    if link not in visited_urls:
                                        queue.put_nowait(link)
                                
                                print(f"[OK] {url}")
                                break # Successfully exit retry loop

                            # B. Rate limit (429)
                            elif response.status == 429:
                                wait_time = (2 ** attempt) + random.uniform(0, 1)
                                print(f"[Wait] 429 Rate limit: {url} -> Wait {wait_time:.1f}s")
                                await asyncio.sleep(wait_time)
                                continue # Retry
                            
                            # C. Other errors
                            else:
                                print(f"[ERR] Status {response.status}: {url}")
                                visited_urls.add(url) # Mark as processed to prevent infinite loop
                                break
                                
                    except asyncio.CancelledError:
                        raise # If cancellation signal, raise directly to outer handler
                    except Exception as e:
                        # Network connection errors, etc.
                        print(f"[NetErr] {url}: {e}")
                        await asyncio.sleep(1) # Wait a bit after error
                else:
                    # If loop finished without break, retries exhausted
                    visited_urls.add(url)
                    print(f"[Fail] Abandoned {url}")

            except asyncio.CancelledError:
                raise # Continue propagating upward
            except Exception as e:
                print(f"[WorkerErr] Unknown error: {e}")
            finally:
                # Mark queue task as done
                queue.task_done()

    except asyncio.CancelledError:
        # Key to graceful exit: catch CancelledError and do nothing, silently end Worker
        pass

async def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    queue.put_nowait(ROOT_ENDPOINT)
    
    connector = aiohttp.TCPConnector(limit=CONCURRENCY_LIMIT)
    
    print(f"--- D&D 5e crawler started (concurrency: {CONCURRENCY_LIMIT}) ---")
    print("Building knowledge base, please wait...")
    
    async with aiohttp.ClientSession(connector=connector) as session:
        # Start workers
        workers = [asyncio.create_task(worker(session)) for _ in range(CONCURRENCY_LIMIT)]
        
        try:
            # Wait for all tasks to complete
            await queue.join()
        except KeyboardInterrupt:
            # If user presses Ctrl+C
            print("\nUser stop detected, cleaning up tasks...")
        finally:
            # Cancel all workers
            for w in workers:
                w.cancel()
            # Wait for workers to exit gracefully
            await asyncio.gather(*workers, return_exceptions=True)

    print(f"\nAll done! Crawled {len(visited_urls)} files.")
    print(f"Data saved to: {OUTPUT_DIR.absolute()}")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass