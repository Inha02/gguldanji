# 꿀단지 AI Engine — 중고 상품 데이터 파이프라인

## 개요

중고 플랫폼 **꿀단지**의 적정 가격 추천 에이전트 학습을 위한 데이터 파이프라인입니다.
중고나라에서 크롤링한 원본 데이터를 정제 → 속성 보강 → 합성 데이터 생성까지 처리합니다.

**최종 목표**: 16개 카테고리 × 3,000건 = 약 48,000건의 합성 데이터 → XGBoost 가격 회귀 모델 학습

---

## 디렉토리 구조

```
gguldanji/ai-engine/
├── .env                            ← OPENAI_API_KEY 설정
├── venv/
└── crawler/
    ├── crawl_joongna.py
    ├── run_all_anchors.py
    ├── pipeline/                   ← 데이터 처리 파이프라인
    │   ├── __init__.py
    │   ├── step1a_dedup.py              # 1단계: 중복 제거
    │   ├── step1b_filter_extract.py     # 1단계: AI 필터링 + 속성 추출
    │   ├── step1c_validate.py           # 1단계: 검증 + 카테고리 병합
    │   ├── step2a_price_analysis.py     # 2단계: 가격 분포 분석
    │   ├── step2a2_impute.py            # 2단계: 결측 속성 보강 (GPT-4o)
    │   └── step2b_synthesize.py         # 2단계: 합성 데이터 생성
    └── data/
        ├── anchors/                ← 카테고리-앵커 키워드 정의 (메타)
        ├── raw/                    ← 크롤링 원본 (삭제 금지)
        ├── config/                 ← 설정 파일들
        │   ├── anchor_config.json       # 앵커 키워드별 카테고리/민감속성 정의
        │   ├── price_analysis.json      # 카테고리별 가격 통계
        │   └── augmentation_rules.json  # augmentation 변형 규칙
        ├── processed/{keyword}/    ← 키워드별 중간 처리 결과
        │   ├── {keyword}_candidates.jsonl    # 원본 후보 (입력)
        │   ├── {keyword}_deduped.jsonl       # 중복 제거 후
        │   ├── {keyword}_cleaned.jsonl       # AI 필터링 + 속성 추출 후
        │   └── {keyword}_filtered_log.jsonl  # 제거된 게시글 로그
        ├── final/                  ← 카테고리별 최종 정제 데이터
        │   └── {category}.jsonl
        ├── final_backup/           ← 속성 보강 전 자동 백업
        ├── synthetic/              ← 합성 데이터 출력
        │   ├── {category}_synth.jsonl    # 카테고리별 합성 데이터
        │   └── all_synthetic.jsonl       # 전체 통합
        └── *.json                  ← 단계별 리포트
```

---

## 사전 준비

```bash
cd gguldanji/ai-engine
source venv/bin/activate

pip install openai numpy tqdm python-dotenv
```

`ai-engine/.env` 파일에 API 키 설정 (대문자 필수):
```
OPENAI_API_KEY=sk-...
```

---

## 전체 파이프라인 실행 순서

```
크롤링 원본 (~16,000건)
  │
  ├─ Step 1A: 중복 제거 ─────────────────── ~13,600건
  ├─ Step 1B: AI 필터링 + 속성 추출 ──────── ~11,200건
  ├─ Step 1C: 검증 + 카테고리 병합 ────────── ~10,700건 (final/)
  │
  ├─ Step 2A:   가격 분포 분석 ────────────── config/ 생성
  ├─ Step 2A-2: 결측 속성 보강 (GPT-4o) ──── final/ 업데이트
  │
  └─ Step 2B: augmentation 합성 ───────────── ~48,000건 (synthetic/)
```

### 실행 명령어

```bash
cd gguldanji/ai-engine

# ── 1단계: 데이터 정제 ──
python -m crawler.pipeline.step1a_dedup
python -m crawler.pipeline.step1b_filter_extract
python -m crawler.pipeline.step1c_validate

# ── 2단계: 합성 데이터 생성 ──
python -m crawler.pipeline.step2a_price_analysis
python -m crawler.pipeline.step2a2_impute            # GPT-4o 속성 보강
python -m crawler.pipeline.step2b_synthesize          # augmentation (target 3000)
```

---

## 각 단계 상세

### Step 1A — 중복 제거

