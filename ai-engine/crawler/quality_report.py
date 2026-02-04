# 병합 결과 기준으로 키워드별/가격/결측/이상치 요약 리포트 생성
import os
import json
import math
from typing import Dict, List, Any, Tuple
from collections import defaultdict


BASE_DIR = os.path.dirname(__file__)
DATA_DIR = os.path.join(BASE_DIR, "data")
MERGED_DIR = os.path.join(DATA_DIR, "merged")
REPORT_DIR = os.path.join(DATA_DIR, "reports")

os.makedirs(REPORT_DIR, exist_ok=True)


def iter_jsonl(path: str):
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            yield json.loads(line)


def percentile(xs: List[float], p: float) -> float:
    if not xs:
        return float("nan")
    xs = sorted(xs)
    k = (len(xs) - 1) * (p / 100.0)
    f = math.floor(k)
    c = math.ceil(k)
    if f == c:
        return xs[int(k)]
    d0 = xs[f] * (c - k)
    d1 = xs[c] * (k - f)
    return d0 + d1


def main():
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--input",
        type=str,
        default=os.path.join(MERGED_DIR, "clean_merged_dedup.jsonl"),
        help="merge_and_dedupe.py 출력 파일",
    )
    parser.add_argument("--out", type=str, default=os.path.join(REPORT_DIR, "quality_report.md"))
    parser.add_argument("--topk", type=int, default=20)
    args = parser.parse_args()

    if not os.path.exists(args.input):
        raise SystemExit(f"[ERR] input이 없음: {args.input} (merge_and_dedupe.py 먼저 실행)")

    total = 0
    missing_price = 0
    zero_or_neg_price = 0
    missing_title = 0

    prices: List[float] = []
    kw_counts = defaultdict(int)

    # title 내 자주 나오는 노이즈 토큰(간단 추적)
    token_hits = defaultdict(int)
    noisy_tokens = ["삽니다", "구해요", "구함", "교환", "무료나눔", "예약", "급처", "하자", "부품", "충전기", "케이스", "거치대", "램", "필름"]

    for row in iter_jsonl(args.input):
        total += 1
        kw = row.get("keyword") or row.get("source_keyword") or "UNKNOWN"
        kw_counts[str(kw)] += 1

        title = row.get("title")
        if not title:
            missing_title += 1
        else:
            t = str(title)
            for tok in noisy_tokens:
                if tok in t:
                    token_hits[tok] += 1

        price = row.get("price")
        if price is None:
            missing_price += 1
        else:
            try:
                pv = float(price)
                if pv <= 0:
                    zero_or_neg_price += 1
                else:
                    prices.append(pv)
            except Exception:
                missing_price += 1

    # 가격 요약
    p_min = min(prices) if prices else float("nan")
    p_max = max(prices) if prices else float("nan")
    p_med = percentile(prices, 50)
    p_p10 = percentile(prices, 10)
    p_p90 = percentile(prices, 90)

    # 상위 키워드
    top_kw = sorted(kw_counts.items(), key=lambda x: x[1], reverse=True)[: args.topk]
    top_tok = sorted(token_hits.items(), key=lambda x: x[1], reverse=True)[: args.topk]

    lines = []
    lines.append("# Quality Report")
    lines.append("")
    lines.append(f"- input: `{args.input}`")
    lines.append(f"- total_rows: **{total}**")
    lines.append("")
    lines.append("## Missing / Invalid")
    lines.append(f"- missing_title: {missing_title} ({missing_title/total:.2%} if total>0 else N/A)")
    lines.append(f"- missing_price: {missing_price} ({missing_price/total:.2%} if total>0 else N/A)")
    lines.append(f"- price<=0: {zero_or_neg_price} ({zero_or_neg_price/total:.2%} if total>0 else N/A)")
    lines.append("")
    lines.append("## Price Summary (valid prices only)")
    lines.append(f"- min: {p_min}")
    lines.append(f"- p10: {p_p10}")
    lines.append(f"- median: {p_med}")
    lines.append(f"- p90: {p_p90}")
    lines.append(f"- max: {p_max}")
    lines.append("")
    lines.append("## Top Keywords (by count)")
    for k, c in top_kw:
        lines.append(f"- {k}: {c}")
    lines.append("")
    lines.append("## Noisy token hits in title (rough signal)")
    for tok, c in top_tok:
        lines.append(f"- {tok}: {c}")

    with open(args.out, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    print("\n===== QUALITY REPORT =====")
    print(f"total_rows: {total}")
    print(f"[saved] {args.out}")


if __name__ == "__main__":
    main()
