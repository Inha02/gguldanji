import os, glob, json, argparse, csv
from collections import defaultdict, Counter
from statistics import mean, median

BASE_DIR = os.path.dirname(__file__)
DATA_DIR = os.path.join(BASE_DIR, "data")
STRUCT_DIR = os.path.join(DATA_DIR, "structured")
OUT_DIR = os.path.join(DATA_DIR, "stats", "spec_key_hash_groups")
os.makedirs(OUT_DIR, exist_ok=True)

def iter_jsonl(path):
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            yield json.loads(line)

def percentile(sorted_vals, p: float):
    if not sorted_vals:
        return None
    k = (len(sorted_vals) - 1) * p
    f = int(k)
    c = min(f + 1, len(sorted_vals) - 1)
    if f == c:
        return sorted_vals[f]
    return sorted_vals[f] + (sorted_vals[c] - sorted_vals[f]) * (k - f)

def safe_float(x):
    try:
        if x is None:
            return None
        return float(x)
    except Exception:
        return None

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--min-count", type=int, default=2)
    args = p.parse_args()

    files = sorted(glob.glob(os.path.join(STRUCT_DIR, "*", "*_structured.jsonl")))
    if not files:
        raise SystemExit("no structured files")

    cat_groups = defaultdict(lambda: defaultdict(list))

    for fp in files:
        cat = os.path.basename(os.path.dirname(fp))
        for r in iter_jsonl(fp):
            s = r.get("structured") or {}
            h = s.get("spec_key_hash")
            if not h:
                continue
            price = safe_float(r.get("price"))
            if price is None:
                continue
            cat_groups[cat][h].append(price)

    summary_rows = []

    for cat, groups in cat_groups.items():
        sizes = [len(v) for v in groups.values()]
        sizes.sort(reverse=True)

        total_groups = len(sizes)
        total_rows = sum(sizes)
        singletons = sum(1 for x in sizes if x == 1)
        singleton_rate = singletons / total_groups * 100 if total_groups else 0
        top1 = sizes[0] if sizes else 0
        top5_share = sum(sizes[:5]) / total_rows * 100 if total_rows else 0

        summary_rows.append({
            "category": cat,
            "rows_used": total_rows,
            "groups": total_groups,
            "singleton_groups": singletons,
            "singleton_group_rate_pct": round(singleton_rate, 2),
            "top1_group_size": top1,
            "top5_share_pct": round(top5_share, 2),
        })

        # per-category csv
        rows = []
        for h, prices in groups.items():
            if len(prices) < args.min_count:
                continue
            ps = sorted(prices)
            rows.append({
                "category": cat,
                "spec_key_hash": h,
                "count": len(ps),
                "min": int(min(ps)),
                "p25": int(percentile(ps, 0.25)),
                "median": int(median(ps)),
                "mean": int(mean(ps)),
                "p75": int(percentile(ps, 0.75)),
                "max": int(max(ps)),
            })

        rows.sort(key=lambda x: x["count"], reverse=True)
        out_fp = os.path.join(OUT_DIR, f"{cat}.csv")
        with open(out_fp, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=rows[0].keys() if rows else [])
            if rows:
                w.writeheader()
                w.writerows(rows)

    osa = os.path.join(OUT_DIR, "_summary.csv")
    with open(osa, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=summary_rows[0].keys() if summary_rows else [])
        if summary_rows:
            w.writeheader()
            w.writerows(summary_rows)

    print(f"[saved] {OUT_DIR}/_summary.csv")
    print(f"[saved] {OUT_DIR}/<category>.csv")

if __name__ == "__main__":
    main()
