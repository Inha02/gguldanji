"""
Step 2B: Augmentation 기반 합성 데이터 생성 (v2)
=================================================
위치: gguldanji/ai-engine/crawler/pipeline/step2b_synthesize.py

실행:
  cd gguldanji/ai-engine
  python -m crawler.pipeline.step2b_synthesize
  python -m crawler.pipeline.step2b_synthesize --target 5000
  python -m crawler.pipeline.step2b_synthesize 패션잡화 디지털기기

수정사항 (v2):
  A) 가격 0원 데이터 augmentation 제외
  B) 카테고리별 augmentation 전략 차등 적용
  C) price_ratio null이면 피처에서 제외 처리
  D) 민감속성(브랜드) 변형 augmentation (실제 데이터 브랜드 간 교차, 3건 이상만)
"""

import json
import sys
import random
import copy
from pathlib import Path
from collections import defaultdict

import numpy as np

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
FINAL_DIR = DATA_DIR / "final"
CONFIG_DIR = DATA_DIR / "config"
SYNTH_DIR = DATA_DIR / "synthetic"

random.seed(42)
np.random.seed(42)

# ──────────────────────────────────────────────
# 설정
# ──────────────────────────────────────────────
DEFAULT_TARGET_PER_CATEGORY = 3000
CONDITION_ORDER = ["S급", "A급", "B급", "C급", "부품용"]

CONDITION_STEP_RATIO = {
    ("S급", "A급"): 0.85,
    ("A급", "S급"): 1.18,
    ("A급", "B급"): 0.78,
    ("B급", "A급"): 1.28,
    ("B급", "C급"): 0.70,
    ("C급", "B급"): 1.43,
    ("C급", "부품용"): 0.50,
    ("부품용", "C급"): 2.00,
}

BOX_PREMIUM = 1.08
ACCESSORY_PREMIUM = 1.05

# ──────────────────────────────────────────────
# [B] 카테고리별 augmentation 전략 설정
# ──────────────────────────────────────────────
# 각 카테고리에서 어떤 전략을 활성화할지 정의
# strategies: condition, usage, accessories, noise, brand
CATEGORY_STRATEGIES = {
    "디지털기기":     ["condition", "usage", "accessories", "noise", "brand"],
    "가구/인테리어":  ["condition", "usage", "accessories", "noise", "brand"],
    "출산/유아동":    ["condition", "usage", "accessories", "noise", "brand"],
    "여성의류":       ["condition", "usage", "noise", "brand"],       # 부속품 변형 의미 적음
    "패션잡화":       ["condition", "usage", "accessories", "noise", "brand"],
    "남성의류":       ["condition", "usage", "noise", "brand"],
    "가전제품":       ["condition", "usage", "accessories", "noise", "brand"],
    "생활용품":       ["condition", "usage", "accessories", "noise"],
    "스포츠/레저":    ["condition", "usage", "accessories", "noise", "brand"],
    "취미/게임":      ["condition", "usage", "accessories", "noise", "brand"],
    "뷰티/미용":      ["condition", "noise", "brand"],               # 사용기간보다 잔량이 핵심
    "반려동물용품":   ["condition", "usage", "noise"],
    "식품":           ["noise"],                                      # condition/usage 의미 없음, 유통기한이 핵심
    "도서":           ["condition", "noise"],                         # 사용기간 의미 없음, 필기여부가 핵심
    "티켓/교환권":    ["noise"],                                      # condition 의미 없음
    "기타 중고물품":  ["condition", "usage", "accessories", "noise"],
}
UNKNOWN_VALUES = {"알수없음", "알 수 없음", "미확인", "미상", "없음", "null", "None", "", None}


# ──────────────────────────────────────────────
# 데이터 로드
# ──────────────────────────────────────────────
def load_final_data() -> dict[str, list[dict]]:
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
    return data


