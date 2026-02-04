# data/anchors/01~16*.txt를 찾아서 전부 실행 + 로그/요약 저장
import os
import sys
import glob
import time
import json
from datetime import datetime
from typing import Dict, List, Tuple

# 같은 폴더의 crawl_joongna.py import
import crawl_joongna as cj


BASE_DIR = os.path.dirname(__file__)
DATA_DIR = os.path.join(BASE_DIR, "data")
ANCHOR_DIR = os.path.join(DATA_DIR, "anchors")
LOG_DIR = os.path.join(DATA_DIR, "logs")
SUMMARY_DIR = os.path.join(DATA_DIR, "reports")

os.makedirs(LOG_DIR, exist_ok=True)
os.makedirs(SUMMARY_DIR, exist_ok=True)


def now_str() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def list_anchor_files() -> List[str]:
    """
    data/anchors/01_*.txt ~ 16_*.txt 파일을 자동으로 잡음.
    """
    files = sorted(glob.glob(os.path.join(ANCHOR_DIR, "[0-9][0-9]_*.txt")))
    return files


def safe(s: str) -> str:
    return cj.safe_filename(s)


def run_one_keyword(keyword: str, collect: int, clean: int) -> Dict:
    """
    crawl_joongna.run() 한 번 실행하고 결과를 리턴.
    run() 내부에서 저장까지 다 하므로 여기서는 "메타"만 기록.
    """
    t0 = time.time()
    cj.run(keyword, target_collect=collect, target_clean=clean)
    t1 = time.time()
    return {
        "keyword": keyword,
        "collect_target": collect,
        "clean_target": clean,
        "elapsed_sec": round(t1 - t0, 2),
    }


def count_jsonl_rows(path: str) -> int:
    if not os.path.exists(path):
        return 0
    n = 0
    with open(path, "r", encoding="utf-8") as f:
        for _ in f:
            n += 1
    return n


def infer_outputs(keyword: str) -> Dict[str, str]:
    """
    crawl_joongna.py가 현재 저장하는 규칙 기준:
      data/processed/<keyword>/<keyword>_clean.jsonl
      data/processed/<keyword>/<keyword>_candidates.jsonl
      data/processed/<keyword>/<keyword>_detail_failures.txt
    """
    kdir = cj.safe_dirname(keyword)
    proc_dir = os.path.join(DATA_DIR, "processed", kdir)
    return {
        "processed_dir": proc_dir,
        "clean": os.path.join(proc_dir, f"{cj.safe_filename(keyword)}_clean.jsonl"),
        "candidates": os.path.join(proc_dir, f"{cj.safe_filename(keyword)}_candidates.jsonl"),
        "failures": os.path.join(proc_dir, f"{cj.safe_filename(keyword)}_detail_failures.txt"),
        "debug_pages": os.path.join(proc_dir, f"{cj.safe_filename(keyword)}_debug_pages.txt"),
    }


def run_anchor_file(anchor_file: str, collect: int, clean: int) -> Tuple[List[Dict], Dict]:
    anchors = cj.read_anchors(anchor_file)
    results: List[Dict] = []

    for kw in anchors:
        print(f"\n==== RUN keyword: {kw} (from {os.path.basename(anchor_file)}) ====")

        meta = run_one_keyword(kw, collect=collect, clean=clean)
        out = infer_outputs(kw)

        meta["outputs"] = out
        meta["clean_count"] = count_jsonl_rows(out["clean"])
        meta["candidate_count"] = count_jsonl_rows(out["candidates"])

        # failures는 파일 줄 수로 대충 파악
        fail_n = 0
        if os.path.exists(out["failures"]):
            with open(out["failures"], "r", encoding="utf-8") as f:
                fail_n = sum(1 for _ in f)
        meta["failure_count"] = fail_n

        # 목표치 충족 여부
        meta["ok_clean_min"] = (meta["clean_count"] >= clean)

        results.append(meta)

    summary = {
        "anchor_file": anchor_file,
        "anchor_count": len(anchors),
        "collect_target": collect,
        "clean_target": clean,
        "ran_at": datetime.now().isoformat(timespec="seconds"),
        "ok_keywords": sum(1 for r in results if r["ok_clean_min"]),
        "fail_keywords": [r["keyword"] for r in results if not r["ok_clean_min"]],
    }
    return results, summary


