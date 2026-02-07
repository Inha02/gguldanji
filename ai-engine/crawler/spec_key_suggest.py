import os
import json
import argparse
from typing import Any, Dict, List, Iterable, Optional
from dotenv import load_dotenv

from openai import OpenAI
from tqdm import tqdm

# -----------------------------
# Paths
# -----------------------------
BASE_DIR = os.path.dirname(__file__)
DATA_DIR = os.path.join(BASE_DIR, "data")
PROCESSED_DIR = os.path.join(DATA_DIR, "processed")
OUT_DIR = os.path.join(DATA_DIR, "spec_key_suggestions")
os.makedirs(OUT_DIR, exist_ok=True)

# -----------------------------
# Helpers
# -----------------------------
def read_anchors(anchor_file: str) -> List[str]:
    anchors: List[str] = []
    with open(anchor_file, "r", encoding="utf-8") as f:
        for line in f:
            s = line.strip()
            if not s or s.startswith("#"):
                continue
            anchors.append(s)
    # unique keep order
    seen = set()
    uniq = []
    for a in anchors:
        if a not in seen:
            uniq.append(a)
            seen.add(a)
    return uniq

def iter_jsonl(path: str) -> Iterable[Dict[str, Any]]:
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            yield json.loads(line)

def truncate_text(s: Any, max_chars: int) -> str:
    if s is None:
        return ""
    s = str(s).strip()
    return s if len(s) <= max_chars else s[: max_chars - 1] + "…"

def pick_text_fields(row: Dict[str, Any], desc_max_chars: int = 450) -> Dict[str, Any]:
    detail = row.get("detail") or {}
    desc = detail.get("productDescription") or detail.get("contents") or ""
    cat = detail.get("categoryName") or ""
    labels = detail.get("labels") or []
    return {
        "seq": row.get("seq"),
        "title": truncate_text(row.get("title"), 120),
        "description": truncate_text(desc, desc_max_chars),
        "price": row.get("price"),
        "categoryName": truncate_text(cat, 60),
        "labels": labels[:8] if isinstance(labels, list) else labels,
    }

def load_anchor_samples(keyword: str, sample_n: int = 100, desc_max_chars: int = 450) -> List[Dict[str, Any]]:
    fp = os.path.join(PROCESSED_DIR, keyword, f"{keyword}_final_100.jsonl")
    if not os.path.exists(fp):
        raise FileNotFoundError(f"not found: {fp}")

    rows: List[Dict[str, Any]] = []
    for r in iter_jsonl(fp):
        if r.get("manual_keep") is True:
            rows.append(pick_text_fields(r, desc_max_chars=desc_max_chars))
    return rows[:sample_n]

def anchor_file_basename(anchor_file: str) -> str:
    return os.path.splitext(os.path.basename(anchor_file))[0]

def category_code_from_anchor_file(anchor_file: str) -> str:
    base = anchor_file_basename(anchor_file)
    if len(base) >= 2 and base[:2].isdigit():
        return base[:2]
    return base

def extract_outer_json(text: str) -> str:
    """
    output_text가 깨지거나 앞뒤에 다른 텍스트가 붙는 경우 대비:
    가장 바깥 { ... } 구간만 잘라서 반환
    """
    if not text:
        return ""
    text = text.strip()
    if text.startswith("{") and text.endswith("}"):
        return text
    first = text.find("{")
    last = text.rfind("}")
    if first != -1 and last != -1 and last > first:
        return text[first:last + 1]
    return text

def save_debug(category_name: str, raw_text: str, suffix: str) -> str:
    fp = os.path.join(OUT_DIR, f"{category_name}.DEBUG{suffix}.txt")
    with open(fp, "w", encoding="utf-8") as f:
        f.write(raw_text or "")
    return fp

# -----------------------------
# Prompt
# -----------------------------
SYSTEM = (
    "You are a data architect for a second-hand marketplace pricing assistant.\n"
    "Design a practical spec_key system for fair price comparison in Korean used-market posts.\n"
    "Return output strictly following the JSON Schema.\n"
    "\n"
    "CRITICAL BREVITY RULES:\n"
    "- Keep every string short.\n"
    "- examples: 1~2 items per field.\n"
    "- extraction_hints: 2~3 hints max per field.\n"
    "- category_item_coverage: 8~12 items.\n"
    "- subtypes: 5~9 items.\n"
    "- normalization_rules: 5~10 rules total.\n"
    "- missing_but_important_specs: 3~6 items.\n"
    "- Do not write long paragraphs.\n"
)

def build_user_prompt(
    category_code: str,
    category_name: str,
    anchor_keywords: List[str],
    payload: Dict[str, Any],
) -> str:
    return f"""
We are building a pricing assistant for used items.
Category code: {category_code}
Category name: {category_name}
Anchor keywords (representative only): {anchor_keywords}

IMPORTANT:
- Anchors are only representative examples. The category can include other item types beyond anchors.
  Example: in 01_digital_devices, besides anchors, there could be: 헤드셋, 맥북, 스탠바이미, 모니터, 태블릿, 스피커, 스마트워치, 공유기, 키보드/마우스 등.
- Therefore propose spec fields and spec_key templates that generalize to the whole category, not only anchors.

Downstream constraints:
- Later an LLM will extract these fields per post.
- Then we will group fields into 3 attribute groups for UI & synthetic data:
  common / major / sensitive
- Output must be concise enough to fit within token limits.

Data payload:
{json.dumps(payload, ensure_ascii=False)}
""".strip()

