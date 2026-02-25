"""
Step 3A: 피처 엔지니어링 (v2)
==============================
개선사항:
  1) log(가격) 변환 → skewed 분포 해결
  2) augmented 비율 max 50% 제한 → 과적합 방지
  3) Target Encoding 시 원본 데이터만 사용 → data leakage 방지
"""

import json
import pickle
import sys
from pathlib import Path
from collections import defaultdict

import numpy as np
import pandas as pd
from sklearn.model_selection import GroupShuffleSplit

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
SYNTH_DIR = DATA_DIR / "synthetic"
MODEL_DIR = DATA_DIR / "models"

TEST_SIZE = 0.2
MAX_AUG_RATIO = 0.5  # augmented 데이터 최대 50%
RANDOM_STATE = 42

CONDITION_MAP = {"S급": 4, "A급": 3, "B급": 2, "C급": 1, "부품용": 0, "알수없음": -1}
UNKNOWN_VALUES = {"알수없음", "알 수 없음", "미확인", "미상", "없음", "null", "None", "", "추론불가"}


# ──────────────────────────────────────────────
# 데이터 로드
# ──────────────────────────────────────────────
def load_synthetic_data() -> pd.DataFrame:
    all_path = SYNTH_DIR / "all_synthetic.jsonl"
    if not all_path.exists():
        print(f"[ERROR] {all_path} 없음")
        return pd.DataFrame()
    records = []
    with open(all_path, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                records.append(json.loads(line))
    print(f"전체 데이터 로드: {len(records)}건")
    return pd.DataFrame(records)


# ──────────────────────────────────────────────
# augmented 비율 제한
# ──────────────────────────────────────────────
def limit_augmented_ratio(cat_df: pd.DataFrame, max_ratio: float = MAX_AUG_RATIO) -> pd.DataFrame:
    """원본은 전부 유지, augmented는 원본 수 이하로 샘플링"""
    originals = cat_df[cat_df["is_original"] == True]
    augmented = cat_df[cat_df["is_original"] == False]

    n_orig = len(originals)
    max_aug = int(n_orig * max_ratio / (1 - max_ratio))  # 50% 비율이면 원본 수와 같음

    if len(augmented) > max_aug:
        augmented = augmented.sample(n=max_aug, random_state=RANDOM_STATE)

    result = pd.concat([originals, augmented]).reset_index(drop=True)
    return result


# ──────────────────────────────────────────────
# 피처 추출
# ──────────────────────────────────────────────
def extract_common_features(df: pd.DataFrame) -> pd.DataFrame:
    common = pd.json_normalize(df["common_features"])
    common.columns = [f"cf_{c}" for c in common.columns]

    common["cf_condition_ord"] = common["cf_condition"].map(CONDITION_MAP).fillna(-1).astype(int)

    for col in ["cf_has_box", "cf_has_accessories", "cf_has_defects", "cf_is_negotiable"]:
        if col in common.columns:
            common[col] = common[col].map({True: 1, False: 0}).fillna(-1).astype(int)

    if "cf_usage_period_months" in common.columns:
        common["cf_usage_period_months"] = common["cf_usage_period_months"].fillna(-1).astype(int)

    if "cf_image_count" in common.columns:
        common["cf_image_count"] = common["cf_image_count"].fillna(0).astype(int)

    return common


def extract_sensitive_features(df: pd.DataFrame) -> pd.DataFrame:
    sensitive = pd.json_normalize(df["sensitive_features"].apply(
        lambda x: x if isinstance(x, dict) else {}
    ))
    sensitive.columns = [f"sf_{c}" for c in sensitive.columns]

    for col in sensitive.columns:
        sensitive[col] = sensitive[col].apply(
            lambda x: np.nan if (isinstance(x, str) and x in UNKNOWN_VALUES) or x is None else x
        )
    return sensitive


def extract_metadata_features(df: pd.DataFrame) -> pd.DataFrame:
    meta = pd.json_normalize(df["metadata"].apply(lambda x: x if isinstance(x, dict) else {}))
    result = pd.DataFrame()
    for col in ["view_count", "wish_count", "chat_count"]:
        if col in meta.columns:
            result[f"meta_{col}"] = meta[col].fillna(0).astype(int)
    return result


def extract_price(df: pd.DataFrame) -> pd.Series:
    return pd.json_normalize(df["price_info"])["selling_price"].astype(float)


# ──────────────────────────────────────────────
# Target Encoding (원본 데이터만 사용)
# ──────────────────────────────────────────────
def target_encode_column(train_df: pd.DataFrame, test_df: pd.DataFrame,
                         col: str, target: str, smoothing: int = 10) -> tuple:
    global_mean = train_df[target].mean()
    agg = train_df.groupby(col)[target].agg(["mean", "count"])
    smooth = (agg["count"] * agg["mean"] + smoothing * global_mean) / (agg["count"] + smoothing)

    train_encoded = train_df[col].map(smooth).fillna(global_mean)
    test_encoded = test_df[col].map(smooth).fillna(global_mean)

    return train_encoded, test_encoded, smooth.to_dict(), global_mean


def build_target_encoding_from_originals(cat_df: pd.DataFrame, sensitive_df: pd.DataFrame,
                                         prices: pd.Series, train_idx: np.ndarray,
                                         test_idx: np.ndarray) -> tuple:
    """
    원본 데이터만으로 Target Encoding 통계를 계산하고 전체에 적용.
    → augmented 데이터의 data leakage 방지
    """
    # 원본 마스크
    is_orig = cat_df["is_original"].values

    encoding_maps = {}
    te_train_parts = []
    te_test_parts = []
    te_col_names = []

    for col in sensitive_df.columns:
        series = sensitive_df[col]
        fill_rate = series.notna().mean()
        n_unique = series.nunique()

        if fill_rate < 0.3 or n_unique < 2:
            continue

        # 숫자형 판별
        numeric_series = pd.to_numeric(series, errors="coerce")
        numeric_rate = numeric_series.notna().mean()
        original_notna = series.notna().mean()
        is_numeric = (original_notna > 0) and (numeric_rate / max(original_notna, 0.01) > 0.8)

        if is_numeric and numeric_rate > 0.3:
            # 순수 숫자형
            fill_val = numeric_series.iloc[train_idx].median() if numeric_series.iloc[train_idx].notna().any() else 0
            te_train_parts.append(numeric_series.iloc[train_idx].fillna(fill_val).values)
            te_test_parts.append(numeric_series.iloc[test_idx].fillna(fill_val).values)
            te_col_names.append(col + "_num")
            encoding_maps[col] = {"type": "numeric", "fill_value": float(fill_val)}
        else:
            # 문자열 → Target Encoding (원본 train 데이터만으로 통계 계산)
            str_series = series.astype(str).replace(
                {"nan": np.nan, "None": np.nan, "-1": np.nan, "-1.0": np.nan}
            )

            # 원본 & train인 데이터만으로 인코딩 맵 계산
            orig_train_mask = is_orig[train_idx]
            orig_train_col = str_series.iloc[train_idx][orig_train_mask]
            orig_train_price = prices.iloc[train_idx][orig_train_mask]

            if orig_train_col.notna().sum() < 5:
                continue

            global_mean = orig_train_price.mean()
            temp_df = pd.DataFrame({"col": orig_train_col, "price": orig_train_price})
            agg = temp_df.groupby("col")["price"].agg(["mean", "count"])
            smooth = (agg["count"] * agg["mean"] + 10 * global_mean) / (agg["count"] + 10)
            enc_map = smooth.to_dict()

            # 전체 train/test에 적용
            train_encoded = str_series.iloc[train_idx].map(enc_map).fillna(global_mean)
            test_encoded = str_series.iloc[test_idx].map(enc_map).fillna(global_mean)

            te_train_parts.append(train_encoded.values)
            te_test_parts.append(test_encoded.values)
            te_col_names.append(col + "_te")
            encoding_maps[col] = {"map": enc_map, "global_mean": float(global_mean)}

    return te_train_parts, te_test_parts, te_col_names, encoding_maps


# ──────────────────────────────────────────────
# sample_weight
# ──────────────────────────────────────────────
def compute_sample_weights(df: pd.DataFrame) -> np.ndarray:
    return np.where(df["is_original"].values, 1.0, 0.3)


# ──────────────────────────────────────────────
# 카테고리별 피처 매트릭스 생성
# ──────────────────────────────────────────────
def build_category_features(category: str, cat_df: pd.DataFrame) -> dict | None:
    if len(cat_df) < 20:
        print(f"  [SKIP] {category}: 데이터 {len(cat_df)}건")
        return None

    # augmented 비율 제한
    before = len(cat_df)
    cat_df = limit_augmented_ratio(cat_df)
    n_orig = (cat_df["is_original"] == True).sum()
    n_aug = (cat_df["is_original"] == False).sum()
    print(f"  데이터: {before}건 → {len(cat_df)}건 (원본 {n_orig}, aug {n_aug}, "
          f"aug비율 {n_aug/len(cat_df)*100:.0f}%)")

    # 가격 0 제거
    prices = extract_price(cat_df)
    valid_mask = prices > 0
    cat_df = cat_df[valid_mask].reset_index(drop=True)
    prices = prices[valid_mask].reset_index(drop=True)

    if len(cat_df) < 20:
        return None

    # log 가격 변환
    log_prices = np.log1p(prices)

    # 피처 추출
    common_df = extract_common_features(cat_df)
    sensitive_df = extract_sensitive_features(cat_df)
    meta_df = extract_metadata_features(cat_df)

    # train/test 분리 (source_seq 기준)
    groups = cat_df["source_seq"].fillna(pd.Series(cat_df.index.astype(str), index=cat_df.index))
    splitter = GroupShuffleSplit(n_splits=1, test_size=TEST_SIZE, random_state=RANDOM_STATE)
    train_idx, test_idx = next(splitter.split(cat_df, groups=groups))

    # 공통 피처
    common_cols = ["cf_condition_ord", "cf_usage_period_months", "cf_has_box",
                   "cf_has_accessories", "cf_has_defects", "cf_is_negotiable", "cf_image_count"]
    common_cols = [c for c in common_cols if c in common_df.columns]

    # 민감속성 Target Encoding (원본 기반)
    te_train_parts, te_test_parts, te_col_names, encoding_maps = \
        build_target_encoding_from_originals(cat_df, sensitive_df, prices, train_idx, test_idx)

    # 메타데이터
    meta_cols = list(meta_df.columns)

    # 합치기
    feature_names = common_cols + te_col_names + meta_cols

    X_train_parts = [common_df[common_cols].iloc[train_idx].values]
    if te_train_parts:
        X_train_parts.append(np.column_stack(te_train_parts))
    X_train_parts.append(meta_df[meta_cols].iloc[train_idx].values)
    X_train = np.hstack(X_train_parts).astype(np.float32)

    X_test_parts = [common_df[common_cols].iloc[test_idx].values]
    if te_test_parts:
        X_test_parts.append(np.column_stack(te_test_parts))
    X_test_parts.append(meta_df[meta_cols].iloc[test_idx].values)
    X_test = np.hstack(X_test_parts).astype(np.float32)

    # log 가격
    y_train = log_prices.iloc[train_idx].values.astype(np.float32)
    y_test = log_prices.iloc[test_idx].values.astype(np.float32)

    # 원래 가격도 저장 (평가용)
    y_train_raw = prices.iloc[train_idx].values.astype(np.float32)
    y_test_raw = prices.iloc[test_idx].values.astype(np.float32)

    w_train = compute_sample_weights(cat_df.iloc[train_idx])
    w_test = compute_sample_weights(cat_df.iloc[test_idx])

    X_train = np.nan_to_num(X_train, nan=-1.0)
    X_test = np.nan_to_num(X_test, nan=-1.0)

    print(f"  피처 {len(feature_names)}개, Train: {X_train.shape[0]}건, Test: {X_test.shape[0]}건")

    return {
        "X_train": X_train, "X_test": X_test,
        "y_train": y_train, "y_test": y_test,           # log 가격
        "y_train_raw": y_train_raw, "y_test_raw": y_test_raw,  # 원래 가격
        "w_train": w_train, "w_test": w_test,
        "feature_names": feature_names,
        "encoding_maps": encoding_maps,
        "train_source_seqs": cat_df.iloc[train_idx]["source_seq"].tolist(),
        "test_source_seqs": cat_df.iloc[test_idx]["source_seq"].tolist(),
    }


# ──────────────────────────────────────────────
# 메인
# ──────────────────────────────────────────────
def main():
    print("=" * 60)
    print("Step 3A: 피처 엔지니어링 (v2)")
    print("  - log(가격) 변환")
    print("  - augmented 비율 max 50%")
    print("  - 원본 기반 Target Encoding")
    print("=" * 60)

    df = load_synthetic_data()
    if df.empty:
        return

    MODEL_DIR.mkdir(parents=True, exist_ok=True)

    categories = sorted(df["category"].unique())
    print(f"카테고리: {len(categories)}개\n")

    summary = []
    for category in categories:
        cat_df = df[df["category"] == category].reset_index(drop=True)
        print(f"\n[{category}] ({len(cat_df)}건)")

        result = build_category_features(category, cat_df)
        if result is None:
            continue

        safe_name = category.replace("/", "_")
        save_path = MODEL_DIR / f"{safe_name}_features.pkl"
        with open(save_path, "wb") as f:
            pickle.dump(result, f)

        summary.append({
            "category": category,
            "total": len(cat_df),
            "used": result["X_train"].shape[0] + result["X_test"].shape[0],
            "train": result["X_train"].shape[0],
            "test": result["X_test"].shape[0],
            "n_features": len(result["feature_names"]),
            "features": result["feature_names"],
        })

    print(f"\n{'=' * 60}")
    for s in summary:
        print(f"  {s['category']}: {s['n_features']}개 피처, "
              f"train={s['train']}, test={s['test']} (전체 {s['total']}→사용 {s['used']})")

    report_path = DATA_DIR / "feature_report.json"
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)
    print(f"\n리포트: {report_path}")


if __name__ == "__main__":
    main()