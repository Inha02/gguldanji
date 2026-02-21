# 1단계: 크롤링 데이터 정제 파이프라인

## 디렉토리 구조

```
gguldanji/ai-engine/
├── crawler/
│   ├── pipeline/               ← 새로 생성
│   │   ├── __init__.py
│   │   ├── step1a_dedup.py          # 중복 제거
│   │   ├── step1b_filter_extract.py # AI 필터링 + 속성 추출
│   │   └── step1c_validate.py       # 검증 + 통계
│   ├── data/
│   │   ├── processed/{keyword}/{keyword}_candidates.jsonl  ← 입력
│   │   ├── processed/{keyword}/{keyword}_deduped.jsonl     ← step1a 출력
│   │   ├── processed/{keyword}/{keyword}_cleaned.jsonl     ← step1b 출력
│   │   ├── processed/{keyword}/{keyword}_filtered_log.jsonl
│   │   ├── final/{category}.jsonl                          ← step1c 최종 출력
│   │   ├── config/anchor_config.json
│   │   └── *.json (리포트들)
│   ├── crawl_joongna.py
│   └── run_all_anchors.py
└── venv/
```

## 사전 준비

```bash
cd gguldanji/ai-engine

# 가상환경 활성화
source venv/bin/activate

# 필요 패키지 설치
pip install openai numpy tqdm

# OpenAI API 키 설정
export OPENAI_API_KEY="sk-..."
```

## 실행 방법

### 전체 실행 (순차)
```bash
cd gguldanji/ai-engine

# Step 1-A: 중복 제거
python -m crawler.pipeline.step1a_dedup

# Step 1-B: AI 필터링 + 속성 추출
python -m crawler.pipeline.step1b_filter_extract

# Step 1-C: 검증 + 카테고리별 병합
python -m crawler.pipeline.step1c_validate
```

### 특정 키워드만 처리
```bash
# 가방, 지갑만 처리
python -m crawler.pipeline.step1a_dedup 가방 지갑
python -m crawler.pipeline.step1b_filter_extract 가방 지갑
python -m crawler.pipeline.step1c_validate
```

## 비용 예측 (OpenAI API)

| 단계 | 모델 | 예상 호출수 | 예상 비용 |
|------|------|------------|----------|
| Step 1-A (임베딩) | text-embedding-3-small | ~16,000건 (배치) | ~$0.03 |
| Step 1-B (필터링) | gpt-4o-mini | ~12,000건 | ~$2.40 |
| **합계** | | | **~$2.50** |

※ GPT-4o로 변경 시 Step 1-B 비용 약 10배 증가 (~$24)

## 출력 데이터 구조

### cleaned.jsonl 각 행의 구조:
```json
{
  "seq": 223999773,
  "keyword": "가방",
  "category": "패션잡화",
  "title": "프라다 남자 서류가방",
  "price": 220000,
  "sortDate": "2026-02-03 21:17:51",
  "location": ["경기도 구리시 인창동"],
  "viewCount": 200,
  "wishCount": 5,
  "chatCount": 4,
  "original_description": "홍콩에서...",
  "original_category": "수입명품,가방/핸드백,서류가방",
  "labels": ["직거래", "택배거래", "배송비 포함", "새상품"],
  "image_count": 6,
  "common_attributes": {
    "product_name": "프라다 남성 서류가방 사피아노",
    "condition": "S급",
    "usage_period": "미사용",
    "original_price": null,
    "selling_price": 220000,
    "includes_box": false,
    "includes_accessories": "알수없음",
    "defects": "없음",
    "negotiable": null
  },
  "sensitive_attributes": {
    "브랜드": "프라다",
    "모델명": "알수없음",
    "소재": "알수없음",
    "종류": "서류가방",
    "색상": "알수없음",
    "정품인증여부": "알수없음",
    "크기": "알수없음"
  }
}
```

## 다음 단계

이 정제된 데이터는 2단계(합성 데이터 생성)의 입력이 됩니다:
- `data/final/{category}.jsonl` → 가격 분포 분석 + 합성 데이터 생성