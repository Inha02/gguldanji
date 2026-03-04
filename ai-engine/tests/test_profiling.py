"""
판매자 성향 분석 테스트 스크립트
================================
3단계 테스트: 초기 분석 → 증분 업데이트 → 리베이스 트리거

실행:
  python -m tests.test_profiling

사전 준비:
  1. .env에 OPENAI_API_KEY 설정
  2. 서버 실행: uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload
"""

import asyncio
import json
import sys

import httpx

BASE_URL = "http://localhost:8000/api/v1/profiling/analyze"

# ──────────────────────────────────────────────
# 더미 채팅 데이터
# ──────────────────────────────────────────────

# 초기 분석용: 가격 민감 + 효율 지향 + 사무적 톤의 판매자
INITIAL_CHAT_LOGS = [
    {"role": "buyer", "message": "안녕하세요, 아직 판매중인가요?", "timestamp": "2026-03-01T10:00:00"},
    {"role": "seller", "message": "네 판매중입니다", "timestamp": "2026-03-01T10:01:00"},
    {"role": "buyer", "message": "상태 어떤가요? 기스 있나요?", "timestamp": "2026-03-01T10:02:00"},
    {"role": "seller", "message": "사용감 거의 없고요, 기스 없습니다. 구매한지 3개월 됐어요. 박스랑 충전기 다 있습니다.", "timestamp": "2026-03-01T10:03:00"},
    {"role": "buyer", "message": "혹시 15만원에 가능할까요?", "timestamp": "2026-03-01T10:05:00"},
    {"role": "seller", "message": "18만원까지는 가능합니다. 그 이하는 어렵습니다.", "timestamp": "2026-03-01T10:06:00"},
    {"role": "buyer", "message": "16만원은요?", "timestamp": "2026-03-01T10:07:00"},
    {"role": "seller", "message": "17만원 어떠세요? 거의 새거라 그 이하로는 힘듭니다.", "timestamp": "2026-03-01T10:08:00"},
    {"role": "buyer", "message": "알겠습니다 17만원에 할게요. 직거래 가능한가요?", "timestamp": "2026-03-01T10:10:00"},
    {"role": "seller", "message": "강남역 가능합니다. 오늘 저녁 7시 어떠세요?", "timestamp": "2026-03-01T10:11:00"},
    {"role": "buyer", "message": "네 좋습니다!", "timestamp": "2026-03-01T10:12:00"},
    {"role": "seller", "message": "네 그럼 오늘 7시 강남역 11번출구에서 뵙겠습니다.", "timestamp": "2026-03-01T10:13:00"},
]

# 증분 업데이트용: 좀 더 유희적이고 친근한 톤이 나타나는 새 거래
UPDATE_CHAT_LOGS = [
    {"role": "buyer", "message": "안녕하세요~ 에어팟 프로 아직 있나요?", "timestamp": "2026-03-02T14:00:00"},
    {"role": "seller", "message": "안녕하세요! 네 있습니다 ㅎㅎ 관심 가져주셔서 감사해요", "timestamp": "2026-03-02T14:01:00"},
    {"role": "buyer", "message": "배터리 상태가 어떤가요?", "timestamp": "2026-03-02T14:02:00"},
    {"role": "seller", "message": "배터리 최대 용량 95%이고요, 솔직히 말씀드리면 왼쪽 이어폰에 아주 미세한 기스가 하나 있어요. 사진 보내드릴까요?", "timestamp": "2026-03-02T14:03:00"},
    {"role": "buyer", "message": "네 보내주세요! 가격 좀 조정 가능할까요?", "timestamp": "2026-03-02T14:05:00"},
    {"role": "seller", "message": "사진 보내드렸어요! 기스 감안해서 원래 12만원인데 11만원에 드릴게요. 사실 이 가격이면 거의 나눔 수준이에요 ㅋㅋ", "timestamp": "2026-03-02T14:06:00"},
    {"role": "buyer", "message": "감사합니다! 10만원은 안될까요?", "timestamp": "2026-03-02T14:07:00"},
    {"role": "seller", "message": "음... 10.5만원이면 괜찮을 것 같아요! 빨리 좋은 분한테 보내드리고 싶네요 ㅎㅎ", "timestamp": "2026-03-02T14:08:00"},
    {"role": "buyer", "message": "좋아요! 택배 가능한가요?", "timestamp": "2026-03-02T14:10:00"},
    {"role": "seller", "message": "택배비 3000원 별도인데 괜찮으시면 오늘 바로 발송해드릴게요! 운송장 번호 바로 보내드립니다", "timestamp": "2026-03-02T14:11:00"},
]

