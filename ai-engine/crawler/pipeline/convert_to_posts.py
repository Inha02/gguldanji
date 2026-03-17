"""
합성 데이터 → 게시글 데이터 변환 스크립트 (LLM 스타일 변형 포함)
================================================================
final/ 폴더의 JSONL 파일을 게시글 DB 스키마로 1:1 변환한다.
각 게시글의 제목과 설명을 LLM을 이용해 다양한 작성 스타일로 생성한다.

실행:
  python -m crawler.pipeline.convert_to_posts --input ./crawler/data/final --output ./crawler/data/posts

옵션:
  --no-llm          LLM 스타일 변형 없이 원본 그대로 변환 (테스트용)
  --batch-size 20   LLM 배치 크기 (기본 20건씩 한 번에 요청)
  --delay 0.5       API 호출 간 딜레이 (초)

필요 패키지:
  pip install openai python-dotenv
"""

import argparse
import json
import hashlib
import re
import random
import time
from pathlib import Path
from datetime import datetime

from dotenv import load_dotenv
from openai import OpenAI

# .env 로드
BASE_DIR = Path(__file__).resolve().parent.parent
ENV_PATH = BASE_DIR.parent / ".env"
load_dotenv(ENV_PATH)

client = OpenAI()

# ── 작성 스타일 풀 ──
WRITING_STYLES = [
    "반말 캐주얼 (친구한테 말하듯, ~요 없이, 이모티콘 가끔 사용, 줄임말 사용)",
    "존댓말 정중 (깔끔하고 예의 바른 톤, ~합니다/~입니다 체)",
    "짧고 간결 (핵심만 나열, 문장 최소화, 슬래시나 쉼표로 구분)",
    "상세 나열 (항목별로 정리, 콜론이나 하이픈으로 구분, 꼼꼼한 스타일)",
    "열정적 판매 (빨리 팔고 싶은 느낌, 강조 표현, 급처 느낌)",
    "담담한 톤 (감정 없이 사실만 나열, 건조한 스타일)",
    "친근한 수다 (일상 대화체, 구매자에게 말 거는 듯한 톤)",
    "꼼꼼 리뷰어 (사용 후기 느낌, 장단점 언급, 솔직한 톤)",
]

# ── 카테고리 → ObjectId 매핑 ──
CATEGORY_IDS = {}
SELLER_POOL = []


def generate_object_id(seed: str) -> str:
    return hashlib.md5(seed.encode()).hexdigest()[:24]


def get_category_id(category: str) -> str:
    if category not in CATEGORY_IDS:
        CATEGORY_IDS[category] = generate_object_id(f"category:{category}")
    return CATEGORY_IDS[category]


def init_seller_pool(n=200):
    global SELLER_POOL
    random.seed(42)
    SELLER_POOL = [generate_object_id(f"seller:{i}") for i in range(n)]


def get_seller_id(seq: int) -> str:
    return SELLER_POOL[seq % len(SELLER_POOL)]


