"""
Prompt 3: Rebase (리베이스)
프로필 드리프트 감지 시 최근 N개 채팅 원문으로 프로필 재구축
"""

import json
from datetime import date


def build_rebase_prompt(
    existing_profile: dict,
    recent_chat_logs: list[dict],
    rebase_reason: str,
) -> list[dict]:
    """
    리베이스 프롬프트를 생성한다.

    Args:
        existing_profile: 기존 판매자 프로필 JSON (보조 참조용)
        recent_chat_logs: 최근 N개 채팅 메시지 리스트
        rebase_reason: 리베이스 트리거 사유

    Returns:
        OpenAI messages 형식 리스트
    """
    formatted_logs = _format_chat_logs(recent_chat_logs)
    profile_json = json.dumps(existing_profile, ensure_ascii=False, indent=2)
    today = date.today().isoformat()
    prev_version = existing_profile.get("profile_version", 1)
    created_at = existing_profile.get("created_at", today)

    system_message = f"""You are an expert analyst specializing in online C2C second-hand marketplace seller behavior profiling.

Your task is to REBUILD a seller's behavioral profile from scratch. This rebase is triggered because the existing profile has accumulated inconsistencies through incremental updates. You must produce a fresh, coherent profile using recent chat history as the primary source of truth, while treating the existing profile as secondary reference.

---

## ANALYSIS FRAMEWORK

You evaluate the seller across 3 dimensions and 11 features:

### Dimension A: Transaction Motivation
1. **price_sensitivity**: Price-focus level (negotiation frequency, discount behavior, price justifications)
2. **efficiency_orientation**: Fast transaction preference (urgency cues, minimal unnecessary communication)
3. **enjoyment_orientation**: Enjoyment of trading process (playful tone, enthusiasm, engagement beyond necessity)
4. **negotiation_flexibility**: Flexibility in negotiations (willingness to adjust terms, counter-offers)

### Dimension B: Communication Style
5. **response_pattern**: Response behavior (length, detail, consistency)
6. **information_proactivity**: Proactive vs. reactive information sharing
7. **tone_friendliness**: Overall tone (friendly / neutral / aggressive)
8. **clarity_structure**: Message organization and clarity

### Dimension C: Trust Building Behavior
9. **product_description_detail**: Thoroughness of product condition descriptions
10. **transaction_transparency**: Clarity of transaction terms
11. **issue_handling_attitude**: Response to problems or complaints

---

## REBASE RULES

**Rule 1 — Primary Source Priority**
The recent chat messages are your PRIMARY evidence source. The existing profile is SECONDARY reference only. If they conflict, the chat messages take precedence.

**Rule 2 — Fresh Scoring**
Score all 11 features independently based on the provided chat messages. Do NOT carry over scores from the existing profile.

**Rule 3 — Evidence Reset**
Build entirely new evidence lists from the provided chat messages. Previous evidence is discarded.

**Rule 4 — Confidence Based on Current Data Only**
- 0.8+ = Clear, repeated evidence across multiple conversations
- 0.5-0.8 = Some evidence exists
- Below 0.5 = Limited data, estimation level

**Rule 5 — Profile Continuity**
- Set profile_version to {prev_version + 1}
- Clear change_history and add a single REBASE entry
- Record the rebase trigger reason

---

## REASONING INSTRUCTIONS

Think step by step:

**Step 1 — Acknowledge Rebase Context**
Note the rebase trigger reason. Understand what inconsistencies existed in the previous profile.

**Step 2 — Analyze Recent Chat Messages**
Read through ALL provided recent chat messages. Extract observable signals for each of the 11 features. Treat this as if you are analyzing this seller for the first time.

**Step 3 — Cross-Reference with Existing Profile (Secondary)**
After completing your independent analysis, briefly compare your findings with the existing profile. Note any major shifts and hypothesize why.

**Step 4 — Score and Generate Profile**
Assign scores, confidence, and evidence for all features. Write a fresh analysis_summary.

---

## OUTPUT FORMAT

Respond in Korean for all text fields.
Output ONLY valid JSON. No markdown fences, no preamble.

Use this exact schema:

{{
  "profile_version": {prev_version + 1},
  "created_at": "{created_at}",
  "last_updated": "{today}",
  "total_messages_analyzed": <count of seller messages in this rebase>,
  "rebase_performed": true,
  "rebase_trigger": "<reason for rebase in Korean>",
  "analysis_summary": "<2-3 sentence fresh summary in Korean>",
  "dimensions": {{
    "transaction_motivation": {{
      "price_sensitivity": {{ "score": <1-5>, "confidence": <0.0-1.0>, "evidence": ["..."] }},
      "efficiency_orientation": {{ "score": <1-5>, "confidence": <0.0-1.0>, "evidence": ["..."] }},
      "enjoyment_orientation": {{ "score": <1-5>, "confidence": <0.0-1.0>, "evidence": ["..."] }},
      "negotiation_flexibility": {{ "score": <1-5>, "confidence": <0.0-1.0>, "evidence": ["..."] }}
    }},
    "communication_style": {{
      "response_pattern": {{ "score": <1-5>, "confidence": <0.0-1.0>, "evidence": ["..."] }},
      "information_proactivity": {{ "score": <1-5>, "confidence": <0.0-1.0>, "evidence": ["..."] }},
      "tone_friendliness": {{ "score": <1-5>, "confidence": <0.0-1.0>, "evidence": ["..."] }},
      "clarity_structure": {{ "score": <1-5>, "confidence": <0.0-1.0>, "evidence": ["..."] }}
    }},
    "trust_building": {{
      "product_description_detail": {{ "score": <1-5>, "confidence": <0.0-1.0>, "evidence": ["..."] }},
      "transaction_transparency": {{ "score": <1-5>, "confidence": <0.0-1.0>, "evidence": ["..."] }},
      "issue_handling_attitude": {{ "score": <1-5>, "confidence": <0.0-1.0>, "evidence": ["..."] }}
    }}
  }},
  "change_history": [
    {{
      "version": {prev_version + 1},
      "action": "REBASE",
      "trigger": "<rebase trigger reason>",
      "note": "Profile rebuilt from recent messages. Previous change history cleared."
    }}
  ],
  "pre_rebase_comparison": {{
    "major_shifts": ["<features where score changed by 2+ compared to previous profile>"],
    "interpretation": "<brief explanation of why shifts occurred, in Korean>"
  }}
}}"""

    user_message = f"""### Rebase Trigger

<rebase_trigger>
{rebase_reason}
</rebase_trigger>

### Existing Profile (Secondary Reference Only)

<existing_profile>
{profile_json}
</existing_profile>

### Recent Chat Messages (Primary Source)

<recent_chat_logs>
{formatted_logs}
</recent_chat_logs>"""

    return [
        {"role": "system", "content": system_message},
        {"role": "user", "content": user_message},
    ]


def _format_chat_logs(chat_logs: list[dict]) -> str:
    """채팅 로그를 텍스트로 포매팅한다."""
    lines = []
    for msg in chat_logs:
        role = "판매자" if msg["role"] == "seller" else "구매자"
        timestamp = msg.get("timestamp", "")
        ts_str = f" [{timestamp}]" if timestamp else ""
        lines.append(f"[{role}]{ts_str}: {msg['message']}")
    return "\n".join(lines)