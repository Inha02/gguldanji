"""
증분 업데이트 단독 실행 테스트
================================
초기 채팅과 비슷한 톤(사무적, 가격 민감)의 신규 채팅으로
리베이스 없이 순수 증분 업데이트만 실행되는지 확인한다.

실행:
  python -m tests.test_update_only

사전 준비:
  서버 실행: uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload
"""

import asyncio
import json
import sys

import httpx

BASE_URL = "http://localhost:8000/api/v1/profiling/analyze"

# ──────────────────────────────────────────────
# 더미 채팅 데이터
# ──────────────────────────────────────────────

# 초기 분석용: 사무적, 가격 민감, 효율 지향 판매자
INITIAL_CHAT_LOGS = [
    {"role": "buyer", "message": "안녕하세요, 노트북 아직 판매중인가요?", "timestamp": "2026-03-01T10:00:00"},
    {"role": "seller", "message": "네 판매중입니다.", "timestamp": "2026-03-01T10:01:00"},
    {"role": "buyer", "message": "상태 어떤가요?", "timestamp": "2026-03-01T10:02:00"},
    {"role": "seller", "message": "사용기간 6개월이고 외관 기스 없습니다. 배터리 사이클 50회 미만입니다.", "timestamp": "2026-03-01T10:03:00"},
    {"role": "buyer", "message": "70만원에 가능할까요?", "timestamp": "2026-03-01T10:05:00"},
    {"role": "seller", "message": "75만원까지 가능합니다. 그 이하는 어렵습니다.", "timestamp": "2026-03-01T10:06:00"},
    {"role": "buyer", "message": "알겠습니다. 75만원에 하겠습니다. 직거래 가능한가요?", "timestamp": "2026-03-01T10:07:00"},
    {"role": "seller", "message": "사당역 가능합니다. 내일 오후 2시 어떠세요?", "timestamp": "2026-03-01T10:08:00"},
    {"role": "buyer", "message": "좋습니다.", "timestamp": "2026-03-01T10:09:00"},
    {"role": "seller", "message": "내일 2시 사당역 4번출구에서 뵙겠습니다.", "timestamp": "2026-03-01T10:10:00"},
]

# 증분 업데이트용: 동일한 톤 유지 (사무적, 가격 민감, 효율 지향)
UPDATE_CHAT_LOGS = [
    {"role": "buyer", "message": "안녕하세요 키보드 판매글 보고 연락드립니다.", "timestamp": "2026-03-03T15:00:00"},
    {"role": "seller", "message": "네 문의 감사합니다.", "timestamp": "2026-03-03T15:01:00"},
    {"role": "buyer", "message": "키캡 마모 있나요?", "timestamp": "2026-03-03T15:02:00"},
    {"role": "seller", "message": "키캡 마모 없고 구매 후 2개월 사용했습니다. 정품 케이블 포함입니다.", "timestamp": "2026-03-03T15:03:00"},
    {"role": "buyer", "message": "8만원에 가능할까요?", "timestamp": "2026-03-03T15:05:00"},
    {"role": "seller", "message": "9만원입니다. 네고 불가입니다.", "timestamp": "2026-03-03T15:06:00"},
    {"role": "buyer", "message": "알겠습니다 9만원에 할게요. 택배 되나요?", "timestamp": "2026-03-03T15:07:00"},
    {"role": "seller", "message": "택배비 3000원 별도입니다. 입금 확인 후 당일 발송합니다.", "timestamp": "2026-03-03T15:08:00"},
    {"role": "buyer", "message": "네 입금하겠습니다.", "timestamp": "2026-03-03T15:09:00"},
    {"role": "seller", "message": "입금 확인되면 운송장 번호 보내드리겠습니다.", "timestamp": "2026-03-03T15:10:00"},
]


# ──────────────────────────────────────────────
# 테스트 실행
# ──────────────────────────────────────────────

