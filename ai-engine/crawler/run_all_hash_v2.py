import os, glob, argparse, subprocess

BASE_DIR = os.path.dirname(__file__)
DATA_DIR = os.path.join(BASE_DIR, "data")
STRUCT_DIR = os.path.join(DATA_DIR, "structured")

def run(cmd):
    print("\n$ " + " ".join(cmd))
    return subprocess.call(cmd)

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--skip-existing", action="store_true")
    args = p.parse_args()

    files = sorted(glob.glob(os.path.join(STRUCT_DIR, "*", "*_structured.jsonl")))
    if not files:
        raise SystemExit("[ERR] no structured files found")

    for fp in files:
        category = os.path.basename(os.path.dirname(fp))
        keyword = os.path.basename(fp).replace("_structured.jsonl", "")
        out_fp = os.path.join(DATA_DIR, "structured_v2", category, f"{keyword}_structured_v2.jsonl")

        if args.skip_existing and os.path.exists(out_fp):
            print(f"[SKIP] exists: {out_fp}")
            continue

        cmd = ["python", "make_hash_v2.py", "--category", category, "--keyword", keyword]
        rc = run(cmd)
        if rc != 0:
            print(f"[ERR] failed: category={category} keyword={keyword} exit={rc}")
            continue

    print("\n[DONE] hash_v2 generation completed.")

if __name__ == "__main__":
    main()
