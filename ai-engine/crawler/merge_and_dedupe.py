import os
import glob
import json
import argparse
from typing import Dict, List


BASE_DIR = os.path.dirname(__file__)
DATA_DIR = os.path.join(BASE_DIR, "data")
PROCESSED_DIR = os.path.join(DATA_DIR, "processed")
ANCHORS_DIR = os.path.join(DATA_DIR, "anchors")
MERGED_DIR = os.path.join(DATA_DIR, "merged")

os.makedirs(MERGED_DIR, exist_ok=True)


# -----------------------------
# Utils
# -----------------------------
def iter_jsonl(path: str):
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            yield json.loads(line)


def write_jsonl(path: str, rows: List[Dict]):
    with open(path, "w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")


# -----------------------------
# Category mapping
# -----------------------------
def load_anchor_category_map() -> Dict[str, str]:
    """
    anchors/*.txt 파일을 읽어서
    anchor_keyword -> category_id (01~16) 매핑 생성
    """
    mapping: Dict[str, str] = {}

    for fp in glob.glob(os.path.join(ANCHORS_DIR, "*.txt")):
        fname = os.path.basename(fp)
        category_id = fname.split("_")[0]  # "01", "02", ...

        with open(fp, "r", encoding="utf-8") as f:
            for line in f:
                kw = line.strip()
                if not kw or kw.startswith("#"):
                    continue
                mapping[kw] = category_id

    return mapping


# -----------------------------
# Main
# -----------------------------
def find_final_files() -> List[str]:
    # data/processed/<anchor>/<anchor>_final_100.jsonl
    return sorted(
        glob.glob(os.path.join(PROCESSED_DIR, "*", "*_final_100.jsonl"))
    )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--out",
        type=str,
        default=os.path.join(MERGED_DIR, "final_merged_dedup.jsonl"),
        help="output merged jsonl path"
    )
    parser.add_argument(
        "--keep",
        type=str,
        default="first",
        choices=["first", "last"],
        help="which row to keep when seq duplicates occur"
    )
    args = parser.parse_args()

    files = find_final_files()
    if not files:
        raise SystemExit(f"[ERR] final_100 파일이 없음: {PROCESSED_DIR}")

    anchor_to_category = load_anchor_category_map()

    by_seq: Dict[int, Dict] = {}
    total_rows = 0
    dup_rows = 0
    missing_seq = 0

    for fp in files:
        anchor = os.path.basename(os.path.dirname(fp))  # processed/<anchor>/
        category = anchor_to_category.get(anchor, "unknown")

        for row in iter_jsonl(fp):
            total_rows += 1
            seq = row.get("seq")

            if not isinstance(seq, int):
                missing_seq += 1
                continue

            if seq in by_seq:
                dup_rows += 1
                existing = by_seq[seq]

                # anchor 누적
                existing.setdefault("anchors", [])
                if anchor not in existing["anchors"]:
                    existing["anchors"].append(anchor)

                # category 누적
                existing.setdefault("categories", [])
                if category not in existing["categories"]:
                    existing["categories"].append(category)

                if args.keep == "last":
                    row["anchors"] = existing["anchors"]
                    row["categories"] = existing["categories"]
                    by_seq[seq] = row

            else:
                row["anchors"] = [anchor]
                row["categories"] = [category]
                by_seq[seq] = row

    merged = list(by_seq.values())

    # duplicate report
    dup_report = [
        {
            "seq": r["seq"],
            "anchors": r.get("anchors", []),
            "categories": r.get("categories", [])
        }
        for r in merged
        if len(r.get("anchors", [])) > 1
    ]

    dup_report_path = os.path.join(MERGED_DIR, "duplicates_by_seq.json")
    with open(dup_report_path, "w", encoding="utf-8") as f:
        json.dump(dup_report, f, ensure_ascii=False, indent=2)

    write_jsonl(args.out, merged)

    print("\n===== MERGE & DEDUPE =====")
    print(f"final_files: {len(files)}")
    print(f"total_rows(read): {total_rows}")
    print(f"unique_by_seq: {len(merged)}")
    print(f"duplicate_rows: {dup_rows}")
    print(f"missing_seq: {missing_seq}")
    print(f"[saved] {args.out}")
    print(f"[saved] {dup_report_path}")


if __name__ == "__main__":
    main()