# -----------------------------
# JSON Schema (Structured Outputs)
# -----------------------------
SPEC_KEY_SCHEMA: Dict[str, Any] = {
    "type": "object",
    "additionalProperties": False,
    "required": [
        "category_code",
        "category_name",
        "category_item_coverage",
        "category_spec_fields",
        "category_spec_key_templates",
        "subtypes",
        "subtype_spec_key_templates",
        "normalization_rules",
        "missing_but_important_specs",
        "anchor_overrides",
        "downstream",
    ],
    "properties": {
        "category_code": {"type": "string"},
        "category_name": {"type": "string"},

        "category_item_coverage": {"type": "array", "items": {"type": "string"}, "minItems": 5},

        "category_spec_fields": {
            "type": "array",
            "minItems": 5,
            "maxItems": 10,
            "items": {
                "type": "object",
                "additionalProperties": False,
                "required": ["field", "importance", "type", "examples", "extraction_hints", "attribute_group_seed"],
                "properties": {
                    "field": {"type": "string"},
                    "importance": {"type": "string", "enum": ["high", "medium", "low"]},
                    "type": {"type": "string", "enum": ["string", "int", "float", "enum", "bool"]},
                    "examples": {"type": "array", "items": {"type": "string"}, "minItems": 1},
                    "extraction_hints": {"type": "array", "items": {"type": "string"}, "minItems": 1},
                    "attribute_group_seed": {"type": "string", "enum": ["common", "major", "sensitive"]},
                },
            },
        },

        "category_spec_key_templates": {
            "type": "array",
            "minItems": 1,
            "maxItems": 3,
            "items": {
                "type": "object",
                "additionalProperties": False,
                "required": ["name", "fields", "rationale"],
                "properties": {
                    "name": {"type": "string"},
                    "fields": {"type": "array", "items": {"type": "string"}, "minItems": 2},
                    "rationale": {"type": "string"},
                },
            },
        },

        "subtypes": {
            "type": "array",
            "minItems": 3,
            "items": {
                "type": "object",
                "additionalProperties": False,
                "required": ["subtype", "examples", "notes"],
                "properties": {
                    "subtype": {"type": "string"},
                    "examples": {"type": "array", "items": {"type": "string"}, "minItems": 1},
                    "notes": {"type": "string"},
                },
            },
        },

        "subtype_spec_key_templates": {
            "type": "array",
            "minItems": 1,
            "items": {
                "type": "object",
                "additionalProperties": False,
                "required": ["subtype", "template_name", "fields", "rationale"],
                "properties": {
                    "subtype": {"type": "string"},
                    "template_name": {"type": "string"},
                    "fields": {"type": "array", "items": {"type": "string"}, "minItems": 2},
                    "rationale": {"type": "string"},
                },
            },
        },

        "normalization_rules": {
            "type": "array",
            "minItems": 3,
            "items": {
                "type": "object",
                "additionalProperties": False,
                "required": ["field", "rules"],
                "properties": {
                    "field": {"type": "string"},
                    "rules": {"type": "array", "items": {"type": "string"}, "minItems": 1},
                },
            },
        },

        "anchor_overrides": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "required": ["anchor", "additional_fields", "preferred_template", "notes"],
                "properties": {
                    "anchor": {"type": "string"},
                    "additional_fields": {"type": "array", "items": {"type": "string"}},
                    "preferred_template": {"type": "string"},
                    "notes": {"type": "string"},
                },
            },
        },

        "missing_but_important_specs": {
            "type": "array",
            "minItems": 3,
            "items": {
                "type": "object",
                "additionalProperties": False,
                "required": ["field", "why_important", "how_to_capture"],
                "properties": {
                    "field": {"type": "string"},
                    "why_important": {"type": "string"},
                    "how_to_capture": {"type": "string"},
                },
            },
        },

        "downstream": {
            "type": "object",
            "additionalProperties": False,
            "required": ["attribute_grouping_guidance", "extraction_policy", "synthetic_data_policy"],
            "properties": {
                "attribute_grouping_guidance": {
                    "type": "object",
                    "additionalProperties": False,
                    "required": ["common", "major", "sensitive", "notes"],
                    "properties": {
                        "common": {"type": "array", "items": {"type": "string"}},
                        "major": {"type": "array", "items": {"type": "string"}},
                        "sensitive": {"type": "array", "items": {"type": "string"}},
                        "notes": {"type": "string"},
                    },
                },
                "extraction_policy": {
                    "type": "object",
                    "additionalProperties": False,
                    "required": ["missing_value_strategy", "confidence_strategy", "conflict_strategy"],
                    "properties": {
                        "missing_value_strategy": {"type": "string"},
                        "confidence_strategy": {"type": "string"},
                        "conflict_strategy": {"type": "string"},
                    },
                },
                "synthetic_data_policy": {
                    "type": "object",
                    "additionalProperties": False,
                    "required": ["value_ranges", "avoid_leakage_fields", "generation_notes"],
                    "properties": {
                        "value_ranges": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "additionalProperties": False,
                                "required": ["field", "range_or_vocab"],
                                "properties": {
                                    "field": {"type": "string"},
                                    "range_or_vocab": {"type": "string"},
                                },
                            },
                        },
                        "avoid_leakage_fields": {"type": "array", "items": {"type": "string"}},
                        "generation_notes": {"type": "string"},
                    },
                },
            },
        },
    },
}

