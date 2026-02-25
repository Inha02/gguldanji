"""
Step 2A: 카테고리별 가격 분포 분석 + Augmentation 규칙 수립
============================================================
위치: gguldanji/ai-engine/crawler/pipeline/step2a_price_analysis.py

실행 방법:
  cd gguldanji/ai-engine
  python -m crawler.pipeline.step2a_price_analysis

필요 패키지:
  pip install pandas numpy

설명:
  final/{category}.jsonl 데이터에서:
  1) 카테고리별 가격 분포 분석
  2) 주요 속성별 가격 영향도 분석
  3) condition별 가격 비율(정가 대비) 산출
  4) augmentation에 사용할 통계 규칙을 config로 저장
  
  API 호출 없음. 로컬에서만 실행.
"""

import json
import statistics
from pathlib import Path
from collections import defaultdict

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
FINAL_DIR = DATA_DIR / "final"
CONFIG_DIR = DATA_DIR / "config"


# ──────────────────────────────────────────────
# 데이터 로드
# ──────────────────────────────────────────────
def load_final_data() -> dict[str, list[dict]]:
    """카테고리별 최종 데이터 로드"""
    data = {}
    if not FINAL_DIR.exists():
        print(f"[ERROR] final 디렉토리 없음: {FINAL_DIR}")
        return data
    
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
    
    return data


# ──────────────────────────────────────────────
# 가격 분포 분석
# ──────────────────────────────────────────────
def analyze_price_distribution(items: list[dict]) -> dict:
    """가격 분포 상세 분석"""
    prices = [item["price"] for item in items if item.get("price", 0) > 0]
    if not prices:
        return {}
    
    prices_sorted = sorted(prices)
    n = len(prices_sorted)
    
    return {
        "count": n,
        "min": prices_sorted[0],
        "max": prices_sorted[-1],
        "mean": round(statistics.mean(prices)),
        "median": round(statistics.median(prices)),
        "stdev": round(statistics.stdev(prices)) if n > 1 else 0,
        "p10": prices_sorted[int(n * 0.1)],
        "p25": prices_sorted[int(n * 0.25)],
        "p75": prices_sorted[int(n * 0.75)],
        "p90": prices_sorted[int(n * 0.9)],
    }


# ──────────────────────────────────────────────
# Condition별 가격 비율 분석
# ──────────────────────────────────────────────
def analyze_condition_price_ratio(items: list[dict]) -> dict:
    """상태(condition)별 가격 통계"""
    condition_prices = defaultdict(list)
    
    for item in items:
        common = item.get("common_attributes", {})
        if not common:
            continue
        condition = common.get("condition", "알수없음")
        price = item.get("price", 0)
        if price > 0 and condition != "알수없음":
            condition_prices[condition].append(price)
    
    result = {}
    all_median = statistics.median([item["price"] for item in items if item.get("price", 0) > 0]) if items else 1
    
    for condition, prices in condition_prices.items():
        if len(prices) >= 3:
            med = statistics.median(prices)
            result[condition] = {
                "count": len(prices),
                "median": round(med),
                "mean": round(statistics.mean(prices)),
                "ratio_to_overall": round(med / all_median, 3) if all_median > 0 else 1.0
            }
    
    return result


# ──────────────────────────────────────────────
# 브랜드별 가격 분석 (민감속성 중 가장 영향이 큰 속성)
# ──────────────────────────────────────────────
def analyze_brand_prices(items: list[dict]) -> dict:
    """브랜드별 가격 통계 (상위 10개)"""
    brand_prices = defaultdict(list)
    
    for item in items:
        sa = item.get("sensitive_attributes", {})
        if not sa:
            continue
        brand = sa.get("브랜드", "알수없음")
        if brand and brand != "알수없음":
            price = item.get("price", 0)
            if price > 0:
                brand_prices[brand].append(price)
    
    # 3건 이상인 브랜드만, 건수 내림차순
    result = {}
    sorted_brands = sorted(brand_prices.items(), key=lambda x: len(x[1]), reverse=True)
    
    for brand, prices in sorted_brands[:15]:
        if len(prices) >= 3:
            result[brand] = {
                "count": len(prices),
                "median": round(statistics.median(prices)),
                "min": min(prices),
                "max": max(prices)
            }
    
    return result


