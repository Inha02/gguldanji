"""
Step 1-A: 중복 제거 (OpenAI Embedding 기반)
============================================
위치: gguldanji/ai-engine/crawler/pipeline/step1a_dedup.py

실행 방법:
  cd gguldanji/ai-engine
  python -m crawler.pipeline.step1a_dedup

필요 패키지:
  pip install openai numpy tqdm

환경변수:
  export OPENAI_API_KEY="sk-..."

설명:
  1) 같은 seq(게시글 ID) 중복 제거
  2) 같은 판매자(storeSeq)의 동일 제목 게시글 → 최신만 유지
  3) 제목+설명 텍스트 임베딩으로 코사인 유사도 0.92 이상이면 중복 → 최신 유지
  4) 결과를 /data/processed/{keyword}/{keyword}_deduped.jsonl 로 저장
"""

import json
import os
import sys
import time
import hashlib
from pathlib import Path
from collections import defaultdict

import numpy as np
from dotenv import load_dotenv
from openai import OpenAI
from tqdm import tqdm

# ──────────────────────────────────────────────
# 설정
# ──────────────────────────────────────────────
EMBEDDING_MODEL = "text-embedding-3-small"  # 비용 효율적
SIMILARITY_THRESHOLD = 0.92
BATCH_SIZE = 100  # OpenAI embedding 배치 크기 (최대 2048)

# 경로 설정 (프로젝트 루트 기준)
BASE_DIR = Path(__file__).resolve().parent.parent  # crawler/
DATA_DIR = BASE_DIR / "data"
PROCESSED_DIR = DATA_DIR / "processed"

# .env 파일에서 API 키 로드 (ai-engine/.env)
ENV_PATH = BASE_DIR.parent / ".env"  # ai-engine/.env
load_dotenv(ENV_PATH)

client = OpenAI()  # .env에서 OPENAI_API_KEY 자동 로드


