"""
판매자 성향 분석 핵심 서비스 (Profiler)
모드 판단 → 프롬프트 선택 → OpenAI 호출 → 결과 반환
"""

import logging

from ..config.constants import N
from ..prompts.initial import build_initial_prompt
from ..prompts.rebase import build_rebase_prompt
from ..prompts.update import build_update_prompt
from .openai_client import call_openai
from .trigger_checker import check_rebase_needed

logger = logging.getLogger(__name__)


async def analyze_seller(
    seller_id: str,
    chat_logs: list[dict],
    existing_profile: dict | None = None,
    all_chat_logs: list[dict] | None = None,
) -> dict:
    """
    판매자 성향을 분석하고 프로필을 반환한다.
    existing_profile 유무에 따라 자동으로 모드를 판단한다.

    Args:
        seller_id: 판매자 고유 ID
        chat_logs: 분석할 채팅 메시지 리스트 (신규 메시지)
            [{"role": "seller"|"buyer", "message": str, "timestamp": str}, ...]
        existing_profile: 기존 프로필 (없으면 초기 분석 모드)
        all_chat_logs: 리베이스 시 사용할 전체 채팅 로그 (최근 N개 추출용)
            없으면 chat_logs를 그대로 사용

    Returns:
        판매자 프로필 JSON dict
    """
    if existing_profile is None:
        # ── 초기 분석 모드 ──
        return await _run_initial(seller_id, chat_logs)
    else:
        # ── 증분 업데이트 모드 ──
        updated_profile = await _run_update(seller_id, chat_logs, existing_profile)

        # ── 리베이스 트리거 체크 ──
        rebase_needed, rebase_reason = check_rebase_needed(updated_profile)

        if rebase_needed:
            recent_logs = _get_recent_logs(all_chat_logs or chat_logs, N)
            updated_profile = await _run_rebase(
                seller_id, recent_logs, updated_profile, rebase_reason
            )

        return updated_profile


async def _run_initial(seller_id: str, chat_logs: list[dict]) -> dict:
    """초기 분석을 실행한다."""
    logger.info("[%s] 초기 분석 시작 (메시지 %d개)", seller_id, len(chat_logs))

    messages = build_initial_prompt(chat_logs)
    profile = await call_openai(messages)

    logger.info("[%s] 초기 분석 완료 (version: %s)", seller_id, profile.get("profile_version"))
    return profile


async def _run_update(
    seller_id: str, chat_logs: list[dict], existing_profile: dict
) -> dict:
    """증분 업데이트를 실행한다."""
    logger.info(
        "[%s] 증분 업데이트 시작 (신규 메시지 %d개, 현재 version: %s)",
        seller_id,
        len(chat_logs),
        existing_profile.get("profile_version"),
    )

    messages = build_update_prompt(existing_profile, chat_logs)
    updated_profile = await call_openai(messages)

    logger.info(
        "[%s] 증분 업데이트 완료 (version: %s)",
        seller_id,
        updated_profile.get("profile_version"),
    )
    return updated_profile


async def _run_rebase(
    seller_id: str,
    recent_chat_logs: list[dict],
    existing_profile: dict,
    rebase_reason: str,
) -> dict:
    """리베이스를 실행한다."""
    logger.warning(
        "[%s] 리베이스 실행 (사유: %s, 최근 메시지 %d개)",
        seller_id,
        rebase_reason,
        len(recent_chat_logs),
    )

    messages = build_rebase_prompt(existing_profile, recent_chat_logs, rebase_reason)
    rebased_profile = await call_openai(messages)

    logger.info(
        "[%s] 리베이스 완료 (version: %s)",
        seller_id,
        rebased_profile.get("profile_version"),
    )
    return rebased_profile


def _get_recent_logs(chat_logs: list[dict], n: int) -> list[dict]:
    """채팅 로그에서 최근 N개를 추출한다."""
    return chat_logs[-n:] if len(chat_logs) > n else chat_logs