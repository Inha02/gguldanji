"""
Step 3C: 가격 추정 엔진 (3-Layer)
===================================
위치: gguldanji/ai-engine/crawler/pipeline/step3c_inference.py

실행 (RAG 인덱스 빌드):
  python -m crawler.pipeline.step3c_inference --build-index

실행 (테스트 추론):
  python -m crawler.pipeline.step3c_inference --test

필요 패키지:
  pip install chromadb openai xgboost lightgbm scikit-learn numpy

아키텍처:
  Layer 1: XGBoost/LightGBM (메인 추정) — 로컬, 무료
  Layer 2: LLM Fallback (미지 상품 대응) — GPT-4o, 건당 ~$0.003
  Layer 3: RAG 설명 근거 (ChromaDB 유사 거래 검색 + LLM 요약)
"""

import json
import pickle
import sys
import time
from pathlib import Path

import numpy as np

try:
    import chromadb
    from chromadb.utils import embedding_functions
except ImportError:
    chromadb = None

from dotenv import load_dotenv
from openai import OpenAI

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
MODEL_DIR = DATA_DIR / "models"
CONFIG_DIR = DATA_DIR / "config"
FINAL_DIR = DATA_DIR / "final"
CHROMA_DIR = DATA_DIR / "chroma_db"

ENV_PATH = BASE_DIR.parent / ".env"
load_dotenv(ENV_PATH)

client = OpenAI()

CONDITION_MAP = {"S급": 4, "A급": 3, "B급": 2, "C급": 1, "부품용": 0, "알수없음": -1}
UNKNOWN_VALUES = {"알수없음", "알 수 없음", "미확인", "미상", "없음", "null", "None", "", "추론불가"}

# ChromaDB는 영문만 허용 → 카테고리 매핑
CATEGORY_TO_COLLECTION = {
    "가구/인테리어": "cat-furniture",
    "가전제품": "cat-appliance",
    "기타 중고물품": "cat-etc",
    "남성의류": "cat-menswear",
    "도서": "cat-books",
    "디지털기기": "cat-digital",
    "반려동물용품": "cat-pet",
    "뷰티/미용": "cat-beauty",
    "생활용품": "cat-living",
    "스포츠/레저": "cat-sports",
    "식품": "cat-food",
    "여성의류": "cat-womenswear",
    "출산/유아동": "cat-baby",
    "취미/게임": "cat-hobby",
    "티켓/교환권": "cat-ticket",
    "패션잡화": "cat-fashion-acc",
}
# 역방향 매핑 (파일명 → 카테고리)
FILESTEM_TO_CATEGORY = {
    "가구_인테리어": "가구/인테리어",
    "가전제품": "가전제품",
    "기타 중고물품": "기타 중고물품",
    "남성의류": "남성의류",
    "도서": "도서",
    "디지털기기": "디지털기기",
    "반려동물용품": "반려동물용품",
    "뷰티_미용": "뷰티/미용",
    "생활용품": "생활용품",
    "스포츠_레저": "스포츠/레저",
    "식품": "식품",
    "여성의류": "여성의류",
    "출산_유아동": "출산/유아동",
    "취미_게임": "취미/게임",
    "티켓_교환권": "티켓/교환권",
    "패션잡화": "패션잡화",
}


