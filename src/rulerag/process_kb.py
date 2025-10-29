"""
Asynchronous processing of D&D 5e data, converting JSON files to knowledge base format
"""
import asyncio
import json
import re
import sys
from pathlib import Path
from typing import List, Tuple

# Add project root directory to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.rulerag.ingest_pipeline import IngestPipeline

# Configure paths (relative to project root)
INPUT_BASE = project_root / "data" / "rules" / "dnd_5e_data"
OUTPUT_BASE = project_root / "data" / "rules" / "kb"
CATEGORIES = ["spells", "features", "conditions", "rule-sections"]

# Concurrency limit
CONCURRENCY_LIMIT = 20


def extract_text_from_json(data: dict, category: str) -> str:
    """Extract text content from JSON data"""
    name = data.get("name", "")
    desc = data.get("desc", "")
    
    # Process desc field (could be string or list)
    if isinstance(desc, list):
        desc_text = "\n".join(desc)
    elif isinstance(desc, str):
        desc_text = desc
    else:
        desc_text = ""
    
    # Combine name and description
    if name and desc_text:
        return f"{name}\n\n{desc_text}"
    elif name:
        return name
    elif desc_text:
        return desc_text
    else:
        return ""


def split_markdown_by_headers(text: str) -> List[Tuple[str, str]]:
    """
    Split Markdown text by level 2 or 3 headers
    Return: List[Tuple[header, content]]
    """
    # Use regex to match lines starting with ## or ###
    pattern = r'^(#{2,3})\s+(.+)$'
    
    chunks = []
    lines = text.split('\n')
    current_header = None
    current_content = []
    has_headers = False
    
    for line in lines:
        match = re.match(pattern, line)
        if match:
            has_headers = True
            # Save previous chunk
            if current_header is not None:
                chunks.append((current_header, '\n'.join(current_content)))
            elif current_content:
                # Save content before headers
                chunks.append(("Introduction", '\n'.join(current_content)))
            
            # Start new chunk
            current_header = match.group(2).strip()
            current_content = [line]
        else:
            current_content.append(line)
    
    # Save last chunk
    if current_header is not None:
        chunks.append((current_header, '\n'.join(current_content)))
    elif not has_headers:
        # If no headers found, treat entire document as one chunk
        chunks.append(("Main Content", text))
    
    return chunks if chunks else [("Content", text)]


async def process_file_async(
    pipeline: IngestPipeline,
    file_path: Path,
    category: str,
    output_dir: Path,
    force_reprocess: bool = False
):
    """Asynchronously process a single file"""
    try:
        # Check if output file already exists
        output_file = output_dir / f"{file_path.stem}.json"
        if not force_reprocess and output_file.exists():
            # Validate if file is valid (non-empty and valid JSON)
            try:
                with open(output_file, 'r', encoding='utf-8') as f:
                    existing_data = json.load(f)
                    # Check if data is valid (non-empty)
                    if existing_data:
                        print(f"[SKIP] {file_path.name}: Already processed")
                        return "skipped"
            except (json.JSONDecodeError, Exception):
                # If file is corrupted, reprocess
                print(f"[INFO] {file_path.name}: Output file corrupted, reprocessing...")
        
        # Read JSON file
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Extract text
        text = extract_text_from_json(data, category)
        if not text.strip():
            print(f"[SKIP] {file_path.name}: No text content")
            return "no_content"
        
        # For rule-sections, split by headers
        if category == "rule-sections":
            chunks = split_markdown_by_headers(text)
            
            # Process each chunk
            all_results = []
            for header, chunk_text in chunks:
                # Use asyncio.to_thread to convert sync call to async
                result = await asyncio.to_thread(
                    pipeline.extract_data_to_kb,
                    chunk_text,
                    category
                )
                if result:
                    # Add chunk information
                    if isinstance(result, dict):
                        result['_chunk_header'] = header
                        result['_source_file'] = file_path.stem
                    all_results.append(result)
            
            # Save results
            if all_results:
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump(all_results, f, indent=2, ensure_ascii=False)
                print(f"[OK] {file_path.name} -> {len(all_results)} chunks")
                return "success"
            else:
                print(f"[FAIL] {file_path.name}: All chunks failed")
                return "failed"
        else:
            # For other categories, process entire file directly
            result = await asyncio.to_thread(
                pipeline.extract_data_to_kb,
                text,
                category
            )
            
            if result:
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump(result, f, indent=2, ensure_ascii=False)
                print(f"[OK] {file_path.name}")
                return "success"
            else:
                print(f"[FAIL] {file_path.name}: Extraction failed")
                return "failed"
    
    except Exception as e:
        print(f"[ERROR] {file_path.name}: {e}")
        return "error"


async def process_category(
    pipeline: IngestPipeline,
    category: str,
    semaphore: asyncio.Semaphore,
    force_reprocess: bool = False
):
    """Process all files in a category"""
    input_dir = INPUT_BASE / category
    output_dir = OUTPUT_BASE / category
    
    if not input_dir.exists():
        print(f"[SKIP] Category {category}: Directory not found")
        return {"skipped": 0, "success": 0, "failed": 0, "error": 0, "no_content": 0}
    
    # Create output directory
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Get all JSON files
    json_files = list(input_dir.glob("*.json"))
    print(f"\n[INFO] Processing {category}: {len(json_files)} files")
    
    # Statistics
    stats = {"skipped": 0, "success": 0, "failed": 0, "error": 0, "no_content": 0}
    
    # Create task list
    async def process_with_semaphore(json_file):
        async with semaphore:
            result = await process_file_async(
                pipeline, json_file, category, output_dir, force_reprocess
            )
            if result in stats:
                stats[result] += 1
    
    tasks = [process_with_semaphore(json_file) for json_file in json_files]
    
    # Wait for all tasks to complete
    await asyncio.gather(*tasks, return_exceptions=True)
    
    # Print statistics
    print(f"[STATS] {category}: "
          f"Success: {stats['success']}, "
          f"Skipped: {stats['skipped']}, "
          f"Failed: {stats['failed']}, "
          f"Error: {stats['error']}, "
          f"No Content: {stats['no_content']}")
    
    return stats


async def main(force_reprocess: bool = False):
    """Main function"""
    pipeline = IngestPipeline()
    
    # Create semaphore to limit concurrency
    semaphore = asyncio.Semaphore(CONCURRENCY_LIMIT)
    
    print("=" * 60)
    print("D&D 5e Knowledge Base Processing")
    if force_reprocess:
        print("Mode: FORCE REPROCESS (will reprocess all files)")
    else:
        print("Mode: RESUME (will skip already processed files)")
    print("=" * 60)
    
    # Process all categories
    all_stats = {"skipped": 0, "success": 0, "failed": 0, "error": 0, "no_content": 0}
    for category in CATEGORIES:
        stats = await process_category(pipeline, category, semaphore, force_reprocess)
        for key in all_stats:
            all_stats[key] += stats.get(key, 0)
    
    print("\n" + "=" * 60)
    print("All processing completed!")
    print("=" * 60)
    print("Overall Statistics:")
    print(f"  Success: {all_stats['success']}")
    print(f"  Skipped: {all_stats['skipped']}")
    print(f"  Failed: {all_stats['failed']}")
    print(f"  Error: {all_stats['error']}")
    print(f"  No Content: {all_stats['no_content']}")
    print("=" * 60)


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Process D&D 5e data to knowledge base")
    parser.add_argument(
        "--force",
        action="store_true",
        help="Force reprocess all files, even if they already exist"
    )
    args = parser.parse_args()
    
    asyncio.run(main(force_reprocess=args.force))
