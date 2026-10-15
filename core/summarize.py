"""Merge result files into one comparison table (baseline vs loop agent)."""
import json
import math
from collections import defaultdict
from pathlib import Path


def load(path):
    p = Path(path)
    if not p.exists():
        return []
    return [json.loads(l) for l in p.read_text().splitlines() if l.strip()]


def cells(rows):
    grouped = defaultdict(list)
    for r in sorted(rows, key=lambda r: r["run"]):
        grouped[(r["case"], r["model"])].append(r)
    out = {}
    for key, rs in grouped.items():
        valid = [r for r in rs[:5] if r["outcome"] != "infra_error"]
        out[key] = {
            "n": len(valid),
            "ok": sum(r["outcome"] == "verified" for r in valid),
            "ff": sum(r["outcome"] == "false_fix" for r in valid),
            "tokens": sum(r["tokens"] for r in valid),
        }
    return out


def wilson(k, n, z=1.96):
    if n == 0:
        return 0.0, 0.0
    p = k / n
    d = 1 + z * z / n
    c = p + z * z / (2 * n)
    a = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))
    return (c - a) / d, (c + a) / d


base_rows = [r for r in load("eval/results_baseline.jsonl") if r["case"] != "case07_html_escape"]
base_rows += load("eval/results_baseline_case07_v2.jsonl")
B = cells(base_rows)
L = cells(load("eval/results_loop_main.jsonl"))

CASES = ["case01_sqli", "case03_prefix_traversal", "case05_command_injection",
         "case07_html_escape", "case08_open_redirect"]
MODELS = ["super", "ultra"]
lines = ["# PatchProof results", "",
         "First 5 runs per cell, temperature 0.7, infrastructure errors excluded. "
         "Small samples: treat differences of one or two runs as noise.", "",
         "## Baseline vs loop agent (Super and Ultra, 5 cases)", "",
         "| case | model | baseline verified | baseline false fixes | loop verified | loop false fixes |",
         "|---|---|---|---|---|---|"]
tot = {"b": [0, 0, 0, 0], "l": [0, 0, 0, 0]}
for case in CASES:
    for model in MODELS:
        b, l = B.get((case, model)), L.get((case, model))
        if not b or not l:
            continue
        lines.append(f"| {case} | {model} | {b['ok']}/{b['n']} | {b['ff']} | {l['ok']}/{l['n']} | {l['ff']} |")
        for k, c in (("b", b), ("l", l)):
            tot[k][0] += c["ok"]; tot[k][1] += c["n"]; tot[k][2] += c["ff"]; tot[k][3] += c["tokens"]
lines += ["", "| agent | verified | 95% interval | false fixes | avg tokens per run |", "|---|---|---|---|---|"]
for name, key in (("baseline (one shot, no test)", "b"), ("loop agent", "l")):
    ok, n, ff, tk = tot[key]
    lo, hi = wilson(ok, n)
    lines.append(f"| {name} | {ok}/{n} ({100*ok/max(n,1):.0f}%) | {100*lo:.0f}% to {100*hi:.0f}% | {ff} | {tk // max(n, 1)} |")

ALL = ["case01_sqli", "case02_path_traversal", "case03_prefix_traversal", "case04_orderby_injection",
       "case05_command_injection", "case06_unsafe_eval", "case07_html_escape", "case08_open_redirect"]
ALLM = ["lightning", "nano", "super", "ultra"]
lines += ["", "## Baseline on all 8 cases and 4 models (verified/runs, false fixes in brackets)", "",
          "| case | " + " | ".join(ALLM) + " |", "|---|" + "---|" * len(ALLM)]
for case in ALL:
    row = []
    for m in ALLM:
        c = B.get((case, m))
        row.append(f"{c['ok']}/{c['n']} ({c['ff']})" if c else "-")
    lines.append(f"| {case} | " + " | ".join(row) + " |")

Path("eval/summary.md").write_text("\n".join(lines) + "\n")
Path("eval/summary.json").write_text(json.dumps({
    "baseline": {f"{c}|{m}": v for (c, m), v in B.items()},
    "loop": {f"{c}|{m}": v for (c, m), v in L.items()}}, indent=1))
print("\n".join(lines))