| 항목 | 내용 |
|------|------|
| 모델 | OpenAI `text-embedding-3-small` |
| 비용 | ~$0.03 |
| 시간 | 5~10분 |

처리 내용:
1. 같은 `seq`(게시글 ID) 중복 → 최신만 유지
2. 같은 판매자(`storeSeq`) + 같은 제목 → 최신만 유지 (가격만 변경한 재게시)
3. 임베딩 코사인 유사도 ≥ 0.92 → 같은 판매자면 중복 제거, 다른 판매자는 0.95 이상만 제거

```bash
# 특정 키워드만 처리
python -m crawler.pipeline.step1a_dedup 가방 지갑
```

### Step 1B — AI 필터링 + 속성 추출

| 항목 | 내용 |
|------|------|
| 모델 | OpenAI `gpt-4o-mini` |
| 비용 | ~$2.40 |
| 시간 | 30~50분 (5스레드 병렬) |

처리 내용:
1. 카테고리 적합성 판단 (예: "목줄" 검색 → 성인용품 제거)
2. 부적절 콘텐츠 필터링
3. 공통속성 + 민감속성 구조화 추출 (JSON)

```bash
python -m crawler.pipeline.step1b_filter_extract 가방 지갑
```

### Step 1C — 검증 + 카테고리 병합

| 항목 | 내용 |
|------|------|
| 비용 | 없음 (로컬) |
| 시간 | 몇 초 |

처리 내용:
1. 필수 필드 존재 여부 검증
2. IQR 기반 가격 이상치 제거 (3.0 IQR)
3. 카테고리별 통계 (가격 분포, 속성 완성도)
4. `final/{category}.jsonl`로 카테고리별 병합 출력

### Step 2A — 가격 분포 분석

| 항목 | 내용 |
|------|------|
| 비용 | 없음 (로컬) |
| 시간 | 몇 초 |

처리 내용:
1. 카테고리별 가격 분포 (p10, p25, 중앙값, p75, p90)
2. condition별 가격 비율 분석
3. 브랜드별 가격 통계
4. augmentation 규칙 생성 (condition multiplier, 감가율, 노이즈 범위)

> **주의**: 소수 데이터 편향으로 condition_multipliers가 역전될 수 있음 (예: C급 > S급).
> Step 2B에서 자동 교정됨.

### Step 2A-2 — 결측 속성 보강 (GPT-4o)

| 항목 | 내용 |
|------|------|
| 모델 | OpenAI `gpt-4o` |
| 비용 | ~$30-40 |
| 시간 | 1~2시간 (5스레드 병렬) |

왜 필요한가:
- Step 1B에서 추출된 속성 중 "알수없음"이 매우 많음 (usage_period 63%, original_price 87%, 소재 69% 등)
- XGBoost는 피처 값이 있어야 학습 가능 → 결측 상태로 augmentation하면 무의미한 복제
- GPT-4o의 제품 지식으로 제목+설명에서 추론 가능한 속성을 채움

처리 내용:
1. "알수없음"인 속성을 GPT-4o가 제목+설명+제품 지식으로 추론
2. 추론된 값에 `inferred_fields` 배열로 플래그 기록
3. 기존에 값이 있는 속성은 절대 덮어쓰지 않음
4. 최초 실행 시 `final/` → `final_backup/` 자동 백업

```bash
# dry-run으로 결측 현황만 확인 (API 호출 없음)
python -m crawler.pipeline.step2a2_impute --dry-run

# 특정 카테고리만 테스트
python -m crawler.pipeline.step2a2_impute 디지털기기

# 전체 실행
python -m crawler.pipeline.step2a2_impute
```

### Step 2B — Augmentation 합성 데이터 생성

| 항목 | 내용 |
|------|------|
| 비용 | 없음 (로컬) |
| 시간 | 몇 초 |
| 기본 target | 카테고리당 3,000건 |

Augmentation 전략:
1. **Condition 변형**: 상태를 한 단계 올리거나 내려 가격 비율 적용
2. **사용기간 변형**: ±3~12개월, 카테고리별 감가율 적용 (디지털 월2%, 식품 월5%, 도서 월0.5%)
3. **부속품 변형**: 풀박스/부속품 유무 토글 (+8% / +5% 프리미엄)
4. **가격 노이즈**: 실제 변동계수 기반 ±5~15%
5. **복합 변형**: 위 전략 2~3개 조합