# 리베이스 트리거 테스트용: 인위적으로 드리프트된 프로필
def make_drifted_profile(base_profile: dict) -> dict:
    """confidence를 낮추고 change_history를 과다 누적시켜 리베이스 트리거를 유도한다."""
    import copy
    drifted = copy.deepcopy(base_profile)

    # confidence 전체 하락
    for dim in drifted.get("dimensions", {}).values():
        for feature in dim.values():
            if isinstance(feature, dict) and "confidence" in feature:
                feature["confidence"] = 0.4

    # change_history 과다 누적 (16개 → 임계값 15 초과)
    drifted["change_history"] = [
        {"version": i, "changed_dimension": "price_sensitivity",
         "previous_score": 3, "new_score": 4, "reason": f"테스트 변경 {i}"}
        for i in range(1, 17)
    ]

    return drifted


# ──────────────────────────────────────────────
# 테스트 실행
# ──────────────────────────────────────────────

async def test_initial_analysis(client: httpx.AsyncClient) -> dict:
    """1단계: 초기 분석 테스트"""
    print("\n" + "=" * 60)
    print("1단계: 초기 분석 (Initial Analysis)")
    print("=" * 60)

    response = await client.post(BASE_URL, json={
        "seller_id": "test_seller_001",
        "chat_logs": INITIAL_CHAT_LOGS,
        "existing_profile": None,
    })

    print(f"Status: {response.status_code}")

    if response.status_code != 200:
        print(f"ERROR: {response.text}")
        return None

    result = response.json()
    profile = result["profile"]

    print(f"Mode: {result['mode']}")
    print(f"Version: {profile['profile_version']}")
    print(f"Summary: {profile['analysis_summary']}")
    print(f"\n점수 요약:")

    for dim_name, features in profile["dimensions"].items():
        print(f"\n  [{dim_name}]")
        for feat_name, feat_data in features.items():
            print(f"    {feat_name}: score={feat_data['score']}, confidence={feat_data['confidence']}")

    return profile


async def test_incremental_update(client: httpx.AsyncClient, existing_profile: dict) -> dict:
    """2단계: 증분 업데이트 테스트"""
    print("\n" + "=" * 60)
    print("2단계: 증분 업데이트 (Incremental Update)")
    print("=" * 60)

    response = await client.post(BASE_URL, json={
        "seller_id": "test_seller_001",
        "chat_logs": UPDATE_CHAT_LOGS,
        "existing_profile": existing_profile,
    })

    print(f"Status: {response.status_code}")

    if response.status_code != 200:
        print(f"ERROR: {response.text}")
        return None

    result = response.json()
    profile = result["profile"]

    print(f"Mode: {result['mode']}")
    print(f"Version: {profile['profile_version']}")
    print(f"Summary: {profile['analysis_summary']}")

    # 변경사항 출력
    changes = profile.get("change_history", [])
    new_changes = [c for c in changes if c.get("version") == profile["profile_version"]]
    if new_changes:
        print(f"\n변경사항 ({len(new_changes)}건):")
        for ch in new_changes:
            print(f"  - {ch}")
    else:
        print("\n변경사항 없음")

    print(f"\n점수 요약:")
    for dim_name, features in profile["dimensions"].items():
        print(f"\n  [{dim_name}]")
        for feat_name, feat_data in features.items():
            print(f"    {feat_name}: score={feat_data['score']}, confidence={feat_data['confidence']}")

    return profile