# ══════════════════════════════════════════════
# Layer 1: 트리 모델 추정
# ══════════════════════════════════════════════
class TreePredictor:
    """카테고리별 학습된 XGBoost/LightGBM 모델로 가격 추정"""

    def __init__(self):
        self.models = {}
        self._load_models()

    def _load_models(self):
        if not MODEL_DIR.exists():
            print("[WARN] models 디렉토리 없음")
            return
        for fp in MODEL_DIR.glob("*_model.pkl"):
            category = fp.stem.replace("_model", "").replace("_", "/")
            with open(fp, "rb") as f:
                self.models[category] = pickle.load(f)
        print(f"[Layer 1] {len(self.models)}개 카테고리 모델 로드됨")

    def predict(self, category: str, features: dict) -> dict | None:
        """
        features: {
            "condition": "A급",
            "usage_period_months": 6,
            "has_box": True,
            "has_accessories": True,
            "has_defects": False,
            "is_negotiable": True,
            "image_count": 5,
            "브랜드": "프라다",
            "모델명": "사피아노",
            ...
            "view_count": 100,
            "wish_count": 5,
            "chat_count": 3,
        }
        """
        if category not in self.models:
            return None

        model_data = self.models[category]
        model = model_data["model"]
        feature_names = model_data["feature_names"]
        encoding_maps = model_data["encoding_maps"]

        # 피처 벡터 구축
        vec = []
        for fname in feature_names:
            if fname == "cf_condition_ord":
                vec.append(CONDITION_MAP.get(features.get("condition", "알수없음"), -1))
            elif fname == "cf_usage_period_months":
                v = features.get("usage_period_months")
                vec.append(v if v is not None else -1)
            elif fname == "cf_has_box":
                v = features.get("has_box")
                vec.append(1 if v is True else (0 if v is False else -1))
            elif fname == "cf_has_accessories":
                v = features.get("has_accessories")
                vec.append(1 if v else 0)
            elif fname == "cf_has_defects":
                v = features.get("has_defects")
                vec.append(1 if v else 0)
            elif fname == "cf_is_negotiable":
                v = features.get("is_negotiable")
                vec.append(1 if v is True else (0 if v is False else -1))
            elif fname == "cf_image_count":
                vec.append(features.get("image_count", 0))
            elif fname.startswith("meta_"):
                key = fname.replace("meta_", "")
                vec.append(features.get(key, 0))
            elif fname.endswith("_te"):
                # Target Encoding된 민감속성
                attr_name = fname.replace("sf_", "").replace("_te", "")
                raw_value = features.get(attr_name, "알수없음")
                enc_info = encoding_maps.get(f"sf_{attr_name}", {})
                enc_map = enc_info.get("map", {})
                global_mean = enc_info.get("global_mean", 0)
                vec.append(enc_map.get(raw_value, global_mean))
            elif fname.endswith("_num"):
                attr_name = fname.replace("sf_", "").replace("_num", "")
                raw_value = features.get(attr_name)
                enc_info = encoding_maps.get(f"sf_{attr_name}", {})
                fill_val = enc_info.get("fill_value", 0)
                try:
                    vec.append(float(raw_value) if raw_value is not None else fill_val)
                except (ValueError, TypeError):
                    vec.append(fill_val)
            else:
                vec.append(-1)

        X = np.array([vec], dtype=np.float32)
        pred_raw = float(model.predict(X)[0])

        # log 변환 모델이면 expm1으로 역변환
        if model_data.get("log_transform", False):
            pred = float(np.expm1(pred_raw))
        else:
            pred = pred_raw
        pred = max(0, pred)

        # 신뢰 구간 (median_pct_error 기반)
        metrics = model_data.get("metrics", {})
        median_pct = metrics.get("median_pct_error", 50) / 100

        price_min = max(0, round(pred * (1 - median_pct) / 1000) * 1000)
        price_max = round(pred * (1 + median_pct) / 1000) * 1000

        # 신뢰도 판단
        known_brands = set()
        for attr_name, enc_info in encoding_maps.items():
            if "map" in enc_info:
                known_brands.update(enc_info["map"].keys())

        brand = features.get("브랜드", "알수없음")
        brand_known = brand in known_brands or brand in UNKNOWN_VALUES

        confidence = "high" if brand_known and median_pct < 0.45 else \
                     "medium" if brand_known else "low"

        return {
            "predicted_price": round(pred),
            "price_range_min": price_min,
            "price_range_max": price_max,
            "confidence": confidence,
            "model_type": model_data.get("model_type", "unknown"),
            "feature_importance": model_data.get("feature_importance", {}),
        }