# ──────────────────────────────────────────────
# Augmentation 규칙 생성
# ──────────────────────────────────────────────
def generate_augmentation_rules(category: str, items: list[dict], 
                                 price_dist: dict, condition_ratios: dict) -> dict:
    """
    카테고리별 augmentation 규칙 생성.
    실제 데이터의 분포를 기반으로 변형 범위를 결정.
    """
    # Condition별 가격 조정 비율
    # 실제 데이터에서 관찰된 condition별 중앙값 비율을 사용
    condition_multipliers = {}
    if condition_ratios:
        for cond, stats in condition_ratios.items():
            condition_multipliers[cond] = stats["ratio_to_overall"]
    
    # 기본 multiplier (데이터 부족 시)
    default_multipliers = {
        "S급": 1.3,
        "A급": 1.0,
        "B급": 0.75,
        "C급": 0.5,
        "부품용": 0.25
    }
    
    for cond, mult in default_multipliers.items():
        if cond not in condition_multipliers:
            condition_multipliers[cond] = mult
    
    # 사용기간별 감가 비율 (개월 기준)
    # 실제 데이터에서 추출하기 어려우므로 일반적인 중고시장 감가 규칙 적용
    depreciation_rules = {
        "디지털기기": {"monthly_rate": 0.02, "min_ratio": 0.20},        # 월 2% 감가, 최소 20%
        "가전제품": {"monthly_rate": 0.015, "min_ratio": 0.15},         # 월 1.5%
        "가구/인테리어": {"monthly_rate": 0.01, "min_ratio": 0.25},     # 월 1%
        "여성의류": {"monthly_rate": 0.03, "min_ratio": 0.10},          # 월 3% (시즌 영향)
        "남성의류": {"monthly_rate": 0.025, "min_ratio": 0.10},
        "패션잡화": {"monthly_rate": 0.015, "min_ratio": 0.20},         # 명품은 감가 적음
        "출산/유아동": {"monthly_rate": 0.025, "min_ratio": 0.15},
        "스포츠/레저": {"monthly_rate": 0.012, "min_ratio": 0.20},
        "취미/게임": {"monthly_rate": 0.02, "min_ratio": 0.25},
        "뷰티/미용": {"monthly_rate": 0.03, "min_ratio": 0.15},        # 소모품 특성
        "생활용품": {"monthly_rate": 0.015, "min_ratio": 0.15},
        "반려동물용품": {"monthly_rate": 0.02, "min_ratio": 0.15},
        "식품": {"monthly_rate": 0.05, "min_ratio": 0.10},              # 유통기한 영향
        "도서": {"monthly_rate": 0.005, "min_ratio": 0.30},             # 감가 적음
        "티켓/교환권": {"monthly_rate": 0.01, "min_ratio": 0.50},       # 유효기한 전엔 감가 적음
        "기타 중고물품": {"monthly_rate": 0.02, "min_ratio": 0.15},
    }
    
    dep = depreciation_rules.get(category, {"monthly_rate": 0.02, "min_ratio": 0.20})
    
    # 가격 변형 노이즈 범위 (실제 데이터 분포 기반)
    if price_dist.get("stdev") and price_dist.get("median"):
        cv = price_dist["stdev"] / price_dist["median"]  # 변동계수
        noise_range = min(0.25, max(0.05, cv * 0.3))  # 변동계수의 30%, 5~25% 범위
    else:
        noise_range = 0.15
    
    return {
        "condition_multipliers": condition_multipliers,
        "depreciation": dep,
        "price_noise_range": round(noise_range, 3),
        "price_distribution": {
            "p10": price_dist.get("p10", 0),
            "p25": price_dist.get("p25", 0),
            "median": price_dist.get("median", 0),
            "p75": price_dist.get("p75", 0),
            "p90": price_dist.get("p90", 0),
        }
    }


# ──────────────────────────────────────────────
# 민감속성 현황 분석
# ──────────────────────────────────────────────
UNKNOWN_VALUES = {"알수없음", "알 수 없음", "미확인", "미상", "없음", "null", "None", "", None}

def analyze_sensitive_attributes(items: list[dict]) -> dict:
    """민감속성별 채워진 비율 + 고유값 분포"""
    if not items:
        return {}
    
    attr_stats = defaultdict(lambda: {"total": 0, "filled": 0, "values": defaultdict(int)})
    
    for item in items:
        sa = item.get("sensitive_attributes", {})
        if not sa:
            continue
        for k, v in sa.items():
            attr_stats[k]["total"] += 1
            is_filled = v not in UNKNOWN_VALUES and not isinstance(v, (list, dict))
            if is_filled:
                attr_stats[k]["filled"] += 1
                # 값 빈도 (상위 집계용)
                attr_stats[k]["values"][str(v)] += 1
    
    result = {}
    for attr, stats in attr_stats.items():
        fill_rate = round(stats["filled"] / stats["total"] * 100, 1) if stats["total"] > 0 else 0
        # 상위 10개 값
        top_values = sorted(stats["values"].items(), key=lambda x: x[1], reverse=True)[:10]
        result[attr] = {
            "fill_rate": fill_rate,
            "filled": stats["filled"],
            "total": stats["total"],
            "unique_values": len(stats["values"]),
            "top_values": {k: v for k, v in top_values}
        }
    
    return result


