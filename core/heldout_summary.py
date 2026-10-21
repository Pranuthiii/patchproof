"""Held-out comparison on cases 09-11: one-shot baseline vs plain loop vs seeded loop."""
import json
import math
from collections import defaultdict
from pathlib import Path

FILES = [("one-shot baseline", "eval/heldout_baseline.jsonl"),
         ("plain loop", "eval/heldout_loop.jsonl"),
         ("seeded loop", "eval/heldout_seeded.jsonl")]
CASES = ["case09_like_search", "case10_zip_extract", "case11_header_injection"]
MODELS = ["lightning", "nano", "super", "ultra"]


def load(path):
    p = Path(path)
    if not p.exists():
        return []
    return [json.loads(x) for x in p.read_text().splitlines() if x.strip()]


def cells(rows):
    grouped = defaultdict(list)
    for r in sorted(rows, key=lambda r: r["run"]):
        grouped[(r["case"], r["model"])].append(r)
    return {k: [r for r in v[:10] if r["outcome"] != "infra_error"] for k, v in grouped.items()}


def wilson(k, n, z=1.96):
    if n == 0:
        return 0.0, 0.0
    p = k / n
    d = 1 + z * z / n
    c = p + z * z / (2 * n)
    a = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))
    return (c - a) / d, (c + a) / d


def tally(cl, cases, models=MODELS):
    ok = n = ff = tok = 0
    for c in cases:
        for m in models:
            for r in cl.get((c, m), []):
                n += 1
                ok += r["outcome"] == "verified"
                ff += r["outcome"] == "false_fix"
                tok += r["tokens"]
    return ok, n, ff, tok


def fmt(t):
    ok, n, ff, tok = t
    lo, hi = wilson(ok, n)
    return f"{ok}/{n} ({100 * ok / max(n, 1):.0f}%), 95% {100 * lo:.0f}% to {100 * hi:.0f}%, {ff} false fixes, ~{tok // max(n, 1)} tokens/run"


data = {name: cells(load(path)) for name, path in FILES}
L = ["# Held-out results (cases 09 to 11)", "",
     "First 10 runs per cell, temperature 0.7, infrastructure errors excluded. The attack library was written "
     "after we had seen the oracles for cases 01 to 08, so only these three cases are an independent test.", ""]

L.append("## Primary question: seeded loop vs plain loop on cases 09 and 10 combined")
L.append("")
prim = {name: tally(data[name], CASES[:2]) for name, _ in FILES}
for name, _ in FILES:
    L.append(f"- {name}: {fmt(prim[name])}")
ok_l, n_l, _, _ = prim["plain loop"]
ok_s, n_s, _, _ = prim["seeded loop"]
lo_l, hi_l = wilson(ok_l, n_l)
lo_s, hi_s = wilson(ok_s, n_s)
if n_l == 0 or n_s == 0:
    verdict = "Not enough data yet."
elif lo_s > hi_l:
    verdict = "The seeded loop verified more, and the 95% intervals do not overlap."
elif lo_l > hi_s:
    verdict = "The seeded loop verified fewer, and the 95% intervals do not overlap."
else:
    verdict = "The 95% intervals overlap, so this data does not separate the seeded loop from the plain loop."
L += ["", "**Pre-registered rule:** " + verdict, ""]

L.append("## Control: case 11 (a class the library does not cover)")
L.append("")
for name, _ in FILES:
    L.append(f"- {name}: {fmt(tally(data[name], CASES[2:]))}")

L += ["", "## By case", "", "| case | " + " | ".join(n for n, _ in FILES) + " |", "|---|---|---|---|"]
for c in CASES:
    row = []
    for name, _ in FILES:
        ok, n, ff, _ = tally(data[name], [c])
        row.append(f"{ok}/{n} ({ff} FF)")
    L.append(f"| {c} | " + " | ".join(row) + " |")

L += ["", "## By model (all three cases)", "", "| model | " + " | ".join(n for n, _ in FILES) + " |", "|---|---|---|---|"]
for m in MODELS:
    row = []
    for name, _ in FILES:
        ok, n, ff, _ = tally(data[name], CASES, [m])
        row.append(f"{ok}/{n} ({ff} FF)")
    L.append(f"| {m} | " + " | ".join(row) + " |")

out = "\n".join(L) + "\n"
Path("eval/heldout_summary.md").write_text(out)
print(out)
