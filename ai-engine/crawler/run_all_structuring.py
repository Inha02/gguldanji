import os
import glob
import json
import argparse
import subprocess
from typing import Dict, Any, List, Tuple, Optional

from dotenv import load_dotenv
from openai import OpenAI

BASE_DIR = os.path.dirname(__file__)
DATA_DIR = os.path.join(BASE_DIR, "data")
PROCESSED_DIR = os.path.join(DATA_DIR, "processed")
SPEC_DIR = os.path.join(DATA_DIR, "spec_key_suggestions")

def iter_jsonl(path: str):
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            yield json.loads(line)

def truncate(s: Any, n: int) -> str:
    if s is None:
        return ""
    s = str(s).strip()
    return s if len(s) <= n else s[: n - 1] + "…"

def pick_post_min(row: Dict[str, Any], desc_max_chars: int = 450) -> Dict[str, Any]:
    detail = row.get("detail") or {}
    desc = detail.get("productDescription") or detail.get("contents") or ""
    cat = detail.get("categoryName") or ""
    labels = detail.get("labels") or []
    return {
        "title": truncate(row.get("title"), 140),
        "description": truncate(desc, desc_max_chars),
        "categoryName": truncate(cat, 60),
        "labels": labels[:8] if isinstance(labels, list) else labels,
        "price": row.get("price"),
    }

def load_spec_configs() -> List[Dict[str, Any]]:
    files = sorted(glob.glob(os.path.join(SPEC_DIR, "*.spec_key.json")))
    if not files:
        raise SystemExit(f"[ERR] No spec_key json found in {SPEC_DIR}. Run run_all_spec_key.py first.")

    cfgs = []
    for fp in files:
        with open(fp, "r", encoding="utf-8") as f:
            data = json.load(f)
        data["_path"] = fp
        cfgs.append(data)
    return cfgs

def discover_keywords() -> List[Tuple[str, str]]:
    """
    returns list of (keyword, final_100_path)
    expects: data/processed/<keyword>/<keyword>_final_100.jsonl
    """
    keywords = []
    if not os.path.exists(PROCESSED_DIR):
        raise SystemExit(f"[ERR] processed dir not found: {PROCESSED_DIR}")

    for kw_dir in sorted(os.listdir(PROCESSED_DIR)):
        full_dir = os.path.join(PROCESSED_DIR, kw_dir)
        if not os.path.isdir(full_dir):
            continue
        fp = os.path.join(full_dir, f"{kw_dir}_final_100.jsonl")
        if os.path.exists(fp):
            keywords.append((kw_dir, fp))
    return keywords

# ---------- LLM classification (keyword -> category spec) ----------

CLASSIFY_SCHEMA: Dict[str, Any] = {
    "type": "object",
    "additionalProperties": False,
    "required": ["category_name", "category_code", "confidence", "reason"],
    "properties": {
        "category_name": {"type": "string"},
        "category_code": {"type": "string"},
        "confidence": {"type": "string", "enum": ["high", "medium", "low"]},
        "reason": {"type": "string"},
    }
}

SYSTEM_CLASSIFY = (
    "You are classifying a used-item keyword dataset into one of the provided categories.\n"
    "Choose the BEST matching category based on the sample posts.\n"
    "Return strictly valid JSON following the schema.\n"
    "Keep 'reason' short.\n"
)

