"""
OpenAI API 호출 래퍼
프롬프트 3개가 공통으로 사용하는 API 호출 로직
"""

import json
import logging
import os

from openai import AsyncOpenAI

from ..config.constants import OPENAI_MAX_TOKENS, OPENAI_MODEL, OPENAI_TEMPERATURE

logger = logging.getLogger(__name__)

_client: AsyncOpenAI | None = None


def _get_client() -> AsyncOpenAI:
    """싱글턴 OpenAI 클라이언트를 반환한다."""
    global _client
    if _client is None:
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY 환경변수가 설정되지 않았습니다.")
        _client = AsyncOpenAI(api_key=api_key)
    return _client


async def call_openai(messages: list[dict]) -> dict:
    """
    OpenAI API를 호출하고 JSON 응답을 파싱하여 반환한다.

    Args:
        messages: OpenAI messages 형식 리스트
            [{"role": "system"|"user", "content": str}, ...]

    Returns:
        파싱된 프로필 JSON dict

    Raises:
        ValueError: JSON 파싱 실패 시
        openai.OpenAIError: API 호출 실패 시
    """
    client = _get_client()

    logger.info(
        "OpenAI API 호출 시작 (model=%s, temperature=%s)",
        OPENAI_MODEL,
        OPENAI_TEMPERATURE,
    )

    response = await client.chat.completions.create(
        model=OPENAI_MODEL,
        messages=messages,
        temperature=OPENAI_TEMPERATURE,
        max_tokens=OPENAI_MAX_TOKENS,
        response_format={"type": "json_object"},
    )

    raw_content = response.choices[0].message.content
    logger.info(
        "OpenAI API 응답 수신 (tokens: prompt=%d, completion=%d)",
        response.usage.prompt_tokens,
        response.usage.completion_tokens,
    )

    try:
        result = json.loads(raw_content)
    except json.JSONDecodeError as e:
        logger.error("JSON 파싱 실패: %s\n원문: %s", e, raw_content[:500])
        raise ValueError(f"OpenAI 응답 JSON 파싱 실패: {e}") from e

    return result