condition_multipliers 자동 교정:
- 비표준 라벨("A", "A+", "A++") 제거 → 5개 표준 등급만 유지
- 역전 감지 시 (C급 > S급 등) 기본값으로 교정
- S급 ≥ A급 ≥ B급 ≥ C급 ≥ 부품용 단조감소 보장

```bash
# 기본 실행 (카테고리당 3000건)
python -m crawler.pipeline.step2b_synthesize

# target 변경
python -m crawler.pipeline.step2b_synthesize --target 5000

# 특정 카테고리만
python -m crawler.pipeline.step2b_synthesize 패션잡화 디지털기기
```

---

## 비용 요약

| 단계 | 모델 | 예상 비용 |
|------|------|----------|
| Step 1A (임베딩) | text-embedding-3-small | ~$0.03 |
| Step 1B (필터링) | gpt-4o-mini | ~$2.40 |
| Step 2A-2 (속성 보강) | gpt-4o | ~$30-40 |
| **합계** | | **~$35** |

Step 1C, 2A, 2B는 로컬 처리로 API 비용 없음.

---

## 출력 데이터 스키마

### final/{category}.jsonl — 정제 + 보강 데이터

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
    "모델명": "사피아노 서류가방",
    "소재": "사피아노 가죽",
    "종류": "서류가방",
    "색상": "블랙",
    "정품인증여부": "알수없음",
    "크기": "알수없음"
  },
  "inferred_fields": ["sensitive.모델명", "sensitive.소재", "sensitive.색상"],
  "imputation_confidence": "medium"
}
```

### synthetic/{category}_synth.jsonl — 합성 데이터 (XGBoost 학습용)

```json
{
  "id": "synth_패션잡화_가방_00001",
  "source_seq": 223999773,
  "is_original": false,
  "category": "패션잡화",
  "anchor_keyword": "가방",
  "common_features": {
    "condition": "A급",
    "usage_period_months": 6,
    "has_box": true,
    "has_accessories": true,
    "has_defects": false,
    "is_negotiable": true,
    "image_count": 5
  },
  "sensitive_features": {
    "브랜드": "프라다",
    "모델명": "사피아노 서류가방",
    "소재": "사피아노 가죽",
    "종류": "서류가방",
    "색상": "블랙",
    "정품인증여부": "알수없음",
    "크기": "알수없음"
  },
  "price_info": {
    "original_price": null,
    "selling_price": 187000,
    "price_ratio": null,
    "price_range_min": 159000,
    "price_range_max": 215000,
    "price_label": "적정"
  },
  "metadata": {
    "view_count": 200,
    "wish_count": 5,
    "chat_count": 4,
    "location": ["경기도 구리시 인창동"],
    "sort_date": "2026-02-03 21:17:51"
  },
  "augmentation": "condition_S급→A급"
}
```

---

## 16개 카테고리 × 앵커 키워드

| 카테고리 | 앵커 키워드 1 | 앵커 키워드 2 |
|----------|-------------|-------------|
| 디지털기기 | 갤럭시북 | 아이폰 |
| 가구/인테리어 | 책상 | 의자 |
| 출산/유아동 | 유모차 | 아기띠 |
| 여성의류 | 원피스 | 코트 |
| 패션잡화 | 가방 | 지갑 |
| 남성의류 | 남성가디건 | 남성셔츠 |
| 가전제품 | 냉장고 | 세탁기 |
| 생활용품 | 수납장 | 청소용품 |
| 스포츠/레저 | 자전거 | 골프채 |
| 취미/게임 | 닌텐도 | 플스 |
| 뷰티/미용 | 향수 | 드라이기 |
| 반려동물용품 | 캣타워 | 목줄 |
| 식품 | 홍삼 | 원두 |
| 도서 | 공인중개사 | 토익 |
| 티켓/교환권 | 기프티콘 | 티켓 |
| 기타 중고물품 | 캠핑용품 | 무료나눔 |

---

## 다음 단계 (예정)

1. **XGBoost 가격 회귀 모델 학습**: `synthetic/all_synthetic.jsonl` 기반
2. **게시글 생성**: 합성 데이터 속성을 기반으로 LLM이 다양한 판매자 스타일의 게시글 제목/내용 생성 → 플랫폼 시드 데이터 투입
3. **판매자 성향 분석 에이전트**: 대화 시나리오 합성 데이터 별도 생성 (가격 에이전트 완성 후)