def call_llm_structured_with_retries(
    client: OpenAI,
    model: str,
    category_name: str,
    user_prompt: str,
    reasoning_effort: str = "low",
    max_output_tokens: int = 8000,
    retries: int = 2,
) -> Dict[str, Any]:
    last_err: Optional[Exception] = None

    for attempt in range(retries + 1):
        try:
            resp = client.responses.create(
                model=model,
                instructions=SYSTEM,
                input=user_prompt,
                max_output_tokens=max_output_tokens,
                reasoning={"effort": reasoning_effort},
                text={
                    "format": {
                        "type": "json_schema",
                        "name": "spec_key_suggestion",
                        "schema": SPEC_KEY_SCHEMA,
                        "strict": True,
                    }
                },
            )

            raw = resp.output_text or ""
            # 1) 그대로 파싱 시도
            try:
                return json.loads(raw)
            except Exception:
                # 2) 바깥 JSON만 추출해서 재시도
                clipped = extract_outer_json(raw)
                return json.loads(clipped)

        except Exception as e:
            last_err = e
            # debug 저장
            try:
                raw_txt = ""
                if "resp" in locals():
                    raw_txt = resp.output_text or ""
                debug_path = save_debug(category_name, raw_txt, suffix=f".attempt{attempt}")
                print(f"[WARN] saved debug to: {debug_path}")
            except Exception:
                pass

            # 다음 시도에서 더 보수적으로(출력 늘리거나, reasoning 낮추기)
            # output이 잘린 케이스가 많으니 tokens를 단계적으로 올림
            max_output_tokens = int(max_output_tokens * 1.25)

    raise RuntimeError(f"LLM call failed after retries. last_error={last_err}")

# -----------------------------
# Main
# -----------------------------
def main():
    load_dotenv()

    parser = argparse.ArgumentParser()
    parser.add_argument("--anchor-file", required=True, help="e.g. data/anchors/01_digital_devices.txt")
    parser.add_argument("--model", default="gpt-5.1", help="e.g. gpt-5.1")
    parser.add_argument("--sample-n", type=int, default=100, help="rows per anchor to send")
    parser.add_argument("--max-anchors", type=int, default=2, help="use only first N anchors (default: 2)")
    parser.add_argument("--desc-max-chars", type=int, default=450, help="max chars for description per sample")
    parser.add_argument("--reasoning-effort", default="low", choices=["none", "low", "medium", "high"])
    parser.add_argument("--max-output-tokens", type=int, default=8000, help="cap model output tokens")
    parser.add_argument("--retries", type=int, default=2, help="retry count on parse/truncation errors")
    args = parser.parse_args()

    anchor_file = args.anchor_file
    if not os.path.isabs(anchor_file):
        anchor_file = os.path.join(BASE_DIR, anchor_file)
    if not os.path.exists(anchor_file):
        raise SystemExit(f"[ERR] anchor file not found: {anchor_file}")

    anchors_all = read_anchors(anchor_file)
    if not anchors_all:
        raise SystemExit(f"[ERR] empty anchor file: {anchor_file}")

    anchors = anchors_all[: max(1, args.max_anchors)]

    category_code = category_code_from_anchor_file(anchor_file)
    category_name = os.path.splitext(os.path.basename(anchor_file))[0]

    payload: Dict[str, Any] = {"anchors": {}}
    print(f"[OK] category={category_name} anchors(all)={anchors_all}")
    print(f"[OK] using anchors={anchors} (max_anchors={args.max_anchors})")

    for kw in tqdm(anchors, desc="load", ncols=90):
        samples = load_anchor_samples(
            kw,
            sample_n=args.sample_n,
            desc_max_chars=args.desc_max_chars,
        )
        if not samples:
            print(f"[WARN] no samples found for anchor={kw} (manual_keep=True).")
        payload["anchors"][kw] = samples

    client = OpenAI()
    user_prompt = build_user_prompt(category_code, category_name, anchors, payload)

    out = call_llm_structured_with_retries(
        client=client,
        model=args.model,
        category_name=category_name,
        user_prompt=user_prompt,
        reasoning_effort=args.reasoning_effort,
        max_output_tokens=args.max_output_tokens,
        retries=args.retries,
    )

    out_path = os.path.join(OUT_DIR, f"{category_name}.spec_key.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)

    print(f"[saved] {out_path}")

if __name__ == "__main__":
    main()
