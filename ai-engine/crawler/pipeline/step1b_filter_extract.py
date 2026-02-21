"""
Step 1-B: AI 기반 필터링 + 속성 추출 (OpenAI GPT-4o-mini)
============================================================
위치: gguldanji/ai-engine/crawler/pipeline/step1b_filter_extract.py

실행 방법:
  cd gguldanji/ai-engine
  python -m crawler.pipeline.step1b_filter_extract

  # 특정 키워드만 처리:
  python -m crawler.pipeline.step1b_filter_extract 가방 지갑

필요 패키지:
  pip install openai tqdm

환경변수:
  export OPENAI_API_KEY="sk-..."

설명:
  deduped 데이터에서:
  1) 카테고리 적합성 필터링
  2) 부적절 콘텐츠 필터링 (성인용품 등)
  3) 공통속성 + 민감속성 구조화 추출
  4) 결과를 {keyword}_cleaned.jsonl 로 저장
"""

import json
import os
import sys
import time
import re
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

from dotenv import load_dotenv
from openai import OpenAI
from tqdm import tqdm

# ──────────────────────────────────────────────
# 설정
# ──────────────────────────────────────────────
MODEL = "gpt-4o-mini"  # 비용 효율적. 정확도 필요시 "gpt-4o"로 변경
MAX_CONCURRENT = 5  # 동시 API 호출 수
RETRY_COUNT = 2
RETRY_DELAY = 2  # 초

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
PROCESSED_DIR = DATA_DIR / "processed"
CONFIG_DIR = DATA_DIR / "config"

# .env 파일에서 API 키 로드 (ai-engine/.env)
ENV_PATH = BASE_DIR.parent / ".env"
load_dotenv(ENV_PATH)

client = OpenAI()

