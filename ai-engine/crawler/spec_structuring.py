import os
import json
import re
import argparse
import hashlib
from typing import Any, Dict, List, Iterable, Optional, Tuple
from dotenv import load_dotenv

from openai import OpenAI
from tqdm import tqdm

# -----------------------------
# Paths
# -----------------------------
BASE_DIR = os.path.dirname(__file__)
DATA_DIR = os.path.join(BASE_DIR, "data")
PROCESSED_DIR = os.path.join(DATA_DIR, "processed")
SPEC_DIR = os.path.join(DATA_DIR, "spec_key_suggestions")
OUT_DIR = os.path.join(DATA_DIR, "structured")
os.makedirs(OUT_DIR, exist_ok=True)

# -----------------------------
# IO helpers
# -----------------------------
def iter_jsonl(path: str) -> Iterable[Dict[str, Any]]:
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            yield json.loads(line)

def write_jsonl(path: str, rows: Iterable[Dict[str, Any]]):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

def truncate_text(s: Any, max_chars: int) -> str:
    if s is None:
        return ""
    s = str(s).strip()
    return s if len(s) <= max_chars else s[: max_chars - 1] + "…"

def pick_text_fields(row: Dict[str, Any], desc_max_chars: int = 800) -> Dict[str, Any]:
    detail = row.get("detail") or {}
    desc = detail.get("productDescription") or detail.get("contents") or ""
    cat = detail.get("categoryName") or ""
    labels = detail.get("labels") or []
    return {
        "seq": row.get("seq"),
        "title": truncate_text(row.get("title"), 180),
        "description": truncate_text(desc, desc_max_chars),
        "price": row.get("price"),
        "categoryName": truncate_text(cat, 80),
        "labels": labels[:12] if isinstance(labels, list) else labels,
    }

# -----------------------------
# Spec config helpers
# -----------------------------
def load_spec_config(spec_json_path: str) -> Dict[str, Any]:
    with open(spec_json_path, "r", encoding="utf-8") as f:
        return json.load(f)