def load_aug_rules() -> dict:
    rules_path = CONFIG_DIR / "augmentation_rules.json"
    if not rules_path.exists():
        print("[ERROR] augmentation_rules.json 없음. step2a를 먼저 실행하세요.")
        return {}
    with open(rules_path, "r", encoding="utf-8") as f:
        rules = json.load(f)

    # condition_multipliers 교정 (이전과 동일)
    VALID_CONDITIONS = ["S급", "A급", "B급", "C급", "부품용"]
    DEFAULT_MULTIPLIERS = {"S급": 1.30, "A급": 1.00, "B급": 0.75, "C급": 0.50, "부품용": 0.25}

    for category, cat_rules in rules.items():
        raw = cat_rules.get("condition_multipliers", {})
        cleaned = {k: v for k, v in raw.items() if k in VALID_CONDITIONS}
        for cond in VALID_CONDITIONS:
            if cond not in cleaned:
                cleaned[cond] = DEFAULT_MULTIPLIERS[cond]

        ordered_vals = [cleaned[c] for c in VALID_CONDITIONS]
        is_monotone = all(ordered_vals[i] >= ordered_vals[i + 1] for i in range(len(ordered_vals) - 1))

        if not is_monotone:
            a_val = cleaned.get("A급", 1.0)
            b_val = cleaned.get("B급", 0.75)
            if a_val > b_val and a_val > 0:
                cleaned["S급"] = max(a_val * 1.15, cleaned.get("S급", a_val * 1.15))
                cleaned["C급"] = min(b_val * 0.65, cleaned.get("C급", b_val * 0.65))
                cleaned["부품용"] = min(cleaned["C급"] * 0.5, 0.25)
            else:
                cleaned = dict(DEFAULT_MULTIPLIERS)

            vals = [cleaned[c] for c in VALID_CONDITIONS]
            for i in range(1, len(vals)):
                if vals[i] >= vals[i - 1]:
                    vals[i] = vals[i - 1] * 0.8
            cleaned = {c: round(v, 3) for c, v in zip(VALID_CONDITIONS, vals)}
            print(f"  [교정] {category}: multipliers 역전 → 교정됨")

        cat_rules["condition_multipliers"] = cleaned

    return rules


def load_brand_stats() -> dict:
    """브랜드별 가격 통계 로드 (D: 브랜드 변형용)"""
    path = CONFIG_DIR / "brand_price_stats.json"
    if not path.exists():
        return {}
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


# ──────────────────────────────────────────────
# 스키마 변환
# ──────────────────────────────────────────────
def parse_usage_months(period_str: str) -> int | None:
    if not period_str or period_str in ["알수없음", "미사용", "새상품"]:
        return 0 if period_str in ["미사용", "새상품"] else None
    period_str = period_str.strip().lower()
    try:
        if "개월" in period_str:
            return int(period_str.replace("개월", "").strip())
        if "년" in period_str:
            parts = period_str.split("년")
            y = int(parts[0].strip()) if parts[0].strip() else 0
            m = int(parts[1].replace("개월", "").strip()) if len(parts) > 1 and parts[1].strip().replace("개월", "").strip() else 0
            return y * 12 + m
        val = int(float(period_str))
        return val if val < 120 else None
    except (ValueError, TypeError):
        return None


def to_synth_schema(item: dict, synth_id: str, is_original: bool = True) -> dict:
    common = item.get("common_attributes", {}) or {}
    sensitive = item.get("sensitive_attributes", {}) or {}
    price = item.get("price", 0)

    usage_months = parse_usage_months(common.get("usage_period", "알수없음"))

    orig_price = common.get("original_price")
    if isinstance(orig_price, str):
        try:
            orig_price = int(orig_price.replace(",", "").replace("원", ""))
        except (ValueError, AttributeError):
            orig_price = None

    # [C] price_ratio: null이면 명시적으로 None (모델에서 피처 제외 가능)
    price_ratio = round(price / orig_price, 3) if orig_price and orig_price > 0 and price > 0 else None

    has_box = common.get("includes_box")
    if isinstance(has_box, str):
        has_box = has_box.lower() in ["true", "예", "yes", "o"]

    negotiable = common.get("negotiable")
    if isinstance(negotiable, str):
        negotiable = negotiable.lower() in ["true", "예", "yes", "가능"]

    defects = common.get("defects", "없음")
    has_defects = defects not in ["없음", "없음/미확인", None, "", "알수없음"]

    accessories = common.get("includes_accessories", "알수없음")
    has_accessories = accessories not in ["알수없음", "없음", None, "", "미포함"]

    return {
        "id": synth_id,
        "source_seq": item.get("seq"),
        "is_original": is_original,
        "category": item.get("category", ""),
        "anchor_keyword": item.get("keyword", ""),
        "common_features": {
            "condition": common.get("condition", "알수없음"),
            "usage_period_months": usage_months,
            "has_box": has_box if isinstance(has_box, bool) else None,
            "has_accessories": has_accessories,
            "has_defects": has_defects,
            "is_negotiable": negotiable if isinstance(negotiable, bool) else None,
            "image_count": item.get("image_count", 0),
        },
        "sensitive_features": sensitive,
        "price_info": {
            "original_price": orig_price,
            "selling_price": price,
            "price_ratio": price_ratio,  # [C] None이면 모델 학습 시 제외
            "price_range_min": None,
            "price_range_max": None,
            "price_label": None,
        },
        "metadata": {
            "view_count": item.get("viewCount", 0),
            "wish_count": item.get("wishCount", 0),
            "chat_count": item.get("chatCount", 0),
            "location": item.get("location", []),
            "sort_date": item.get("sortDate", ""),
        }
    }


