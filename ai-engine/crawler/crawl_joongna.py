import os
import re
import time
import json
import random
import argparse
from urllib.parse import quote
from typing import Any, Dict, List, Optional, Set, Tuple

import requests
from tqdm import tqdm


# -----------------------------
# Config
# -----------------------------
BASE_WEB = "https://web.joongna.com"
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36"

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
RAW_DIR = os.path.join(DATA_DIR, "raw")
PROCESSED_DIR = os.path.join(DATA_DIR, "processed")

os.makedirs(RAW_DIR, exist_ok=True)
os.makedirs(PROCESSED_DIR, exist_ok=True)


# -----------------------------
# Utils
# -----------------------------
def jdump(path: str, obj: Any) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)


def jwrite_jsonl(path: str, rows: List[Dict[str, Any]]) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")


def write_lines(path: str, lines: List[str]) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        for line in lines:
            f.write(line.rstrip("\n") + "\n")


def sleep_jitter(base: float = 0.35, jitter: float = 0.35) -> None:
    time.sleep(base + random.random() * jitter)


def safe_filename(s: str) -> str:
    return re.sub(r"[\\/:*?\"<>| ]+", "_", s).strip("_")


def safe_dirname(s: str) -> str:
    # 폴더명으로 쓰기 좋게: 위험문자 + 공백 정리
    return re.sub(r"[\\/:*?\"<>|]+", "_", s).strip().strip("_")


def read_anchors(path: str) -> List[str]:
    anchors: List[str] = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            s = line.strip()
            if not s:
                continue
            if s.startswith("#"):
                continue
            anchors.append(s)

    # 중복 제거(순서 유지)
    seen: Set[str] = set()
    uniq: List[str] = []
    for a in anchors:
        if a not in seen:
            seen.add(a)
            uniq.append(a)
    return uniq


# -----------------------------
# HTTP
# -----------------------------
def make_session() -> requests.Session:
    s = requests.Session()
    s.headers.update({
        "user-agent": UA,
        "accept": "*/*",
        "accept-language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
    })
    return s


def http_get_json(
    sess: requests.Session,
    url: str,
    headers: Optional[Dict[str, str]] = None,
    timeout: int = 20,
    retries: int = 3,
) -> Dict[str, Any]:
    last_err = None
    for _ in range(retries):
        try:
            h = {}
            if headers:
                h.update(headers)
            r = sess.get(url, headers=h, timeout=timeout)
            if r.status_code >= 400:
                raise RuntimeError(f"HTTP {r.status_code}: {r.text[:200]}")
            return r.json()
        except Exception as e:
            last_err = e
            sleep_jitter(0.6, 0.6)
    raise RuntimeError(f"GET failed after retries: {url}\nlast_err={last_err}")


# -----------------------------
# BuildId
# -----------------------------
def extract_build_id(html: str) -> Optional[str]:
    """
    Next.js 페이지에서 buildId 추출.
    보통 /_next/static/{buildId}/_buildManifest.js 형태가 포함됨.
    """
    m = re.search(r"/_next/static/([^/]+)/_buildManifest\.js", html)
    if m:
        return m.group(1)
    return None


def get_build_id(sess: requests.Session) -> str:
    r = sess.get(BASE_WEB, timeout=20)
    r.raise_for_status()
    bid = extract_build_id(r.text)
    if not bid:
        raise RuntimeError("buildId 추출 실패: 홈 HTML에서 /_next/static/.../_buildManifest.js 패턴을 못 찾음")
    return bid


# -----------------------------
# Search (pagination)
# -----------------------------
def next_data_search_url(build_id: str, keyword: str, page: int) -> str:
    """
    /_next/data/{buildId}/search/{keyword}.json?keyword=...&keywordSource=INPUT_KEYWORD&page=N
    """
    path_keyword = quote(keyword, safe="")
    q = quote(keyword, safe="")
    return (
        f"{BASE_WEB}/_next/data/{build_id}/search/{path_keyword}.json"
        f"?keyword={q}&keywordSource=INPUT_KEYWORD&page={page}"
    )