# ══════════════════════════════════════════════
# Layer 3: RAG — ChromaDB 유사 거래 검색
# ══════════════════════════════════════════════
class RAGRetriever:
    """ChromaDB 기반 유사 거래 데이터 검색"""

    def __init__(self):
        self.chroma_client = None
        self.collections = {}
        self._init_chroma()

    def _init_chroma(self):
        if chromadb is None:
            print("[WARN] chromadb 미설치. pip install chromadb")
            return

        CHROMA_DIR.mkdir(parents=True, exist_ok=True)
        self.chroma_client = chromadb.PersistentClient(path=str(CHROMA_DIR))

        # 기존 컬렉션 로드
        for col in self.chroma_client.list_collections():
            self.collections[col.name] = self.chroma_client.get_collection(col.name)

        if self.collections:
            print(f"[Layer 3] {len(self.collections)}개 카테고리 RAG 인덱스 로드됨")

    def build_index(self):
        """final/ 데이터를 ChromaDB에 인덱싱"""
        if self.chroma_client is None:
            print("[ERROR] ChromaDB 초기화 실패")
            return

        openai_ef = embedding_functions.OpenAIEmbeddingFunction(
            model_name="text-embedding-3-small",
        )

        for filepath in sorted(FINAL_DIR.glob("*.jsonl")):
            filestem = filepath.stem
            category = FILESTEM_TO_CATEGORY.get(filestem, filestem.replace("_", "/"))
            col_name = CATEGORY_TO_COLLECTION.get(category, f"cat-{filestem}")
            print(f"\n[{category}] → 컬렉션: {col_name}")

            items = []
            with open(filepath, "r", encoding="utf-8") as f:
                for line in f:
                    if line.strip():
                        items.append(json.loads(line))

            if not items:
                continue

            # 기존 컬렉션 삭제 후 재생성
            try:
                self.chroma_client.delete_collection(col_name)
            except Exception:
                pass

            collection = self.chroma_client.create_collection(
                name=col_name,
                embedding_function=openai_ef,
                metadata={"category": category}
            )

            # 배치 인덱싱 (ChromaDB 제한: 한 번에 ~5000건)
            batch_size = 500
            for i in range(0, len(items), batch_size):
                batch = items[i:i + batch_size]

                ids = []
                documents = []
                metadatas = []

                for j, item in enumerate(batch):
                    seq = str(item.get("seq", "unk"))
                    unique_id = f"{seq}_{i+j}"
                    ids.append(unique_id)

                    # 검색 문서: 제목 + 주요 속성 조합
                    common = item.get("common_attributes", {}) or {}
                    sensitive = item.get("sensitive_attributes", {}) or {}
                    title = item.get("title", "")
                    brand = sensitive.get("브랜드", "")
                    condition = common.get("condition", "")
                    price = item.get("price", 0)

                    doc_text = f"{title} {brand} {condition} {price}원"
                    for k, v in sensitive.items():
                        if v and v not in UNKNOWN_VALUES:
                            doc_text += f" {v}"
                    documents.append(doc_text)

                    # 메타데이터에 가격과 주요 속성 저장
                    meta = {
                        "price": int(price),
                        "condition": str(condition),
                        "brand": str(brand),
                        "title": str(title)[:200],
                    }
                    metadatas.append(meta)

                collection.add(ids=ids, documents=documents, metadatas=metadatas)

            self.collections[col_name] = collection
            print(f"  → {len(items)}건 인덱싱 완료")

        print(f"\n총 {len(self.collections)}개 카테고리 인덱스 빌드 완료")
        print(f"저장 위치: {CHROMA_DIR}")

    def search_similar(self, category: str, query: str, n_results: int = 5) -> list[dict]:
        """유사 거래 데이터 검색"""
        col_name = CATEGORY_TO_COLLECTION.get(category, f"cat-{category.replace('/', '_')}")
        collection = self.collections.get(col_name)

        if collection is None:
            return []

        try:
            results = collection.query(query_texts=[query], n_results=n_results)
        except Exception as e:
            print(f"[RAG ERROR] {e}")
            return []

        similar = []
        if results and results["metadatas"]:
            for meta, distance in zip(results["metadatas"][0], results["distances"][0]):
                similar.append({
                    "title": meta.get("title", ""),
                    "price": meta.get("price", 0),
                    "condition": meta.get("condition", ""),
                    "brand": meta.get("brand", ""),
                    "similarity": round(1 - distance, 3),
                })

        return similar