# ──────────────────────────────────────────────
# Augmentation 전략들
# ──────────────────────────────────────────────
def augment_condition(item: dict) -> dict:
    item = copy.deepcopy(item)
    current = item["common_features"]["condition"]
    if current not in CONDITION_ORDER:
        return item

    idx = CONDITION_ORDER.index(current)
    if idx == 0:
        new_idx = 1
    elif idx == len(CONDITION_ORDER) - 1:
        new_idx = idx - 1
    else:
        new_idx = idx + random.choice([-1, 1])

    new_condition = CONDITION_ORDER[new_idx]
    ratio = CONDITION_STEP_RATIO.get((current, new_condition), 1.0)

    old_price = item["price_info"]["selling_price"]
    new_price = max(1000, round(old_price * ratio / 1000) * 1000)

    item["common_features"]["condition"] = new_condition
    item["price_info"]["selling_price"] = new_price
    if new_condition in ["C급", "부품용"]:
        item["common_features"]["has_defects"] = True
    elif new_condition == "S급":
        item["common_features"]["has_defects"] = False

    item["is_original"] = False
    item["augmentation"] = f"condition_{current}→{new_condition}"
    return item


def augment_usage(item: dict, cat_rules: dict) -> dict:
    item = copy.deepcopy(item)
    current = item["common_features"].get("usage_period_months")
    if current is None:
        return item

    dep = cat_rules.get("depreciation", {"monthly_rate": 0.02, "min_ratio": 0.20})
    delta = random.choice([-12, -6, -3, 3, 6, 12])
    new_months = max(0, current + delta)

    rate = dep["monthly_rate"]
    min_ratio = dep["min_ratio"]
    if delta > 0:
        price_ratio = max(min_ratio, 1.0 - delta * rate)
    else:
        price_ratio = min(2.0, 1.0 + abs(delta) * rate * 0.8)

    old_price = item["price_info"]["selling_price"]
    new_price = max(1000, round(old_price * price_ratio / 1000) * 1000)

    item["common_features"]["usage_period_months"] = new_months
    item["price_info"]["selling_price"] = new_price
    if new_months == 0 and item["common_features"]["condition"] in ["B급", "C급"]:
        item["common_features"]["condition"] = "A급"

    item["is_original"] = False
    item["augmentation"] = f"usage_{current}→{new_months}m"
    return item


def augment_accessories(item: dict) -> dict:
    item = copy.deepcopy(item)
    old_price = item["price_info"]["selling_price"]
    changes = []

    if random.random() < 0.5:
        has_box = item["common_features"].get("has_box")
        if has_box is True:
            item["common_features"]["has_box"] = False
            old_price = round(old_price / BOX_PREMIUM)
            changes.append("box_removed")
        elif has_box is False:
            item["common_features"]["has_box"] = True
            old_price = round(old_price * BOX_PREMIUM)
            changes.append("box_added")

    if random.random() < 0.5:
        has_acc = item["common_features"].get("has_accessories")
        if has_acc:
            item["common_features"]["has_accessories"] = False
            old_price = round(old_price / ACCESSORY_PREMIUM)
            changes.append("acc_removed")
        else:
            item["common_features"]["has_accessories"] = True
            old_price = round(old_price * ACCESSORY_PREMIUM)
            changes.append("acc_added")

    if not changes:
        return item

    item["price_info"]["selling_price"] = max(1000, round(old_price / 1000) * 1000)
    item["is_original"] = False
    item["augmentation"] = "+".join(changes)
    return item


def augment_noise(item: dict, noise_range: float = 0.10) -> dict:
    item = copy.deepcopy(item)
    old_price = item["price_info"]["selling_price"]

    noise = np.random.normal(0, noise_range / 2)
    noise = max(-noise_range, min(noise_range, noise))
    new_price = round(old_price * (1 + noise))

    if new_price >= 100000:
        new_price = round(new_price / 10000) * 10000
    elif new_price >= 10000:
        new_price = round(new_price / 1000) * 1000
    else:
        new_price = round(new_price / 500) * 500

    item["price_info"]["selling_price"] = max(500, new_price)
    item["is_original"] = False
    item["augmentation"] = f"noise_{noise:+.2f}"
    return item