# ──────────────────────────────────────────────
# 유틸리티 함수
# ──────────────────────────────────────────────
def load_candidates(keyword: str) -> list[dict]:
    """키워드별 candidates.jsonl 로드"""
    filepath = PROCESSED_DIR / keyword / f"{keyword}_candidates.jsonl"
    if not filepath.exists():
        print(f"  [SKIP] 파일 없음: {filepath}")
        return []
    
    items = []
    with open(filepath, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    items.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
    return items


def extract_text_for_embedding(item: dict) -> str:
    """임베딩용 텍스트 추출 (제목 + 설명 앞 200자)"""
    title = item.get("title", "")
    desc = ""
    detail = item.get("detail", {})
    if detail:
        desc = detail.get("productDescription", "")
    # 설명이 너무 길면 앞부분만
    desc = desc[:200] if desc else ""
    return f"{title} {desc}".strip()


def get_embeddings(texts: list[str]) -> list[list[float]]:
    """OpenAI Embedding API 호출 (배치 처리)"""
    all_embeddings = []
    
    for i in range(0, len(texts), BATCH_SIZE):
        batch = texts[i:i + BATCH_SIZE]
        # 빈 텍스트 처리
        batch = [t if t.strip() else "empty" for t in batch]
        
        try:
            response = client.embeddings.create(
                model=EMBEDDING_MODEL,
                input=batch
            )
            batch_embeddings = [item.embedding for item in response.data]
            all_embeddings.extend(batch_embeddings)
        except Exception as e:
            print(f"  [ERROR] Embedding API 오류: {e}")
            # 실패 시 재시도 (1회)
            time.sleep(2)
            try:
                response = client.embeddings.create(
                    model=EMBEDDING_MODEL,
                    input=batch
                )
                batch_embeddings = [item.embedding for item in response.data]
                all_embeddings.extend(batch_embeddings)
            except Exception as e2:
                print(f"  [FATAL] 재시도 실패: {e2}")
                # 제로 벡터로 채움 (중복 판정 안 됨)
                all_embeddings.extend([[0.0] * 1536] * len(batch))
        
        if i + BATCH_SIZE < len(texts):
            time.sleep(0.5)  # Rate limit 대비
    
    return all_embeddings


def cosine_similarity_matrix(embeddings: np.ndarray) -> np.ndarray:
    """코사인 유사도 행렬 계산"""
    # 정규화
    norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
    norms[norms == 0] = 1  # 0벡터 방지
    normalized = embeddings / norms
    return np.dot(normalized, normalized.T)


# ──────────────────────────────────────────────
# Phase 1: 정확 중복 제거 (seq 기반 + 같은 판매자 같은 제목)
# ──────────────────────────────────────────────
def remove_exact_duplicates(items: list[dict]) -> list[dict]:
    """
    1) 같은 seq → 최신만 유지
    2) 같은 storeSeq + 같은 제목 → 최신만 유지 (가격 변경 재게시)
    """
    # seq 기준 중복 제거
    seen_seq = {}
    for item in items:
        seq = item.get("seq")
        if seq not in seen_seq:
            seen_seq[seq] = item
        else:
            # 더 최신 것만 유지
            existing_date = seen_seq[seq].get("sortDate", "")
            new_date = item.get("sortDate", "")
            if new_date > existing_date:
                seen_seq[seq] = item
    
    items = list(seen_seq.values())
    
    # 같은 판매자 + 같은 제목 → 최신만 유지
    seller_title_map = defaultdict(list)
    for item in items:
        store_seq = item.get("detail", {}).get("storeSeq", "unknown")
        title = item.get("title", "").strip()
        key = f"{store_seq}_{title}"
        seller_title_map[key].append(item)
    
    deduped = []
    for key, group in seller_title_map.items():
        if len(group) == 1:
            deduped.append(group[0])
        else:
            # 최신 글만 유지
            group.sort(key=lambda x: x.get("sortDate", ""), reverse=True)
            deduped.append(group[0])
    
    return deduped


# ──────────────────────────────────────────────
# Phase 2: 임베딩 유사도 기반 중복 제거
# ──────────────────────────────────────────────
def remove_similar_duplicates(items: list[dict]) -> list[dict]:
    """임베딩 코사인 유사도 기반 유사 중복 제거"""
    if len(items) <= 1:
        return items
    
    # 텍스트 추출
    texts = [extract_text_for_embedding(item) for item in items]
    
    print(f"  임베딩 생성 중... ({len(texts)}건)")
    embeddings = get_embeddings(texts)
    embeddings_np = np.array(embeddings)
    
    print(f"  유사도 계산 중...")
    sim_matrix = cosine_similarity_matrix(embeddings_np)
    
    # 중복 그룹 찾기 (Union-Find 대신 단순 그리디)
    n = len(items)
    is_duplicate = [False] * n
    duplicate_pairs = 0
    
    for i in range(n):
        if is_duplicate[i]:
            continue
        for j in range(i + 1, n):
            if is_duplicate[j]:
                continue
            if sim_matrix[i][j] >= SIMILARITY_THRESHOLD:
                # 같은 판매자인 경우만 중복 처리 (다른 판매자는 비슷해도 다른 물건)
                store_i = items[i].get("detail", {}).get("storeSeq", -1)
                store_j = items[j].get("detail", {}).get("storeSeq", -2)
                
                if store_i == store_j:
                    # 최신 것을 살리고 오래된 것을 제거
                    date_i = items[i].get("sortDate", "")
                    date_j = items[j].get("sortDate", "")
                    if date_i >= date_j:
                        is_duplicate[j] = True
                    else:
                        is_duplicate[i] = True
                        break  # i가 제거되었으므로 i 루프 종료
                    duplicate_pairs += 1
                # 다른 판매자 + 유사도 0.95 이상이면 업자의 동일 템플릿 게시글
                elif sim_matrix[i][j] >= 0.95:
                    date_i = items[i].get("sortDate", "")
                    date_j = items[j].get("sortDate", "")
                    if date_i >= date_j:
                        is_duplicate[j] = True
                    else:
                        is_duplicate[i] = True
                        break
                    duplicate_pairs += 1
    
    result = [item for item, dup in zip(items, is_duplicate) if not dup]
    print(f"  임베딩 중복 제거: {duplicate_pairs}쌍 발견, {n} → {len(result)}건")
    return result


# ──────────────────────────────────────────────
# 메인 처리
# ──────────────────────────────────────────────
def process_keyword(keyword: str) -> dict:
    """키워드 하나에 대한 중복 제거 파이프라인"""
    print(f"\n{'='*50}")
    print(f"[{keyword}] 처리 시작")
    print(f"{'='*50}")
    
    # 로드
    items = load_candidates(keyword)
    if not items:
        return {"keyword": keyword, "original": 0, "after_exact": 0, "after_embedding": 0}
    
    original_count = len(items)
    print(f"  원본: {original_count}건")
    
    # Phase 1: 정확 중복 제거
    items = remove_exact_duplicates(items)
    after_exact = len(items)
    print(f"  정확 중복 제거 후: {after_exact}건 (제거: {original_count - after_exact}건)")
    
    # Phase 2: 임베딩 유사도 중복 제거
    items = remove_similar_duplicates(items)
    after_embedding = len(items)
    
    # 저장
    output_dir = PROCESSED_DIR / keyword
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f"{keyword}_deduped.jsonl"
    
    with open(output_path, "w", encoding="utf-8") as f:
        for item in items:
            f.write(json.dumps(item, ensure_ascii=False) + "\n")
    
    print(f"  최종: {after_embedding}건 → {output_path}")
    
    return {
        "keyword": keyword,
        "original": original_count,
        "after_exact": after_exact,
        "after_embedding": after_embedding
    }


def get_all_keywords() -> list[str]:
    """processed 폴더에서 모든 키워드 목록 추출"""
    keywords = []
    if not PROCESSED_DIR.exists():
        print(f"[ERROR] processed 디렉토리 없음: {PROCESSED_DIR}")
        return keywords
    
    for subdir in sorted(PROCESSED_DIR.iterdir()):
        if subdir.is_dir():
            # _candidates.jsonl 파일이 있는지 확인
            candidates_file = subdir / f"{subdir.name}_candidates.jsonl"
            if candidates_file.exists():
                keywords.append(subdir.name)
    
    return keywords


def main():
    print("=" * 60)
    print("Step 1-A: 중복 제거 (OpenAI Embedding 기반)")
    print("=" * 60)
    
    # 특정 키워드만 처리하려면 인자로 전달
    if len(sys.argv) > 1:
        keywords = sys.argv[1:]
    else:
        keywords = get_all_keywords()
    
    if not keywords:
        print("[ERROR] 처리할 키워드가 없습니다.")
        print(f"  확인 경로: {PROCESSED_DIR}")
        return
    
    print(f"\n처리 대상 키워드 ({len(keywords)}개): {keywords}")
    
    results = []
    for keyword in keywords:
        result = process_keyword(keyword)
        results.append(result)
    
    # 요약 리포트
    print("\n" + "=" * 60)
    print("중복 제거 요약 리포트")
    print("=" * 60)
    print(f"{'키워드':<15} {'원본':>6} {'정확중복제거':>10} {'임베딩중복제거':>12} {'제거율':>8}")
    print("-" * 60)
    
    total_orig = 0
    total_final = 0
    for r in results:
        orig = r["original"]
        final = r["after_embedding"]
        total_orig += orig
        total_final += final
        rate = f"{(1 - final/orig)*100:.1f}%" if orig > 0 else "N/A"
        print(f"{r['keyword']:<15} {orig:>6} {r['after_exact']:>10} {final:>12} {rate:>8}")
    
    total_rate = f"{(1 - total_final/total_orig)*100:.1f}%" if total_orig > 0 else "N/A"
    print("-" * 60)
    print(f"{'합계':<15} {total_orig:>6} {'':>10} {total_final:>12} {total_rate:>8}")
    
    # 리포트 저장
    report_path = DATA_DIR / "dedup_report.json"
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"\n리포트 저장: {report_path}")


if __name__ == "__main__":
    main()