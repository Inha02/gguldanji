import os, glob, json, argparse
from collections import Counter, defaultdict

BASE_DIR = os.path.dirname(__file__)
DATA_DIR = os.path.join(BASE_DIR, "data")
STRUCT_DIR = os.path.join(DATA_DIR, "structured")

def iter_jsonl(path):
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line=line.strip()
            if not line: 
                continue
            yield json.loads(line)

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--topk", type=int, default=15)
    args = p.parse_args()

    files = sorted(glob.glob(os.path.join(STRUCT_DIR, "*", "*_structured.jsonl")))
    if not files:
        raise SystemExit(f"[ERR] no structured files found under {STRUCT_DIR}")

    total_rows = 0
    by_cat = Counter()
    by_keyword = Counter()
    subtype_counter = Counter()
    missing_field_counts = Counter()
    field_presence = Counter()

    for fp in files:
        cat = os.path.basename(os.path.dirname(fp))
        keyword = os.path.basename(fp).replace("_structured.jsonl", "")
        by_cat[cat] += 1
        by_keyword[keyword] += 1

        for r in iter_jsonl(fp):
            total_rows += 1
            s = (r.get("structured") or {})
            subtype_counter[s.get("subtype") or "null"] += 1
            spec = (s.get("spec") or {})

            # 핵심 필드만 간단히 체크(필요하면 늘려도 됨)
            must = ["device_type", "brand", "model_name"]
            for f in must:
                if spec.get(f) is None or spec.get(f) == "":
                    missing_field_counts[f] += 1
                else:
                    field_presence[f] += 1

    print(f"\n[OK] structured files: {len(files)}")
    print(f"[OK] total rows: {total_rows}")

    print("\n[By category] (number of structured files per category)")
    for k, v in by_cat.most_common():
        print(f"- {k}: {v} files")

    print("\n[Subtype top]")
    for k, v in subtype_counter.most_common(args.topk):
        print(f"- {k}: {v}")

    print("\n[Missing rate for key fields]")
    for f in ["device_type", "brand", "model_name"]:
        miss = missing_field_counts[f]
        rate = (miss / total_rows * 100.0) if total_rows else 0.0
        print(f"- {f}: missing {miss} ({rate:.1f}%)")

if __name__ == "__main__":
    main()