def extract_search_items(next_json: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    next/data 응답에서 dehydratedState.queries 안의
    queryKey가 ["get-search-products", {...}] 인 쿼리를 찾아
    state.data.data.items 반환
    """
    page_props = next_json.get("pageProps", {})
    dehydrated = page_props.get("dehydratedState", {})
    queries = dehydrated.get("queries", [])

    for q in queries:
        qk = q.get("queryKey")
        if isinstance(qk, list) and len(qk) >= 1 and qk[0] == "get-search-products":
            state = q.get("state", {})
            data = state.get("data", {})
            inner = data.get("data", {})
            items = inner.get("items", [])
            if isinstance(items, list):
                return items
    return []


def collect_seqs(
    sess: requests.Session,
    build_id: str,
    keyword: str,
    target_n: int = 500,
    max_pages: int = 50,
    raw_dir: Optional[str] = None,
) -> Tuple[List[int], List[str]]:
    """
    page=0.. 반복해서 seq 수집 + search_page{N}.json 저장
    """
    seqs: List[int] = []
    seen: Set[int] = set()
    debug_logs: List[str] = []

    save_dir = raw_dir or os.path.join(RAW_DIR, safe_dirname(keyword))
    os.makedirs(save_dir, exist_ok=True)

    for page in range(max_pages):
        url = next_data_search_url(build_id, keyword, page)
        js = http_get_json(sess, url, headers={"x-nextjs-data": "1"})

        raw_path = os.path.join(save_dir, f"search_page{page}.json")
        jdump(raw_path, js)

        items = extract_search_items(js)
        debug_logs.append(f"page={page} items={len(items)} url={url}")

        if not items:
            break

        for it in items:
            seq = it.get("seq")
            if isinstance(seq, int) and seq not in seen:
                seen.add(seq)
                seqs.append(seq)
                if len(seqs) >= target_n:
                    return seqs, debug_logs

        sleep_jitter()

    return seqs, debug_logs


# -----------------------------
# Detail
# -----------------------------
def next_data_detail_url(build_id: str, keyword: str, product_seq: int) -> str:
    """
    /_next/data/{buildId}/product/{seq}.json?keyword=...&productSeq=...
    """
    q = quote(keyword, safe="")
    return (
        f"{BASE_WEB}/_next/data/{build_id}/product/{product_seq}.json"
        f"?keyword={q}&productSeq={product_seq}"
    )


def deep_find_first(obj: Any, keys: Set[str]) -> Optional[Dict[str, Any]]:
    if isinstance(obj, dict):
        hit = sum(1 for k in keys if k in obj)
        if hit >= 2:
            return obj
        for v in obj.values():
            found = deep_find_first(v, keys)
            if found:
                return found
    elif isinstance(obj, list):
        for v in obj:
            found = deep_find_first(v, keys)
            if found:
                return found
    return None


def parse_detail(next_json: Dict[str, Any]) -> Dict[str, Any]:
    hint_keys = {
        "productSeq", "seq", "title", "price", "contents", "content", "images",
        "category", "seller", "storeSeq", "location", "locationNames",
        "createdAt", "updatedAt", "registDate", "saleYn",
    }

    page_props = next_json.get("pageProps", {})
    found = deep_find_first(page_props, hint_keys)
    if found:
        return found

    found2 = deep_find_first(next_json, hint_keys)
    return found2 or {}


def build_candidate_from_search_item(item: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "seq": item.get("seq"),
        "title": item.get("title"),
        "price": item.get("price"),
        "parcelFee": item.get("parcelFee"),
        "thumbUrl": item.get("url"),
        "sortDate": item.get("sortDate"),
        "mainLocationName": item.get("mainLocationName"),
        "locationNames": item.get("locationNames"),
        "wishCount": item.get("wishCount"),
        "chatCount": item.get("chatCount"),
        "platformType": item.get("platformType"),
        "jnPayBadgeFlag": item.get("jnPayBadgeFlag"),
        "objectType": item.get("objectType"),
    }


def is_noise_by_title(title: str, anchor: str) -> bool:
    if not title:
        return True

    t = title.lower()
    negative = [
        "충전기", "어댑터", "adapter", "아답터",
        "램", "ram", "ddr", "메모리",
        "키보드", "마우스", "거치대", "스탠드", "파우치",
        "액정", "패널", "부품용", "부품", "하판", "상판",
        "케이스", "보호필름"
    ]
    if any(n in t for n in negative) and ("노트북" not in t):
        return True

    return False


# -----------------------------
# Main pipeline
# -----------------------------
def run(keyword: str, target_collect: int = 500, target_clean: int = 100) -> None:
    anchor_name = safe_dirname(keyword)

    anchor_raw_dir = os.path.join(RAW_DIR, anchor_name)
    anchor_processed_dir = os.path.join(PROCESSED_DIR, anchor_name)
    os.makedirs(anchor_raw_dir, exist_ok=True)
    os.makedirs(anchor_processed_dir, exist_ok=True)

    sess = make_session()
    build_id = get_build_id(sess)
    print(f"[OK] buildId: {build_id}")

    # 1) Search pages -> seqs (search_page*.json saved under raw/<keyword>/)
    seqs, logs = collect_seqs(
        sess, build_id, keyword,
        target_n=target_collect,
        max_pages=80,
        raw_dir=anchor_raw_dir,
    )
    print(f"[OK] collected seqs: {len(seqs)} (target={target_collect})")

    log_path = os.path.join(anchor_processed_dir, f"{safe_filename(keyword)}_debug_pages.txt")
    write_lines(log_path, logs)
    print(f"[saved] {log_path}")

    # 2) reconstruct items_by_seq from saved search pages
    items_by_seq: Dict[int, Dict[str, Any]] = {}
    page = 0
    while True:
        raw_path = os.path.join(anchor_raw_dir, f"search_page{page}.json")
        if not os.path.exists(raw_path):
            break
        with open(raw_path, "r", encoding="utf-8") as f:
            js = json.load(f)
        items = extract_search_items(js)
        for it in items:
            s = it.get("seq")
            if isinstance(s, int) and s not in items_by_seq:
                items_by_seq[s] = it
        page += 1

    # 3) Detail fetch
    failures: List[str] = []
    candidates: List[Dict[str, Any]] = []
    clean: List[Dict[str, Any]] = []

    pbar = tqdm(seqs, desc=f"detail({keyword})", ncols=100)
    for seq in pbar:
        durl = next_data_detail_url(build_id, keyword, seq)
        try:
            djs = http_get_json(sess, durl, headers={"x-nextjs-data": "1"})

            # raw detail 저장: raw/<keyword>/detail_<seq>.json
            raw_d_path = os.path.join(anchor_raw_dir, f"detail_{seq}.json")
            jdump(raw_d_path, djs)

            detail_block = parse_detail(djs)

            base_item = items_by_seq.get(seq, {})
            row = build_candidate_from_search_item(base_item)
            row["keyword"] = keyword
            row["detail_url"] = durl
            row["detail"] = detail_block

            candidates.append(row)

            title = str(row.get("title") or "")
            if not is_noise_by_title(title, anchor=keyword):
                clean.append(row)

            pbar.set_postfix(ok=len(candidates), clean=len(clean), fail=len(failures))
        except Exception as e:
            failures.append(f"{seq}\t{durl}\t{repr(e)}")

        sleep_jitter()

    # 4) Save outputs under processed/<keyword>/
    cand_path = os.path.join(anchor_processed_dir, f"{safe_filename(keyword)}_candidates.jsonl")
    clean_path = os.path.join(anchor_processed_dir, f"{safe_filename(keyword)}_clean.jsonl")
    fail_path = os.path.join(anchor_processed_dir, f"{safe_filename(keyword)}_detail_failures.txt")

    jwrite_jsonl(cand_path, candidates)
    jwrite_jsonl(clean_path, clean)
    write_lines(fail_path, failures)

    print("\n===== 결과 =====")
    print(f"수집 seq: {len(seqs)}")
    print(f"상세 호출 실패: {len(failures)}")
    print(f"정제 후보(candidates): {len(candidates)}")
    print(f"최종 clean: {len(clean)}")
    print(f"[saved] {cand_path}")
    print(f"[saved] {clean_path}")
    print(f"[saved] {fail_path}")

    if len(clean) < target_clean:
        print(f"\n[경고] clean {target_clean}개를 못 채웠습니다.")
        print("- 원인1) 실제로 노이즈가 많거나(악세서리/부품)")
        print("- 원인2) 필터가 과하게 걸렸거나(필터 완화 필요)")
        print("- 원인3) 검색 page가 더 있는데 max_pages가 부족했거나/막혔을 수 있음")
    else:
        print(f"\n[OK] clean {target_clean}개 이상 확보!")


# -----------------------------
# CLI
# -----------------------------
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--keyword", type=str, help="예: 노트북 (단일 키워드 실행)")
    parser.add_argument("--anchor-file", type=str, help="예: data/anchors/01_digital_devices.txt (여러 키워드 실행)")
    parser.add_argument("--collect", type=int, default=500, help="총 수집 목표 seq 수")
    parser.add_argument("--clean", type=int, default=100, help="정제 목표 개수")
    args = parser.parse_args()

    if not args.keyword and not args.anchor_file:
        raise SystemExit("Either --keyword or --anchor-file is required")

    if args.keyword:
        run(args.keyword, target_collect=args.collect, target_clean=args.clean)
    else:
        anchors = read_anchors(args.anchor_file)
        print(f"[OK] anchors loaded: {len(anchors)} from {args.anchor_file}")
        for kw in anchors:
            try:
                print(f"\n==== RUN: {kw} ====")
                run(kw, target_collect=args.collect, target_clean=args.clean)
            except Exception as e:
                print(f"[ERROR] {kw}: {e}")
            time.sleep(2.0)