def summarize_categories_for_prompt(spec_cfgs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    out = []
    for c in spec_cfgs:
        out.append({
            "category_code": c.get("category_code"),
            "category_name": c.get("category_name"),
            "coverage": (c.get("category_item_coverage") or [])[:12],
            "subtypes": [x.get("subtype") for x in (c.get("subtypes") or [])][:12],
        })
    return out

def classify_keyword_to_category(
    client: OpenAI,
    model: str,
    reasoning_effort: str,
    spec_cfgs: List[Dict[str, Any]],
    keyword: str,
    posts: List[Dict[str, Any]],
    max_output_tokens: int = 400
) -> Dict[str, Any]:
    cats = summarize_categories_for_prompt(spec_cfgs)
    prompt = f"""
Keyword folder: {keyword}

Available categories:
{json.dumps(cats, ensure_ascii=False)}

Sample posts:
{json.dumps(posts, ensure_ascii=False)}

Pick the best category among 'Available categories'.
""".strip()

    resp = client.responses.create(
        model=model,
        instructions=SYSTEM_CLASSIFY,
        input=prompt,
        max_output_tokens=max_output_tokens,
        reasoning={"effort": reasoning_effort},
        text={"format": {"type": "json_schema", "name": "category_classify", "schema": CLASSIFY_SCHEMA, "strict": True}},
    )
    return json.loads(resp.output_text)

def find_spec_path(spec_cfgs: List[Dict[str, Any]], category_name: str, category_code: str) -> Optional[str]:
    for c in spec_cfgs:
        if c.get("category_name") == category_name:
            return c["_path"]
    # fallback by code
    for c in spec_cfgs:
        if str(c.get("category_code")) == str(category_code):
            return c["_path"]
    return None

def output_exists(category_name: str, keyword: str) -> bool:
    out_path = os.path.join(DATA_DIR, "structured", category_name, f"{keyword}_structured.jsonl")
    return os.path.exists(out_path)

def run_cmd(cmd: List[str]) -> int:
    print("\n$ " + " ".join(cmd))
    return subprocess.call(cmd)

def main():
    load_dotenv()

    p = argparse.ArgumentParser()
    p.add_argument("--model", default="gpt-5.1")
    p.add_argument("--reasoning-effort", default="low", choices=["none", "low", "medium", "high"])
    p.add_argument("--classify-samples", type=int, default=6, help="how many posts to sample for category classification")
    p.add_argument("--max-keywords", type=int, default=0, help="0 means all")
    p.add_argument("--skip-existing", action="store_true")
    p.add_argument("--dry-run", action="store_true")
    args = p.parse_args()

    spec_cfgs = load_spec_configs()
    keywords = discover_keywords()

    if args.max_keywords and args.max_keywords > 0:
        keywords = keywords[:args.max_keywords]

    print(f"[OK] spec configs: {len(spec_cfgs)}")
    print(f"[OK] keywords discovered: {len(keywords)}")

    client = OpenAI()

    for keyword, fp in keywords:
        # (optional) skip if already structured (but we don't know category yet -> check after classify)
        # load sample posts for classification
        posts = []
        for r in iter_jsonl(fp):
            if r.get("manual_keep") is True:
                posts.append(pick_post_min(r))
            if len(posts) >= args.classify_samples:
                break

        if not posts:
            print(f"[SKIP] {keyword}: no manual_keep=True posts found.")
            continue

        # 1) classify keyword -> category
        cls = classify_keyword_to_category(
            client=client,
            model=args.model,
            reasoning_effort=args.reasoning_effort,
            spec_cfgs=spec_cfgs,
            keyword=keyword,
            posts=posts,
        )
        cat_name = cls["category_name"]
        cat_code = cls["category_code"]
        spec_path = find_spec_path(spec_cfgs, cat_name, cat_code)

        if not spec_path:
            print(f"[WARN] {keyword}: could not map to spec json. cls={cls}")
            continue

        if args.skip_existing and output_exists(cat_name, keyword):
            print(f"[SKIP] {keyword}: output already exists for category={cat_name}")
            continue

        print(f"[MAP] {keyword} -> {cat_name} (code={cat_code}, conf={cls['confidence']}) reason={cls['reason']}")

        # 2) run structuring
        cmd = [
            "python", "spec_structuring.py",
            "--spec-json", os.path.relpath(spec_path, BASE_DIR),
            "--keyword", keyword,
            "--model", args.model,
            "--reasoning-effort", args.reasoning_effort,
        ]

        if args.dry_run:
            print("\n$ " + " ".join(cmd))
            continue

        rc = run_cmd(cmd)
        if rc != 0:
            print(f"[ERR] structuring failed: keyword={keyword}, category={cat_name}, exit={rc}")
            # 계속 진행(전체 배치 중단 방지)
            continue

    print("\n[DONE] All structuring runs finished.")

if __name__ == "__main__":
    main()
