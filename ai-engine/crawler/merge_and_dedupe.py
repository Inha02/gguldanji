# data/processed/*/*_clean.jsonl 전부 합치고 seq 기준 전역 중복 제거
import os
import glob
import json
from typing import Dict, List, Tuple


BASE_DIR = os.path.dirname(__file__)
DATA_DIR = os.path.join(BASE_DIR, "data")
PROCESSED_DIR = os.path.join(DATA_DIR, "processed")
MERGED_DIR = os.path.join(DATA_DIR, "merged")

os.makedirs(MERGED_DIR, exist_ok=True)


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


def find_clean_files() -> List[str]:
    # data/processed/<keyword>/<keyword>_clean.jsonl 전부 수집
    files = sorted(glob.glob(os.path.join(PROCESSED_DIR, "*", "*_clean.jsonl")))
    return files


def main():
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=str, default=os.path.join(MERGED_DIR, "clean_merged_dedup.jsonl"))
    parser.add_argument("--keep", type=str, default="first", choices=["first", "last"])
    args = parser.parse_args()

    files = find_clean_files()
    if not files:
        raise SystemExit(f"[ERR] clean 파일이 없음: {PROCESSED_DIR}")

    # seq 기준 전역 중복 제거
    by_seq: Dict[int, Dict] = {}
    sources: Dict[int, List[str]] = {}  # seq가 어떤 키워드 폴더에서 왔는지 기록

    total_rows = 0
    dup_rows = 0
    missing_seq = 0

    for fp in files:
        keyword_dir = os.path.basename(os.path.dirname(fp))  # processed/<keyword_dir>/
        for row in iter_jsonl(fp):
            total_rows += 1
            seq = row.get("seq")
            if not isinstance(seq, int):
                missing_seq += 1
                continue

            sources.setdefault(seq, []).append(keyword_dir)

            if seq in by_seq:
                dup_rows += 1
                if args.keep == "last":
                    by_seq[seq] = row
            else:
                by_seq[seq] = row

    merged = list(by_seq.values())

    # 중복 정보도 저장
    dup_report = []
    for seq, ks in sources.items():
        if len(ks) >= 2:
            dup_report.append({"seq": seq, "keywords": ks})

    dup_report_path = os.path.join(MERGED_DIR, "duplicates_by_seq.json")
    with open(dup_report_path, "w", encoding="utf-8") as f:
        json.dump(dup_report, f, ensure_ascii=False, indent=2)

    write_jsonl(args.out, merged)

    print("\n===== MERGE & DEDUPE =====")
    print(f"clean_files: {len(files)}")
    print(f"total_rows(read): {total_rows}")
    print(f"unique_by_seq: {len(merged)}")
    print(f"duplicate_rows(skipped): {dup_rows}")
    print(f"missing_seq(rows): {missing_seq}")
    print(f"[saved] {args.out}")
    print(f"[saved] {dup_report_path}")


if __name__ == "__main__":
    main()
