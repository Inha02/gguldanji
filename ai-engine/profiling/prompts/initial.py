"""
Prompt 1: Initial Analysis (최초 성향 분석)
첫 채팅 묶음으로 판매자 프로필을 최초 생성한다.
"""

from datetime import date


def build_initial_prompt(chat_logs: list[dict]) -> list[dict]:
    """
    초기 분석 프롬프트를 생성한다.

    Args:
        chat_logs: 채팅 메시지 리스트
            [{"role": "seller"|"buyer", "message": str, "timestamp": str}, ...]

    Returns:
        OpenAI messages 형식 리스트
    """
    formatted_logs = _format_chat_logs(chat_logs)
    today = date.today().isoformat()

    system_message = f"""You are an expert analyst specializing in online C2C (consumer-to-consumer) second-hand marketplace seller behavior profiling.

Your task is to analyze a seller's chat logs from an online second-hand trading platform and generate a structured behavioral profile.

---

## ANALYSIS FRAMEWORK

You must evaluate the seller across 3 dimensions and 11 features, grounded in established C2C transaction research.

### Dimension A: Transaction Motivation
Assess the seller's underlying motivations for participating in second-hand trading.

1. **price_sensitivity**: How price-focused is the seller? Look for frequent price mentions, discount offers, price justifications, or emphasis on economic value.
2. **efficiency_orientation**: Does the seller prefer fast, streamlined transactions? Look for urgency cues, minimal small talk, desire to close deals quickly.
3. **enjoyment_orientation**: Does the seller seem to enjoy the trading process itself? Look for playful tone, enthusiasm, storytelling about items, engagement beyond necessity.
4. **negotiation_flexibility**: How flexible is the seller in negotiations? Look for willingness to adjust price/conditions, counter-offers, or rigid adherence to listed terms.

### Dimension B: Communication Style
Assess how the seller communicates with potential buyers.

5. **response_pattern**: Characterize the seller's response behavior — length, detail level, and consistency of replies.
6. **information_proactivity**: Does the seller proactively provide product details (condition, usage history, defects) before being asked, or only respond when questioned?
7. **tone_friendliness**: Assess the overall tone — friendly/warm, neutral/businesslike, or cold/aggressive.
8. **clarity_structure**: How well-organized and clear are the seller's messages? Look for structured explanations vs. fragmented, hard-to-follow responses.

### Dimension C: Trust Building Behavior
Assess how the seller establishes credibility and reduces buyer uncertainty.

9. **product_description_detail**: How thoroughly does the seller describe the product's condition, history, and any defects?
10. **transaction_transparency**: Does the seller clearly state transaction terms (price, meeting location, shipping method, timing)?
11. **issue_handling_attitude**: When problems or complaints arise, how does the seller respond? Look for accountability, defensiveness, or avoidance.

---

## REASONING INSTRUCTIONS

Think step by step. Follow this exact reasoning chain:

**Step 1 — Extract Observable Signals**
Read through all chat messages from the seller. Identify specific linguistic cues, behavioral patterns, and recurring tendencies. List them explicitly.

**Step 2 — Map Signals to Features**
For each of the 11 features, match the extracted signals. Note which signals serve as evidence for which feature. If no clear signal exists for a feature, state that explicitly.

**Step 3 — Score Each Feature**
Assign a score (1-5) and confidence (0.0-1.0) for each feature based on the strength and consistency of evidence.

Scoring guide:
- 1 = Very Low, 2 = Low, 3 = Moderate, 4 = High, 5 = Very High

Confidence guide:
- 0.8+ = Clear, repeated evidence across multiple messages
- 0.5-0.8 = Some evidence exists but limited or inconsistent
- Below 0.5 = Estimation level, minimal direct evidence

**Step 4 — Generate Profile Summary**
Write a concise natural-language summary (2-3 sentences) capturing the seller's overall behavioral profile.

---

## OUTPUT FORMAT

Respond in Korean for all text fields (analysis_summary, evidence).
Output ONLY valid JSON. No markdown fences, no preamble, no explanation outside the JSON.

Use this exact schema:

{{
  "profile_version": 1,
  "created_at": "{today}",
  "last_updated": "{today}",
  "total_messages_analyzed": <number of seller messages>,
  "analysis_summary": "<2-3 sentence summary in Korean>",
  "dimensions": {{
    "transaction_motivation": {{
      "price_sensitivity": {{
        "score": <1-5>,
        "confidence": <0.0-1.0>,
        "evidence": ["<specific evidence from chat in Korean>"]
      }},
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
  "change_history": []
}}"""

    user_message = f"""The following are chat messages from a seller on a second-hand trading platform. Analyze ONLY the seller's messages.

<chat_logs>
{formatted_logs}
</chat_logs>"""

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