# ──────────────────────────────────────────────
# 앵커 키워드 → 카테고리 매핑 + 민감속성 정의
# ──────────────────────────────────────────────
ANCHOR_CONFIG = {
    # 디지털기기
    "갤럭시북": {
        "category": "디지털기기",
        "sensitive_attrs": ["브랜드", "모델명", "출시년도", "저장용량", "RAM", "색상", "화면크기", "보증기간_잔여"],
        "description": "노트북/랩탑 제품"
    },
    "아이폰": {
        "category": "디지털기기",
        "sensitive_attrs": ["브랜드", "모델명", "출시년도", "저장용량", "색상", "배터리_성능", "통신사", "보증기간_잔여"],
        "description": "스마트폰 제품"
    },
    # 가구/인테리어
    "책상": {
        "category": "가구/인테리어",
        "sensitive_attrs": ["브랜드", "소재", "크기_가로x세로x높이", "조립여부", "용도", "색상"],
        "description": "책상/데스크 가구"
    },
    "의자": {
        "category": "가구/인테리어",
        "sensitive_attrs": ["브랜드", "소재", "종류", "색상", "높이조절_여부", "팔걸이_여부"],
        "description": "의자 가구"
    },
    # 출산/유아동
    "유모차": {
        "category": "출산/유아동",
        "sensitive_attrs": ["브랜드", "모델명", "종류", "사용개월수", "안전인증", "접이식여부"],
        "description": "유모차 제품"
    },
    "아기띠": {
        "category": "출산/유아동",
        "sensitive_attrs": ["브랜드", "모델명", "종류", "사용개월수", "세탁여부", "최대체중"],
        "description": "아기띠/힙시트 제품"
    },
    # 여성의류
    "원피스": {
        "category": "여성의류",
        "sensitive_attrs": ["브랜드", "사이즈", "시즌", "소재", "착용횟수", "색상", "기장"],
        "description": "여성 원피스 의류"
    },
    "코트": {
        "category": "여성의류",
        "sensitive_attrs": ["브랜드", "사이즈", "시즌", "소재", "착용횟수", "색상", "기장"],
        "description": "여성 코트 의류"
    },
    # 패션잡화
    "가방": {
        "category": "패션잡화",
        "sensitive_attrs": ["브랜드", "모델명", "소재", "종류", "색상", "정품인증여부", "크기"],
        "description": "가방/핸드백 제품"
    },
    "지갑": {
        "category": "패션잡화",
        "sensitive_attrs": ["브랜드", "모델명", "소재", "종류", "색상", "정품인증여부"],
        "description": "지갑 제품"
    },
    # 남성의류
    "남성가디건": {
        "category": "남성의류",
        "sensitive_attrs": ["브랜드", "사이즈", "시즌", "소재", "착용횟수", "색상"],
        "description": "남성 가디건 의류"
    },
    "남성셔츠": {
        "category": "남성의류",
        "sensitive_attrs": ["브랜드", "사이즈", "시즌", "소재", "착용횟수", "색상", "목사이즈"],
        "description": "남성 셔츠 의류"
    },
    # 가전제품
    "냉장고": {
        "category": "가전제품",
        "sensitive_attrs": ["브랜드", "모델명", "용량_리터", "에너지등급", "도어타입", "설치여부", "보증잔여"],
        "description": "냉장고 가전"
    },
    "세탁기": {
        "category": "가전제품",
        "sensitive_attrs": ["브랜드", "모델명", "용량_kg", "에너지등급", "종류", "설치여부", "보증잔여"],
        "description": "세탁기 가전"
    },
    # 생활용품
    "수납장": {
        "category": "생활용품",
        "sensitive_attrs": ["브랜드", "소재", "크기", "칸수", "색상", "조립여부"],
        "description": "수납장/정리함"
    },
    "청소용품": {
        "category": "생활용품",
        "sensitive_attrs": ["브랜드", "종류", "모델명", "사용기간"],
        "description": "청소 관련 용품"
    },
    # 스포츠/레저
    "자전거": {
        "category": "스포츠/레저",
        "sensitive_attrs": ["브랜드", "모델명", "종류", "프레임사이즈", "바퀴사이즈", "변속기", "부품교체이력"],
        "description": "자전거"
    },
    "골프채": {
        "category": "스포츠/레저",
        "sensitive_attrs": ["브랜드", "모델명", "종류", "샤프트종류", "로프트각도", "세트구성"],
        "description": "골프채/골프 장비"
    },
    # 취미/게임
    "닌텐도": {
        "category": "취미/게임",
        "sensitive_attrs": ["모델명", "저장용량", "색상", "동봉게임수", "개조여부", "조이콘상태"],
        "description": "닌텐도 게임기/게임 제품 (칩/악세사리 아닌 본체 위주)"
    },
    "플스": {
        "category": "취미/게임",
        "sensitive_attrs": ["모델명", "저장용량", "에디션", "동봉게임수", "컨트롤러수"],
        "description": "플레이스테이션 게임기/게임 제품"
    },
    # 뷰티/미용
    "향수": {
        "category": "뷰티/미용",
        "sensitive_attrs": ["브랜드", "제품명", "용량_ml", "잔량_퍼센트", "유통기한", "개봉여부"],
        "description": "향수 제품"
    },
    "드라이기": {
        "category": "뷰티/미용",
        "sensitive_attrs": ["브랜드", "모델명", "종류", "사용기간", "보증잔여"],
        "description": "헤어드라이기/미용기기"
    },
    # 반려동물용품
    "캣타워": {
        "category": "반려동물용품",
        "sensitive_attrs": ["브랜드", "크기_높이", "소재", "단수", "색상", "스크래처포함여부"],
        "description": "고양이 캣타워"
    },
    "목줄": {
        "category": "반려동물용품",
        "sensitive_attrs": ["브랜드", "소재", "크기", "대상동물크기", "종류"],
        "description": "반려동물 목줄/하네스 (성인용품 아님)"
    },
    # 식품
    "홍삼": {
        "category": "식품",
        "sensitive_attrs": ["브랜드", "제품명", "용량", "유통기한", "개봉여부", "형태"],
        "description": "홍삼 건강식품"
    },
    "원두": {
        "category": "식품",
        "sensitive_attrs": ["브랜드", "원산지", "용량_g", "로스팅정도", "유통기한", "개봉여부"],
        "description": "커피 원두 (원두머신/커피머신 아닌 원두 자체)"
    },
    # 도서
    "공인중개사": {
        "category": "도서",
        "sensitive_attrs": ["출판사", "판수", "발행년도", "과목구성", "필기여부", "세트구성"],
        "description": "공인중개사 시험 교재/도서"
    },
    "토익": {
        "category": "도서",
        "sensitive_attrs": ["출판사", "판수", "발행년도", "종류", "필기여부", "세트구성"],
        "description": "토익 시험 교재/도서"
    },
    # 티켓/교환권
    "기프티콘": {
        "category": "티켓/교환권",
        "sensitive_attrs": ["사용처", "권종금액", "유효기한", "종류"],
        "description": "기프티콘/모바일상품권"
    },
    "티켓": {
        "category": "티켓/교환권",
        "sensitive_attrs": ["종류", "이벤트명", "날짜", "좌석등급", "매수", "유효기한"],
        "description": "공연/스포츠/교통 티켓"
    },
    # 기타 중고물품
    "캠핑용품": {
        "category": "기타 중고물품",
        "sensitive_attrs": ["브랜드", "종류", "모델명", "크기", "무게", "사용횟수"],
        "description": "캠핑 관련 용품"
    },
    "무료나눔": {
        "category": "기타 중고물품",
        "sensitive_attrs": ["물품종류", "상태", "수량"],
        "description": "무료 나눔 물품"
    },
}

