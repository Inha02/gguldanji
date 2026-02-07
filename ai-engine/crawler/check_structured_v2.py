import os, glob, json, argparse
from collections import Counter, defaultdict

BASE_DIR = os.path.dirname(__file__)
DATA_DIR = os.path.join(BASE_DIR, "data")
STRUCT_DIR = os.path.join(DATA_DIR, "structured")
SPEC_DIR = os.path.join(DATA_DIR, "spec_key_suggestions")

def iter_jsonl(path):
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            yield json.loads(line)

def load_spec_map():
    """
    category_name -> spec_key.json path
    """
    spec_files = glob.glob(os.path.join(SPEC_DIR, "*.spec_key.json"))
    m = {}
    for fp in spec_files:
        with open(fp, "r", encoding="utf-8") as f:
            d = json.load(f)
        name = d.get("category_name")
        if name:
            m[name] = fp
    return m

def get_priority_fields(spec_cfg: dict, max_template_fields: int = 12):
    """
    1) category_spec_fields에서 importance high/medium인 필드
    2) subtype templates에 자주 등장하는 필드 상위 max_template_fields
    """
    pri = []
    for x in spec_cfg.get("category_spec_fields", []):
        if x.get("importance") in ("high", "medium"):
            pri.append(x.get("field"))

    # subtype templates field frequency
    freq = Counter()
    for t in spec_cfg.get("subtype_spec_key_templates", []):
        for f in t.get("fields", []):
            freq[f] += 1

    # 너무 많아지니까 상위 N개만
    for f, _ in freq.most_common(max_template_fields):
        if f not in pri:
            pri.append(f)

    # None 제거
    pri = [x for x in pri if x]
    return pri

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--topk", type=int, default=15, help="topk lines to print per category")
    p.add_argument("--max-template-fields", type=int, default=12, help="how many frequent template fields to include")
    args = p.parse_args()

    files = sorted(glob.glob(os.path.join(STRUCT_DIR, "*", "*_structured.jsonl")))
    if not files:
        raise SystemExit(f"[ERR] no structured files under {STRUCT_DIR}")

    spec_map = load_spec_map()

    # category -> counters
    cat_rows = Counter()
    cat_missing = defaultdict(Counter)
    cat_present = defaultdict(Counter)
    cat_subtype = defaultdict(Counter)

    # category -> priority fields (loaded lazily)
    cat_priority_fields = {}

    for fp in files:
        cat = os.path.basename(os.path.dirname(fp))  # category_name
        if cat not in spec_map:
            # spec_key.json 없으면 체크 못함
            continue

        if cat not in cat_priority_fields:
            with open(spec_map[cat], "r", encoding="utf-8") as f:
                spec_cfg = json.load(f)
            cat_priority_fields[cat] = get_priority_fields(spec_cfg, max_template_fields=args.max_template_fields)

        pri_fields = cat_priority_fields[cat]

        for r in iter_jsonl(fp):
            s = r.get("structured") or {}
            spec = s.get("spec") or {}
            subtype = s.get("subtype") or "null"
            cat_rows[cat] += 1
            cat_subtype[cat][subtype] += 1

            for f in pri_fields:
                v = spec.get(f)
                if v is None or v == "":
                    cat_missing[cat][f] += 1
                else:
                    cat_present[cat][f] += 1

    # 출력
    cats = sorted(cat_rows.keys())
    total = sum(cat_rows.values())
    print(f"\n[OK] categories checked: {len(cats)}")
    print(f"[OK] total structured rows checked: {total}")

    for cat in cats:
        n = cat_rows[cat]
        print(f"\n=== {cat} ===")
        print(f"- rows: {n}")
        # subtype top
        print("- subtype top:")
        for st, c in cat_subtype[cat].most_common(5):
            print(f"  - {st}: {c}")

        pri_fields = list(cat_missing[cat].keys() | cat_present[cat].keys())
        # missing rate 정렬(높은 순)
        rates = []
        for f in pri_fields:
            miss = cat_missing[cat][f]
            rate = miss / n * 100.0 if n else 0.0
            rates.append((rate, f, miss))
        rates.sort(reverse=True)

        print(f"- priority fields (missing rate top {args.topk}):")
        for rate, f, miss in rates[:args.topk]:
            print(f"  - {f}: missing {miss} ({rate:.1f}%)")

if __name__ == "__main__":
    main()