def parse_usage_period(text) -> int | None:
    if text is None or text in ("알수없음", "알 수 없음", "미확인", ""):
        return None
    if isinstance(text, (int, float)):
        return int(text)
    text = str(text)
    m = re.search(r"(\d+)\s*년", text)
    if m:
        years = int(m.group(1))
        if "미만" in text:
            return max(1, years * 12 - 6)
        if "이상" in text:
            return years * 12 + 6
        return years * 12
    m = re.search(r"(\d+)\s*개월", text)
    if m:
        return int(m.group(1))
    m = re.search(r"(\d+)\s*일", text)
    if m:
        return max(1, int(m.group(1)) // 30)
    if any(kw in text for kw in ("새상품", "미사용", "미개봉", "새것", "단순개봉")):
        return 0
    return None


def convert_location(location_list: list) -> dict:
    if not location_list:
        return {"address": "", "lat": None, "lng": None}
    address = " ".join(location_list) if isinstance(location_list, list) else str(location_list)
    return {"address": address, "lat": None, "lng": None}


def assign_image_count() -> int:
    """1장(70%) 또는 2장(30%) 랜덤 할당"""
    return 1 if random.random() < 0.7 else 2


# ══════════════════════════════════════════════
# LLM 스타일 변형
# ══════════════════════════════════════════════

def build_style_prompt(records: list[dict]) -> str:
    """배치 단위로 LLM 프롬프트 생성"""
    items = []
    for i, rec in enumerate(records):
        common = rec.get("common_attributes", {}) or {}
        sensitive = rec.get("sensitive_attributes", {}) or {}
        style = random.choice(WRITING_STYLES)

        info_parts = []
        info_parts.append(f"카테고리: {rec.get('category', '')}")
        info_parts.append(f"가격: {rec.get('price', 0):,}원")

        if common.get("condition"):
            info_parts.append(f"상태: {common['condition']}")
        if common.get("usage_period"):
            info_parts.append(f"사용기간: {common['usage_period']}")
        if common.get("defects") and common["defects"] != "없음":
            info_parts.append(f"하자: {common['defects']}")
        if common.get("includes_box"):
            info_parts.append("정품박스 있음")
        if common.get("includes_accessories"):
            info_parts.append("부속품 포함")
        if common.get("negotiable"):
            info_parts.append("가격 네고 가능")

        for k, v in sensitive.items():
            if v and str(v) not in ("알수없음", "알 수 없음", "미확인", "없음"):
                info_parts.append(f"{k}: {v}")

        orig_desc = rec.get("original_description", "")
        if orig_desc:
            info_parts.append(f"원본설명참고: {orig_desc[:150]}")

        items.append(f"[{i}]\n스타일: {style}\n상품정보: {' / '.join(info_parts)}")

    items_text = "\n\n".join(items)

    return f"""당신은 중고거래 플랫폼의 다양한 판매자입니다.
각 상품에 대해 지정된 스타일로 게시글 제목과 설명을 작성하세요.

규칙:
- 각 게시글이 서로 다른 사람이 쓴 것처럼 문체, 길이, 표현이 모두 달라야 합니다.
- 제목은 15~40자 사이로 작성하세요.
- 설명은 2~6줄로 작성하세요.
- 실제 중고거래 앱에서 볼 법한 자연스러운 게시글이어야 합니다.
- 가격은 설명에 넣지 마세요 (별도 필드에 있으므로).
- 원본설명참고가 있으면 내용을 참고하되, 지정된 스타일로 완전히 새로 작성하세요.

아래 형식의 JSON으로만 응답하세요. 다른 텍스트 없이 JSON만 출력하세요.

{items_text}

응답 형식:
{{"items": [
  {{"index": 0, "title": "제목", "description": "설명"}},
  {{"index": 1, "title": "제목", "description": "설명"}}
]}}"""


def call_llm_batch(records: list[dict], max_retries: int = 3) -> list[dict]:
    """배치 단위로 LLM 호출하여 제목+설명 생성"""
    prompt = build_style_prompt(records)

    for attempt in range(max_retries):
        try:
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "중고거래 게시글 작성 전문가. JSON으로만 응답."},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.9,
                max_tokens=4096,
                response_format={"type": "json_object"},
            )
            raw = response.choices[0].message.content
            parsed = json.loads(raw)

            # 응답 구조 처리
            if isinstance(parsed, dict):
                for key in ("items", "results", "data", "posts"):
                    if key in parsed and isinstance(parsed[key], list):
                        return parsed[key]
                return [parsed]

            if isinstance(parsed, list):
                return parsed

        except Exception as e:
            print(f" [오류] attempt {attempt + 1}: {e}")
            time.sleep(2)

    # 실패 시 원본 반환
    return [
        {"index": i, "title": rec.get("title", ""), "description": rec.get("original_description", "")}
        for i, rec in enumerate(records)
    ]


# ══════════════════════════════════════════════
# 메인 변환
# ══════════════════════════════════════════════

def convert_record(record: dict, llm_result: dict | None = None) -> dict:
    """합성 데이터 1건 → 게시글 데이터 1건 변환"""
    seq = record.get("seq", 0)
    common = record.get("common_attributes", {}) or {}
    sensitive = record.get("sensitive_attributes", {}) or {}

    defects_raw = common.get("defects", "없음")
    has_defects = defects_raw not in ("없음", None, "", "알수없음", "없습니다", "무")

    price = record.get("price", 0) or 0

    sort_date = record.get("sortDate", "")
    try:
        created_at = datetime.strptime(sort_date, "%Y-%m-%d %H:%M:%S").isoformat()
    except (ValueError, TypeError):
        created_at = datetime.now().isoformat()

    if llm_result:
        title = llm_result.get("title", record.get("title", ""))
        description = llm_result.get("description", record.get("original_description", ""))
    else:
        title = record.get("title", "")
        description = record.get("original_description", "")

    post = {
        "_id": generate_object_id(f"post:{seq}"),
        "sellerId": get_seller_id(seq),
        "title": title,
        "description": description,
        "images": [],
        "imageCount": assign_image_count(),
        "categoryId": get_category_id(record.get("category", "기타 중고물품")),
        "category": record.get("category", "기타 중고물품"),
        "price": price,
        "isFree": price == 0,
        "condition": common.get("condition", "알수없음"),
        "sensitiveAttributes": sensitive,
        "options": {
            "hasBox": bool(common.get("includes_box", False)),
            "hasAccessories": bool(common.get("includes_accessories", False)),
            "hasDefects": has_defects,
            "isNegotiable": bool(common.get("negotiable", False)),
            "usagePeriodMonths": parse_usage_period(common.get("usage_period")),
        },
        "aiPriceMin": None,
        "aiPriceMax": None,
        "aiPriceReason": None,
        "location": convert_location(record.get("location", [])),
        "status": "selling",
        "viewCount": record.get("viewCount", 0) or 0,
        "likeCount": record.get("wishCount", 0) or 0,
        "createdAt": created_at,
        "updatedAt": created_at,
    }

    return post


