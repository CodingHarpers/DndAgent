"""
Asynchronous processing of D&D 5e data, converting JSON files to knowledge base format
"""
import asyncio
import json
import re
import sys
from pathlib import Path
from typing import List, Tuple, Dict, Any

# Add project root directory to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from ruleGenerationPipeline import RuleGenerationPipeline

# Configure paths (relative to project root)
INPUT_BASE = project_root / "data" / "rules" / "dnd_5e_data"
OUTPUT_BASE = project_root / "data" / "rules" / "kb"
CATEGORIES = ["spells", "features", "conditions", "rule-sections", "classes", "races"]

# Concurrency limit
CONCURRENCY_LIMIT = 30


def extract_text_from_json(data: dict, category: str) -> str:
    """Extract text content from JSON data"""
    IGNORE_KEYS = {"index", "url", "updated_at", "_id", "full_name"}

    def _recursive_parse(obj, indent_level=0):
        lines = []
        indent = "  " * indent_level  # 缩进，体现层级结构
        
        if isinstance(obj, dict):
            for key, value in obj.items():
                if key in IGNORE_KEYS:
                    continue
                
                # 特殊处理：如果是 desc/description 且是列表，直接拼成文本，不要显示成 List 结构
                if key in ["desc", "description"] and isinstance(value, list):
                    text_block = "\n".join(value)
                    # 这里的缩进处理是为了让大段文本更好看
                    formatted_desc = text_block.replace("\n", f"\n{indent}  ")
                    lines.append(f"{indent}{key}: {formatted_desc}")
                
                # 如果值是复杂的字典或列表，递归处理
                elif isinstance(value, (dict, list)):
                    # 如果是空列表或空字典，跳过
                    if not value:
                        continue
                    lines.append(f"{indent}{key}:")
                    lines.append(_recursive_parse(value, indent_level + 1))
                
                # 如果是基本类型 (str, int, float, bool)
                else:
                    lines.append(f"{indent}{key}: {value}")
                    
        elif isinstance(obj, list):
            for item in obj:
                # 如果列表里是复杂的对象
                if isinstance(item, (dict, list)):
                    lines.append(f"{indent}- entry:") # 用个标记表示列表项
                    lines.append(_recursive_parse(item, indent_level + 1))
                else:
                    # 如果列表里只是简单的字符串（比如 tags）
                    lines.append(f"{indent}- {item}")
        
        return "\n".join(line for line in lines if line)

    return _recursive_parse(data)


def build_class_payload(class_file: Path, base_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Build a rich payload for class data by merging:
    - top-level class JSON (e.g. classes/wizard.json)
    - optional aggregated levels.json under classes/{class_name}/levels.json
    - all per-level JSON files under classes/{class_name}/levels/*.json
    - any additional helper JSONs under the class folder (e.g. spellcasting.json, spells.json, fighter.json)
    """
    class_name = base_data.get("name") or class_file.stem
    class_index = base_data.get("index", class_file.stem)

    class_dir = class_file.parent / class_file.stem  # e.g. classes/wizard.json -> classes/wizard/

    payload: Dict[str, Any] = {
        "class_name": class_name,
        "class_index": class_index,
        "class_data": base_data,
    }

    if not class_dir.exists():
        # No extra files; just return base payload
        return payload

    # 1) Aggregated levels.json (if present)
    levels_overview_path = class_dir / "levels.json"
    if levels_overview_path.exists():
        try:
            with open(levels_overview_path, "r", encoding="utf-8") as f:
                payload["levels_overview"] = json.load(f)
        except Exception as e:
            print(f"[WARN] Failed to load {levels_overview_path.name} for {class_name}: {e}")

    # 2) All per-level JSON files under levels/
    levels_dir = class_dir / "levels"
    if levels_dir.exists() and levels_dir.is_dir():
        level_entries: List[Dict[str, Any]] = []

        def _level_sort_key(p: Path) -> Any:
            # Prefer numeric ordering if filename is a number, otherwise lexical
            stem = p.stem
            return int(stem) if stem.isdigit() else stem

        for level_file in sorted(levels_dir.glob("*.json"), key=_level_sort_key):
            try:
                with open(level_file, "r", encoding="utf-8") as f:
                    level_entries.append(json.load(f))
            except Exception as e:
                print(f"[WARN] Failed to load level file {level_file}: {e}")

        if level_entries:
            payload["levels"] = level_entries

    # 3) Any other helpful JSONs directly under the class directory
    #    e.g. wizard/spellcasting.json, wizard/spells.json, fighter/fighter.json, etc.
    extra_files: Dict[str, Any] = {}
    for extra_path in class_dir.glob("*.json"):
        # Skip files we've already explicitly handled
        if extra_path.name in {"levels.json"}:
            continue

        try:
            with open(extra_path, "r", encoding="utf-8") as f:
                extra_files[extra_path.stem] = json.load(f)
        except Exception as e:
            print(f"[WARN] Failed to load extra class file {extra_path}: {e}")

    if extra_files:
        payload["extra"] = extra_files

    return payload


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
    pipeline: RuleGenerationPipeline,
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
        
        # Extract text / build payload
        if category == "classes":
            # For classes, build a merged payload that includes
            # top-level class data + all level JSONs + aggregated levels.json etc.
            merged = build_class_payload(file_path, data)
            # Send as JSON string so the class prompt can see the full structure,
            # including level progression table information.
            text = json.dumps(merged, ensure_ascii=False)
        else:
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
    pipeline: RuleGenerationPipeline,
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
    pipeline = RuleGenerationPipeline()
    
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
