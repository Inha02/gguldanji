"""
꿀단지 AI Engine — 가격 가이드 API
====================================
FastAPI 서버

실행:
  uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload

Swagger UI:
  http://localhost:8000/docs
"""

import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from api.schemas import (
    EstimateRequest, EstimateResponse, Explanation, SimilarTrade, TopFactor,
    CategoriesResponse, CategoryInfo, HealthResponse,
    CATEGORY_SCHEMA, VALID_CONDITIONS,
)
from api.dependencies import get_engine
from profiling.router import router as profiling_router


# ──────────────────────────────────────────────
# 서버 시작/종료 이벤트
# ──────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    """서버 시작 시 모델 로드 (콜드스타트 방지)"""
    print("=" * 50)
    print("꿀단지 AI Engine 시작")
    print("=" * 50)
    start = time.time()
    engine = get_engine()
    elapsed = time.time() - start
    n_models = len(engine.tree.models)
    n_rag = len(engine.rag.collections)
    print(f"초기화 완료: 모델 {n_models}개, RAG {n_rag}개 ({elapsed:.1f}초)")
    yield
    print("서버 종료")


# ──────────────────────────────────────────────
# FastAPI 앱
# ──────────────────────────────────────────────
app = FastAPI(
    title="꿀단지 가격 가이드 API",
    description="중고 상품 적정 가격 추정 API (3-Layer: ML 모델 + LLM Fallback + RAG)",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS 설정 (개발 중에는 전체 허용, 배포 시 도메인 제한)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ──────────────────────────────────────────────
# POST /api/v1/estimate
# ──────────────────────────────────────────────
@app.post(
    "/api/v1/estimate",
    response_model=EstimateResponse,
    summary="가격 추정",
    description="상품 카테고리와 속성을 입력하면 적정 가격 범위와 유사 거래 근거를 반환합니다.",
)
async def estimate_price(req: EstimateRequest):
    # 검증: 카테고리
    if req.category not in CATEGORY_SCHEMA:
        raise HTTPException(
            status_code=400,
            detail={"code": "INVALID_CATEGORY", "message": f"지원하지 않는 카테고리입니다: {req.category}"}
        )

    # 검증: 상태
    if req.condition not in VALID_CONDITIONS:
        raise HTTPException(
            status_code=400,
            detail={"code": "INVALID_CONDITION", "message": f"유효하지 않은 상태입니다: {req.condition}. 가능한 값: {VALID_CONDITIONS}"}
        )

    # 요청 → PriceEstimator 입력 형태로 변환
    features = _build_features(req)

    # 추론
    engine = get_engine()
    try:
        result = engine.estimate(req.category, features, with_explanation=True)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={"code": "ESTIMATION_FAILED", "message": f"가격 추정 중 오류가 발생했습니다: {str(e)}"}
        )

    if "error" in result:
        raise HTTPException(
            status_code=500,
            detail={"code": "ESTIMATION_FAILED", "message": result["error"]}
        )

    # 응답 변환
    return _build_response(result)


# ──────────────────────────────────────────────
# GET /api/v1/categories
# ──────────────────────────────────────────────
@app.get(
    "/api/v1/categories",
    response_model=CategoriesResponse,
    summary="카테고리 목록",
    description="지원하는 카테고리와 각 카테고리별 입력 속성 스키마를 반환합니다.",
)
async def get_categories():
    categories = []
    for name, schema in CATEGORY_SCHEMA.items():
        categories.append(CategoryInfo(
            name=name,
            recommended_attributes=schema["recommended"],
            optional_attributes=schema["optional"],
        ))
    return CategoriesResponse(categories=categories)


# ──────────────────────────────────────────────
# GET /api/v1/health
# ──────────────────────────────────────────────
@app.get(
    "/api/v1/health",
    response_model=HealthResponse,
    summary="헬스체크",
)
async def health_check():
    engine = get_engine()
    return HealthResponse(
        status="ok",
        models_loaded=len(engine.tree.models),
        rag_collections=len(engine.rag.collections),
    )




app.include_router(profiling_router, prefix="/api/v1")



# ──────────────────────────────────────────────
# 헬퍼 함수
# ──────────────────────────────────────────────
def _build_features(req: EstimateRequest) -> dict:
    """EstimateRequest → PriceEstimator.estimate()에 넘길 features dict"""
    features = {
        "condition": req.condition,
        "view_count": req.view_count or 0,
        "wish_count": req.wish_count or 0,
        "chat_count": req.chat_count or 0,
    }

    # 공통 선택 속성
    if req.usage_period_months is not None:
        features["usage_period_months"] = req.usage_period_months
    if req.has_box is not None:
        features["has_box"] = req.has_box
    if req.has_accessories is not None:
        features["has_accessories"] = req.has_accessories
    if req.has_defects is not None:
        features["has_defects"] = req.has_defects
    if req.is_negotiable is not None:
        features["is_negotiable"] = req.is_negotiable
    if req.image_count is not None:
        features["image_count"] = req.image_count

    # 카테고리별 민감속성 → 플랫하게 병합
    if req.sensitive_attributes:
        features.update(req.sensitive_attributes)

    return features


def _build_response(result: dict) -> EstimateResponse:
    """PriceEstimator 결과 → EstimateResponse 변환"""
    explanation = None
    if "explanation" in result:
        exp = result["explanation"]
        similar_trades = []
        for s in exp.get("similar_trades", []):
            similar_trades.append(SimilarTrade(
                title=s.get("title", "")[:100],
                price=s.get("price", 0),
                condition=s.get("condition", ""),
                brand=s.get("brand", ""),
            ))
        top_factors = []
        for tf in exp.get("top_factors", []):
            top_factors.append(TopFactor(
                factor=tf.get("factor", ""),
                weight=round(tf.get("weight", 0), 4),
            ))
        explanation = Explanation(
            summary=exp.get("summary", ""),
            similar_trades=similar_trades,
            top_factors=top_factors,
        )

    return EstimateResponse(
        predicted_price=result.get("predicted_price", 0),
        price_range_min=result.get("price_range_min", 0),
        price_range_max=result.get("price_range_max", 0),
        confidence=result.get("confidence", "low"),
        model_type=result.get("model_type", "unknown"),
        model_raw_price=result.get("model_raw_price"),
        rag_median_price=result.get("rag_median_price"),
        rag_sample_count=result.get("rag_sample_count"),
        explanation=explanation,
    )