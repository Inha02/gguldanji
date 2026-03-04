"""
Step 2A-2: GPT-4o 기반 결측 속성 보강 (Imputation)
====================================================
위치: gguldanji/ai-engine/crawler/pipeline/step2a2_impute.py

실행 방법:
  cd gguldanji/ai-engine
  python -m crawler.pipeline.step2a2_impute

  # 특정 카테고리만:
  python -m crawler.pipeline.step2a2_impute 디지털기기 패션잡화

  # dry-run (API 호출 없이 결측 현황만 확인):
  python -m crawler.pipeline.step2a2_impute --dry-run

필요 패키지:
  pip install openai tqdm python-dotenv

환경변수:
  ai-engine/.env에 OPENAI_API_KEY 설정

설명:
  final/{category}.jsonl의 "알수없음" 속성을 GPT-4o가 추론하여 채움.
  - 제목 + 설명 + 이미 알려진 속성을 컨텍스트로 제공
  - GPT-4o의 제품 지식으로 결측 속성 추론
  - 추론된 값에는 inferred: true 플래그
  - 결과를 final/ 에 덮어씀 (원본은 final_backup/에 백업)

예상 비용: ~$30-40 (10,747건 × GPT-4o)
"""

import json
import sys
import time
import shutil
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

from dotenv import load_dotenv
from openai import OpenAI
from tqdm import tqdm

# ──────────────────────────────────────────────
# 설정
# ──────────────────────────────────────────────
MODEL = "gpt-4o"
MAX_CONCURRENT = 3        # 3스레드 병렬
RETRY_COUNT = 2
RETRY_DELAY = 3           # 재시도 간격
REQUEST_DELAY = 0.5       # 요청 간 딜레이 (초)

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
FINAL_DIR = DATA_DIR / "final"
BACKUP_DIR = DATA_DIR / "final_backup"
CONFIG_DIR = DATA_DIR / "config"

ENV_PATH = BASE_DIR.parent / ".env"
load_dotenv(ENV_PATH)

client = OpenAI()

# "알수없음"으로 간주할 값들
UNKNOWN_VALUES = {"알수없음", "알 수 없음", "미확인", "미상", "없음", "null", "None", "", None}


