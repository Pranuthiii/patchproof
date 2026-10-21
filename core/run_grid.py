"""Run the agent repeatedly on every case/model and log one result per run."""
import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import time
from collections import Counter, defaultdict
from pathlib import Path

CASES = ["case01_sqli", "case02_path_traversal"]
MODELS = ["lightning", "nano", "super", "ultra"]
RESULTS = Path(os.environ.get("PATCHPROOF_RESULTS", "eval/results.jsonl"))
AGENT = os.environ.get("PATCHPROOF_AGENT", "core/agent.py")
GRID_DIR = Path(os.environ.get("PATCHPROOF_GRIDDIR", "runs/grid"))


def classify(out):
    if "SandboxError" in out or "APIConnectionError" in out or "APITimeoutError" in out:
        return "infra_error"
    if "TRUNCATED" in out:
        return "truncated"
    if "VERDICT: VERIFIED" in out:
        return "verified"
    if "VERDICT: FALSE FIX" in out:
        return "false_fix"
    if "VERDICT: NOT VERIFIED" in out:
        return "not_verified"
    if "TEST REJECTED" in out:
        return "test_rejected"
    if "No test returned" in out:
        return "no_test"
    if "No patch returned" in out:
        return "no_patch"
    return "other_error"


def load():
    if not RESULTS.exists():
        return []
    return [json.loads(l) for l in RESULTS.read_text().splitlines() if l.strip()]


def run_one(case, model, idx):
    t0 = time.time()
    try:
        p = subprocess.run(
            [sys.executable, AGENT, f"fixtures/{case}", model],
            capture_output=True, text=True, timeout=900)
        out = p.stdout + p.stderr
        outcome = classify(out)
    except subprocess.TimeoutExpired:
        out, outcome = "", "other_error"
    tokens = sum(int(n) for n in re.findall(r"tokens: (\d+)", out))
    src = Path("runs") / f"agent_{case}_{model}"
    if src.exists():
        dst = GRID_DIR / f"{case}_{model}_{idx}"
        if dst.exists():
            shutil.rmtree(dst)
        shutil.copytree(src, dst)
    rec = {"case": case, "model": model, "run": idx, "outcome": outcome,
           "tokens": tokens, "seconds": round(time.time() - t0),
           "tier": (re.findall(r"TIER: (\w+)", out) or [""])[-1]}
    with RESULTS.open("a") as f:
        f.write(json.dumps(rec) + "\n")
    return rec


def cmd_run(args):
    if subprocess.run(["docker", "info"], capture_output=True).returncode != 0:
        sys.exit("Docker is not running. Start it first.")
    done = Counter((r["case"], r["model"]) for r in load())
    for case in args.cases:
        for model in args.models:
            for _ in range(args.repeats):
                done[(case, model)] += 1
                rec = run_one(case, model, done[(case, model)])
                print(f"{case:24} {model:10} run {rec['run']}: {rec['outcome']:14} "
                      f"{rec['tokens']:>6} tokens  {rec['seconds']}s", flush=True)


def cmd_summary(args):
    rows = load()
    if not rows:
        sys.exit("No results yet.")
    by = defaultdict(list)
    for r in rows:
        by[(r["case"], r["model"])].append(r)
    print(f"{'case':24} {'model':10} {'verified':>9}   other outcomes")
    totals = defaultdict(lambda: [0, 0])
    for (case, model), rs in sorted(by.items()):
        valid = [r for r in rs if r["outcome"] != "infra_error"]
        ok = sum(r["outcome"] == "verified" for r in valid)
        rest = Counter(r["outcome"] for r in valid if r["outcome"] != "verified")
        infra = len(rs) - len(valid)
        extra = dict(rest) | ({"infra_error(excluded)": infra} if infra else {})
        print(f"{case:24} {model:10} {ok:>4}/{len(valid):<4}  {extra or ''}")
        totals[model][0] += ok
        totals[model][1] += len(valid)
    print("\nPer model, all cases:")
    for model, (ok, n) in totals.items():
        print(f"  {model:10} {ok}/{n}")
    print("\nFalse fixes (AI checks passed, oracle failed):",
          sum(r["outcome"] == "false_fix" for r in rows))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("run")
    r.add_argument("--repeats", type=int, default=3)
    r.add_argument("--cases", nargs="+", default=CASES)
    r.add_argument("--models", nargs="+", default=MODELS)
    r.set_defaults(func=cmd_run)
    s = sub.add_parser("summary")
    s.set_defaults(func=cmd_summary)
    a = ap.parse_args()
    a.func(a)