def main():
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--collect", type=int, default=500)
    parser.add_argument("--clean", type=int, default=100)
    parser.add_argument("--only", type=str, default="", help="예: 01 또는 03 이런식으로 특정 파일만")
    args = parser.parse_args()

    files = list_anchor_files()
    if args.only:
        files = [f for f in files if os.path.basename(f).startswith(args.only)]
        if not files:
            raise SystemExit(f"[ERR] --only={args.only}에 해당하는 anchor 파일이 없음: {ANCHOR_DIR}")

    run_id = now_str()
    log_path = os.path.join(LOG_DIR, f"run_{run_id}.log")
    json_path = os.path.join(SUMMARY_DIR, f"run_summary_{run_id}.json")
    md_path = os.path.join(SUMMARY_DIR, f"run_summary_{run_id}.md")

    # stdout을 파일에도 같이 기록 (간단하게 tee 구현)
    class Tee:
        def __init__(self, *files):
            self.files = files
        def write(self, data):
            for f in self.files:
                f.write(data)
                f.flush()
        def flush(self):
            for f in self.files:
                f.flush()

    with open(log_path, "w", encoding="utf-8") as lf:
        old = sys.stdout
        sys.stdout = Tee(sys.stdout, lf)
        try:
            all_results: List[Dict] = []
            all_summaries: List[Dict] = []

            print(f"[RUN] {run_id}")
            print(f"[INFO] anchor_files={len(files)} collect={args.collect} clean={args.clean}")
            for af in files:
                print(f"\n========== ANCHOR FILE: {os.path.basename(af)} ==========")
                results, summary = run_anchor_file(af, collect=args.collect, clean=args.clean)
                all_results.extend(results)
                all_summaries.append(summary)

            payload = {
                "run_id": run_id,
                "collect_target": args.collect,
                "clean_target": args.clean,
                "anchor_files": files,
                "file_summaries": all_summaries,
                "keyword_results": all_results,
            }

            with open(json_path, "w", encoding="utf-8") as f:
                json.dump(payload, f, ensure_ascii=False, indent=2)

            # 마크다운 요약도 같이
            lines = []
            lines.append(f"# Run Summary ({run_id})")
            lines.append("")
            lines.append(f"- collect_target: {args.collect}")
            lines.append(f"- clean_target: {args.clean}")
            lines.append(f"- anchor_files: {len(files)}")
            lines.append("")
            lines.append("## By Anchor File")
            for s in all_summaries:
                lines.append(f"- **{os.path.basename(s['anchor_file'])}**: anchors={s['anchor_count']}, ok={s['ok_keywords']}, fail={len(s['fail_keywords'])}")
                if s["fail_keywords"]:
                    lines.append(f"  - fail_keywords: {', '.join(s['fail_keywords'][:20])}" + (" ..." if len(s["fail_keywords"]) > 20 else ""))

            lines.append("")
            lines.append("## Failed Keywords (clean < target)")
            failed = [r for r in all_results if not r["ok_clean_min"]]
            if not failed:
                lines.append("- (none)")
            else:
                for r in failed:
                    lines.append(f"- {r['keyword']} | clean={r['clean_count']} cand={r['candidate_count']} fail={r['failure_count']}")

            with open(md_path, "w", encoding="utf-8") as f:
                f.write("\n".join(lines))

            print(f"\n[saved] {log_path}")
            print(f"[saved] {json_path}")
            print(f"[saved] {md_path}")

        finally:
            sys.stdout = old


if __name__ == "__main__":
    main()