# 공통 속성 정의
COMMON_ATTRS = [
    "product_name",       # 정제된 상품명
    "condition",          # S급/A급/B급/C급/부품용
    "usage_period",       # 사용 기간 (예: "6개월", "2년", "미사용")
    "original_price",     # 정가 (알 수 있는 경우, 원 단위. 모르면 null)
    "selling_price",      # 판매 희망가 (원 단위)
    "includes_box",       # 풀박스 여부 (true/false)
    "includes_accessories",  # 부속품/구성품 정보 (문자열)
    "defects",            # 하자 정보 (문자열, 없으면 "없음")
    "negotiable",         # 네고 가능 여부 (true/false/unknown)
]


# ──────────────────────────────────────────────
# 프롬프트 생성
# ──────────────────────────────────────────────
def build_system_prompt():
    return """당신은 중고거래 플랫폼 '꿀단지'의 데이터 정제 전문가입니다.
크롤링된 중고 게시글을 분석하여 다음을 판단하고 추출합니다:
1. 해당 게시글이 지정된 카테고리/앵커 키워드에 적합한 상품인지 판단
2. 부적절한 콘텐츠(성인용품, 불법 등) 필터링
3. 적합한 경우, 공통속성과 민감속성을 구조화하여 추출

반드시 JSON 형식으로만 응답하세요. 마크다운 백틱이나 다른 텍스트 없이 순수 JSON만 출력하세요."""


def build_user_prompt(item: dict, keyword: str) -> str:
    config = ANCHOR_CONFIG[keyword]
    
    # 게시글 정보 추출
    title = item.get("title", "")
    detail = item.get("detail", {})
    description = detail.get("productDescription", "")
    price = item.get("price", 0)
    category_name = detail.get("categoryName", "")
    condition_data = detail.get("condition", {})
    labels = detail.get("labels", [])
    location = item.get("locationNames", [])
    location_str = location[0] if location else "미지정"
    
    # condition 해석
    product_condition = condition_data.get("productCondition", -1)
    condition_map = {0: "새상품", 1: "거의새것", 2: "중고", 3: "낡은"}
    condition_str = condition_map.get(product_condition, "알수없음")
    
    options = condition_data.get("options", {})
    full_package = options.get("fullPackageYn", 0) == 1
    limited_edition = options.get("limitedEditionYn", 0) == 1
    flawed = options.get("flawedYn", 0) == 1

    return f"""[앵커 키워드]: {keyword}
[타겟 카테고리]: {config['category']}
[상품 설명]: {config['description']}

[게시글 정보]
- 제목: {title}
- 설명: {description[:500]}
- 가격: {price}원
- 중고나라 카테고리: {category_name}
- 상태: {condition_str}
- 풀박스: {"예" if full_package else "아니오/미확인"}
- 한정판: {"예" if limited_edition else "아니오"}
- 하자: {"있음" if flawed else "없음/미확인"}
- 라벨: {', '.join(labels)}
- 지역: {location_str}

[요청]
아래 JSON 구조로 응답하세요:

{{
  "is_relevant": true/false,
  "reject_reason": "적합한 경우 null, 부적합 시 사유 (카테고리불일치/성인용품/복합상품/광고글/기타)",
  "common_attributes": {{
    "product_name": "정제된 상품명 (브랜드+모델+핵심특징)",
    "condition": "S급/A급/B급/C급/부품용 중 하나",
    "usage_period": "사용 기간 (예: 6개월, 2년, 미사용, 알수없음)",
    "original_price": 정가(숫자) 또는 null,
    "selling_price": {price},
    "includes_box": true/false/null,
    "includes_accessories": "부속품 정보 문자열 또는 알수없음",
    "defects": "하자 정보 또는 없음",
    "negotiable": true/false/null
  }},
  "sensitive_attributes": {{
    {', '.join(f'"{attr}": "값 또는 알수없음"' for attr in config['sensitive_attrs'])}
  }}
}}

- is_relevant가 false이면 common_attributes와 sensitive_attributes는 null로 설정
- 게시글에서 파악할 수 없는 정보는 "알수없음" 또는 null로 기입
- condition 판단 기준: S급(미사용/미개봉), A급(거의새것/사용감거의없음), B급(사용감있으나양호), C급(사용감많음/하자있음), 부품용(고장/부품만)
- 가격이 0원이면 무료나눔 가능성 고려"""


