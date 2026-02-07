import os, glob, json, argparse, csv, random
from collections import defaultdict, Counter
from statistics import median

BASE_DIR = os.path.dirname(__file__)
DATA_DIR = os.path.join(BASE_DIR, "data")
IN_DIR = os.path.join(DATA_DIR, "structured_v2")
CFG_DIR = os.path.join(DATA_DIR, "config")
OUT_ROOT = os.path.join(DATA_DIR, "synthetic")
os.makedirs(OUT_ROOT, exist_ok=True)

def iter_jsonl(path: str):
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            yield json.loads(line)

def load_json(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def safe_float(x):
    try:
        if x is None:
            return None
        return float(x)
    except Exception:
        return None

def choose_weighted(items, weights):
    # items: list, weights: list of float
    total = sum(weights)
    if total <= 0:
        return random.choice(items)
    r = random.random() * total
    upto = 0.0
    for it, w in zip(items, weights):
        upto += w
        if upto >= r:
            return it
    return items[-1]

def clamp(x, lo, hi):
    return max(lo, min(hi, x))

def build_group_stats(rows, hash_key: str):
    """
    rows: structured rows list
    returns:
      groups[hash] = dict(count, prices(list), field_value_counters)
    """
    groups = {}
    cat_prices = []

    for r in rows:
        price = safe_float(r.get("price"))
        if price is None:
            continue
        s = r.get("structured") or {}
        h = s.get(hash_key)
        if not h:
            continue
        spec = s.get("spec") or {}

        if h not in groups:
            groups[h] = {"prices": [], "count": 0, "spec_samples": []}
        groups[h]["prices"].append(price)
        groups[h]["count"] += 1
        groups[h]["spec_samples"].append(spec)

        cat_prices.append(price)

    cat_prices.sort()
    return groups, cat_prices

def sample_price_from_group(prices: list, mode: str):
    """
    간단하지만 안정적인 가격 샘플링:
    - group median 중심으로 ±(p75-p25) 범위 내에서 샘플링(관측치 기반)
    """
    if not prices:
        return None
    ps = sorted(prices)
    m = median(ps)
    lo, hi = ps[0], ps[-1]

    if len(ps) >= 4:
        p25 = ps[int((len(ps)-1)*0.25)]
        p75 = ps[int((len(ps)-1)*0.75)]
        spread = max(1.0, p75 - p25)
        # training은 보수적으로, demo는 조금 더 퍼지게
        factor = 0.6 if mode == "training" else 0.9
        x = random.uniform(m - factor*spread, m + factor*spread)
        x = clamp(x, lo, hi)
        return int(round(x))
    else:
        # 표본 적으면 관측치 중 랜덤
        return int(round(random.choice(ps)))

def build_vocab(rows, fields: list):
    vocab = {f: Counter() for f in fields}
    for r in rows:
        spec = (r.get("structured") or {}).get("spec") or {}
        for f in fields:
            v = spec.get(f)
            if v is None or v == "":
                continue
            vocab[f][str(v)] += 1
    return vocab

def sample_spec_from_group(spec_samples: list, synth_fields: list, vocab: dict, mode: str):
    """
    spec_samples: 실제 그룹 내 spec dict 리스트
    - training: 그룹 샘플에서 그대로 하나 뽑아서 필드만 취함
    - demo: 그룹 샘플 기반 + 일부 필드를 vocab에서 확률적으로 대체(다양화)
    """
    if not spec_samples:
        base = {}
    else:
        base = random.choice(spec_samples)

    out = {}
    for f in synth_fields:
        v = base.get(f)
        if v is None or v == "":
            # 그룹에 없으면 카테고리 vocab에서 샘플
            cnt = vocab.get(f) or Counter()
            if cnt:
                keys = list(cnt.keys())
                weights = list(cnt.values())
                out[f] = choose_weighted(keys, weights)
            else:
                out[f] = None
        else:
            out[f] = v

    if mode == "demo":
        # 10% 확률로 몇 개 필드 다양화
        for f in synth_fields:
            if random.random() < 0.10:
                cnt = vocab.get(f) or Counter()
                if cnt:
                    keys = list(cnt.keys())
                    weights = list(cnt.values())
                    out[f] = choose_weighted(keys, weights)
    return out

def flatten_spec(spec: dict):
    flat = {}
    for k, v in spec.items():
        if isinstance(v, (dict, list)):
            flat[k] = json.dumps(v, ensure_ascii=False)
        else:
            flat[k] = v
    return flat

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--category", required=True, help="e.g. 01_digital_devices")
    p.add_argument("--mode", default="training", choices=["training", "demo"])
    p.add_argument("--hash", default="v2", choices=["v1", "v2"])
    p.add_argument("--n", type=int, default=2000, help="synthetic rows per category")
    p.add_argument("--seed", type=int, default=42)
    args = p.parse_args()

    random.seed(args.seed)

    schema_path = os.path.join(CFG_DIR, "synth_schema.json")
    if not os.path.exists(schema_path):
        raise SystemExit("[ERR] synth_schema.json not found. Run build_synth_schema.py first.")

    schema = load_json(schema_path)
    cat_cfg = (schema.get("categories") or {}).get(args.category)
    if not cat_cfg:
        raise SystemExit(f"[ERR] category not in synth_schema.json: {args.category}")

    synth_fields = cat_cfg.get("synth_fields") or []
    if not (6 <= len(synth_fields) <= 10):
        print(f"[WARN] synth_fields count is {len(synth_fields)} (recommended 6~8).")

    # load rows for category
    files = sorted(glob.glob(os.path.join(IN_DIR, args.category, "*_structured_v2.jsonl")))
    if not files:
        raise SystemExit(f"[ERR] no structured_v2 files for category: {args.category}")

    rows = []
    for fp in files:
        for r in iter_jsonl(fp):
            rows.append(r)

    hash_key = "spec_key_hash_v2" if args.hash == "v2" else "spec_key_hash"
    groups, cat_prices = build_group_stats(rows, hash_key=hash_key)
    if not groups:
        raise SystemExit(f"[ERR] no groups found (hash={hash_key}). maybe run run_all_hash_v2.py first?")

    # group sampling weights
    group_ids = list(groups.keys())
    weights = [groups[g]["count"] for g in group_ids]

    # build vocab for fallback fill
    vocab = build_vocab(rows, synth_fields)

    out_mode_dir = os.path.join(OUT_ROOT, args.mode)
    os.makedirs(out_mode_dir, exist_ok=True)
    out_csv = os.path.join(out_mode_dir, f"{args.category}.csv")
    out_jsonl = os.path.join(out_mode_dir, f"{args.category}.jsonl")

    # write
    with open(out_csv, "w", newline="", encoding="utf-8") as fcsv, open(out_jsonl, "w", encoding="utf-8") as fjs:
        # header
        fieldnames = ["item_id", "category_name", "category_code", "spec_key_hash", "hash_version", "used_price"] + synth_fields
        w = csv.DictWriter(fcsv, fieldnames=fieldnames)
        w.writeheader()

        for i in range(args.n):
            gid = choose_weighted(group_ids, weights)
            g = groups[gid]
            spec = sample_spec_from_group(g["spec_samples"], synth_fields, vocab, mode=args.mode)
            price = sample_price_from_group(g["prices"], mode=args.mode)
            if price is None and cat_prices:
                price = int(round(random.choice(cat_prices)))
            if price is None:
                price = 0

            row = {
                "item_id": f"{args.category}-{args.mode}-{i:06d}",
                "category_name": args.category,
                "category_code": cat_cfg.get("category_code"),
                "spec_key_hash": gid,
                "hash_version": args.hash,
                "used_price": price,
            }
            for f in synth_fields:
                row[f] = spec.get(f)

            w.writerow(row)
            fjs.write(json.dumps(row, ensure_ascii=False) + "\n")

    print(f"[saved] {out_csv}")
    print(f"[saved] {out_jsonl}")

if __name__ == "__main__":
    main()