# ──────────────────────────────────────────────
# 앵커 설정 로드
# ──────────────────────────────────────────────
def load_anchor_config() -> dict:
    config_path = CONFIG_DIR / "anchor_config.json"
    if config_path.exists():
        with open(config_path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


# ──────────────────────────────────────────────
# 결측 분석
# ──────────────────────────────────────────────
def analyze_missing(items: list[dict]) -> dict:
    """결측 현황 분석"""
    if not items:
        return {}

    common_fields = ["condition", "usage_period", "original_price",
                     "includes_box", "includes_accessories", "defects", "negotiable"]

    common_missing = {}
    for field in common_fields:
        missing = sum(1 for item in items
                      if item.get("common_attributes", {}).get(field) in UNKNOWN_VALUES
                      or item.get("common_attributes", {}).get(field) is None)
        common_missing[field] = round(missing / len(items) * 100, 1)

    sensitive_missing = {}
    for item in items:
        sa = item.get("sensitive_attributes", {})
        if sa:
            for k, v in sa.items():
                if k not in sensitive_missing:
                    sensitive_missing[k] = {"total": 0, "missing": 0}
                sensitive_missing[k]["total"] += 1
                if v in UNKNOWN_VALUES:
                    sensitive_missing[k]["missing"] += 1

    sensitive_pct = {}
    for k, v in sensitive_missing.items():
        if v["total"] > 0:
            sensitive_pct[k] = round(v["missing"] / v["total"] * 100, 1)

    return {"common": common_missing, "sensitive": sensitive_pct}


def needs_imputation(item: dict) -> bool:
    """이 아이템이 보강이 필요한지 판단"""
    common = item.get("common_attributes", {}) or {}
    sensitive = item.get("sensitive_attributes", {}) or {}

    # 공통속성 중 결측
    important_common = ["condition", "usage_period", "original_price"]
    common_missing = sum(1 for f in important_common if common.get(f) in UNKNOWN_VALUES or common.get(f) is None)

    # 민감속성 중 결측
    sensitive_missing = sum(1 for v in sensitive.values() if v in UNKNOWN_VALUES)
    sensitive_total = len(sensitive)

    # 결측이 하나라도 있으면 보강 대상
    return common_missing > 0 or (sensitive_total > 0 and sensitive_missing > 0)


# ──────────────────────────────────────────────
# 프롬프트 생성
# ──────────────────────────────────────────────
def build_imputation_prompt(item: dict) -> str:
    common = item.get("common_attributes", {}) or {}
    sensitive = item.get("sensitive_attributes", {}) or {}
    title = item.get("title", "")
    desc = item.get("original_description", "")[:400]
    category = item.get("category", "")
    keyword = item.get("keyword", "")
    price = item.get("price", 0)
    labels = item.get("labels", [])
    orig_category = item.get("original_category", "")

    # 현재 알려진 속성과 결측 속성 분리
    known_common = {k: v for k, v in common.items() if v not in UNKNOWN_VALUES and v is not None}
    missing_common = [k for k, v in common.items() if v in UNKNOWN_VALUES or v is None]

    known_sensitive = {k: v for k, v in sensitive.items() if v not in UNKNOWN_VALUES}
    missing_sensitive = [k for k, v in sensitive.items() if v in UNKNOWN_VALUES]

    if not missing_common and not missing_sensitive:
        return None  # 보강 불필요

    return f"""당신은 중고 거래 상품 데이터 전문가입니다.
아래 중고 상품의 알려진 정보를 바탕으로, 결측된 속성값을 추론해주세요.

[상품 정보]
- 카테고리: {category}
- 키워드: {keyword}
- 제목: {title}
- 설명: {desc}
- 가격: {price:,}원
- 라벨: {', '.join(labels)}
- 중고나라 카테고리: {orig_category}

[이미 알려진 공통속성]
{json.dumps(known_common, ensure_ascii=False, indent=2)}

[이미 알려진 민감속성]
{json.dumps(known_sensitive, ensure_ascii=False, indent=2)}

[추론이 필요한 공통속성]
{json.dumps(missing_common, ensure_ascii=False)}

[추론이 필요한 민감속성]
{json.dumps(missing_sensitive, ensure_ascii=False)}

아래 규칙을 따라 JSON으로만 응답하세요:

1. 제목, 설명, 알려진 속성, 가격대, 제품 일반 지식을 종합하여 추론
2. 확실히 추론 가능한 것만 채우세요
3. 도저히 추론 불가능한 속성은 "추론불가"로 표기
4. usage_period는 "6개월", "1년" 등 한국어로
5. original_price는 정가를 숫자(원 단위)로. 추론 불가시 null
6. condition은 S급/A급/B급/C급/부품용 중 하나
7. includes_box는 true/false
8. negotiable은 true/false

응답 형식 (JSON만, 마크다운 백틱 없이):
{{
  "common_attributes": {{결측 공통속성만 키:값}},
  "sensitive_attributes": {{결측 민감속성만 키:값}},
  "confidence": "high/medium/low"
}}"""


# ──────────────────────────────────────────────
# API 호출
# ──────────────────────────────────────────────
def call_gpt_impute(item: dict) -> dict | str | None:
    """반환: dict(성공), "quota_exceeded"(크레딧 소진), None(기타 에러)"""
    prompt = build_imputation_prompt(item)
    if prompt is None:
        return None

    for attempt in range(RETRY_COUNT + 1):
        try:
            time.sleep(REQUEST_DELAY)  # 요청간 딜레이
            response = client.chat.completions.create(
                model=MODEL,
                messages=[
                    {"role": "system", "content": "당신은 중고 상품 데이터 보강 전문가입니다. JSON으로만 응답하세요."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.2,
                max_tokens=800,
                response_format={"type": "json_object"}
            )
            content = response.choices[0].message.content.strip()
            return json.loads(content)

        except json.JSONDecodeError:
            if attempt < RETRY_COUNT:
                time.sleep(RETRY_DELAY)
                continue
            return None
        except Exception as e:
            error_str = str(e)
            # quota 소진 감지 → 즉시 중단 신호
            if "insufficient_quota" in error_str or "exceeded your current quota" in error_str:
                print(f"\n  [FATAL] API 크레딧 소진! 충전 후 재실행하세요.")
                return "quota_exceeded"
            # rate limit (429) → 대기 후 재시도
            if "429" in error_str and "insufficient_quota" not in error_str:
                wait = min(60, RETRY_DELAY * (attempt + 1) * 5)
                print(f"  [RATE_LIMIT] {wait}초 대기 후 재시도...")
                time.sleep(wait)
                continue
            if attempt < RETRY_COUNT:
                time.sleep(RETRY_DELAY)
                continue
            print(f"  [ERROR] seq={item.get('seq')}: {e}")
            return None


# ──────────────────────────────────────────────
# 속성 병합
# ──────────────────────────────────────────────
def _is_valid_value(v) -> bool:
    """보강값이 유효한지 체크 (리스트/딕셔너리 등 비정상 타입 방어)"""
    if v is None:
        return False
    if isinstance(v, (list, dict)):
        return False
    try:
        return v and v != "추론불가" and v not in UNKNOWN_VALUES
    except TypeError:
        return False


def _is_unknown(v) -> bool:
    """현재값이 결측인지 체크"""
    if v is None:
        return True
    try:
        return v in UNKNOWN_VALUES
    except TypeError:
        return False


def merge_imputed(item: dict, imputed: dict) -> dict:
    """추론된 속성을 원본에 병합 (기존 값은 덮어쓰지 않음)"""
    result = json.loads(json.dumps(item))  # deep copy

    # inferred 트래킹 초기화
    if "inferred_fields" not in result:
        result["inferred_fields"] = []

    # 공통속성 병합
    imp_common = imputed.get("common_attributes", {})
    if imp_common and result.get("common_attributes"):
        for k, v in imp_common.items():
            if _is_valid_value(v):
                current = result["common_attributes"].get(k)
                if _is_unknown(current):
                    result["common_attributes"][k] = v
                    result["inferred_fields"].append(f"common.{k}")

    # 민감속성 병합
    imp_sensitive = imputed.get("sensitive_attributes", {})
    if imp_sensitive and result.get("sensitive_attributes"):
        for k, v in imp_sensitive.items():
            if _is_valid_value(v):
                current = result["sensitive_attributes"].get(k)
                if _is_unknown(current):
                    result["sensitive_attributes"][k] = v
                    result["inferred_fields"].append(f"sensitive.{k}")

    result["imputation_confidence"] = imputed.get("confidence", "unknown")
    return result


# ──────────────────────────────────────────────
# 단건 처리
# ──────────────────────────────────────────────
def process_single(item: dict) -> tuple[dict, str, int]:
    """
    반환: (아이템, 상태, 보강 필드 수)
    상태: "ok", "skipped", "error", "quota_exceeded"
    """
    # 이미 보강된 아이템은 스킵
    if item.get("inferred_fields") and len(item["inferred_fields"]) > 0:
        return item, "skipped", 0

    if not needs_imputation(item):
        return item, "skipped", 0

    result = call_gpt_impute(item)

    if result == "quota_exceeded":
        return item, "quota_exceeded", 0
    if result is None:
        return item, "error", 0

    merged = merge_imputed(item, result)
    filled_count = len(merged.get("inferred_fields", []))
    return merged, "ok", filled_count


# ──────────────────────────────────────────────
# 카테고리별 처리
# ──────────────────────────────────────────────
def process_category(category: str, items: list[dict], dry_run: bool = False) -> dict:
    print(f"\n{'='*50}")
    print(f"[{category}] {len(items)}건")
    print(f"{'='*50}")

    # 결측 현황
    missing = analyze_missing(items)
    need_impute = sum(1 for item in items if needs_imputation(item))
    print(f"  보강 필요: {need_impute}/{len(items)}건")

    if missing.get("common"):
        high_missing = {k: v for k, v in missing["common"].items() if v > 30}
        if high_missing:
            print(f"  공통속성 결측률(>30%): {high_missing}")

    if missing.get("sensitive"):
        high_missing = {k: v for k, v in missing["sensitive"].items() if v > 50}
        if high_missing:
            top5 = dict(list(sorted(high_missing.items(), key=lambda x: x[1], reverse=True))[:5])
            print(f"  민감속성 결측률(>50%): {top5}")

    if dry_run:
        return {"category": category, "total": len(items), "need_impute": need_impute,
                "imputed": 0, "fields_filled": 0, "errors": 0, "skipped": 0}

    # 이미 보강된 건수 확인
    already_done = sum(1 for item in items
                       if item.get("inferred_fields") and len(item["inferred_fields"]) > 0)
    if already_done > 0:
        print(f"  이미 보강됨: {already_done}건 (스킵)")

    actual_todo = need_impute - already_done
    if actual_todo <= 0:
        print(f"  → 보강할 항목 없음, 스킵")
        return {"category": category, "total": len(items), "need_impute": need_impute,
                "imputed": 0, "fields_filled": 0, "errors": 0, "skipped": already_done}

    print(f"  실제 처리 대상: {actual_todo}건")

    # 병렬 처리 (quota 소진 시 즉시 중단)
    import threading
    quota_flag = threading.Event()  # quota 소진 신호

    processed_items = [None] * len(items)  # 순서 보장용
    errors = 0
    total_fields_filled = 0
    imputed_count = 0
    skipped = 0
    quota_hit = False

    def process_with_quota_check(args):
        idx, item = args
        if quota_flag.is_set():
            return idx, item, "quota_exceeded", 0
        merged, status, filled = process_single(item)
        if status == "quota_exceeded":
            quota_flag.set()
        return idx, merged, status, filled

    args_list = list(enumerate(items))

    with ThreadPoolExecutor(max_workers=MAX_CONCURRENT) as executor:
        futures = {executor.submit(process_with_quota_check, args): args for args in args_list}

        with tqdm(total=len(items), desc=f"  [{category}]") as pbar:
            for future in as_completed(futures):
                idx, merged, status, filled = future.result()
                processed_items[idx] = merged

                if status == "quota_exceeded":
                    quota_hit = True
                elif status == "skipped":
                    skipped += 1
                elif status == "error":
                    errors += 1
                elif status == "ok":
                    imputed_count += 1
                    total_fields_filled += filled

                pbar.update(1)

    # quota로 None 남은 슬롯은 원본으로 채움
    for i, item_result in enumerate(processed_items):
        if item_result is None:
            processed_items[i] = items[i]

    if quota_hit:
        print(f"\n  [FATAL] 크레딧 소진! {imputed_count}건 보강 후 중단됨.")
        print(f"  충전 후 다시 실행하면 보강된 건은 스킵하고 나머지만 처리합니다.")

    # 저장
    safe_name = category.replace("/", "_")
    output_path = FINAL_DIR / f"{safe_name}.jsonl"
    with open(output_path, "w", encoding="utf-8") as f:
        for item in processed_items:
            f.write(json.dumps(item, ensure_ascii=False) + "\n")

    print(f"  보강 완료: {imputed_count}건, 총 {total_fields_filled}개 필드 채움, "
          f"스킵 {skipped}건, 오류 {errors}건")

    # 보강 후 결측 현황
    after_missing = analyze_missing(processed_items)
    if after_missing.get("common"):
        improved = {}
        for k in missing.get("common", {}):
            before = missing["common"].get(k, 0)
            after = after_missing["common"].get(k, 0)
            if before > after:
                improved[k] = f"{before}% → {after}%"
        if improved:
            print(f"  개선된 공통속성: {improved}")

    return {
        "category": category,
        "total": len(items),
        "need_impute": need_impute,
        "imputed": imputed_count,
        "fields_filled": total_fields_filled,
        "errors": errors,
        "skipped": skipped,
        "quota_hit": quota_hit
    }


# ──────────────────────────────────────────────
# 메인
# ──────────────────────────────────────────────
def main():
    print("=" * 60)
    print("Step 2A-2: GPT-4o 기반 결측 속성 보강")
    print(f"모델: {MODEL}")
    print("=" * 60)

    # 인자 파싱
    dry_run = "--dry-run" in sys.argv
    categories_filter = [a for a in sys.argv[1:] if a != "--dry-run"]

    if dry_run:
        print("*** DRY-RUN 모드: API 호출 없이 결측 현황만 확인 ***\n")

    # 데이터 로드
    if not FINAL_DIR.exists():
        print(f"[ERROR] final 디렉토리 없음: {FINAL_DIR}")
        return

    data = {}
    for filepath in sorted(FINAL_DIR.glob("*.jsonl")):
        category = filepath.stem.replace("_", "/")
        items = []
        with open(filepath, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    items.append(json.loads(line))
        if items:
            data[category] = items

    if categories_filter:
        data = {k: v for k, v in data.items() if k in categories_filter}

    if not data:
        print("[ERROR] 데이터 없음")
        return

    # 백업 (최초 1회)
    if not dry_run and not BACKUP_DIR.exists():
        print(f"원본 백업: {FINAL_DIR} → {BACKUP_DIR}")
        shutil.copytree(FINAL_DIR, BACKUP_DIR)

    # 비용 예측 (이미 보강된 건 제외)
    total_items = sum(len(v) for v in data.values())
    total_already = sum(1 for items in data.values() for item in items
                        if item.get("inferred_fields") and len(item.get("inferred_fields", [])) > 0)
    total_need_raw = sum(1 for items in data.values() for item in items if needs_imputation(item))
    total_actual = total_need_raw - total_already
    estimated_cost = max(0, total_actual) * 0.003
    print(f"\n전체: {total_items}건, 보강 필요: {total_need_raw}건, 이미 보강됨: {total_already}건")
    print(f"실제 처리 대상: {total_actual}건, 예상 비용: ~${estimated_cost:.2f}")

    if not dry_run:
        print("\n3초 후 시작합니다... (Ctrl+C로 취소)")
        time.sleep(3)

    # 처리
    results = []
    for category, items in sorted(data.items()):
        result = process_category(category, items, dry_run)
        results.append(result)

        # quota 소진 시 나머지 카테고리 중단
        if result.get("quota_hit"):
            print(f"\n[FATAL] 크레딧 소진으로 전체 중단.")
            print(f"  충전 후 다시 실행하면 보강된 건은 스킵하고 나머지만 처리합니다.")
            break

    # 요약
    print(f"\n{'='*60}")
    print("속성 보강 요약")
    print(f"{'='*60}")
    print(f"{'카테고리':<18} {'전체':>6} {'보강필요':>8} {'보강완료':>8} {'필드수':>8} {'오류':>6}")
    print("-" * 60)

    t_total = 0
    t_need = 0
    t_imputed = 0
    t_fields = 0
    t_errors = 0

    for r in results:
        t_total += r["total"]
        t_need += r["need_impute"]
        t_imputed += r["imputed"]
        t_fields += r["fields_filled"]
        t_errors += r["errors"]
        print(f"{r['category']:<18} {r['total']:>6} {r['need_impute']:>8} "
              f"{r['imputed']:>8} {r['fields_filled']:>8} {r['errors']:>6}")

    print("-" * 60)
    print(f"{'합계':<18} {t_total:>6} {t_need:>8} {t_imputed:>8} {t_fields:>8} {t_errors:>6}")

    # 리포트 저장
    report_path = DATA_DIR / "imputation_report.json"
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"\n리포트: {report_path}")


if __name__ == "__main__":
    main()