# ══════════════════════════════════════════════
# Layer 2: LLM Fallback
# ══════════════════════════════════════════════
class LLMFallback:
    """학습 데이터에 없는 상품 대응 — GPT-4o 기반 가격 추정"""

    def __init__(self, rag: RAGRetriever):
        self.rag = rag

    def estimate(self, category: str, features: dict) -> dict:
        # RAG로 유사 거래 검색 (컨텍스트로 제공)
        query = self._build_query(features)
        similar = self.rag.search_similar(category, query, n_results=10)

        # 가격 통계 로드
        price_stats = self._load_price_stats(category)

        prompt = self._build_prompt(category, features, similar, price_stats)

        try:
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "당신은 중고 상품 가격 추정 전문가입니다. JSON으로만 응답하세요."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=500,
                response_format={"type": "json_object"}
            )
            result = json.loads(response.choices[0].message.content)
            return {
                "predicted_price": result.get("predicted_price", 0),
                "price_range_min": result.get("price_range_min", 0),
                "price_range_max": result.get("price_range_max", 0),
                "confidence": "medium",
                "model_type": "llm_fallback",
                "reasoning": result.get("reasoning", ""),
            }
        except Exception as e:
            print(f"[LLM ERROR] {e}")
            return None

    def _build_query(self, features: dict) -> str:
        parts = []
        for key in ["브랜드", "모델명", "종류", "condition"]:
            v = features.get(key, "")
            if v and v not in UNKNOWN_VALUES:
                parts.append(str(v))
        return " ".join(parts) if parts else "중고 상품"

    def _load_price_stats(self, category: str) -> dict:
        path = CONFIG_DIR / "price_analysis.json"
        if path.exists():
            with open(path, "r", encoding="utf-8") as f:
                all_stats = json.load(f)
            return all_stats.get(category, {})
        return {}

    def _build_prompt(self, category: str, features: dict,
                      similar: list, price_stats: dict) -> str:
        similar_text = ""
        if similar:
            lines = []
            for s in similar[:5]:
                lines.append(f"  - {s['title']} / {s['condition']} / {s['price']:,}원")
            similar_text = "유사 실거래:\n" + "\n".join(lines)

        stats_text = ""
        if price_stats.get("price_distribution"):
            pd = price_stats["price_distribution"]
            stats_text = f"카테고리 가격 분포: p25={pd.get('p25', 0):,}원, 중앙값={pd.get('median', 0):,}원, p75={pd.get('p75', 0):,}원"

        features_text = json.dumps(features, ensure_ascii=False, indent=2)

        return f"""아래 중고 상품의 적정 가격을 추정해주세요.

카테고리: {category}

상품 속성:
{features_text}

{similar_text}

{stats_text}

JSON으로만 응답하세요:
{{
  "predicted_price": 추정가격(원),
  "price_range_min": 최저가(원),
  "price_range_max": 최고가(원),
  "reasoning": "추정 근거 (한국어, 2~3문장)"
}}"""


# ══════════════════════════════════════════════
# Layer 3: 설명 근거 생성
# ══════════════════════════════════════════════
class ExplanationGenerator:
    """가격 추정 근거 설명 생성"""

    def __init__(self, rag: RAGRetriever):
        self.rag = rag

    def generate(self, category: str, features: dict,
                 prediction: dict, similar_override: list[dict] = None) -> dict:
        """RAG 유사 거래 + 피처 중요도 기반 설명 생성"""
        # 유사 거래: 이미 필터링된 것이 있으면 사용
        if similar_override is not None:
            similar = similar_override
        else:
            query = self._build_query(features)
            similar = self.rag.search_similar(category, query, n_results=5)

        # 피처 중요도 해석
        importance = prediction.get("feature_importance", {})
        top_features = sorted(importance.items(), key=lambda x: x[1], reverse=True)[:5]

        # 피처명 한국어 매핑
        feature_kr = {
            "cf_condition_ord": "상태등급", "cf_usage_period_months": "사용기간",
            "cf_has_box": "정품박스", "cf_has_accessories": "부속품",
            "cf_has_defects": "하자유무", "cf_is_negotiable": "네고가능",
            "cf_image_count": "사진수", "meta_view_count": "조회수",
            "meta_wish_count": "찜수", "meta_chat_count": "채팅수",
        }

        # LLM 요약 생성
        explanation = self._generate_summary(
            category, features, prediction, similar, top_features, feature_kr
        )

        return {
            "summary": explanation,
            "similar_trades": similar,
            "top_factors": [
                {"factor": feature_kr.get(f, f.replace("sf_", "").replace("_te", "")),
                 "weight": round(w, 4)}
                for f, w in top_features
            ],
        }

    def _build_query(self, features: dict) -> str:
        parts = []
        for key in ["브랜드", "모델명", "종류", "condition"]:
            v = features.get(key, "")
            if v and v not in UNKNOWN_VALUES:
                parts.append(str(v))
        return " ".join(parts) if parts else "중고 상품"

    def _generate_summary(self, category, features, prediction,
                          similar, top_features, feature_kr) -> str:
        pred_price = prediction.get("predicted_price", 0)
        price_min = prediction.get("price_range_min", 0)
        price_max = prediction.get("price_range_max", 0)

        similar_text = ""
        if similar:
            prices = [s["price"] for s in similar if s["price"] > 0]
            if prices:
                avg_price = int(np.mean(prices))
                similar_text = f"유사 상품 {len(prices)}건의 평균 거래가는 {avg_price:,}원입니다."

        factors = []
        total_weight = sum(w for _, w in top_features) if top_features else 1
        for f, w in top_features[:3]:
            name = feature_kr.get(f, f.replace("sf_", "").replace("_te", ""))
            pct = round(w / total_weight * 100)
            factors.append(f"{name}({pct}%)")

        factor_text = f"가격에 가장 큰 영향을 준 요소: {', '.join(factors)}" if factors else ""

        condition = features.get("condition", "")
        brand = features.get("브랜드", "")

        summary = f"적정 가격: {pred_price:,}원 (범위: {price_min:,}원 ~ {price_max:,}원)\n"
        if similar_text:
            summary += f"{similar_text}\n"
        if brand and brand not in UNKNOWN_VALUES:
            summary += f"{brand} 브랜드 {condition} 상품 기준입니다.\n"
        if factor_text:
            summary += factor_text
        return summary.strip()


