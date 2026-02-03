import re
import json
import time
import random
import urllib.parse
from dataclasses import dataclass, asdict
from typing import Any, Dict, List, Optional, Tuple

import requests
import pandas as pd
from bs4 import BeautifulSoup
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from tqdm import tqdm


BASE = "https://web.joongna.com"
UA = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/120.0.0.0 Safari/537.36"
)

SESSION = requests.Session()
SESSION.headers.update({"User-Agent": UA, "Accept-Language": "ko-KR,ko;q=0.9,en;q=0.8"})


# -----------------------
# 1) buildId 추출
# -----------------------
@retry(
    reraise=True,
    stop=stop_after_attempt(5),
    wait=wait_exponential(multiplier=1, min=1, max=10),
    retry=retry_if_exception_type(requests.RequestException),
)
def fetch_html(url: str) -> str:
    r = SESSION.get(url, timeout=15)
    r.raise_for_status()
    return r.text


def extract_build_id_from_html(html: str) -> str:
    """
    Next.js는 보통 <script id="__NEXT_DATA__" type="application/json"> ... </script> 안에 buildId가 있음.
    """
    soup = BeautifulSoup(html, "lxml")
    tag = soup.find("script", id="__NEXT_DATA__")
    if not tag or not tag.string:
        # fallback: 정규식으로도 한 번 시도
        m = re.search(r'__NEXT_DATA__"\s*type="application/json"\s*>\s*(\{.*?\})\s*</script>', html, re.S)
        if not m:
            raise ValueError("Cannot find __NEXT_DATA__ in HTML")
        data = json.loads(m.group(1))
    else:
        data = json.loads(tag.string)

    build_id = data.get("buildId")
    if not build_id:
        raise ValueError("Cannot find buildId in __NEXT_DATA__")
    return build_id


def get_build_id(keyword: str) -> str:
    url = f"{BASE}/search/{urllib.parse.quote(keyword)}"
    html = fetch_html(url)
    return extract_build_id_from_html(html)


# -----------------------
# 2) search JSON 호출 → items.seq 수집
# -----------------------
@retry(
    reraise=True,
    stop=stop_after_attempt(5),
    wait=wait_exponential(multiplier=1, min=1, max=10),
    retry=retry_if_exception_type(requests.RequestException),
)
def fetch_json(url: str) -> Dict[str, Any]:
    r = SESSION.get(url, timeout=15)
    r.raise_for_status()
    return r.json()


def build_search_json_url(build_id: str, keyword: str) -> str:
    # 네가 준 형태 그대로
    q = urllib.parse.urlencode({"keyword": keyword, "keywordSource": "INPUT_KEYWORD"})
    return f"{BASE}/_next/data/{build_id}/search/{urllib.parse.quote(keyword)}.json?{q}"


def extract_items_from_search_payload(payload: Dict[str, Any]) -> Tuple[List[Dict[str, Any]], int]:
    """
    payload["pageProps"]["dehydratedState"]["queries"] 중 queryKey[0] == "get-search-products" 찾기
    """
    queries = (
        payload.get("pageProps", {})
        .get("dehydratedState", {})
        .get("queries", [])
    )

    items = []
    total_size = 0

    for q in queries:
        qk = q.get("queryKey")
        if isinstance(qk, list) and len(qk) > 0 and qk[0] == "get-search-products":
            state = q.get("state", {})
            data = state.get("data", {}).get("data", {})
            items = data.get("items", []) or []
            total_size = int(data.get("totalSize", 0) or 0)
            return items, total_size

    raise ValueError("Cannot find get-search-products query in search payload")


# -----------------------
# 3) 상세 JSON 호출 (후보 경로 자동 탐색)
# -----------------------
DETAIL_PATH_CANDIDATES = [
    # 가장 흔한 패턴들: 실제 서비스에 따라 다를 수 있어 후보를 넉넉히 둠
    "product/{seq}",
    "products/{seq}",
    "detail/{seq}",
    "item/{seq}",
    "post/{seq}",
]


