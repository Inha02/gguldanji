# 꿀단지 AI Engine — 중고 상품 데이터 파이프라인

## 개요

중고 플랫폼 **꿀단지**의 적정 가격 추천 에이전트 학습을 위한 데이터 파이프라인입니다.
중고나라에서 크롤링한 원본 데이터를 정제 → 속성 보강 → 합성 데이터 생성 → 가격 추정 모델 학습까지 처리합니다.

**최종 목표**: 3-Layer 가격 추정 시스템
- **Layer 1**: XGBoost/LightGBM 카테고리별 가격 회귀 모델 (로컬, 무료)
- **Layer 2**: GPT-4o LLM Fallback (미지 상품 대응, 건당 ~$0.003)
- **Layer 3**: ChromaDB RAG 유사 거래 검색 + 설명 근거 생성

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
    │   ├── step2a_price_analysis.py     # 2단계: 가격 분포 분석 + 민감속성 리포트
    │   ├── step2a2_impute.py            # 2단계: 결측 속성 보강 (GPT-4o)
    │   ├── step2b_synthesize.py         # 2단계: 합성 데이터 생성 (v2)
    │   ├── step3a_features.py           # 3단계: 피처 엔지니어링 (v2)
    │   ├── step3b_train.py              # 3단계: 모델 학습 + Optuna 튜닝
    │   └── step3c_inference.py          # 3단계: 3-Layer 추론 엔진
    └── data/
        ├── config/                 ← 설정 및 분석 파일
        │   ├── anchor_config.json              # 앵커 키워드별 카테고리/민감속성 정의
        │   ├── price_analysis.json             # 카테고리별 가격 통계
        │   ├── augmentation_rules.json         # augmentation 변형 규칙
        │   ├── sensitive_attributes_report.json # 민감속성 현황 리포트
        │   └── brand_price_stats.json          # 브랜드별 가격 통계
        ├── processed/{keyword}/    ← 키워드별 중간 처리 결과
        ├── final/                  ← 카테고리별 최종 정제 데이터
        ├── final_backup/           ← 속성 보강 전 자동 백업
        ├── synthetic/              ← 합성 데이터 출력
        │   ├── {category}_synth.jsonl
        │   └── all_synthetic.jsonl       # 전체 통합 (48,000건)
        ├── models/                 ← 학습된 모델 + 피처
        │   ├── {category}_features.pkl   # 피처 매트릭스
        │   └── {category}_model.pkl      # 학습된 모델 (XGBoost/LightGBM)
        ├── chroma_db/              ← ChromaDB 벡터 인덱스 (RAG용)
        └── *.json                  ← 단계별 리포트
```

---

## 사전 준비

```bash
cd gguldanji/ai-engine
source venv/bin/activate