async def main():
    print("=" * 60)
    print("증분 업데이트 단독 실행 테스트")
    print("(리베이스 없이 순수 업데이트만 발생하는지 확인)")
    print("=" * 60)

    async with httpx.AsyncClient(timeout=60.0) as client:
        # 서버 연결 확인
        try:
            health = await client.get("http://localhost:8000/api/v1/health")
            print(f"서버 상태: {health.status_code}")
        except httpx.ConnectError:
            print("ERROR: 서버에 연결할 수 없습니다.")
            sys.exit(1)

        # ── 1단계: 초기 분석 ──
        print("\n" + "-" * 60)
        print("1단계: 초기 분석")
        print("-" * 60)

        resp1 = await client.post(BASE_URL, json={
            "seller_id": "test_seller_update",
            "chat_logs": INITIAL_CHAT_LOGS,
            "existing_profile": None,
        })

        if resp1.status_code != 200:
            print(f"ERROR: {resp1.text}")
            sys.exit(1)

        result1 = resp1.json()
        profile1 = result1["profile"]

        print(f"Mode: {result1['mode']}")
        print(f"Version: {profile1['profile_version']}")
        print(f"Summary: {profile1['analysis_summary']}")
        _print_scores(profile1)

        # ── 2단계: 증분 업데이트 (동일 톤) ──
        print("\n" + "-" * 60)
        print("2단계: 증분 업데이트 (동일 톤 채팅)")
        print("-" * 60)

        resp2 = await client.post(BASE_URL, json={
            "seller_id": "test_seller_update",
            "chat_logs": UPDATE_CHAT_LOGS,
            "existing_profile": profile1,
        })

        if resp2.status_code != 200:
            print(f"ERROR: {resp2.text}")
            sys.exit(1)

        result2 = resp2.json()
        profile2 = result2["profile"]

        print(f"Mode: {result2['mode']}")
        print(f"Version: {profile2['profile_version']}")
        print(f"Rebase performed: {profile2.get('rebase_performed', False)}")
        print(f"Rebase recommended: {profile2.get('rebase_recommended', False)}")
        print(f"Summary: {profile2['analysis_summary']}")

        # 변경사항 출력
        changes = profile2.get("change_history", [])
        new_changes = [c for c in changes if c.get("version") == profile2["profile_version"]]
        if new_changes:
            print(f"\n변경사항 ({len(new_changes)}건):")
            for ch in new_changes:
                print(f"  - {ch}")
        else:
            print("\n변경사항 없음 (점수 유지, confidence 상승)")

        _print_scores(profile2)

        # ── 비교 ──
        print("\n" + "-" * 60)
        print("점수 비교 (초기 → 업데이트)")
        print("-" * 60)
        _compare_profiles(profile1, profile2)

        # 결과 저장
        results = {
            "step1_initial": profile1,
            "step2_updated": profile2,
        }
        with open("test_update_only_results.json", "w", encoding="utf-8") as f:
            json.dump(results, f, ensure_ascii=False, indent=2)

        print("\n결과 저장 완료: test_update_only_results.json")


def _print_scores(profile: dict):
    """프로필 점수 요약 출력"""
    print(f"\n  점수 요약:")
    for dim_name, features in profile["dimensions"].items():
        print(f"\n  [{dim_name}]")
        for feat_name, feat_data in features.items():
            print(f"    {feat_name}: score={feat_data['score']}, confidence={feat_data['confidence']}")


def _compare_profiles(before: dict, after: dict):
    """두 프로필의 점수 변화를 비교 출력"""
    for dim_name in before["dimensions"]:
        for feat_name in before["dimensions"][dim_name]:
            b = before["dimensions"][dim_name][feat_name]
            a = after["dimensions"][dim_name][feat_name]

            score_diff = a["score"] - b["score"]
            conf_diff = a["confidence"] - b["confidence"]

            marker = ""
            if score_diff > 0:
                marker = " ▲"
            elif score_diff < 0:
                marker = " ▼"

            conf_marker = ""
            if conf_diff > 0:
                conf_marker = " ▲"
            elif conf_diff < 0:
                conf_marker = " ▼"

            print(
                f"  {feat_name:30s}: "
                f"score {b['score']}→{a['score']}{marker:3s}  "
                f"confidence {b['confidence']:.2f}→{a['confidence']:.2f}{conf_marker}"
            )


if __name__ == "__main__":
    asyncio.run(main())