# ──────────────────────────────────────────────
# API 호출
# ──────────────────────────────────────────────
def call_gpt(item: dict, keyword: str) -> dict | None:
    """GPT-4o-mini로 필터링 + 속성 추출"""
    for attempt in range(RETRY_COUNT + 1):
        try:
            response = client.chat.completions.create(
                model=MODEL,
                messages=[
                    {"role": "system", "content": build_system_prompt()},
                    {"role": "user", "content": build_user_prompt(item, keyword)}
                ],
                temperature=0.1,
                max_tokens=1000,
                response_format={"type": "json_object"}
            )
            
            content = response.choices[0].message.content.strip()
            # JSON 파싱
            result = json.loads(content)
            return result
            
        except json.JSONDecodeError as e:
            if attempt < RETRY_COUNT:
                time.sleep(RETRY_DELAY)
                continue
            print(f"  [WARN] JSON 파싱 실패 (seq={item.get('seq')}): {e}")
            return None
        except Exception as e:
            if attempt < RETRY_COUNT:
                time.sleep(RETRY_DELAY)
                continue
            print(f"  [ERROR] API 오류 (seq={item.get('seq')}): {e}")
            return None


# ──────────────────────────────────────────────
# 단건 처리 함수 (스레드풀용)
# ──────────────────────────────────────────────
def process_single_item(args):
    """단일 아이템 처리 → (원본, AI결과, 키워드)"""
    item, keyword = args
    result = call_gpt(item, keyword)
    return item, result, keyword