# ──────────────────────────────────────────────
# [D] 브랜드 변형 augmentation
# ──────────────────────────────────────────────
def augment_brand(item: dict, brand_stats: dict, category: str) -> dict:
    """
    같은 카테고리 내 실제 존재하는 브랜드로 교차.
    - 3건 이상인 브랜드만 대상
    - 현재 브랜드의 중앙값 vs 새 브랜드의 중앙값 비율로 가격 재산정
    """
    item = copy.deepcopy(item)
    cat_brands = brand_stats.get(category, {})

    if len(cat_brands) < 2:
        return item

    current_brand = item["sensitive_features"].get("브랜드", "알수없음")
    if current_brand in UNKNOWN_VALUES:
        return item

    # 현재 브랜드의 통계
    current_stats = cat_brands.get(current_brand)
    if not current_stats or current_stats.get("count", 0) < 3:
        return item

    # 교차 대상 브랜드 선택 (3건 이상, 현재와 다른 것)
    candidates = [(b, s) for b, s in cat_brands.items()
                  if b != current_brand and s.get("count", 0) >= 3]
    if not candidates:
        return item

    new_brand, new_stats = random.choice(candidates)

    # 가격 비율 계산
    current_median = current_stats.get("median", 1)
    new_median = new_stats.get("median", 1)
    if current_median <= 0:
        current_median = 1

    ratio = new_median / current_median
    # 비율이 너무 극단적이면 제한 (0.1x ~ 10x)
    ratio = max(0.1, min(10.0, ratio))

    old_price = item["price_info"]["selling_price"]
    new_price = round(old_price * ratio)

    if new_price >= 100000:
        new_price = round(new_price / 10000) * 10000
    elif new_price >= 10000:
        new_price = round(new_price / 1000) * 1000
    else:
        new_price = round(new_price / 500) * 500

    new_price = max(500, new_price)

    item["sensitive_features"]["브랜드"] = new_brand
    item["price_info"]["selling_price"] = new_price
    item["is_original"] = False
    item["augmentation"] = f"brand_{current_brand}→{new_brand}"
    return item


# ──────────────────────────────────────────────
# 가격 범위 & 라벨
# ──────────────────────────────────────────────
def assign_price_range_and_label(item: dict, price_dist: dict) -> dict:
    price = item["price_info"]["selling_price"]
    if not price_dist or price <= 0:
        return item

    p25 = price_dist.get("p25", 0)
    p75 = price_dist.get("p75", 0)

    item["price_info"]["price_range_min"] = max(1000, round(price * 0.85 / 1000) * 1000)
    item["price_info"]["price_range_max"] = round(price * 1.15 / 1000) * 1000

    if price <= p25:
        item["price_info"]["price_label"] = "저렴"
    elif price <= p75:
        item["price_info"]["price_label"] = "적정"
    else:
        item["price_info"]["price_label"] = "비쌈"

    return item


# ──────────────────────────────────────────────
# 카테고리별 합성
# ──────────────────────────────────────────────
def synthesize_category(category: str, items: list[dict], aug_rules: dict,
                        brand_stats: dict, target_count: int) -> list[dict]:
    cat_rules = aug_rules.get(category, {})
    noise_range = cat_rules.get("price_noise_range", 0.10)
    price_dist = cat_rules.get("price_distribution", {})
    strategies = CATEGORY_STRATEGIES.get(category, ["condition", "usage", "noise"])

    synth_data = []
    counter = 0

    # [A] 가격 0원 제외한 원본만 augmentation 대상
    augmentable_items = []

    for item in items:
        counter += 1
        safe_cat = category.replace("/", "_")
        synth_id = f"synth_{safe_cat}_{item.get('keyword', 'unk')}_{counter:05d}"
        synth_item = to_synth_schema(item, synth_id, is_original=True)
        synth_item = assign_price_range_and_label(synth_item, price_dist)
        synth_data.append(synth_item)

        # [A] 0원이 아닌 것만 augmentation 대상
        if item.get("price", 0) > 0:
            augmentable_items.append(synth_item)

    original_count = len(synth_data)
    remaining = target_count - original_count

    if remaining <= 0:
        print(f"  원본({original_count}건) ≥ 목표({target_count}건) → augmentation 불필요")
        return synth_data

    if not augmentable_items:
        print(f"  [WARN] augmentation 대상 0건 (전부 0원)")
        return synth_data

    print(f"  augmentation 대상: {len(augmentable_items)}건, 생성 필요: {remaining}건")

    # [B] 카테고리별 활성 전략으로만 augmentation
    augmented = []
    max_attempts = remaining * 3  # 무한루프 방지
    attempts = 0

    while len(augmented) < remaining and attempts < max_attempts:
        source = random.choice(augmentable_items)
        strategy = random.choice(strategies)
        attempts += 1

        if strategy == "condition":
            aug_item = augment_condition(source)
        elif strategy == "usage":
            aug_item = augment_usage(source, cat_rules)
        elif strategy == "accessories":
            aug_item = augment_accessories(source)
            if not aug_item.get("augmentation"):
                continue
        elif strategy == "noise":
            aug_item = augment_noise(source, noise_range)
        elif strategy == "brand":
            aug_item = augment_brand(source, brand_stats, category)
            if not aug_item.get("augmentation"):
                continue
        else:
            continue

        # 가격 유효성
        if aug_item["price_info"]["selling_price"] <= 0:
            continue

        counter += 1
        safe_cat = category.replace("/", "_")
        aug_item["id"] = f"synth_{safe_cat}_{source.get('anchor_keyword', 'unk')}_{counter:05d}"
        aug_item = assign_price_range_and_label(aug_item, price_dist)
        augmented.append(aug_item)

    synth_data.extend(augmented)
    return synth_data


