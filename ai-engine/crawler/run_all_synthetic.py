import os, glob, argparse, subprocess, json

BASE_DIR = os.path.dirname(__file__)
DATA_DIR = os.path.join(BASE_DIR, "data")
CFG_DIR = os.path.join(DATA_DIR, "config")
SCHEMA_FP = os.path.join(CFG_DIR, "synth_schema.json")

def run(cmd):
    print("\n$ " + " ".join(cmd))
    return subprocess.call(cmd)

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--mode", default="training", choices=["training", "demo"])
    p.add_argument("--hash", default="v2", choices=["v1", "v2"])
    p.add_argument("--n", type=int, default=2000)
    p.add_argument("--seed", type=int, default=42)
    args = p.parse_args()

    if not os.path.exists(SCHEMA_FP):
        raise SystemExit("[ERR] synth_schema.json not found. Run build_synth_schema.py first.")

    with open(SCHEMA_FP, "r", encoding="utf-8") as f:
        schema = json.load(f)

    cats = sorted((schema.get("categories") or {}).keys())
    if not cats:
        raise SystemExit("[ERR] no categories in synth_schema.json")

    for cat in cats:
        cmd = [
            "python", "synthetic_generate.py",
            "--category", cat,
            "--mode", args.mode,
            "--hash", args.hash,
            "--n", str(args.n),
            "--seed", str(args.seed),
        ]
        rc = run(cmd)
        if rc != 0:
            print(f"[ERR] failed category={cat} exit={rc}")
            continue

    print("\n[DONE] all synthetic generation completed.")

if __name__ == "__main__":
    main()
