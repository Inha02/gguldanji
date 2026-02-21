"""
Step 1-C: 정제 결과 검증 + 통계 리포트
=======================================
위치: gguldanji/ai-engine/crawler/pipeline/step1c_validate.py

실행 방법:
  cd gguldanji/ai-engine
  python -m crawler.pipeline.step1c_validate

설명:
  cleaned 데이터의 품질을 검증하고 카테고리별 통계를 생성합니다.
  - 필수 필드 존재 여부 체크
  - 가격 이상치 탐지
  - 카테고리별 가격 분포 통계
  - 속성 완성도 리포트
  - 검증 통과 데이터를 카테고리별로 병합하여 최종 출력
"""

import json
import sys
import statistics
from pathlib import Path
from collections import defaultdict, Counter

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
PROCESSED_DIR = DATA_DIR / "processed"
OUTPUT_DIR = DATA_DIR / "final"


def load_cleaned(keyword: str) -> list[dict]:
    filepath = PROCESSED_DIR / keyword / f"{keyword}_cleaned.jsonl"
    if not filepath.exists():
        return []
    items = []
    with open(filepath, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                items.append(json.loads(line))
    return items


def validate_item(item: dict) -> list[str]:
    """단건 검증 → 문제점 리스트 반환"""
    issues = []
    
    # 필수 필드 체크
    required = ["seq", "keyword", "category", "title", "price"]
    for field in required:
        if not item.get(field) and item.get(field) != 0:
            issues.append(f"missing_{field}")
    
    # 공통속성 체크
    common = item.get("common_attributes")
    if not common:
        issues.append("missing_common_attributes")
    else:
        if not common.get("product_name"):
            issues.append("missing_product_name")
        if not common.get("condition"):
            issues.append("missing_condition")
        if common.get("selling_price") is None:
            issues.append("missing_selling_price")
    
    # 민감속성 체크
    sensitive = item.get("sensitive_attributes")
    if not sensitive:
        issues.append("missing_sensitive_attributes")
    
    # 가격 검증
    price = item.get("price", 0)
    if price < 0:
        issues.append("negative_price")
    if price > 100_000_000:  # 1억 이상은 의심
        issues.append("suspicious_high_price")
    
    return issues


def detect_price_outliers(items: list[dict]) -> tuple[list[dict], list[dict]]:
    """IQR 기반 가격 이상치 탐지"""
    if len(items) < 4:
        return items, []
    
    prices = [item["price"] for item in items if item.get("price", 0) > 0]
    if len(prices) < 4:
        return items, []
    
    prices_sorted = sorted(prices)
    q1 = prices_sorted[len(prices_sorted) // 4]
    q3 = prices_sorted[3 * len(prices_sorted) // 4]
    iqr = q3 - q1
    
    lower = max(0, q1 - 3.0 * iqr)  # 3.0 IQR로 느슨하게 (중고 시장은 가격 범위가 넓음)
    upper = q3 + 3.0 * iqr
    
    normal = []
    outliers = []
    for item in items:
        p = item.get("price", 0)
        if p == 0:  # 무료나눔은 이상치 아님
            normal.append(item)
        elif lower <= p <= upper:
            normal.append(item)
        else:
            outliers.append(item)
    
    return normal, outliers


def compute_category_stats(items: list[dict]) -> dict:
    """카테고리별 통계"""
    prices = [item["price"] for item in items if item.get("price", 0) > 0]
    
    if not prices:
        return {"count": len(items), "price_stats": None}
    
    return {
        "count": len(items),
        "price_stats": {
            "min": min(prices),
            "max": max(prices),
            "mean": round(statistics.mean(prices)),
            "median": round(statistics.median(prices)),
            "stdev": round(statistics.stdev(prices)) if len(prices) > 1 else 0,
            "q1": round(sorted(prices)[len(prices) // 4]),
            "q3": round(sorted(prices)[3 * len(prices) // 4]),
        }
    }


def compute_attribute_completeness(items: list[dict]) -> dict:
    """속성 완성도 계산"""
    if not items:
        return {}
    
    # 공통속성 완성도
    common_fields = ["product_name", "condition", "usage_period", "original_price",
                     "selling_price", "includes_box", "includes_accessories", "defects", "negotiable"]
    common_completion = {}
    for field in common_fields:
        filled = sum(1 for item in items
                     if item.get("common_attributes", {}).get(field) not in [None, "", "알수없음"])
        common_completion[field] = round(filled / len(items) * 100, 1)
    
    # 민감속성 완성도 (키워드별로 다르므로 전체 평균)
    sensitive_fields = defaultdict(lambda: {"filled": 0, "total": 0})
    for item in items:
        sa = item.get("sensitive_attributes", {})
        if sa:
            for k, v in sa.items():
                sensitive_fields[k]["total"] += 1
                if v not in [None, "", "알수없음"]:
                    sensitive_fields[k]["filled"] += 1
    
    sensitive_completion = {}
    for k, v in sensitive_fields.items():
        if v["total"] > 0:
            sensitive_completion[k] = round(v["filled"] / v["total"] * 100, 1)
    
    return {
        "common": common_completion,
        "sensitive": sensitive_completion
    }


def main():
    print("=" * 60)
    print("Step 1-C: 정제 결과 검증 + 통계")
    print("=" * 60)
    
    # 모든 키워드의 cleaned 데이터 로드
    all_items_by_category = defaultdict(list)
    all_items_by_keyword = {}
    validation_issues = defaultdict(list)
    
    keywords = []
    for subdir in sorted(PROCESSED_DIR.iterdir()):
        if subdir.is_dir():
            cleaned = subdir / f"{subdir.name}_cleaned.jsonl"
            if cleaned.exists():
                keywords.append(subdir.name)
    
    if not keywords:
        print("[ERROR] cleaned 파일이 없습니다. step1b를 먼저 실행하세요.")
        return
    
    print(f"검증 대상: {len(keywords)}개 키워드")
    
    total_items = 0
    total_valid = 0
    total_outliers = 0
    
    for keyword in keywords:
        items = load_cleaned(keyword)
        if not items:
            continue
        
        all_items_by_keyword[keyword] = items
        
        # 검증
        valid_items = []
        for item in items:
            issues = validate_item(item)
            if issues:
                validation_issues[keyword].append({
                    "seq": item.get("seq"),
                    "title": item.get("title"),
                    "issues": issues
                })
            else:
                valid_items.append(item)
        
        # 이상치 제거
        normal, outliers = detect_price_outliers(valid_items)
        total_items += len(items)
        total_valid += len(normal)
        total_outliers += len(outliers)
        
        category = items[0].get("category", "기타")
        all_items_by_category[category].extend(normal)
        
        invalid_count = len(items) - len(valid_items)
        print(f"  [{keyword}] 전체={len(items)}, 검증통과={len(valid_items)}, "
              f"이상치={len(outliers)}, 최종={len(normal)}")
    
    # 카테고리별 통계
    print(f"\n{'='*60}")
    print("카테고리별 통계")
    print(f"{'='*60}")
    print(f"{'카테고리':<18} {'건수':>6} {'최저가':>10} {'중앙값':>10} {'평균':>10} {'최고가':>12}")
    print("-" * 70)
    
    category_stats = {}
    for category in sorted(all_items_by_category.keys()):
        items = all_items_by_category[category]
        stats = compute_category_stats(items)
        category_stats[category] = stats
        
        ps = stats.get("price_stats")
        if ps:
            print(f"{category:<18} {stats['count']:>6} {ps['min']:>10,} {ps['median']:>10,} "
                  f"{ps['mean']:>10,} {ps['max']:>12,}")
        else:
            print(f"{category:<18} {stats['count']:>6} {'N/A':>10}")
    
    # 속성 완성도
    print(f"\n{'='*60}")
    print("속성 완성도 (공통속성)")
    print(f"{'='*60}")
    
    all_flat = []
    for items in all_items_by_category.values():
        all_flat.extend(items)
    
    completeness = compute_attribute_completeness(all_flat)
    for field, pct in completeness.get("common", {}).items():
        bar = "█" * int(pct / 5) + "░" * (20 - int(pct / 5))
        print(f"  {field:<25} {bar} {pct}%")
    
    # 최종 데이터 저장 (카테고리별)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    for category, items in all_items_by_category.items():
        safe_name = category.replace("/", "_")
        output_path = OUTPUT_DIR / f"{safe_name}.jsonl"
        with open(output_path, "w", encoding="utf-8") as f:
            for item in items:
                f.write(json.dumps(item, ensure_ascii=False) + "\n")
        print(f"\n  저장: {output_path} ({len(items)}건)")
    
    # 전체 요약
    print(f"\n{'='*60}")
    print("전체 요약")
    print(f"{'='*60}")
    print(f"  전체 입력: {total_items}건")
    print(f"  검증 통과 + 이상치 제외: {total_valid}건")
    print(f"  이상치: {total_outliers}건")
    print(f"  카테고리 수: {len(all_items_by_category)}개")
    print(f"  최종 데이터: {OUTPUT_DIR}")
    
    # 리포트 저장
    report = {
        "summary": {
            "total_input": total_items,
            "total_valid": total_valid,
            "total_outliers": total_outliers,
            "categories": len(all_items_by_category)
        },
        "category_stats": category_stats,
        "attribute_completeness": completeness,
        "validation_issues_count": {k: len(v) for k, v in validation_issues.items()}
    }
    
    report_path = DATA_DIR / "validation_report.json"
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    print(f"\n  검증 리포트: {report_path}")


if __name__ == "__main__":
    main()