def process_file(input_path: Path, output_path: Path, use_llm: bool = True,
                 batch_size: int = 20, delay: float = 0.5) -> int:
    """JSONL 파일 1개를 변환"""
    records = []
    with open(input_path, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                records.append(json.loads(line))

    if not records:
        return 0

    all_posts = []

    if use_llm:
        for i in range(0, len(records), batch_size):
            batch = records[i:i + batch_size]
            batch_num = i // batch_size + 1
            total_batches = (len(records) + batch_size - 1) // batch_size

            print(f"    배치 {batch_num}/{total_batches} ({len(batch)}건) LLM 호출 중...", end="", flush=True)

            llm_results = call_llm_batch(batch)

            result_map = {}
            for r in llm_results:
                if not isinstance(r, dict):
                    continue
                idx = r.get("index", -1)
                if isinstance(idx, int) and 0 <= idx < len(batch):
                    result_map[idx] = r

            for j, rec in enumerate(batch):
                llm_result = result_map.get(j)
                post = convert_record(rec, llm_result)
                all_posts.append(post)

            print(f" 완료")

            if i + batch_size < len(records):
                time.sleep(delay)
    else:
        for rec in records:
            post = convert_record(rec)
            all_posts.append(post)

    with open(output_path, "w", encoding="utf-8") as f:
        for post in all_posts:
            f.write(json.dumps(post, ensure_ascii=False) + "\n")

    return len(all_posts)


def main():
    parser = argparse.ArgumentParser(description="합성 데이터 → 게시글 데이터 변환 (LLM 스타일 변형)")
    parser.add_argument("--input", type=str, required=True, help="final/ 디렉토리 경로")
    parser.add_argument("--output", type=str, required=True, help="출력 디렉토리 경로")
    parser.add_argument("--no-llm", action="store_true", help="LLM 스타일 변형 없이 원본 그대로")
    parser.add_argument("--batch-size", type=int, default=20, help="LLM 배치 크기 (기본 20)")
    parser.add_argument("--delay", type=float, default=0.5, help="API 호출 간 딜레이 초 (기본 0.5)")
    args = parser.parse_args()

    input_dir = Path(args.input)
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)

    if not input_dir.exists():
        print(f"ERROR: 입력 디렉토리가 없습니다: {input_dir}")
        return

    init_seller_pool()
    random.seed(42)

    jsonl_files = sorted(input_dir.glob("*.jsonl"))
    if not jsonl_files:
        print(f"ERROR: {input_dir}에 JSONL 파일이 없습니다.")
        return

    use_llm = not args.no_llm

    total = 0
    all_output = output_dir / "posts_all.jsonl"

    print("=" * 60)
    print("합성 데이터 → 게시글 데이터 변환")
    print(f"LLM 스타일 변형: {'ON (gpt-4o-mini)' if use_llm else 'OFF'}")
    print(f"배치 크기: {args.batch_size}, 딜레이: {args.delay}초")
    print("=" * 60)

    with open(all_output, "w", encoding="utf-8") as fall:
        for fp in jsonl_files:
            out_name = f"posts_{fp.stem}.jsonl"
            out_path = output_dir / out_name

            print(f"\n[{fp.stem}]")
            count = process_file(fp, out_path, use_llm, args.batch_size, args.delay)

            with open(out_path, "r", encoding="utf-8") as fin:
                for line in fin:
                    fall.write(line)

            print(f"  → {out_name} ({count:,}건)")
            total += count

    print(f"\n{'=' * 60}")
    print(f"총 {total:,}건 변환 완료")
    print(f"카테고리별: {output_dir}/posts_*.jsonl")
    print(f"전체 통합:  {all_output}")

    mapping_path = output_dir / "category_mapping.json"
    with open(mapping_path, "w", encoding="utf-8") as f:
        json.dump(CATEGORY_IDS, f, ensure_ascii=False, indent=2)
    print(f"카테고리 매핑: {mapping_path}")

    seller_path = output_dir / "seller_ids.json"
    with open(seller_path, "w", encoding="utf-8") as f:
        json.dump(SELLER_POOL[:50], f, indent=2)
    print(f"판매자 ID 샘플: {seller_path}")

    if use_llm:
        est_cost = total * 500 / 1_000_000 * 0.75
        print(f"\n예상 LLM 비용: ~${est_cost:.2f} (gpt-4o-mini)")


if __name__ == "__main__":
    main()