pip install openai numpy tqdm python-dotenv pandas scikit-learn xgboost lightgbm optuna chromadb
```

Mac 환경에서는 추가로:
```bash
brew install libomp   # XGBoost용 OpenMP
```

`ai-engine/.env` 파일에 API 키 설정 (대문자 필수):
```
OPENAI_API_KEY=sk-...
```

---

## 전체 파이프라인 실행 순서

```
크롤링 원본 (15,523건)
  │
  ├─ Step 1A: 중복 제거 ─────────────────── 13,651건
  ├─ Step 1B: AI 필터링 + 속성 추출 ──────── 11,443건
  ├─ Step 1C: 검증 + 카테고리 병합 ────────── 10,747건 (final/)
  │
  ├─ Step 2A:   가격 분포 분석 ────────────── config/ 생성
  ├─ Step 2A-2: 결측 속성 보강 (GPT-4o) ──── final/ 업데이트 (21,514 필드 보강)
  ├─ Step 2A:   가격 분포 재분석 ──────────── config/ 갱신
  ├─ Step 2B: augmentation 합성 ───────────── 48,000건 (synthetic/)
  │
  ├─ Step 3A: 피처 엔지니어링 ─────────────── models/*_features.pkl
  ├─ Step 3B: 모델 학습 + 튜닝 ────────────── models/*_model.pkl
  └─ Step 3C: RAG 인덱스 빌드 ─────────────── chroma_db/ (추론 준비 완료)
```

### 실행 명령어

```bash
cd gguldanji/ai-engine

# ── 1단계: 데이터 정제 ──
python -m crawler.pipeline.step1a_dedup
python -m crawler.pipeline.step1b_filter_extract
python -m crawler.pipeline.step1c_validate

# ── 2단계: 합성 데이터 생성 ──
python -m crawler.pipeline.step2a_price_analysis        # 1차 분석
python -m crawler.pipeline.step2a2_impute               # GPT-4o 속성 보강
python -m crawler.pipeline.step2a_price_analysis        # 2차 분석 (보강 반영)
python -m crawler.pipeline.step2b_synthesize            # augmentation (target 3000)

# ── 3단계: 가격 추정 모델 ──
python -m crawler.pipeline.step3a_features              # 피처 엔지니어링
python -m crawler.pipeline.step3b_train                 # 모델 학습 + Optuna 튜닝 (~30분)
python -m crawler.pipeline.step3c_inference --build-index  # RAG 인덱스 빌드 (~$0.02)
python -m crawler.pipeline.step3c_inference --test      # 16개 카테고리 테스트
```

> **주의**: Step 2A는 Step 2A-2 전후로 2번 실행합니다. 보강 전에 한 번(기본 통계 확인용), 보강 후에 한 번(보강된 데이터 기반 augmentation 규칙 생성용).

---

## 각 단계 상세

### Step 1A — 중복 제거

| 항목 | 내용 |
|------|------|
| 모델 | OpenAI `text-embedding-3-small` |
| 비용 | ~$0.03 |
| 시간 | 5~10분 |
| 실행 결과 | 15,523건 → 13,651건 (12% 제거) |

처리 내용:
1. 같은 `seq`(게시글 ID) 중복 → 최신만 유지
2. 같은 판매자(`storeSeq`) + 같은 제목 → 최신만 유지 (가격만 변경한 재게시)
3. 임베딩 코사인 유사도 ≥ 0.92 → 같은 판매자면 중복 제거, 다른 판매자는 0.95 이상만 제거

```bash
python -m crawler.pipeline.step1a_dedup 가방 지갑   # 특정 키워드만
```

### Step 1B — AI 필터링 + 속성 추출

| 항목 | 내용 |
|------|------|
| 모델 | OpenAI `gpt-4o-mini` |
| 비용 | ~$2.40 |
| 시간 | 30~50분 (5스레드 병렬) |
| 실행 결과 | 13,651건 → 11,443건 적합 (84%) |

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
| 실행 결과 | 11,215건 → 10,747건 유효 (468건 이상치 제거) |

처리 내용:
1. 필수 필드 존재 여부 검증
2. IQR 기반 가격 이상치 제거 (3.0 IQR)
3. 카테고리별 통계 (가격 분포, 속성 완성도)
4. `final/{category}.jsonl`로 카테고리별 병합 출력

### Step 2A — 가격 분포 분석 + 민감속성 리포트

| 항목 | 내용 |
|------|------|
| 비용 | 없음 (로컬) |
| 시간 | 몇 초 |

처리 내용:
1. 카테고리별 가격 분포 (p10, p25, 중앙값, p75, p90)
2. condition별 가격 비율 분석
3. 브랜드별 가격 통계 → `brand_price_stats.json` (브랜드 변형 augmentation용)
4. 민감속성 현황 → `sensitive_attributes_report.json` (채워진 비율, 고유값 분포, 상위 10개 값)
5. augmentation 규칙 생성 → `augmentation_rules.json`

> **주의**: 소수 데이터 편향으로 condition_multipliers가 역전될 수 있음 (예: C급 > S급). Step 2B에서 자동 교정됨.

### Step 2A-2 — 결측 속성 보강 (GPT-4o)

| 항목 | 내용 |
|------|------|
| 모델 | OpenAI `gpt-4o` |
| 비용 | ~$30-40 |
| 시간 | ~2시간 (3스레드 병렬 + 0.5초 딜레이) |
| 실행 결과 | 9,643건 보강, 21,514개 필드 채움, 에러 0건 |

왜 필요한가:
- Step 1B에서 추출된 속성 중 "알수없음"이 매우 많음 (usage_period 63%, original_price 87%, 소재 69% 등)
- XGBoost는 피처 값이 있어야 학습 가능 → 결측 상태로 augmentation하면 무의미한 복제
- GPT-4o의 제품 지식으로 제목+설명에서 추론 가능한 속성을 채움

처리 내용:
1. "알수없음"인 속성을 GPT-4o가 제목+설명+제품 지식으로 추론
2. 추론된 값에 `inferred_fields` 배열로 플래그 기록
3. 기존에 값이 있는 속성은 절대 덮어쓰지 않음
4. 이미 보강된 아이템(`inferred_fields` 존재)은 자동 스킵 → 중단 후 재실행 안전
5. 최초 실행 시 `final/` → `final_backup/` 자동 백업
6. API 크레딧 소진(`insufficient_quota`) 감지 시 즉시 중단, 처리된 건은 저장

```bash
python -m crawler.pipeline.step2a2_impute --dry-run    # 결측 현황만 확인
python -m crawler.pipeline.step2a2_impute 디지털기기   # 특정 카테고리만
python -m crawler.pipeline.step2a2_impute               # 전체 실행
```

> **운영 주의사항**: GPT-4o API 크레딧을 사전에 충분히 충전해두세요 (~$35 필요). 크레딧 소진 시 자동 중단되며, 충전 후 재실행하면 이미 보강된 건은 스킵하고 나머지만 처리합니다.

### Step 2B — Augmentation 합성 데이터 생성 (v2)

| 항목 | 내용 |
|------|------|
| 비용 | 없음 (로컬) |
| 시간 | 몇 초 |
| 기본 target | 카테고리당 3,000건 |
| 실행 결과 | 원본 12,142건 → 합성 48,000건 |

Augmentation 전략 (5가지):
1. **Condition 변형**: 상태를 한 단계 올리거나 내려 가격 비율 적용 (9,302건)
2. **사용기간 변형**: ±3~12개월, 카테고리별 감가율 적용 (6,027건)
3. **부속품 변형**: 풀박스/부속품 유무 토글, +8%/+5% 프리미엄 (3,766건)
4. **가격 노이즈**: 실제 변동계수 기반 ±5~15% (14,520건)
5. **브랜드 변형**: 같은 카테고리 내 실제 브랜드 간 교차, 중앙값 비율로 가격 재산정 (2,243건)

v2 개선사항:
- **[A] 가격 0원 제외**: 무료나눔 등 0원 데이터는 원본으로만 포함, augmentation 대상에서 제외
- **[B] 카테고리별 전략 차등**: 식품/티켓은 noise만, 도서는 condition+noise만, 의류는 brand+condition+usage+noise 등
- **[C] price_ratio 결측 처리**: original_price 없으면 price_ratio를 null로 유지 → 모델 학습 시 피처 제외 가능
- **[D] 브랜드 변형**: 3건 이상 실제 데이터가 있는 브랜드 간에서만 교차, 비율 0.1x~10x 제한

카테고리별 활성 전략:

| 카테고리 | condition | usage | accessories | noise | brand |
|----------|:---------:|:-----:|:-----------:|:-----:|:-----:|
| 디지털기기, 가전, 가구, 패션잡화, 출산/유아동, 스포츠/레저, 취미/게임 | ✓ | ✓ | ✓ | ✓ | ✓ |
| 여성의류, 남성의류 | ✓ | ✓ | | ✓ | ✓ |
| 뷰티/미용 | ✓ | | | ✓ | ✓ |
| 생활용품 | ✓ | ✓ | ✓ | ✓ | |
| 반려동물용품 | ✓ | ✓ | | ✓ | |
| 기타 중고물품 | ✓ | ✓ | ✓ | ✓ | |
| 도서 | ✓ | | | ✓ | |
| 식품, 티켓/교환권 | | | | ✓ | |

condition_multipliers 자동 교정:
- 비표준 라벨("A", "A+", "A++") 제거 → 5개 표준 등급만 유지
- 역전 감지 시 (C급 > S급 등) 기본값으로 교정
- S급 ≥ A급 ≥ B급 ≥ C급 ≥ 부품용 단조감소 보장

```bash
python -m crawler.pipeline.step2b_synthesize                 # 기본 (카테고리당 3000건)
python -m crawler.pipeline.step2b_synthesize --target 5000   # target 변경
python -m crawler.pipeline.step2b_synthesize 패션잡화        # 특정 카테고리만
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
    "브랜드": "구찌",
    "모델명": "사피아노 서류가방",
    "소재": "사피아노 가죽",
    "종류": "서류가방",
    "색상": "블랙",
    "정품인증여부": "알수없음",
    "크기": "알수없음"
  },
  "price_info": {
    "original_price": null,
    "selling_price": 350000,
    "price_ratio": null,
    "price_range_min": 298000,
    "price_range_max": 403000,
    "price_label": "적정"
  },
  "metadata": {
    "view_count": 200,
    "wish_count": 5,
    "chat_count": 4,
    "location": ["경기도 구리시 인창동"],
    "sort_date": "2026-02-03 21:17:51"
  },
  "augmentation": "brand_프라다→구찌"
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

## Step 3 — 가격 추정 모델 (3-Layer)

### 아키텍처

```
사용자 입력 (카테고리, 브랜드, 상태, 속성들)
  │
  ├─ Layer 1: XGBoost/LightGBM (메인 추정, 로컬, 무료, ms 단위)
  │   → 학습된 브랜드/모델이면 즉시 가격 추정
  │   → 신뢰도 함께 반환 (high/medium/low)
  │
  ├─ Layer 2: GPT-4o Fallback (미지 상품 대응, 건당 ~$0.003)
  │   → Layer 1 신뢰도 낮을 때 자동 전환
  │   → RAG 유사거래 + 카테고리 가격 통계를 컨텍스트로 제공
  │
  └─ Layer 3: RAG 설명 근거 (ChromaDB 유사 거래 검색)
      → 유사 실거래 데이터 검색 + IQR 이상치 필터링
      → 모델 예측 + RAG 유사거래 가중 평균으로 최종 가격 산출
      → 피처 중요도 기반 "이 가격을 추정한 이유" 설명
```

### Step 3A — 피처 엔지니어링 (v2)

| 항목 | 내용 |
|------|------|
| 비용 | 없음 (로컬) |
| 시간 | 몇 초 |

처리 내용:
1. log(가격) 변환 → skewed 분포 해결
2. augmented 데이터 비율 max 50% 제한 → 과적합 방지
3. Target Encoding: 원본 train 데이터만으로 통계 계산 (data leakage 방지)
4. 민감속성: 숫자 변환 성공률로 문자열/숫자 자동 판별
5. augmented sample_weight 0.3 (원본 1.0)
6. train/test 분리: source_seq 기준 (같은 원본 파생 데이터는 반드시 같은 세트)

### Step 3B — 모델 학습 + Optuna 튜닝

| 항목 | 내용 |
|------|------|
| 비용 | 없음 (로컬) |
| 시간 | 20~30분 (Optuna 30 trials × 16 카테고리) |

처리 내용:
1. 카테고리별 XGBoost + LightGBM 둘 다 학습
2. Optuna 하이퍼파라미터 튜닝 (카테고리별 30 trials, MAPE 최소화)
3. log 가격 학습 → expm1 역변환 후 원래 스케일로 평가
4. median % 오차 기준 승자 선택
5. 모델 + 인코딩 맵 + 피처 중요도를 pickle 저장

테스트 결과 (16개 카테고리 median % 오차):

| 카테고리 | 승자 | median 오차 | R² | 피처 중요도 Top 3 |
|----------|------|-----------|-----|------------------|
| 남성의류 | XGBoost | 40.8% | 0.35 | 브랜드, 소재, 사이즈 |
| 식품 | XGBoost | 42.9% | -0.06 | 제품명, 브랜드, 용량 |
| 가전제품 | XGBoost | 46.6% | -0.01 | 모델명, 브랜드, 용량 |
| 도서 | XGBoost | 47.9% | 0.14 | 세트구성, 종류, 과목 |
| 디지털기기 | LightGBM | 49.0% | 0.23 | 모델명, 조회수, 출시년도 |
| 반려동물 | LightGBM | 49.9% | 0.32 | 조회수, 브랜드, 사진수 |
| 뷰티/미용 | LightGBM | 50.0% | -0.17 | 브랜드, 조회수, 모델명 |
| 패션잡화 | LightGBM | 50.2% | 0.17 | 조회수, 브랜드, 종류 |

### Step 3C — 3-Layer 추론 엔진

| 항목 | 내용 |
|------|------|
| RAG 인덱스 빌드 | ~$0.02 (text-embedding-3-small), 몇 분 |
| 추론 (Layer 1만) | 무료, ms 단위 |
| 추론 (Layer 2 fallback) | 건당 ~$0.003 |

RAG 보정 로직:
1. 유사거래 10건 검색 (ChromaDB + OpenAI 임베딩)
2. IQR 1.5배 + 기준점 ±4배 범위 이상치 필터링
3. 모델 예측 + RAG 유사거래 중앙값 가중 평균 (유사거래 5건 이상이면 모델 30%:RAG 70%)

16개 카테고리 테스트 결과 (RAG 보정 후):

| 카테고리 | 테스트 상품 | 최종 추정 | 가격 범위 | 시세 대비 |
|----------|-----------|----------|----------|----------|
| 가전제품 | 삼성 비스포크 냉장고 B급 | 64.1만 | 38~90만 | ✅ 적정 |
| 스포츠 | 타이틀리스트 아이언 A급 | 80.3만 | 48~113만 | ✅ 적정 |
| 출산 | 부가부 폭스5 A급 | 36.9만 | 22~52만 | ✅ 적정 |
| 취미 | 닌텐도 스위치 OLED A급 | 24.6만 | 15~35만 | ✅ 적정 |
| 남성의류 | 폴로 랄프로렌 A급 | 10.5만 | 7~14만 | ✅ 적정 |
| 식품 | 정관장 홍삼 S급 | 4.0만 | 2.8~5.2만 | ✅ 적정 |
| 도서 | 수험서 세트 B급 | 1.0만 | 0.6~1.4만 | ✅ 적정 |
| 디지털기기 | 아이폰 15 프로 A급 | 54.8만 | 33~77만 | △ 약간 과소 |
| 패션잡화 | 루이비통 네버풀 S급 | 32.8만 | 20~46만 | △ 과소 (데이터 한계) |

**16개 카테고리 중 10개 적정, 4개 약간 과소, 2개 확실 과소 (62.5% 적정)**

```bash
# RAG 인덱스 빌드
python -m crawler.pipeline.step3c_inference --build-index

# 16개 카테고리 테스트
python -m crawler.pipeline.step3c_inference --test

# Python에서 직접 사용
from crawler.pipeline.step3c_inference import PriceEstimator
engine = PriceEstimator()
result = engine.estimate("디지털기기", {"브랜드": "애플", "모델명": "아이폰 15 프로", "condition": "A급", ...})
```

---

## 비용 요약

| 단계 | 모델 | 예상 비용 |
|------|------|----------|
| Step 1A (임베딩) | text-embedding-3-small | ~$0.03 |
| Step 1B (필터링) | gpt-4o-mini | ~$2.40 |
| Step 2A-2 (속성 보강) | gpt-4o | ~$30-40 |
| Step 3C (RAG 인덱스) | text-embedding-3-small | ~$0.02 |
| **합계** | | **~$35** |

Step 1C, 2A, 2B, 3A, 3B는 로컬 처리로 API 비용 없음.
추론 시 Layer 1(트리 모델)은 무료, Layer 2(LLM Fallback)는 건당 ~$0.003.

---

## 다음 단계 (예정)

1. **API 서비스화**: FastAPI로 가격 추정 엔진을 REST API로 제공
2. **게시글 생성**: 합성 데이터 속성 기반으로 LLM이 다양한 판매자 스타일의 게시글 제목/내용 생성 → 플랫폼 시드 데이터 투입
3. **판매자 성향 분석 에이전트**: 대화 시나리오 합성 데이터 별도 생성 (가격 에이전트 완성 후)
4. **성능 개선 로드맵**: 크롤링 데이터 확대 (앵커 키워드 추가), 티켓/교환권 매수×단가 로직 추가, 고가 브랜드(명품) 특화 모델