# ══════════════════════════════════════════════
# 통합 추론 엔진
# ══════════════════════════════════════════════
class PriceEstimator:
    """3-Layer 가격 추정 통합 엔진"""

    def __init__(self):
        print("가격 추정 엔진 초기화 중...")
        self.tree = TreePredictor()
        self.rag = RAGRetriever()
        self.fallback = LLMFallback(self.rag)
        self.explainer = ExplanationGenerator(self.rag)
        print("초기화 완료\n")

    def estimate(self, category: str, features: dict,
                 with_explanation: bool = True) -> dict:
        """
        가격 추정 메인 함수.
        모델 예측 + RAG 유사거래 가중 평균으로 최종 가격 산출.
        """
        result = {}

        # Layer 1: 트리 모델 시도
        tree_result = self.tree.predict(category, features)

        if tree_result and tree_result["confidence"] != "low":
            result = tree_result
        else:
            # Layer 2: LLM Fallback
            print(f"  [Fallback] 트리 모델 신뢰도 낮음 → LLM 추정")
            llm_result = self.fallback.estimate(category, features)
            if llm_result:
                result = llm_result
            elif tree_result:
                result = tree_result
            else:
                return {"error": "가격 추정 실패", "category": category}

        # ── RAG 보정: 유사거래 검색 + 이상치 필터링 + 가중 평균 ──
        query = self._build_rag_query(features)
        similar_raw = self.rag.search_similar(category, query, n_results=10)

        model_price = result.get("predicted_price", 0)
        similar_filtered = self._filter_similar(similar_raw, model_price)
        rag_adjusted = self._rag_adjust(result, similar_filtered)
        result.update(rag_adjusted)

        # Layer 3: 설명 근거
        if with_explanation:
            explanation = self.explainer.generate(
                category, features, result,
                similar_override=similar_filtered
            )
            result["explanation"] = explanation

        return result

    def _build_rag_query(self, features: dict) -> str:
        parts = []
        # 모델명을 먼저 넣어서 부속품보다 본품이 매칭되도록
        for key in ["모델명", "브랜드", "종류", "condition"]:
            v = features.get(key, "")
            if v and v not in UNKNOWN_VALUES:
                parts.append(str(v))
        # 소재, 색상 등 추가 속성도 포함하여 검색 정밀도 향상
        for key in ["소재", "색상"]:
            v = features.get(key, "")
            if v and v not in UNKNOWN_VALUES:
                parts.append(str(v))
        return " ".join(parts) if parts else "중고 상품"

    def _filter_similar(self, similar: list[dict], model_price: float) -> list[dict]:
        """
        유사거래 필터링 (2단계):
        1단계: 가격 0 제거 + IQR 기반 이상치 제거
        2단계: 유사거래 중앙값과 모델 예측의 중간 기준점에서 너무 먼 것 제거
        """
        if not similar:
            return []

        # 가격 0 제외
        with_price = [s for s in similar if s.get("price", 0) > 0]
        if len(with_price) < 2:
            return with_price

        prices = sorted([s["price"] for s in with_price])

        # 1단계: IQR 필터
        q1 = np.percentile(prices, 25)
        q3 = np.percentile(prices, 75)
        iqr = q3 - q1

        if iqr > 0:
            lower = q1 - 1.5 * iqr
            upper = q3 + 1.5 * iqr
            step1 = [s for s in with_price if lower <= s["price"] <= upper]
        else:
            step1 = with_price

        if len(step1) < 2:
            step1 = with_price

        # 2단계: 중앙값 기준 ±3배 범위 필터
        # 모델 예측값과 유사거래 중앙값의 중간을 기준점으로 사용
        step1_prices = [s["price"] for s in step1]
        rag_median = np.median(step1_prices)

        if model_price > 0:
            reference = (model_price + rag_median) / 2
        else:
            reference = rag_median

        # 기준점의 1/4 ~ 4배 범위만 유지
        range_low = reference / 4
        range_high = reference * 4
        step2 = [s for s in step1 if range_low <= s["price"] <= range_high]

        if len(step2) < 2:
            step2 = step1

        return step2

    def _rag_adjust(self, result: dict, similar: list[dict]) -> dict:
        """
        모델 예측과 RAG 유사거래 가격을 가중 평균.
        유사거래가 3건 이상이면 RAG에 더 높은 가중치.
        """
        model_price = result.get("predicted_price", 0)
        if not similar or model_price <= 0:
            return {}

        rag_prices = [s["price"] for s in similar if s["price"] > 0]
        if not rag_prices:
            return {}

        rag_median = float(np.median(rag_prices))

        # 가중치: 유사거래가 많고 유사도가 높을수록 RAG 비중 증가
        n = len(rag_prices)
        if n >= 5:
            model_weight, rag_weight = 0.3, 0.7
        elif n >= 3:
            model_weight, rag_weight = 0.4, 0.6
        else:
            model_weight, rag_weight = 0.6, 0.4

        adjusted_price = model_price * model_weight + rag_median * rag_weight
        adjusted_price = max(0, round(adjusted_price))

        # 가격 범위도 재조정
        median_pct = result.get("confidence", "medium")
        pct = 0.3 if median_pct == "high" else 0.4
        price_min = max(0, round(adjusted_price * (1 - pct) / 1000) * 1000)
        price_max = round(adjusted_price * (1 + pct) / 1000) * 1000

        return {
            "predicted_price": adjusted_price,
            "price_range_min": price_min,
            "price_range_max": price_max,
            "model_raw_price": model_price,
            "rag_median_price": round(rag_median),
            "blend_weights": {"model": model_weight, "rag": rag_weight},
            "rag_sample_count": n,
        }


