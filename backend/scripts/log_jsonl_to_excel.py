import glob
import json
import os
from typing import Any, Dict, List

import pandas as pd


def _iter_jsonl_records(path: str) -> List[Dict[str, Any]]:
    records: List[Dict[str, Any]] = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            records.append(json.loads(line))
    return records


def _collect_input_files(input_path: str) -> List[str]:
    # If user passes a file, use it; if directory, scan *.jsonl; if glob, expand.
    if os.path.isfile(input_path):
        return [input_path]
    if os.path.isdir(input_path):
        return sorted(glob.glob(os.path.join(input_path, "*.jsonl")))
    expanded = sorted(glob.glob(input_path))
    return [p for p in expanded if os.path.isfile(p)]


def export_excel(input_path: str, output_path: str) -> int:
    files = _collect_input_files(input_path)
    if not files:
        print(f"No input jsonl files found for: {input_path}")
        return 1

    records: List[Dict[str, Any]] = []
    for fp in files:
        records.extend(_iter_jsonl_records(fp))

    df = pd.DataFrame.from_records(records)

    # Map internal JSON keys to required output columns (exact names per request)
    rename_map = {
        "round_number": "round number",
        "session_id": "session id",
    }
    df = df.rename(columns=rename_map)

    # Required output columns (exact names + order)
    columns = ["round number", "session id", "player_input", "rule_result", "narrative_text"]
    for c in columns:
        if c not in df.columns:
            df[c] = None
    df = df[columns]

    # Sort for readability: session id then round number
    df["round number"] = pd.to_numeric(df["round number"], errors="coerce")
    df = df.sort_values(by=["session id", "round number"], kind="stable").reset_index(drop=True)

    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
    df.to_excel(output_path, index=False)
    print(f"Wrote {len(df)} rows to: {output_path}")
    return 0


def main(input_filepath: str, output_filepath: str) -> int:
    return export_excel(input_filepath, output_filepath)


if __name__ == "__main__":
    # Fill in paths as needed.
    main("logs", "logs.xlsx")