async def test_rebase_trigger(client: httpx.AsyncClient, base_profile: dict) -> dict:
    """3단계: 리베이스 트리거 테스트"""
    print("\n" + "=" * 60)
    print("3단계: 리베이스 트리거 (Rebase Trigger)")
    print("=" * 60)

    drifted = make_drifted_profile(base_profile)
    print(f"드리프트 프로필 생성: confidence 전체 0.4, change_history {len(drifted['change_history'])}건")

    # all_chat_logs로 초기 + 업데이트 채팅 모두 전달 (리베이스 시 최근 N개 원문으로 사용)
    all_logs = INITIAL_CHAT_LOGS + UPDATE_CHAT_LOGS

    response = await client.post(BASE_URL, json={
        "seller_id": "test_seller_001",
        "chat_logs": UPDATE_CHAT_LOGS,
        "existing_profile": drifted,
        "all_chat_logs": all_logs,
    })

    print(f"Status: {response.status_code}")

    if response.status_code != 200:
        print(f"ERROR: {response.text}")
        return None

    result = response.json()
    profile = result["profile"]

    print(f"Mode: {result['mode']}")
    print(f"Version: {profile['profile_version']}")
    print(f"Rebase performed: {profile.get('rebase_performed', False)}")
    print(f"Rebase trigger: {profile.get('rebase_trigger', 'N/A')}")
    print(f"Summary: {profile['analysis_summary']}")

    # pre_rebase_comparison 출력
    comparison = profile.get("pre_rebase_comparison", {})
    if comparison:
        print(f"\n리베이스 전후 비교:")
        print(f"  Major shifts: {comparison.get('major_shifts', [])}")
        print(f"  Interpretation: {comparison.get('interpretation', '')}")

    print(f"\n점수 요약:")
    for dim_name, features in profile["dimensions"].items():
        print(f"\n  [{dim_name}]")
        for feat_name, feat_data in features.items():
            print(f"    {feat_name}: score={feat_data['score']}, confidence={feat_data['confidence']}")

    return profile


async def main():
    print("=" * 60)
    print("판매자 성향 분석 시스템 테스트")
    print("Stateful LLM Profiling System")
    print("=" * 60)

    async with httpx.AsyncClient(timeout=60.0) as client:
        # 서버 연결 확인
        try:
            health = await client.get("http://localhost:8000/api/v1/health")
            print(f"서버 상태: {health.status_code}")
        except httpx.ConnectError:
            print("ERROR: 서버에 연결할 수 없습니다.")
            print("서버를 먼저 실행하세요: uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload")
            sys.exit(1)

        # 1단계: 초기 분석
        profile = await test_initial_analysis(client)
        if profile is None:
            print("\n초기 분석 실패. 테스트 중단.")
            sys.exit(1)

        # 2단계: 증분 업데이트
        updated_profile = await test_incremental_update(client, profile)
        if updated_profile is None:
            print("\n증분 업데이트 실패. 테스트 중단.")
            sys.exit(1)

        # 3단계: 리베이스 트리거
        rebased_profile = await test_rebase_trigger(client, updated_profile)

        # 최종 결과 저장
        print("\n" + "=" * 60)
        print("테스트 완료! 결과 저장 중...")
        print("=" * 60)

        results = {
            "step1_initial": profile,
            "step2_updated": updated_profile,
            "step3_rebased": rebased_profile,
        }

        with open("test_results.json", "w", encoding="utf-8") as f:
            json.dump(results, f, ensure_ascii=False, indent=2)

        print("결과 저장 완료: test_results.json")


if __name__ == "__main__":
    asyncio.run(main())