# ──────────────────────────────────────────────
# 키워드별 처리
# ──────────────────────────────────────────────
def process_keyword(keyword: str) -> dict:
    """키워드 하나에 대한 필터링 + 속성 추출"""
    print(f"\n{'='*50}")
    print(f"[{keyword}] 필터링 + 속성 추출 시작")
    print(f"{'='*50}")
    
    # deduped 파일 로드
    deduped_path = PROCESSED_DIR / keyword / f"{keyword}_deduped.jsonl"
    if not deduped_path.exists():
        print(f"  [SKIP] deduped 파일 없음: {deduped_path}")
        print(f"  먼저 step1a_dedup.py를 실행하세요.")
        return {"keyword": keyword, "input": 0, "relevant": 0, "filtered": 0, "error": 0}
    
    items = []
    with open(deduped_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                items.append(json.loads(line))
    
    total = len(items)
    print(f"  입력: {total}건")
    
    if keyword not in ANCHOR_CONFIG:
        print(f"  [ERROR] 앵커 설정 없음: {keyword}")
        return {"keyword": keyword, "input": total, "relevant": 0, "filtered": 0, "error": total}
    
    # 병렬 처리
    relevant_items = []
    filtered_items = []
    error_count = 0
    
    args_list = [(item, keyword) for item in items]
    
    with ThreadPoolExecutor(max_workers=MAX_CONCURRENT) as executor:
        futures = {executor.submit(process_single_item, args): args for args in args_list}
        
        with tqdm(total=total, desc=f"  [{keyword}]") as pbar:
            for future in as_completed(futures):
                item, result, kw = future.result()
                
                if result is None:
                    error_count += 1
                elif result.get("is_relevant", False):
                    # 원본 데이터에 AI 추출 결과를 병합
                    enriched = {
                        "seq": item.get("seq"),
                        "keyword": keyword,
                        "category": ANCHOR_CONFIG[keyword]["category"],
                        "title": item.get("title"),
                        "price": item.get("price"),
                        "sortDate": item.get("sortDate"),
                        "location": item.get("locationNames", []),
                        "viewCount": item.get("detail", {}).get("viewCount", 0),
                        "wishCount": item.get("wishCount", 0),
                        "chatCount": item.get("chatCount", 0),
                        "original_description": item.get("detail", {}).get("productDescription", ""),
                        "original_category": item.get("detail", {}).get("categoryName", ""),
                        "original_condition": item.get("detail", {}).get("condition", {}),
                        "labels": item.get("detail", {}).get("labels", []),
                        "image_count": len(item.get("detail", {}).get("media", [])),
                        "thumb_url": item.get("thumbUrl", ""),
                        # AI 추출 결과
                        "common_attributes": result.get("common_attributes"),
                        "sensitive_attributes": result.get("sensitive_attributes"),
                    }
                    relevant_items.append(enriched)
                else:
                    filtered_items.append({
                        "seq": item.get("seq"),
                        "title": item.get("title"),
                        "reject_reason": result.get("reject_reason", "unknown")
                    })
                
                pbar.update(1)
    
    # 저장: cleaned (적합 데이터)
    output_dir = PROCESSED_DIR / keyword
    output_dir.mkdir(parents=True, exist_ok=True)
    
    cleaned_path = output_dir / f"{keyword}_cleaned.jsonl"
    with open(cleaned_path, "w", encoding="utf-8") as f:
        for item in relevant_items:
            f.write(json.dumps(item, ensure_ascii=False) + "\n")
    
    # 저장: filtered (제거된 데이터 로그)
    filtered_path = output_dir / f"{keyword}_filtered_log.jsonl"
    with open(filtered_path, "w", encoding="utf-8") as f:
        for item in filtered_items:
            f.write(json.dumps(item, ensure_ascii=False) + "\n")
    
    print(f"  적합: {len(relevant_items)}건 → {cleaned_path}")
    print(f"  필터링: {len(filtered_items)}건 → {filtered_path}")
    print(f"  오류: {error_count}건")
    
    return {
        "keyword": keyword,
        "input": total,
        "relevant": len(relevant_items),
        "filtered": len(filtered_items),
        "error": error_count
    }


def get_all_keywords() -> list[str]:
    """deduped 파일이 있는 키워드 목록"""
    keywords = []
    if not PROCESSED_DIR.exists():
        return keywords
    for subdir in sorted(PROCESSED_DIR.iterdir()):
        if subdir.is_dir():
            deduped = subdir / f"{subdir.name}_deduped.jsonl"
            if deduped.exists():
                keywords.append(subdir.name)
    return keywords


def main():
    print("=" * 60)
    print("Step 1-B: AI 기반 필터링 + 속성 추출")
    print(f"모델: {MODEL}")
    print("=" * 60)
    
    if len(sys.argv) > 1:
        keywords = sys.argv[1:]
    else:
        keywords = get_all_keywords()
    
    if not keywords:
        print("[ERROR] 처리할 키워드가 없습니다.")
        print("  먼저 step1a_dedup.py를 실행하세요.")
        return
    
    # 앵커 설정에 없는 키워드 경고
    for kw in keywords:
        if kw not in ANCHOR_CONFIG:
            print(f"  [WARN] '{kw}'에 대한 앵커 설정이 없습니다. ANCHOR_CONFIG에 추가하세요.")
    
    keywords = [kw for kw in keywords if kw in ANCHOR_CONFIG]
    print(f"\n처리 대상 키워드 ({len(keywords)}개): {keywords}")
    
    # 비용 예측
    estimated_items = len(keywords) * 400  # dedup 후 평균 ~400건 가정
    estimated_cost = estimated_items * 0.0002  # GPT-4o-mini 기준 ~$0.0002/call
    print(f"예상 API 호출: ~{estimated_items}건, 예상 비용: ~${estimated_cost:.2f}")
    
    results = []
    for keyword in keywords:
        result = process_keyword(keyword)
        results.append(result)
    
    # 요약 리포트
    print("\n" + "=" * 60)
    print("필터링 + 속성 추출 요약 리포트")
    print("=" * 60)
    print(f"{'키워드':<15} {'입력':>6} {'적합':>6} {'필터링':>6} {'오류':>6} {'적합률':>8}")
    print("-" * 60)
    
    total_input = 0
    total_relevant = 0
    total_filtered = 0
    total_error = 0
    
    for r in results:
        total_input += r["input"]
        total_relevant += r["relevant"]
        total_filtered += r["filtered"]
        total_error += r["error"]
        rate = f"{r['relevant']/r['input']*100:.1f}%" if r["input"] > 0 else "N/A"
        print(f"{r['keyword']:<15} {r['input']:>6} {r['relevant']:>6} {r['filtered']:>6} {r['error']:>6} {rate:>8}")
    
    total_rate = f"{total_relevant/total_input*100:.1f}%" if total_input > 0 else "N/A"
    print("-" * 60)
    print(f"{'합계':<15} {total_input:>6} {total_relevant:>6} {total_filtered:>6} {total_error:>6} {total_rate:>8}")
    
    # 리포트 저장
    report_path = DATA_DIR / "filter_extract_report.json"
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"\n리포트 저장: {report_path}")
    
    # 앵커 설정도 저장 (나중에 합성 데이터 생성 시 사용)
    config_path = CONFIG_DIR / "anchor_config.json"
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    with open(config_path, "w", encoding="utf-8") as f:
        json.dump(ANCHOR_CONFIG, f, ensure_ascii=False, indent=2)
    print(f"앵커 설정 저장: {config_path}")


if __name__ == "__main__":
    main()