# ──────────────────────────────────────────────
# 메인 (CLI)
# ──────────────────────────────────────────────
def main():
    if "--build-index" in sys.argv:
        print("=" * 60)
        print("RAG 인덱스 빌드 (ChromaDB)")
        print("=" * 60)
        rag = RAGRetriever()
        rag.build_index()
        return

    if "--test" in sys.argv:
        print("=" * 60)
        print("가격 추정 테스트")
        print("=" * 60)

        engine = PriceEstimator()

        # 테스트 케이스들 (16개 카테고리)
        test_cases = [
            {
                "category": "디지털기기",
                "features": {
                    "condition": "A급", "usage_period_months": 12,
                    "has_box": True, "has_accessories": True, "has_defects": False,
                    "is_negotiable": True, "image_count": 5,
                    "브랜드": "애플", "모델명": "아이폰 15 프로",
                    "저장용량": "256GB", "색상": "블랙",
                    "view_count": 50, "wish_count": 3, "chat_count": 2,
                }
            },
            {
                "category": "패션잡화",
                "features": {
                    "condition": "S급", "usage_period_months": 0,
                    "has_box": True, "has_accessories": True, "has_defects": False,
                    "is_negotiable": False, "image_count": 8,
                    "브랜드": "루이비통", "모델명": "네버풀",
                    "소재": "모노그램 캔버스", "종류": "토트백", "색상": "브라운",
                    "view_count": 200, "wish_count": 15, "chat_count": 8,
                }
            },
            {
                "category": "가전제품",
                "features": {
                    "condition": "B급", "usage_period_months": 36,
                    "has_box": False, "has_accessories": False, "has_defects": False,
                    "is_negotiable": True, "image_count": 3,
                    "브랜드": "삼성", "모델명": "비스포크 냉장고",
                    "용량_리터": "870L", "도어타입": "4도어",
                    "view_count": 80, "wish_count": 5, "chat_count": 3,
                }
            },
            {
                "category": "가구/인테리어",
                "features": {
                    "condition": "A급", "usage_period_months": 24,
                    "has_box": False, "has_accessories": False, "has_defects": False,
                    "is_negotiable": True, "image_count": 4,
                    "브랜드": "이케아", "종류": "책상", "소재": "원목",
                    "색상": "화이트", "용도": "사무용",
                    "view_count": 120, "wish_count": 8, "chat_count": 5,
                }
            },
            {
                "category": "남성의류",
                "features": {
                    "condition": "A급", "usage_period_months": 6,
                    "has_box": False, "has_accessories": False, "has_defects": False,
                    "is_negotiable": True, "image_count": 4,
                    "브랜드": "폴로 랄프로렌", "사이즈": "L",
                    "시즌": "겨울", "소재": "울", "색상": "네이비",
                    "view_count": 60, "wish_count": 4, "chat_count": 2,
                }
            },
            {
                "category": "여성의류",
                "features": {
                    "condition": "S급", "usage_period_months": 1,
                    "has_box": True, "has_accessories": True, "has_defects": False,
                    "is_negotiable": False, "image_count": 6,
                    "브랜드": "막스마라", "사이즈": "S",
                    "시즌": "겨울", "소재": "캐시미어", "색상": "베이지", "기장": "롱",
                    "view_count": 300, "wish_count": 25, "chat_count": 10,
                }
            },
            {
                "category": "스포츠/레저",
                "features": {
                    "condition": "A급", "usage_period_months": 12,
                    "has_box": True, "has_accessories": True, "has_defects": False,
                    "is_negotiable": True, "image_count": 6,
                    "브랜드": "타이틀리스트", "모델명": "T200 아이언세트",
                    "종류": "골프채", "세트구성": "5-PW 6개",
                    "view_count": 150, "wish_count": 10, "chat_count": 6,
                }
            },
            {
                "category": "출산/유아동",
                "features": {
                    "condition": "A급", "usage_period_months": 18,
                    "has_box": True, "has_accessories": True, "has_defects": False,
                    "is_negotiable": True, "image_count": 5,
                    "브랜드": "부가부", "모델명": "폭스5",
                    "종류": "유모차",
                    "view_count": 200, "wish_count": 15, "chat_count": 8,
                }
            },
            {
                "category": "취미/게임",
                "features": {
                    "condition": "A급", "usage_period_months": 6,
                    "has_box": True, "has_accessories": True, "has_defects": False,
                    "is_negotiable": True, "image_count": 4,
                    "모델명": "닌텐도 스위치 OLED",
                    "동봉게임수": 2,
                    "view_count": 100, "wish_count": 8, "chat_count": 4,
                }
            },
            {
                "category": "뷰티/미용",
                "features": {
                    "condition": "A급", "usage_period_months": 3,
                    "has_box": True, "has_accessories": False, "has_defects": False,
                    "is_negotiable": True, "image_count": 3,
                    "브랜드": "다이슨", "모델명": "에어랩 컴플리트",
                    "종류": "드라이기",
                    "view_count": 180, "wish_count": 20, "chat_count": 12,
                }
            },
            {
                "category": "반려동물용품",
                "features": {
                    "condition": "A급", "usage_period_months": 6,
                    "has_box": False, "has_accessories": False, "has_defects": False,
                    "is_negotiable": True, "image_count": 3,
                    "브랜드": "캣츠태그", "종류": "캣타워",
                    "크기": "대형", "소재": "원목",
                    "view_count": 80, "wish_count": 5, "chat_count": 3,
                }
            },
            {
                "category": "생활용품",
                "features": {
                    "condition": "A급", "usage_period_months": 12,
                    "has_box": True, "has_accessories": False, "has_defects": False,
                    "is_negotiable": True, "image_count": 4,
                    "브랜드": "한샘", "종류": "수납장",
                    "크기": "3단", "소재": "MDF", "색상": "화이트",
                    "view_count": 60, "wish_count": 3, "chat_count": 2,
                }
            },
            {
                "category": "도서",
                "features": {
                    "condition": "B급", "usage_period_months": 12,
                    "has_box": False, "has_accessories": False, "has_defects": False,
                    "is_negotiable": True, "image_count": 2,
                    "종류": "수험서", "과목구성": "전과목 세트",
                    "세트구성": "10권 세트", "필기여부": "약간 필기",
                    "view_count": 40, "wish_count": 2, "chat_count": 1,
                }
            },
            {
                "category": "식품",
                "features": {
                    "condition": "S급", "usage_period_months": 0,
                    "has_box": True, "has_accessories": False, "has_defects": False,
                    "is_negotiable": False, "image_count": 3,
                    "브랜드": "정관장", "제품명": "홍삼정 에브리타임",
                    "용량": "10ml x 30포",
                    "view_count": 50, "wish_count": 3, "chat_count": 1,
                }
            },
            {
                "category": "티켓/교환권",
                "features": {
                    "condition": "S급", "usage_period_months": 0,
                    "has_box": False, "has_accessories": False, "has_defects": False,
                    "is_negotiable": True, "image_count": 1,
                    "종류": "상품권", "사용처": "신세계백화점",
                    "권종금액": 50000, "매수": 5,
                    "view_count": 30, "wish_count": 2, "chat_count": 1,
                }
            },
            {
                "category": "기타 중고물품",
                "features": {
                    "condition": "A급", "usage_period_months": 12,
                    "has_box": True, "has_accessories": True, "has_defects": False,
                    "is_negotiable": True, "image_count": 5,
                    "브랜드": "스노우피크", "종류": "텐트",
                    "view_count": 100, "wish_count": 8, "chat_count": 5,
                }
            },
        ]

        all_results = []
        for tc in test_cases:
            print(f"\n{'='*50}")
            print(f"[테스트] {tc['category']} — {tc['features'].get('브랜드', '')} {tc['features'].get('모델명', '')}")
            print(f"{'='*50}")

            result = engine.estimate(tc["category"], tc["features"])

            if "error" in result:
                print(f"  ❌ {result['error']}")
                continue

            print(f"  추정 가격: {result['predicted_price']:,}원")
            print(f"  가격 범위: {result['price_range_min']:,}원 ~ {result['price_range_max']:,}원")
            print(f"  신뢰도: {result['confidence']}")
            print(f"  모델: {result['model_type']}")

            # RAG 보정 정보
            if "model_raw_price" in result:
                print(f"\n  [RAG 보정]")
                print(f"  모델 원래 추정: {result['model_raw_price']:,}원")
                print(f"  RAG 유사거래 중앙값: {result['rag_median_price']:,}원 ({result['rag_sample_count']}건)")
                w = result['blend_weights']
                print(f"  가중 평균: 모델 {w['model']:.0%} + RAG {w['rag']:.0%} → {result['predicted_price']:,}원")

            if "explanation" in result:
                exp = result["explanation"]
                print(f"\n  [설명]")
                print(f"  {exp['summary']}")
                if exp.get("similar_trades"):
                    print(f"\n  [유사 거래]")
                    for s in exp["similar_trades"][:3]:
                        print(f"    - {s['title'][:30]}... / {s['condition']} / {s['price']:,}원")
                if exp.get("top_factors"):
                    print(f"\n  [가격 영향 요소]")
                    for tf in exp["top_factors"][:3]:
                        print(f"    - {tf['factor']}: {tf['weight']:.4f}")

            all_results.append({
                "category": tc["category"],
                "product": f"{tc['features'].get('브랜드', '')} {tc['features'].get('모델명', tc['features'].get('종류', ''))}".strip(),
                "condition": tc["features"].get("condition", ""),
                "model_price": result.get("model_raw_price", result.get("predicted_price", 0)),
                "rag_median": result.get("rag_median_price", 0),
                "final_price": result.get("predicted_price", 0),
                "price_min": result.get("price_range_min", 0),
                "price_max": result.get("price_range_max", 0),
                "rag_count": result.get("rag_sample_count", 0),
                "confidence": result.get("confidence", ""),
            })

        # ── 전체 요약 테이블 ──
        print(f"\n\n{'='*100}")
        print("전체 카테고리 테스트 요약")
        print(f"{'='*100}")
        print(f"{'카테고리':<14} {'상품':<20} {'상태':>4} {'모델추정':>10} {'RAG중앙':>10} {'최종가격':>10} {'범위':>22} {'RAG':>4} {'신뢰':>6}")
        print("-" * 100)
        for r in all_results:
            product = r['product'][:18]
            rng = f"{r['price_min']:,}~{r['price_max']:,}"
            print(f"{r['category']:<14} {product:<20} {r['condition']:>4} "
                  f"{r['model_price']:>9,}원 {r['rag_median']:>9,}원 {r['final_price']:>9,}원 "
                  f"{rng:>22} {r['rag_count']:>3}건 {r['confidence']:>6}")

        return

    print("사용법:")
    print("  python -m crawler.pipeline.step3c_inference --build-index   # RAG 인덱스 빌드")
    print("  python -m crawler.pipeline.step3c_inference --test          # 테스트 추론")


if __name__ == "__main__":
    main()