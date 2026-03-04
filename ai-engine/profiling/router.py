"""
판매자 성향 분석 API 라우터
백엔드 팀이 호출하는 엔드포인트를 정의한다.

사용법:
    기존 FastAPI app에 아래와 같이 연결
    >>> from profiling.router import router as profiling_router
    >>> app.include_router(profiling_router)
"""

import logging

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from .services.profiler import analyze_seller

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/profiling", tags=["seller-profiling"])


# ── Request / Response 스키마 ───────────────────────────


class ChatMessage(BaseModel):
    """채팅 메시지 단위"""

    role: str = Field(
        ...,
        description="메시지 발신자 역할",
        examples=["seller", "buyer"],
    )
    message: str = Field(..., description="메시지 내용")
    timestamp: str | None = Field(
        None, description="메시지 발신 시각 (ISO 8601)", examples=["2026-03-04T14:30:00"]
    )


class AnalyzeRequest(BaseModel):
    """판매자 성향 분석 요청"""

    seller_id: str = Field(..., description="판매자 고유 ID")
    chat_logs: list[ChatMessage] = Field(
        ...,
        description="분석할 채팅 메시지 리스트 (신규 메시지)",
        min_length=1,
    )
    existing_profile: dict | None = Field(
        None,
        description="기존 프로필 JSON. null이면 초기 분석, 있으면 증분 업데이트",
    )
    all_chat_logs: list[ChatMessage] | None = Field(
        None,
        description="리베이스 시 사용할 전체 채팅 로그. 없으면 chat_logs 사용",
    )


class AnalyzeResponse(BaseModel):
    """판매자 성향 분석 응답"""

    success: bool
    seller_id: str
    mode: str = Field(
        ..., description="실행된 분석 모드", examples=["initial", "update", "rebase"]
    )
    profile: dict = Field(..., description="판매자 프로필 JSON")


# ── 엔드포인트 ─────────────────────────────────────────


@router.post("/analyze", response_model=AnalyzeResponse)
async def analyze_seller_profile(request: AnalyzeRequest):
    """
    판매자 성향을 분석하고 프로필을 반환한다.

    - **existing_profile이 null** → 초기 분석 (Initial)
    - **existing_profile이 있음** → 증분 업데이트 (Update)
      - 업데이트 결과 리베이스 조건 충족 시 → 자동 리베이스 (Rebase)
    """
    try:
        chat_logs = [msg.model_dump() for msg in request.chat_logs]
        all_logs = (
            [msg.model_dump() for msg in request.all_chat_logs]
            if request.all_chat_logs
            else None
        )

        # 모드 판단
        mode = "initial" if request.existing_profile is None else "update"

        profile = await analyze_seller(
            seller_id=request.seller_id,
            chat_logs=chat_logs,
            existing_profile=request.existing_profile,
            all_chat_logs=all_logs,
        )

        # 리베이스가 실행되었는지 확인
        if profile.get("rebase_performed"):
            mode = "rebase"

        logger.info(
            "[%s] 분석 완료 (mode=%s, version=%s)",
            request.seller_id,
            mode,
            profile.get("profile_version"),
        )

        return AnalyzeResponse(
            success=True,
            seller_id=request.seller_id,
            mode=mode,
            profile=profile,
        )

    except ValueError as e:
        logger.error("[%s] 분석 실패: %s", request.seller_id, e)
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        logger.error("[%s] 예기치 않은 오류: %s", request.seller_id, e, exc_info=True)
        raise HTTPException(status_code=500, detail="프로필 분석 중 오류가 발생했습니다.")