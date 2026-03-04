"""
판매자 성향 분석 시스템 설정값
Stateful LLM Profiling System Configuration
"""

# ── 업데이트 주기 ──────────────────────────────────────
K = 10          # 증분 업데이트 트리거: 신규 채팅 메시지 수
N = 50          # 리베이스 시 참조할 최근 채팅 메시지 수

# ── OpenAI 설정 ──────────────────────────────────────
OPENAI_MODEL = "gpt-4o"
OPENAI_TEMPERATURE = 0.2       # 낮을수록 일관된 분석
OPENAI_MAX_TOKENS = 4096

# ── 리베이스 트리거 임계값 ────────────────────────────
REBASE_CHANGE_HISTORY_LIMIT = 15       # change_history 누적 건수 초과 시
REBASE_CONFIDENCE_THRESHOLD = 0.55     # confidence 평균 미만 시
REBASE_CONFLICT_THRESHOLD = 3          # dimension 간 충돌 항목 수 초과 시
REBASE_MAX_EVIDENCE_PER_FEATURE = 5    # feature당 evidence 최대 보관 수

# ── 점수 체계 ────────────────────────────────────────
SCORE_MIN = 1
SCORE_MAX = 5
CONFIDENCE_MIN = 0.0
CONFIDENCE_MAX = 1.0

# ── 분석 대상 feature 목록 ───────────────────────────
DIMENSIONS = {
    "transaction_motivation": [
        "price_sensitivity",
        "efficiency_orientation",
        "enjoyment_orientation",
        "negotiation_flexibility",
    ],
    "communication_style": [
        "response_pattern",
        "information_proactivity",
        "tone_friendliness",
        "clarity_structure",
    ],
    "trust_building": [
        "product_description_detail",
        "transaction_transparency",
        "issue_handling_attitude",
    ],
}

ALL_FEATURES = [f for features in DIMENSIONS.values() for f in features]