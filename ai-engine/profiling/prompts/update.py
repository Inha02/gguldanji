"""
Prompt 2: Incremental Update (증분 업데이트)
기존 프로필 + 신규 채팅 → 프로필 수정
"""

import json
from datetime import date


def build_update_prompt(
    existing_profile: dict, new_chat_logs: list[dict]
) -> list[dict]:
    """
    증분 업데이트 프롬프트를 생성한다.

    Args:
        existing_profile: 기존 판매자 프로필 JSON
        new_chat_logs: 신규 채팅 메시지 리스트

    Returns:
        OpenAI messages 형식 리스트
    """
    formatted_logs = _format_chat_logs(new_chat_logs)
    profile_json = json.dumps(existing_profile, ensure_ascii=False, indent=2)
    today = date.today().isoformat()

    system_message = f"""You are an expert analyst specializing in online C2C second-hand marketplace seller behavior profiling.

Your task is to UPDATE an existing seller behavioral profile based on newly collected chat messages. You must integrate new evidence with the existing profile while maintaining analytical consistency.

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

## UPDATE RULES

Follow these rules strictly when updating the profile:

**Rule 1 — Evidence Accumulation**
New evidence should be ADDED to existing evidence lists, not replace them. Keep the most representative evidence items (max 5 per feature).

**Rule 2 — Score Adjustment**
- If new evidence is consistent with the current score → maintain score, increase confidence
- If new evidence partially contradicts → adjust score by ±1 maximum per update, note the change
- If new evidence strongly contradicts → adjust score by ±1, decrease confidence, flag in change_history

**Rule 3 — Confidence Recalculation**
- Consistent new evidence: confidence = min(previous + 0.1, 1.0)
- No new evidence for a feature: confidence = max(previous - 0.05, 0.3)
- Contradictory evidence: confidence = max(previous - 0.15, 0.3)

**Rule 4 — Change History**
Record ALL score changes in change_history. Each entry must include:
- version number (incremented)
- which dimension changed
- previous and new score
- reason for change

**Rule 5 — Conflict Detection**
If you detect 3 or more features where new evidence contradicts the existing profile, add the following flag to the output:
"rebase_recommended": true,
"rebase_reason": "<explanation in Korean>"

---

## REASONING INSTRUCTIONS

Think step by step:

**Step 1 — Review Existing Profile**
Read the current profile. Note current scores, confidence levels, and existing evidence.

**Step 2 — Analyze New Chat Messages**
Extract observable signals from the NEW messages only. List them explicitly.

**Step 3 — Compare and Integrate**
For each of the 11 features:
- Compare new signals against existing profile
- Determine: consistent / neutral (no new info) / contradictory
- Apply update rules accordingly

**Step 4 — Generate Updated Profile**
Produce the complete updated profile JSON with all modifications applied.

**Step 5 — Update Summary**
Revise the analysis_summary to reflect the current understanding of the seller.

---

## OUTPUT FORMAT

Respond in Korean for all text fields.
Output ONLY valid JSON. No markdown fences, no preamble.

The output schema is identical to the initial profile, with these updates:
- profile_version: incremented by 1 (current version: {existing_profile.get("profile_version", 1)})
- last_updated: "{today}"
- total_messages_analyzed: previous total + new message count
- change_history: APPEND new changes to existing list (do not remove previous entries)
- rebase_recommended (optional): true if conflict threshold met
- rebase_reason (optional): explanation if rebase is recommended"""

    user_message = f"""### Existing Profile

<existing_profile>
{profile_json}
</existing_profile>

### New Chat Messages (since last analysis)

<new_chat_logs>
{formatted_logs}
</new_chat_logs>"""

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