def build_field_registry(spec_cfg: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    """
    subtype templates + category templates에 등장하는 모든 field를 registry로 만들기.
    (category_spec_fields는 '핵심'이라 전체를 커버 못함 → registry가 필요)
    """
    registry: Dict[str, Dict[str, Any]] = {}

    # 1) seed from category_spec_fields
    for item in spec_cfg.get("category_spec_fields", []):
        field = item["field"]
        registry[field] = {
            "type": item.get("type", "string"),
            "importance": item.get("importance", "medium"),
            "attribute_group_seed": item.get("attribute_group_seed", "common"),
            "extraction_hints": item.get("extraction_hints", []),
        }

    def add_field(field: str):
        if field not in registry:
            registry[field] = {
                "type": "string",
                "importance": "medium",
                "attribute_group_seed": "major",  # 템플릿에 나오면 대개 비교에 중요
                "extraction_hints": [],
            }

    # 2) from category templates
    for t in spec_cfg.get("category_spec_key_templates", []):
        for f in t.get("fields", []):
            add_field(f)

    # 3) from subtype templates
    for t in spec_cfg.get("subtype_spec_key_templates", []):
        for f in t.get("fields", []):
            add_field(f)

    # 4) normalization rules hint
    norm_map = {x["field"]: x["rules"] for x in spec_cfg.get("normalization_rules", [])}
    for f, meta in registry.items():
        if f in norm_map:
            meta["normalization_rules"] = norm_map[f]

    return registry

def choose_subtype_and_template(spec_cfg: Dict[str, Any], device_type: Optional[str]) -> Tuple[Optional[str], Optional[Dict[str, Any]]]:
    """
    device_type(노트북/스마트폰 등)로 subtype 매핑.
    매핑이 애매하면 None 반환 → generic template 사용
    """
    if not device_type:
        return None, None

    dt = device_type.lower()

    # 간단 규칙 매핑 (나중에 json에 매핑 테이블로 승격 가능)
    if "노트북" in device_type or "맥북" in device_type or "laptop" in dt:
        subtype = "laptop_pc"
    elif "본체" in device_type or "데스크탑" in device_type or "pc" in dt:
        subtype = "desktop_pc"
    elif "아이폰" in device_type or "갤럭시" in device_type or "스마트폰" in device_type:
        subtype = "smartphone"
    elif "태블릿" in device_type or "아이패드" in device_type or "전자책" in device_type:
        subtype = "tablet_ebook"
    elif "모니터" in device_type or "tv" in dt or "스탠" in device_type:
        subtype = "monitor_tv"
    elif "이어폰" in device_type or "헤드" in device_type or "스피커" in device_type:
        subtype = "audio_device"
    elif "워치" in device_type or "밴드" in device_type:
        subtype = "wearable"
    elif "공유기" in device_type or "허브" in device_type or "네트워크" in device_type:
        subtype = "network_device"
    elif "키보드" in device_type or "마우스" in device_type:
        subtype = "input_accessory"
    else:
        return None, None

    # subtype template 찾기
    for t in spec_cfg.get("subtype_spec_key_templates", []):
        if t.get("subtype") == subtype:
            return subtype, t
    return subtype, None

def compute_spec_key_hash(template_fields: List[str], spec: Dict[str, Any]) -> str:
    """
    spec_key는 '스펙 동일성'을 위한 키.
    - trade info(상태/거래) 섞이면 같은 스펙인데 키가 달라져서 검색이 깨짐
    그래서 hash는 "스펙 동일성" 필드만으로 만들도록 기본 정책을 둠.
    """
    # spec_key 후보에서 거래/상태 필드는 제외(정책적으로)
    exclude = {
        "condition_grade", "defect_notes", "accessory_included", "is_box_included",
        "is_new", "usage_months", "warranty_left_months", "trade_method", "shipping_fee_included"
    }
    key_fields = [f for f in template_fields if f not in exclude]

    obj = {}
    for f in key_fields:
        v = spec.get(f)
        if v is None or v == "":
            continue
        obj[f] = v

    s = json.dumps(obj, ensure_ascii=False, sort_keys=True)
    return hashlib.sha256(s.encode("utf-8")).hexdigest()[:16]

# -----------------------------
# LLM extraction (Structured Outputs)
# -----------------------------
SYSTEM_EXTRACT = (
    "Extract structured specification fields from Korean used-market post text.\n"
    "Only use information supported by the given title/description/labels.\n"
    "If missing, output null.\n"
    "Keep outputs short.\n"
)

def build_extract_prompt(category_name: str, registry: Dict[str, Dict[str, Any]], fields: List[str], post: Dict[str, Any]) -> str:
    # 필드별 힌트 짧게 붙이기
    hint_lines = []
    for f in fields:
        meta = registry.get(f, {})
        hints = meta.get("extraction_hints", [])
        if hints:
            hint_lines.append(f"- {f}: " + "; ".join(hints[:2]))
    hints_block = "\n".join(hint_lines)

    return f"""
Category: {category_name}

Extract these fields (return null if unknown):
{fields}

Extraction hints (if any):
{hints_block}

Post:
{json.dumps(post, ensure_ascii=False)}
""".strip()

def make_schema_for_fields(fields: List[str]) -> Dict[str, Any]:
    props = {}
    req = []
    for f in fields:
        props[f] = {"type": ["string", "number", "integer", "boolean", "null"]}
        req.append(f)
    return {
        "type": "object",
        "additionalProperties": False,
        "required": req,
        "properties": props
    }

def extract_fields_once(
    client: OpenAI,
    model: str,
    prompt: str,
    schema: Dict[str, Any],
    reasoning_effort: str,
    max_output_tokens: int,
) -> Dict[str, Any]:
    resp = client.responses.create(
        model=model,
        instructions=SYSTEM_EXTRACT,
        input=prompt,
        max_output_tokens=max_output_tokens,
        reasoning={"effort": reasoning_effort},
        text={"format": {"type": "json_schema", "name": "field_extract", "schema": schema, "strict": True}},
    )
    return json.loads(resp.output_text)

# -----------------------------
# Main
# -----------------------------
def main():
    load_dotenv()

    parser = argparse.ArgumentParser()
    parser.add_argument("--spec-json", required=True, help="e.g. data/spec_key_suggestions/01_digital_devices.spec_key.json")
    parser.add_argument("--keyword", required=True, help="processed/<keyword>/<keyword>_final_100.jsonl")
    parser.add_argument("--model", default="gpt-5.1")
    parser.add_argument("--reasoning-effort", default="low", choices=["none", "low", "medium", "high"])
    parser.add_argument("--max-output-tokens", type=int, default=1200)
    args = parser.parse_args()

    spec_json_path = args.spec_json
    if not os.path.isabs(spec_json_path):
        spec_json_path = os.path.join(BASE_DIR, spec_json_path)

    spec_cfg = load_spec_config(spec_json_path)
    category_name = spec_cfg.get("category_name", "category")
    registry = build_field_registry(spec_cfg)

    in_path = os.path.join(PROCESSED_DIR, args.keyword, f"{args.keyword}_final_100.jsonl")
    if not os.path.exists(in_path):
        raise SystemExit(f"[ERR] not found: {in_path}")

    out_path = os.path.join(OUT_DIR, category_name, f"{args.keyword}_structured.jsonl")
    os.makedirs(os.path.dirname(out_path), exist_ok=True)

    client = OpenAI()

    # 기본 템플릿(스펙 동일성용): subtype_core가 있으면 그걸, 없으면 generic_digital_basic 기반
    generic_template = None
    for t in spec_cfg.get("category_spec_key_templates", []):
        if t.get("name") == "generic_digital_basic":
            generic_template = t
            break
    if generic_template is None:
        # fallback
        generic_template = {"name": "generic", "fields": ["device_type", "brand", "model_name"]}

    rows_out = []
    for row in tqdm(iter_jsonl(in_path), desc=f"extract:{args.keyword}", ncols=90):
        if row.get("manual_keep") is not True:
            continue

        post = pick_text_fields(row)

        # 1) 1차: 최소 필드(device_type 등) 먼저 뽑기
        seed_fields = ["device_type", "brand", "series_name", "model_name"]
        seed_schema = make_schema_for_fields(seed_fields)
        seed_prompt = build_extract_prompt(category_name, registry, seed_fields, post)
        seed = extract_fields_once(
            client, args.model, seed_prompt, seed_schema,
            reasoning_effort=args.reasoning_effort, max_output_tokens=min(args.max_output_tokens, 900)
        )

        device_type = seed.get("device_type")
        subtype, subtype_template = choose_subtype_and_template(spec_cfg, device_type)

        # 2) 2차: subtype/core 템플릿 필드 추출
        template = subtype_template if subtype_template else generic_template
        fields = template.get("fields", [])

        # 필드가 너무 많으면 2번에 나눠 추출(토큰 안정화)
        # (많은 템플릿은 15~16개로 안전한데, 혹시 커질 대비)
        chunk_size = 14
        spec: Dict[str, Any] = {}
        for i in range(0, len(fields), chunk_size):
            chunk = fields[i:i+chunk_size]
            schema = make_schema_for_fields(chunk)
            prompt = build_extract_prompt(category_name, registry, chunk, post)
            extracted = extract_fields_once(
                client, args.model, prompt, schema,
                reasoning_effort=args.reasoning_effort, max_output_tokens=args.max_output_tokens
            )
            spec.update(extracted)

        # seed를 우선 반영(없으면 subtype 추출값 유지)
        for k, v in seed.items():
            if v is not None and v != "":
                spec[k] = v

        # 3) attribute groups (seed 기반)
        grouping = spec_cfg.get("downstream", {}).get("attribute_grouping_guidance", {})
        common = set(grouping.get("common", []))
        major = set(grouping.get("major", []))
        sensitive = set(grouping.get("sensitive", []))

        attr_groups = {"common": {}, "major": {}, "sensitive": {}, "other": {}}
        for k, v in spec.items():
            if k in sensitive:
                attr_groups["sensitive"][k] = v
            elif k in major:
                attr_groups["major"][k] = v
            elif k in common:
                attr_groups["common"][k] = v
            else:
                attr_groups["other"][k] = v

        # 4) spec_key_hash (상태/거래 제외한 동일스펙용)
        spec_key_hash = compute_spec_key_hash(fields, spec)

        # 5) row에 structured 추가
        out_row = dict(row)
        out_row["structured"] = {
            "category_name": category_name,
            "subtype": subtype,
            "template_name": template.get("template_name") or template.get("name"),
            "spec": spec,
            "attribute_groups": attr_groups,
            "spec_key_hash": spec_key_hash,
        }
        rows_out.append(out_row)

    write_jsonl(out_path, rows_out)
    print(f"[saved] {out_path}")

if __name__ == "__main__":
    main()