def build_detail_json_candidates(build_id: str, seq: int) -> List[str]:
    urls = []
    for fmt in DETAIL_PATH_CANDIDATES:
        path = fmt.format(seq=seq)
        urls.append(f"{BASE}/_next/data/{build_id}/{path}.json")
    return urls


def is_valid_next_data(payload: Dict[str, Any]) -> bool:
    # 최소한 pageProps가 있으면 Next data일 확률이 높음
    return isinstance(payload, dict) and "pageProps" in payload


def fetch_detail_payload(build_id: str, seq: int) -> Dict[str, Any]:
    last_err = None
    for url in build_detail_json_candidates(build_id, seq):
        try:
            payload = fetch_json(url)
            if is_valid_next_data(payload):
                return payload
        except Exception as e:
            last_err = e
            continue
    raise RuntimeError(f"Failed to fetch detail next-data for seq={seq}. last_err={last_err}")


def extract_detail_data(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    상세 페이지도 보통 dehydratedState.queries 안에 상세 데이터가 들어있음.
    서비스마다 queryKey가 다르기 때문에,
    - queries 중 state.data.data 처럼 상품 정보로 보이는 덩어리를 최대한 뽑아주는 방식으로 구현.
    """
    queries = (
        payload.get("pageProps", {})
        .get("dehydratedState", {})
        .get("queries", [])
    )
    # heuristic: data 안에 title/price 같은 key가 있으면 그걸 우선
    best = None
    for q in queries:
        state = q.get("state", {})
        data = state.get("data", {}).get("data")
        if isinstance(data, dict):
            keys = set(data.keys())
            score = 0
            for k in ["title", "price", "content", "description", "images", "image", "category"]:
                if k in keys:
                    score += 1
            if best is None or score > best[0]:
                best = (score, data)

    if best and isinstance(best[1], dict):
        return best[1]

    # fallback: pageProps 직하에서라도 뽑기
    pp = payload.get("pageProps", {})
    if isinstance(pp, dict):
        return pp

    return {}


# -----------------------
# 4) 저장 스키마 매핑 (예시)
# -----------------------
@dataclass
class SavedItem:
    seq: int
    title: str
    price: Optional[int]
    thumbnail_url: Optional[str]
    sort_date: Optional[str]
    location: Optional[str]
    raw_search_item: Dict[str, Any]
    raw_detail: Dict[str, Any]


def map_to_schema(search_item: Dict[str, Any], detail: Dict[str, Any]) -> SavedItem:
    return SavedItem(
        seq=int(search_item.get("seq")),
        title=str(search_item.get("title", "")),
        price=search_item.get("price"),
        thumbnail_url=search_item.get("url"),
        sort_date=search_item.get("sortDate"),
        location=search_item.get("mainLocationName"),
        raw_search_item=search_item,
        raw_detail=detail,
    )


def polite_sleep():
    time.sleep(random.uniform(0.15, 0.45))


def crawl_keyword(keyword: str, limit: int = 50) -> List[SavedItem]:
    build_id = get_build_id(keyword)
    search_url = build_search_json_url(build_id, keyword)
    payload = fetch_json(search_url)

    items, total = extract_items_from_search_payload(payload)
    items = items[:limit]

    results: List[SavedItem] = []
    for it in tqdm(items, desc=f"Crawling {keyword} (buildId={build_id})"):
        seq = it.get("seq")
        if not seq:
            continue

        polite_sleep()
        detail_payload = fetch_detail_payload(build_id, int(seq))
        detail_data = extract_detail_data(detail_payload)

        results.append(map_to_schema(it, detail_data))

    print(f"[OK] keyword={keyword} got {len(results)} items (totalSize={total})")
    return results


def save_results(items: List[SavedItem], out_prefix: str):
    rows = [asdict(x) for x in items]
    df = pd.DataFrame(rows)

    df.to_csv(f"{out_prefix}.csv", index=False, encoding="utf-8-sig")
    # raw jsonl도 같이 저장(디버깅/추후 파싱에 유리)
    with open(f"{out_prefix}.jsonl", "w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")


if __name__ == "__main__":
    # 테스트: 노트북 30개만
    kw = "노트북"
    items = crawl_keyword(kw, limit=30)
    save_results(items, out_prefix=f"joongna_{kw}_sample")
