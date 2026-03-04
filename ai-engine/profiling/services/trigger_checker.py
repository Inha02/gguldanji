"""
리베이스 트리거 조건 체크
업데이트 결과를 분석하여 리베이스 필요 여부를 판단한다.
"""

import logging

from ..config.constants import (
    DIMENSIONS,
    REBASE_CHANGE_HISTORY_LIMIT,
    REBASE_CONFIDENCE_THRESHOLD,
)

logger = logging.getLogger(__name__)


def check_rebase_needed(profile: dict) -> tuple[bool, str | None]:
    """
    프로필 상태를 분석하여 리베이스 필요 여부를 판단한다.

    트리거 조건 (하나라도 충족 시 리베이스):
      1. LLM이 rebase_recommended=true를 반환한 경우 (모순 감지)
      2. change_history 누적 건수 초과
      3. confidence 평균 미달

    Note:
      충돌 감지는 LLM의 rebase_recommended 판단에 위임한다.
      단순 점수 변경은 자연스러운 업데이트이므로 충돌로 세지 않는다.

    Args:
        profile: 업데이트된 판매자 프로필 JSON

    Returns:
        (리베이스 필요 여부, 사유 문자열 또는 None)
    """
    reasons = []

    # 1. LLM이 직접 rebase를 권고한 경우 (모순 감지)
    if profile.get("rebase_recommended"):
        llm_reason = profile.get("rebase_reason", "LLM이 리베이스를 권고함")
        reasons.append(f"LLM 권고: {llm_reason}")

    # 2. change_history 누적 건수 초과
    change_count = len(profile.get("change_history", []))
    if change_count > REBASE_CHANGE_HISTORY_LIMIT:
        reasons.append(
            f"change_history 누적 {change_count}건 "
            f"(임계값: {REBASE_CHANGE_HISTORY_LIMIT})"
        )

    # 3. confidence 평균 미달
    avg_confidence = _calc_avg_confidence(profile)
    if avg_confidence is not None and avg_confidence < REBASE_CONFIDENCE_THRESHOLD:
        reasons.append(
            f"confidence 평균 {avg_confidence:.2f} "
            f"(임계값: {REBASE_CONFIDENCE_THRESHOLD})"
        )

    if reasons:
        combined_reason = " | ".join(reasons)
        logger.warning("리베이스 트리거 발동: %s", combined_reason)
        return True, combined_reason

    return False, None


def _calc_avg_confidence(profile: dict) -> float | None:
    """전체 feature의 confidence 평균을 계산한다."""
    confidences = []
    dimensions = profile.get("dimensions", {})

    for dim_name, features in DIMENSIONS.items():
        dim_data = dimensions.get(dim_name, {})
        for feature_name in features:
            feature_data = dim_data.get(feature_name, {})
            conf = feature_data.get("confidence")
            if conf is not None:
                confidences.append(conf)

    if not confidences:
        return None
    return sum(confidences) / len(confidences)