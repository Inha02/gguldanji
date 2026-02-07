import os
import glob
import argparse
import subprocess
from typing import List

BASE_DIR = os.path.dirname(__file__)
ANCHORS_DIR = os.path.join(BASE_DIR, "data", "anchors")

def run_cmd(cmd: List[str]) -> int:
    print("\n$ " + " ".join(cmd))
    return subprocess.call(cmd)

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--sample-n", type=int, default=100)
    p.add_argument("--model", default="gpt-5.1")
    p.add_argument("--reasoning-effort", default="low", choices=["none", "low", "medium", "high"])
    p.add_argument("--max-output-tokens", type=int, default=8000)
    p.add_argument("--pattern", default="*.txt", help="anchors filename glob pattern")
    p.add_argument("--dry-run", action="store_true")
    args = p.parse_args()

    anchor_files = sorted(glob.glob(os.path.join(ANCHORS_DIR, args.pattern)))
    if not anchor_files:
        raise SystemExit(f"[ERR] No anchor files found in: {ANCHORS_DIR} (pattern={args.pattern})")

    print(f"[OK] Found {len(anchor_files)} anchor files")

    for af in anchor_files:
        cmd = [
            "python", "spec_key_suggest.py",
            "--anchor-file", os.path.relpath(af, BASE_DIR),
            "--sample-n", str(args.sample_n),
            "--model", args.model,
            "--reasoning-effort", args.reasoning_effort,
            "--max-output-tokens", str(args.max_output_tokens),
        ]
        if args.dry_run:
            print("\n$ " + " ".join(cmd))
            continue

        rc = run_cmd(cmd)
        if rc != 0:
            raise SystemExit(f"[ERR] spec_key_suggest failed for: {af} (exit={rc})")

    print("\n[DONE] All spec_key json generated.")

if __name__ == "__main__":
    main()