# ──────────────────────────────────────────────
# 메인
# ──────────────────────────────────────────────
def main():
    print("=" * 60)
    print("Step 2B: Augmentation 합성 데이터 생성 (v2)")
    print("=" * 60)

    target_count = DEFAULT_TARGET_PER_CATEGORY
    categories_filter = []
    args = sys.argv[1:]
    i = 0
    while i < len(args):
        if args[i] == "--target" and i + 1 < len(args):
            target_count = int(args[i + 1])
            i += 2
        else:
            categories_filter.append(args[i])
            i += 1

    data = load_final_data()
    aug_rules = load_aug_rules()
    brand_stats = load_brand_stats()

    if not data or not aug_rules:
        return

    if categories_filter:
        data = {k: v for k, v in data.items() if k in categories_filter}

    print(f"목표: 카테고리당 {target_count}건")
    print(f"대상: {len(data)}개 카테고리\n")

    SYNTH_DIR.mkdir(parents=True, exist_ok=True)

    total_original = 0
    total_synth = 0
    strategy_summary = defaultdict(int)

    for category, items in sorted(data.items()):
        active = CATEGORY_STRATEGIES.get(category, [])
        print(f"[{category}] 원본 {len(items)}건 → 목표 {target_count}건 | 전략: {active}")

        synth_data = synthesize_category(category, items, aug_rules, brand_stats, target_count)

        orig = sum(1 for s in synth_data if s.get("is_original"))
        aug = len(synth_data) - orig
        total_original += orig
        total_synth += len(synth_data)

        # augmentation 유형 집계
        for s in synth_data:
            aug_type = s.get("augmentation", "original")
            if aug_type.startswith("condition"):
                strategy_summary["condition"] += 1
            elif aug_type.startswith("usage"):
                strategy_summary["usage"] += 1
            elif aug_type.startswith("box") or aug_type.startswith("acc"):
                strategy_summary["accessories"] += 1
            elif aug_type.startswith("noise"):
                strategy_summary["noise"] += 1
            elif aug_type.startswith("brand"):
                strategy_summary["brand"] += 1
            else:
                strategy_summary["original"] += 1

        safe_name = category.replace("/", "_")
        output_path = SYNTH_DIR / f"{safe_name}_synth.jsonl"
        with open(output_path, "w", encoding="utf-8") as f:
            for item in synth_data:
                f.write(json.dumps(item, ensure_ascii=False) + "\n")

        print(f"  → {len(synth_data)}건 (원본 {orig} + aug {aug})")

    # 통합 파일
    all_synth = []
    for filepath in sorted(SYNTH_DIR.glob("*_synth.jsonl")):
        with open(filepath, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    all_synth.append(json.loads(line))

    all_path = SYNTH_DIR / "all_synthetic.jsonl"
    with open(all_path, "w", encoding="utf-8") as f:
        for item in all_synth:
            f.write(json.dumps(item, ensure_ascii=False) + "\n")

    print(f"\n{'=' * 60}")
    print(f"합성 데이터 생성 완료")
    print(f"{'=' * 60}")
    print(f"  카테고리: {len(data)}개")
    print(f"  원본: {total_original}건")
    print(f"  합성 (원본 포함): {total_synth}건")
    print(f"  통합: {all_path} ({len(all_synth)}건)")
    print(f"\n  전략별 건수:")
    for k, v in sorted(strategy_summary.items()):
        print(f"    {k}: {v}건")

    report = {
        "target_per_category": target_count,
        "total_original": total_original,
        "total_synthetic": total_synth,
        "categories": len(data),
        "strategy_breakdown": dict(strategy_summary),
    }
    report_path = DATA_DIR / "synthesis_report.json"
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    main()