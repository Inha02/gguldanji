import os, glob, json, argparse, hashlib
from typing import Any, Dict, List, Optional, Tuple
from collections import Counter

BASE_DIR = os.path.dirname(__file__)
DATA_DIR = os.path.join(BASE_DIR, "data")
STRUCT_DIR = os.path.join(DATA_DIR, "structured")
SPEC_DIR = os.path.join(DATA_DIR, "spec_key_suggestions")
OUT_DIR = os.path.join(DATA_DIR, "structured_v2")
CFG_DIR = os.path.join(DATA_DIR, "config")
os.makedirs(OUT_DIR, exist_ok=True)
os.makedirs(CFG_DIR, exist_ok=True)

def iter_jsonl(path: str):
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            yield json.loads(line)

def write_jsonl(path: str, rows):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

def load_json(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def safe_str(x: Any) -> Optional[str]:
    if x is None:
        return None
    if isinstance(x, bool):
        return "true" if x else "false"
    if isinstance(x, (int, float)):
        # 숫자는 문자열로(소수는 최대 3자리 정도)
        if isinstance(x, float):
            return f"{x:.3f}".rstrip("0").rstrip(".")
        return str(x)
    s = str(x).strip()
    return s if s else None

def normalize_value(field: str, val: Any) -> Optional[str]:
    """
    v2 해시용 정규화 (너무 공격적으로 추정/변형하지 않음)
    - 문자열: 소문자/공백정리
    - 일부 필드: 구간화(사이즈/연식/용량 등)는 합성 스키마에서 처리, 여기선 최소만.
    """
    s = safe_str(val)
    if s is None:
        return None
    s2 = " ".join(s.split()).lower()

    # 흔한 표기 흔들림만 통일
    if field in ("condition_grade", "condition", "grade"):
        return s2.upper()  # NEW/S/A/B/C 같은 등급은 대문자
    if field.endswith("_gb"):
        # "512 gb" -> "512"
        s2 = s2.replace("gb", "").strip()
        return s2
    if field.endswith("_inch"):
        s2 = s2.replace("inch", "").replace("in", "").replace('"', "").strip()
        return s2
    if "date" in field:
        # date는 v2에는 보통 넣지 않지만 혹시 있으면 원문 유지(정규화 최소)
        return s2
    return s2

def stable_hash_from_kv(kv: List[Tuple[str, str]]) -> str:
    # key 정렬해서 안정적 해시
    kv_sorted = sorted(kv, key=lambda x: x[0])
    raw = "|".join([f"{k}={v}" for k, v in kv_sorted])
    return hashlib.sha1(raw.encode("utf-8")).hexdigest()[:16]

# ---------------------------
# Config: v2 templates
# ---------------------------

DEFAULT_DROP_FIELDS_GLOBAL = {
    # 너무 세분화/민감/가변성이 큰 것들(대부분 v2에서 제외 권장)
    "model_code",
    "serial",
    "serial_number",
    "purchase_date",
    "exact_location",
    "seller_contact",
    "chat_id",
    "account_id",
    "valid_until_date",
    "valid_from_date",
    "event_date",
    "days_to_expiry",
    "warranty_left_months",  # 필요하면 v2에 넣지 말고 합성에서 파생
}

def ensure_default_hash_v2_templates(spec_files: List[str], out_path: str):
    """
    카테고리별 v2 필드 템플릿을 자동 생성해 저장.
    - 원칙: common 위주 + major 1~2개(있으면)
    - 민감/고변동 필드는 drop
    """
    if os.path.exists(out_path):
        return

    cfg = {"version": 1, "drop_fields_global": sorted(list(DEFAULT_DROP_FIELDS_GLOBAL)), "categories": {}}

    for sf in spec_files:
        spec = load_json(sf)
        cat = spec.get("category_name")
        code = spec.get("category_code")
        guidance = (spec.get("downstream") or {}).get("attribute_grouping_guidance") or {}
        common = guidance.get("common") or []
        major = guidance.get("major") or []

        # 자동 선택: common 최대 5개 + major 최대 2개
        fields = []
        for f in common:
            if f in DEFAULT_DROP_FIELDS_GLOBAL:
                continue
            fields.append(f)
            if len(fields) >= 5:
                break

        major_added = 0
        for f in major:
            if f in DEFAULT_DROP_FIELDS_GLOBAL:
                continue
            # 너무 희귀/고변동일 수 있는 것 일부 제외(필요시 나중에 category override로 넣으면 됨)
            if f in ("battery_cycles", "usage_months"):
                continue
            fields.append(f)
            major_added += 1
            if major_added >= 2:
                break

        # 카테고리별 자주 쓰는 대체 필드 보정(없으면 넘어감)
        # (티켓/쿠폰은 model_name 대신 product_name류가 더 적합한 경우가 많음)
        # 여기서는 "있으면"만 추가하고 강제는 안 함.
        cat_spec_fields = {x.get("field") for x in (spec.get("category_spec_fields") or []) if x.get("field")}
        if "product_name" in cat_spec_fields and "product_name" not in fields:
            fields.append("product_name")
        if "merchant_brand" in cat_spec_fields and "merchant_brand" not in fields:
            fields.append("merchant_brand")
        if "publisher_brand" in cat_spec_fields and "publisher_brand" not in fields:
            fields.append("publisher_brand")

        # 중복 제거
        seen = set()
        uniq = []
        for f in fields:
            if f and f not in seen:
                uniq.append(f)
                seen.add(f)

        cfg["categories"][cat] = {
            "category_code": code,
            "hash_v2_fields": uniq[:8],  # 안전하게 8개 제한
            "drop_fields": [],           # 카테고리별 추가 drop(사용자 수정용)
            "notes": "auto-generated; edit if needed"
        }

    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(cfg, f, ensure_ascii=False, indent=2)
    print(f"[saved] {out_path}")

def load_templates() -> dict:
    spec_files = glob.glob(os.path.join(SPEC_DIR, "*.spec_key.json"))
    cfg_path = os.path.join(CFG_DIR, "hash_v2_templates.json")
    ensure_default_hash_v2_templates(spec_files, cfg_path)
    return load_json(cfg_path)

# ---------------------------
# Main
# ---------------------------

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--category", required=True, help="e.g. 01_digital_devices")
    p.add_argument("--keyword", required=True, help="e.g. 갤럭시북")
    p.add_argument("--in-dir", default=STRUCT_DIR)
    p.add_argument("--out-dir", default=OUT_DIR)
    p.add_argument("--inplace", action="store_true", help="overwrite original structured file (not recommended)")
    args = p.parse_args()

    templates = load_templates()
    drop_global = set(templates.get("drop_fields_global") or [])
    cat_cfg = (templates.get("categories") or {}).get(args.category)
    if not cat_cfg:
        raise SystemExit(f"[ERR] category not found in templates: {args.category}")

    v2_fields = cat_cfg.get("hash_v2_fields") or []
    drop_cat = set(cat_cfg.get("drop_fields") or [])

    in_fp = os.path.join(args.in_dir, args.category, f"{args.keyword}_structured.jsonl")
    if not os.path.exists(in_fp):
        raise SystemExit(f"[ERR] not found: {in_fp}")

    out_fp = in_fp if args.inplace else os.path.join(args.out_dir, args.category, f"{args.keyword}_structured_v2.jsonl")

    rows_out = []
    missing_hash = 0
    for r in iter_jsonl(in_fp):
        s = r.get("structured") or {}
        spec = s.get("spec") or {}

        kv = []
        for f in v2_fields:
            if f in drop_global or f in drop_cat:
                continue
            v = normalize_value(f, spec.get(f))
            if v is None:
                continue
            kv.append((f, v))

        if not kv:
            missing_hash += 1
            h2 = None
        else:
            h2 = stable_hash_from_kv(kv)

        # structured 하위에 v2를 추가(원본 보존)
        s["spec_key_hash_v2"] = h2
        s["spec_key_v2_fields"] = v2_fields
        r["structured"] = s
        rows_out.append(r)

    write_jsonl(out_fp, rows_out)
    print(f"[saved] {out_fp} (rows={len(rows_out)}, missing_hash_v2={missing_hash})")

if __name__ == "__main__":
    main()
