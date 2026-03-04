"""
Step 3B: 모델 학습 + 평가 (v2)
================================
개선사항:
  1) log(가격) 학습 → exp 변환 후 평가
  2) Optuna 하이퍼파라미터 튜닝 (카테고리별 최적화)
  3) XGBoost vs LightGBM 비교 유지
"""

import json
import pickle
from pathlib import Path

import numpy as np
import pandas as pd
import xgboost as xgb
import lightgbm as lgb
from sklearn.metrics import mean_absolute_error, r2_score

try:
    import optuna
    optuna.logging.set_verbosity(optuna.logging.WARNING)
    HAS_OPTUNA = True
except ImportError:
    HAS_OPTUNA = False
    print("[WARN] optuna 미설치. 기본 파라미터로 학습합니다. pip install optuna")

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
MODEL_DIR = DATA_DIR / "models"

RANDOM_STATE = 42
N_OPTUNA_TRIALS = 30  # 카테고리당 튜닝 횟수


# ──────────────────────────────────────────────
# 평가 (원래 가격 스케일)
# ──────────────────────────────────────────────
def mape(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    mask = y_true > 0
    if mask.sum() == 0:
        return 0.0
    return float(np.mean(np.abs((y_true[mask] - y_pred[mask]) / y_true[mask])) * 100)


def evaluate_raw(y_test_raw: np.ndarray, y_pred_log: np.ndarray) -> dict:
    """log 예측을 원래 스케일로 변환 후 평가"""
    y_pred_raw = np.expm1(y_pred_log)  # log1p의 역변환
    y_pred_raw = np.maximum(y_pred_raw, 0)

    return {
        "MAPE": round(mape(y_test_raw, y_pred_raw), 2),
        "MAE": round(float(mean_absolute_error(y_test_raw, y_pred_raw)), 0),
        "R2": round(float(r2_score(y_test_raw, y_pred_raw)), 4),
        "median_error": round(float(np.median(np.abs(y_test_raw - y_pred_raw))), 0),
        "median_pct_error": round(float(np.median(
            np.abs(y_test_raw - y_pred_raw) / np.maximum(y_test_raw, 1) * 100
        )), 1),
    }


# ──────────────────────────────────────────────
# Optuna 튜닝
# ──────────────────────────────────────────────
def tune_xgboost(features: dict) -> dict:
    if not HAS_OPTUNA:
        return {
            "max_depth": 6, "learning_rate": 0.05, "n_estimators": 500,
            "min_child_weight": 5, "subsample": 0.8, "colsample_bytree": 0.8,
            "reg_alpha": 0.1, "reg_lambda": 1.0,
        }

    def objective(trial):
        params = {
            "max_depth": trial.suggest_int("max_depth", 3, 8),
            "learning_rate": trial.suggest_float("learning_rate", 0.01, 0.2, log=True),
            "n_estimators": trial.suggest_int("n_estimators", 100, 800),
            "min_child_weight": trial.suggest_int("min_child_weight", 1, 20),
            "subsample": trial.suggest_float("subsample", 0.6, 1.0),
            "colsample_bytree": trial.suggest_float("colsample_bytree", 0.5, 1.0),
            "reg_alpha": trial.suggest_float("reg_alpha", 1e-3, 10.0, log=True),
            "reg_lambda": trial.suggest_float("reg_lambda", 1e-3, 10.0, log=True),
        }
        model = xgb.XGBRegressor(
            objective="reg:squarederror", random_state=RANDOM_STATE,
            n_jobs=-1, **params
        )
        model.fit(features["X_train"], features["y_train"],
                  sample_weight=features["w_train"],
                  eval_set=[(features["X_test"], features["y_test"])],
                  verbose=False)
        pred = model.predict(features["X_test"])
        y_pred_raw = np.expm1(pred)
        y_pred_raw = np.maximum(y_pred_raw, 0)
        return mape(features["y_test_raw"], y_pred_raw)

    study = optuna.create_study(direction="minimize",
                                sampler=optuna.samplers.TPESampler(seed=RANDOM_STATE))
    study.optimize(objective, n_trials=N_OPTUNA_TRIALS, show_progress_bar=False)
    return study.best_params


def tune_lightgbm(features: dict) -> dict:
    if not HAS_OPTUNA:
        return {
            "max_depth": 6, "learning_rate": 0.05, "n_estimators": 500,
            "min_child_samples": 5, "subsample": 0.8, "colsample_bytree": 0.8,
            "reg_alpha": 0.1, "reg_lambda": 1.0,
        }

    def objective(trial):
        params = {
            "max_depth": trial.suggest_int("max_depth", 3, 8),
            "learning_rate": trial.suggest_float("learning_rate", 0.01, 0.2, log=True),
            "n_estimators": trial.suggest_int("n_estimators", 100, 800),
            "min_child_samples": trial.suggest_int("min_child_samples", 1, 30),
            "subsample": trial.suggest_float("subsample", 0.6, 1.0),
            "colsample_bytree": trial.suggest_float("colsample_bytree", 0.5, 1.0),
            "reg_alpha": trial.suggest_float("reg_alpha", 1e-3, 10.0, log=True),
            "reg_lambda": trial.suggest_float("reg_lambda", 1e-3, 10.0, log=True),
        }
        model = lgb.LGBMRegressor(
            objective="regression", random_state=RANDOM_STATE,
            n_jobs=-1, verbose=-1, **params
        )
        model.fit(features["X_train"], features["y_train"],
                  sample_weight=features["w_train"],
                  eval_set=[(features["X_test"], features["y_test"])])
        pred = model.predict(features["X_test"])
        y_pred_raw = np.expm1(pred)
        y_pred_raw = np.maximum(y_pred_raw, 0)
        return mape(features["y_test_raw"], y_pred_raw)

    study = optuna.create_study(direction="minimize",
                                sampler=optuna.samplers.TPESampler(seed=RANDOM_STATE))
    study.optimize(objective, n_trials=N_OPTUNA_TRIALS, show_progress_bar=False)
    return study.best_params


# ──────────────────────────────────────────────
# 학습
# ──────────────────────────────────────────────
def train_xgboost(features: dict, params: dict) -> tuple:
    model = xgb.XGBRegressor(
        objective="reg:squarederror", random_state=RANDOM_STATE, n_jobs=-1, **params
    )
    model.fit(features["X_train"], features["y_train"],
              sample_weight=features["w_train"],
              eval_set=[(features["X_test"], features["y_test"])],
              verbose=False)
    y_pred_log = model.predict(features["X_test"])
    metrics = evaluate_raw(features["y_test_raw"], y_pred_log)
    importance = dict(zip(features["feature_names"], model.feature_importances_.tolist()))
    return model, metrics, importance


def train_lightgbm(features: dict, params: dict) -> tuple:
    model = lgb.LGBMRegressor(
        objective="regression", random_state=RANDOM_STATE, n_jobs=-1, verbose=-1, **params
    )
    model.fit(features["X_train"], features["y_train"],
              sample_weight=features["w_train"],
              eval_set=[(features["X_test"], features["y_test"])])
    y_pred_log = model.predict(features["X_test"])
    metrics = evaluate_raw(features["y_test_raw"], y_pred_log)
    importance = dict(zip(features["feature_names"], model.feature_importances_.tolist()))
    return model, metrics, importance


# ──────────────────────────────────────────────
# 카테고리별 학습 + 비교
# ──────────────────────────────────────────────
def train_category(category: str, features: dict) -> dict:
    print(f"\n{'='*50}")
    print(f"[{category}]")
    print(f"  Train: {features['X_train'].shape}, Test: {features['X_test'].shape}")

    # Optuna 튜닝
    print(f"  XGBoost 튜닝 중 ({N_OPTUNA_TRIALS} trials)...")
    xgb_params = tune_xgboost(features)
    xgb_model, xgb_metrics, xgb_imp = train_xgboost(features, xgb_params)
    print(f"  XGBoost — MAPE: {xgb_metrics['MAPE']}%, MAE: {xgb_metrics['MAE']:,.0f}원, "
          f"R²: {xgb_metrics['R2']}, median오차: {xgb_metrics['median_pct_error']}%")

    print(f"  LightGBM 튜닝 중 ({N_OPTUNA_TRIALS} trials)...")
    lgb_params = tune_lightgbm(features)
    lgb_model, lgb_metrics, lgb_imp = train_lightgbm(features, lgb_params)
    print(f"  LightGBM — MAPE: {lgb_metrics['MAPE']}%, MAE: {lgb_metrics['MAE']:,.0f}원, "
          f"R²: {lgb_metrics['R2']}, median오차: {lgb_metrics['median_pct_error']}%")

    # 승자 선택 (median_pct_error 기준 — MAPE보다 이상치에 안정적)
    if xgb_metrics["median_pct_error"] <= lgb_metrics["median_pct_error"]:
        winner = "xgboost"
        best_model, best_metrics, best_imp = xgb_model, xgb_metrics, xgb_imp
        best_params = xgb_params
    else:
        winner = "lightgbm"
        best_model, best_metrics, best_imp = lgb_model, lgb_metrics, lgb_imp
        best_params = lgb_params

    print(f"  → 승자: {winner} (median 오차 {best_metrics['median_pct_error']}%)")

    sorted_imp = sorted(best_imp.items(), key=lambda x: x[1], reverse=True)[:5]
    for fname, score in sorted_imp:
        print(f"    {fname}: {score:.4f}")

    # 저장
    safe_name = category.replace("/", "_")
    model_path = MODEL_DIR / f"{safe_name}_model.pkl"
    model_data = {
        "model": best_model,
        "model_type": winner,
        "metrics": best_metrics,
        "feature_names": features["feature_names"],
        "encoding_maps": features["encoding_maps"],
        "feature_importance": best_imp,
        "best_params": best_params,
        "log_transform": True,  # 추론 시 expm1 필요
    }
    with open(model_path, "wb") as f:
        pickle.dump(model_data, f)

    return {
        "category": category,
        "winner": winner,
        "xgboost": xgb_metrics,
        "lightgbm": lgb_metrics,
        "n_features": len(features["feature_names"]),
        "train_size": features["X_train"].shape[0],
        "test_size": features["X_test"].shape[0],
        "top_features": sorted_imp,
        "best_params": best_params,
    }


# ──────────────────────────────────────────────
# 메인
# ──────────────────────────────────────────────
def main():
    print("=" * 60)
    print("Step 3B: 모델 학습 (v2)")
    print(f"  - log(가격) 학습 → 원래 스케일 평가")
    print(f"  - Optuna 튜닝 ({N_OPTUNA_TRIALS} trials/모델)")
    print(f"  - median % 오차 기준 승자 선택")
    print("=" * 60)

    feature_files = sorted(MODEL_DIR.glob("*_features.pkl"))
    if not feature_files:
        print("[ERROR] 피처 파일 없음")
        return

    print(f"피처 파일: {len(feature_files)}개")

    results = []
    for fp in feature_files:
        category = fp.stem.replace("_features", "").replace("_", "/")
        with open(fp, "rb") as f:
            features = pickle.load(f)
        result = train_category(category, features)
        results.append(result)

    # 요약
    print(f"\n{'='*70}")
    print(f"{'카테고리':<18} {'승자':<10} {'MAPE':>8} {'MAE':>10} {'R²':>8} {'median%':>8}")
    print("-" * 70)

    xgb_wins = lgb_wins = 0
    median_errors = []

    for r in results:
        w = r["winner"]
        m = r[w]
        if w == "xgboost": xgb_wins += 1
        else: lgb_wins += 1
        median_errors.append(m["median_pct_error"])
        print(f"{r['category']:<18} {w:<10} {m['MAPE']:>7.1f}% {m['MAE']:>9,.0f}원 "
              f"{m['R2']:>7.4f} {m['median_pct_error']:>7.1f}%")

    print("-" * 70)
    print(f"XGBoost: {xgb_wins}승, LightGBM: {lgb_wins}승")
    print(f"전체 median 오차: {np.mean(median_errors):.1f}% (평균)")

    # 리포트
    def convert(obj):
        if isinstance(obj, (np.integer,)): return int(obj)
        if isinstance(obj, (np.floating, float)): return round(float(obj), 4)
        if isinstance(obj, np.ndarray): return obj.tolist()
        return obj

    report_path = DATA_DIR / "training_report.json"
    serializable = json.loads(json.dumps(results, default=convert))
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(serializable, f, ensure_ascii=False, indent=2)
    print(f"\n리포트: {report_path}")


if __name__ == "__main__":
    main()