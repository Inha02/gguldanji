import os, glob, json, argparse
from collections import Counter

BASE_DIR = os.path.dirname(__file__)
DATA_DIR = os.path.join(BASE_DIR, "data")
SPEC_DIR = os.path.join(DATA_DIR, "spec_key_suggestions")
CFG_DIR = os.path.join(DATA_DIR, "config")
os.makedirs(CFG_DIR, exist_ok=True)

DEFAULT_EXCLUDE = {
    "seller_contact", "exact_location", "chat_id", "account_id",
    "purchase_date", "serial", "serial_number",
    # 합성에서는 파생/정책으로 처리하는 편이 나은 것들
    "valid_until_date", "valid_from_date", "event_date", "days_to_expiry",
}

def load_json(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def save_json(path: str, obj: dict):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--target-fields", type=int, default=8, help="6~8 추천, 기본 8")
    args = p.parse_args()

    spec_files = sorted(glob.glob(os.path.join(SPEC_DIR, "*.spec_key.json")))
    if not spec_files:
        raise SystemExit("[ERR] no spec_key.json found")

    out = {"version": 1, "target_fields": args.target_fields, "exclude": sorted(list(DEFAULT_EXCLUDE)), "categories": {}}

    for sf in spec_files:
        spec = load_json(sf)
        cat = spec.get("category_name")
        code = spec.get("category_code")
        guidance = (spec.get("downstream") or {}).get("attribute_grouping_guidance") or {}
        common = guidance.get("common") or []
        major = guidance.get("major") or []
        sensitive = set(guidance.get("sensitive") or [])

        fields = []
        # 1) common에서 우선 채움
        for f in common:
            if f in DEFAULT_EXCLUDE or f in sensitive:
                continue
            fields.append(f)
            if len(fields) >= args.target_fields:
                break

        # 2) 부족하면 major에서 채움
        if len(fields) < args.target_fields:
            for f in major:
                if f in DEFAULT_EXCLUDE or f in sensitive:
                    continue
                if f not in fields:
                    fields.append(f)
                if len(fields) >= args.target_fields:
                    break

        out["categories"][cat] = {
            "category_code": code,
            "synth_fields": fields[:args.target_fields],
            "drop_sensitive": True,
            "notes": "auto-generated; edit synth_fields per category if needed"
        }

    out_path = os.path.join(CFG_DIR, "synth_schema.json")
    save_json(out_path, out)
    print(f"[saved] {out_path}")
    print("Edit per-category synth_fields to 6~8 high-impact fields if needed.")

if __name__ == "__main__":
    main()
