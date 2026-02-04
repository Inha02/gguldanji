# python select_top100.py --input data/processed/키워드/키워드_clean.jsonl --output data/processed/키워드/키워드_final_100.jsonl
import json
import argparse
import os

def select_top100(input_path: str, output_path: str, limit: int = 100):
    selected = []

    with open(input_path, "r", encoding="utf-8") as f:
        for line in f:
            if len(selected) >= limit:
                break

            row = json.loads(line)

            if row.get("manual_keep") is True:
                selected.append(row)

    if not selected:
        raise RuntimeError("manual_keep == true 인 데이터가 하나도 없습니다.")

    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    with open(output_path, "w", encoding="utf-8") as f:
        for row in selected:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")

    print(f"[OK] saved {len(selected)} rows → {output_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True, help="예: data/processed/노트북/노트북_clean.jsonl")
    parser.add_argument("--output", required=True, help="예: data/processed/노트북/노트북_final_100.jsonl")
    parser.add_argument("--limit", type=int, default=100, help="default=100")

    args = parser.parse_args()

    select_top100(
        input_path=args.input,
        output_path=args.output,
        limit=args.limit
    )