# ──────────────────────────────────────────────
# 메인
# ──────────────────────────────────────────────
def main():
    print("=" * 60)
    print("Step 2A: 카테고리별 가격 분포 분석")
    print("=" * 60)
    
    data = load_final_data()
    if not data:
        print("[ERROR] 데이터 없음. step1c를 먼저 실행하세요.")
        return
    
    all_analysis = {}
    all_aug_rules = {}
    all_sensitive_report = {}  # 민감속성 현황 리포트
    all_brand_stats = {}       # 브랜드별 가격 통계 (D: 브랜드 변형용)
    
    for category, items in sorted(data.items()):
        print(f"\n[{category}] ({len(items)}건)")
        
        # 1. 가격 분포
        price_dist = analyze_price_distribution(items)
        if price_dist:
            print(f"  가격: {price_dist['p25']:,}원 ~ {price_dist['median']:,}원(중앙) ~ {price_dist['p75']:,}원")
        
        # 2. Condition별 분석
        condition_ratios = analyze_condition_price_ratio(items)
        if condition_ratios:
            for cond, stats in sorted(condition_ratios.items()):
                print(f"  {cond}: 중앙값 {stats['median']:,}원 (전체 대비 {stats['ratio_to_overall']:.2f}x, {stats['count']}건)")
        
        # 3. 브랜드별 분석
        brand_prices = analyze_brand_prices(items)
        if brand_prices:
            top3 = list(brand_prices.items())[:3]
            brands_str = ", ".join(f"{b}({s['count']}건/{s['median']:,}원)" for b, s in top3)
            print(f"  주요 브랜드: {brands_str}")
        
        # 4. Augmentation 규칙
        aug_rules = generate_augmentation_rules(category, items, price_dist, condition_ratios)
        
        # 5. 민감속성 현황
        sensitive_report = analyze_sensitive_attributes(items)
        if sensitive_report:
            filled_attrs = {k: v for k, v in sensitive_report.items() if v["fill_rate"] >= 50}
            print(f"  민감속성 (50%이상 채워진 것): {list(filled_attrs.keys())}")
        
        all_analysis[category] = {
            "item_count": len(items),
            "price_distribution": price_dist,
            "condition_ratios": condition_ratios,
            "top_brands": brand_prices,
        }
        all_aug_rules[category] = aug_rules
        all_sensitive_report[category] = sensitive_report
        all_brand_stats[category] = brand_prices
    
    # 저장
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    
    analysis_path = CONFIG_DIR / "price_analysis.json"
    with open(analysis_path, "w", encoding="utf-8") as f:
        json.dump(all_analysis, f, ensure_ascii=False, indent=2)
    print(f"\n\n가격 분석 저장: {analysis_path}")
    
    aug_rules_path = CONFIG_DIR / "augmentation_rules.json"
    with open(aug_rules_path, "w", encoding="utf-8") as f:
        json.dump(all_aug_rules, f, ensure_ascii=False, indent=2)
    print(f"Augmentation 규칙 저장: {aug_rules_path}")
    
    # 민감속성 현황 리포트
    sensitive_path = CONFIG_DIR / "sensitive_attributes_report.json"
    with open(sensitive_path, "w", encoding="utf-8") as f:
        json.dump(all_sensitive_report, f, ensure_ascii=False, indent=2)
    print(f"민감속성 현황 저장: {sensitive_path}")
    
    # 브랜드별 가격 통계 (브랜드 변형 augmentation용)
    brand_stats_path = CONFIG_DIR / "brand_price_stats.json"
    with open(brand_stats_path, "w", encoding="utf-8") as f:
        json.dump(all_brand_stats, f, ensure_ascii=False, indent=2)
    print(f"브랜드 가격 통계 저장: {brand_stats_path}")
    
    # 전체 요약
    total = sum(a["item_count"] for a in all_analysis.values())
    print(f"\n총 {len(all_analysis)}개 카테고리, {total}건 분석 완료")


if __name__ == "__main__":
    main()