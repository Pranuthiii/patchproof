"""Hybrid agent vs one-shot baseline (first 5 runs per cell), plus how well the tier label predicts the oracle."""
import json
import math
from collections import Counter, defaultdict
from pathlib import Path

CASES = ["case01_sqli", "case02_path_traversal", "case03_prefix_traversal", "case04_orderby_injection",
         "case05_command_injection", "case06_unsafe_eval", "case07_html_escape", "case08_open_redirect",
         "case09_like_search", "case10_zip_extract", "case11_header_injection"]
MODELS = ["lightning", "nano", "super", "ultra"]


def load(p):
    f = Path(p)
    return [json.loads(x) for x in f.read_text().splitlines() if x.strip()] if f.exists() else []


def first5(rows):
    g = defaultdict(list)
    for r in sorted(rows, key=lambda r: r["run"]):
        g[(r["case"], r["model"])].append(r)
    out = []
    for v in g.values():
        out += [r for r in v[:5] if r["outcome"] != "infra_error"]
    return out


def wilson(k, n, z=1.96):
    if n == 0:
        return 0.0, 0.0
    p = k / n
    d = 1 + z * z / n
    c = p + z * z / (2 * n)
    a = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))
    return (c - a) / d, (c + a) / d


def tally(rows, cases=CASES, models=MODELS):
    sel = [r for r in rows if r["case"] in cases and r["model"] in models]
    ok = sum(r["outcome"] == "verified" for r in sel)
    ff = sum(r["outcome"] == "false_fix" for r in sel)
    tok = sum(r["tokens"] for r in sel)
    return ok, len(sel), ff, tok


def fmt(t):
    ok, n, ff, tok = t
    lo, hi = wilson(ok, n)
    return f"{ok}/{n} ({100 * ok / max(n, 1):.0f}%), 95% {100 * lo:.0f}% to {100 * hi:.0f}%, {ff} false fixes, ~{tok // max(n, 1)} tokens/run"


base = [r for r in load("eval/results_baseline.jsonl") if r["case"] != "case07_html_escape"]
base += load("eval/results_baseline_case07_v2.jsonl") + load("eval/heldout_baseline.jsonl")
base, hyb = first5(base), first5(load("eval/results_hybrid.jsonl"))

L = ["# Hybrid agent vs one-shot baseline", "",
     "First 5 runs per cell, temperature 0.7, infrastructure errors excluded. The hybrid was designed after the "
     "results for all 11 cases were seen, so these cases are a development set, not an independent test.", "",
     "## Overall (11 cases, 4 models)", "",
     "- one-shot baseline: " + fmt(tally(base)),
     "- hybrid: " + fmt(tally(hyb)), "",
     "## By case", "", "| case | one-shot baseline | hybrid |", "|---|---|---|"]
for c in CASES:
    b, h = tally(base, [c]), tally(hyb, [c])
    L.append(f"| {c} | {b[0]}/{b[1]} ({b[2]} FF) | {h[0]}/{h[1]} ({h[2]} FF) |")
L += ["", "## By model", "", "| model | one-shot baseline | hybrid |", "|---|---|---|"]
for m in MODELS:
    b, h = tally(base, CASES, [m]), tally(hyb, CASES, [m])
    L.append(f"| {m} | {b[0]}/{b[1]} ({b[2]} FF) | {h[0]}/{h[1]} ({h[2]} FF) |")

tiers = defaultdict(lambda: [0, 0])
for r in hyb:
    t = r.get("tier") or "none"
    tiers[t][0] += 1
    tiers[t][1] += r["outcome"] == "verified"
L += ["", "## Does the tier label predict the hidden oracle?", "",
      "| tier | runs | passed the oracle | rate |", "|---|---|---|---|"]
for t, (n, ok) in sorted(tiers.items()):
    L.append(f"| {t} | {n} | {ok} | {100 * ok / max(n, 1):.0f}% |")
out = "\n".join(L) + "\n"
Path("eval/hybrid_summary.md").write_text(out)
print(out)
