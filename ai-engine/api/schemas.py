"""
API 스키마 정의
===============
요청/응답 모델 + 카테고리별 속성 정보
"""

from pydantic import BaseModel, Field
from typing import Optional

# ──────────────────────────────────────────────
# 카테고리별 속성 스키마 (GET /categories 응답용)
# ──────────────────────────────────────────────
CATEGORY_SCHEMA = {
    "디지털기기": {
        "recommended": ["브랜드", "모델명"],
        "optional": ["저장용량", "색상", "출시년도", "RAM", "화면크기", "배터리성능"],
    },
    "가전제품": {
        "recommended": ["브랜드", "모델명"],
        "optional": ["종류", "용량_리터", "용량_kg", "도어타입", "설치여부"],
    },
    "패션잡화": {
        "recommended": ["브랜드"],
        "optional": ["모델명", "종류", "소재", "색상", "정품인증여부"],
    },
    "남성의류": {
        "recommended": ["브랜드"],
        "optional": ["사이즈", "시즌", "소재", "착용횟수", "색상"],
    },
    "여성의류": {
        "recommended": ["브랜드"],
        "optional": ["사이즈", "시즌", "소재", "착용횟수", "색상", "기장"],
    },
    "스포츠/레저": {
        "recommended": ["브랜드"],
        "optional": ["모델명", "종류", "샤프트종류", "세트구성"],
    },
    "출산/유아동": {
        "recommended": ["브랜드"],
        "optional": ["모델명", "종류", "사용개월수"],
    },
    "취미/게임": {
        "recommended": [],
        "optional": ["모델명", "동봉게임수"],
    },
    "뷰티/미용": {
        "recommended": ["브랜드"],
        "optional": ["모델명", "종류", "제품명", "용량_ml", "잔량_퍼센트", "개봉여부"],
    },
    "반려동물용품": {
        "recommended": [],
        "optional": ["브랜드", "종류", "소재", "크기", "대상동물크기"],
    },
    "생활용품": {
        "recommended": [],
        "optional": ["브랜드", "종류", "소재", "크기", "칸수", "색상", "조립여부"],
    },
    "가구/인테리어": {
        "recommended": [],
        "optional": ["브랜드", "종류", "소재", "색상", "조립여부", "용도"],
    },
    "도서": {
        "recommended": [],
        "optional": ["출판사", "종류", "과목구성", "세트구성", "필기여부", "발행년도"],
    },
    "식품": {
        "recommended": [],
        "optional": ["브랜드", "제품명", "용량", "유통기한", "형태", "개봉여부"],
    },
    "티켓/교환권": {
        "recommended": ["종류"],
        "optional": ["사용처", "권종금액", "매수", "유효기한", "이벤트명", "날짜", "좌석등급"],
    },
    "기타 중고물품": {
        "recommended": [],
        "optional": ["브랜드", "종류", "사용횟수"],
    },
}

VALID_CONDITIONS = ["S급", "A급", "B급", "C급", "부품용"]


# ──────────────────────────────────────────────
# Request / Response 모델
# ──────────────────────────────────────────────
class EstimateRequest(BaseModel):
    category: str = Field(..., description="16개 카테고리 중 하나", examples=["디지털기기"])
    condition: str = Field(..., description="S급/A급/B급/C급/부품용", examples=["A급"])

    # 공통 선택 속성
    usage_period_months: Optional[int] = Field(None, description="사용 기간 (개월)")
    has_box: Optional[bool] = Field(None, description="정품 박스 유무")
    has_accessories: Optional[bool] = Field(None, description="부속품 유무")
    has_defects: Optional[bool] = Field(None, description="하자 유무")
    is_negotiable: Optional[bool] = Field(None, description="네고 가능 여부")
    image_count: Optional[int] = Field(None, description="등록 사진 수")

    # 카테고리별 민감속성
    sensitive_attributes: Optional[dict] = Field(
        default_factory=dict,
        description="카테고리별 속성 (브랜드, 모델명 등)",
        examples=[{"브랜드": "애플", "모델명": "아이폰 15 프로"}]
    )

    # 메타데이터 (선택)
    view_count: Optional[int] = Field(0, description="조회수")
    wish_count: Optional[int] = Field(0, description="찜수")
    chat_count: Optional[int] = Field(0, description="채팅수")


class SimilarTrade(BaseModel):
    title: str
    price: int
    condition: str
    brand: str = ""


class TopFactor(BaseModel):
    factor: str
    weight: float


class Explanation(BaseModel):
    summary: str
    similar_trades: list[SimilarTrade] = []
    top_factors: list[TopFactor] = []


class PriceRange(BaseModel):
    """가격 범위 (판매자용 또는 구매자용)"""
    min: int = Field(..., description="최저 추천가")
    max: int = Field(..., description="최고 추천가")


class Quartiles(BaseModel):
    """가격 분위수"""
    q1: int = Field(..., description="25th percentile")
    q2: int = Field(..., description="50th percentile (중앙값)")
    q3: int = Field(..., description="75th percentile")
    q4: int = Field(..., description="상한 추정가")


class EstimateResponse(BaseModel):
    predicted_price: int
    price_range_min: int
    price_range_max: int

    # 판매자/구매자 맞춤 가격 범위
    seller_range: Optional[PriceRange] = Field(
        None, description="판매자 추천 가격 범위 (Q2~Q4)"
    )
    buyer_range: Optional[PriceRange] = Field(
        None, description="구매자 추천 가격 범위 (Q1~Q3)"
    )
    quartiles: Optional[Quartiles] = Field(
        None, description="가격 분위수 (Q1~Q4)"
    )

    confidence: str
    model_type: str
    model_raw_price: Optional[int] = None
    rag_median_price: Optional[int] = None
    rag_sample_count: Optional[int] = None
    explanation: Optional[Explanation] = None


class CategoryInfo(BaseModel):
    name: str
    recommended_attributes: list[str]
    optional_attributes: list[str]
    conditions: list[str] = VALID_CONDITIONS


class CategoriesResponse(BaseModel):
    categories: list[CategoryInfo]


class HealthResponse(BaseModel):
    status: str
    models_loaded: int
    rag_collections: int