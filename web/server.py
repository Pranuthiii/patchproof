"""PatchProof viewer: browse recorded agent runs."""
import difflib
import html
import json
from pathlib import Path

from flask import Flask, abort

from charts import CHART_CSS, comparison_html, heatmap_html

ROOT = Path(__file__).resolve().parent.parent
SOURCES = [
    ("loop agent", ROOT / "eval/results_loop.jsonl", ROOT / "runs/grid_loop"),
    ("single-shot agent", ROOT / "eval/results.jsonl", ROOT / "runs/grid"),
]

CSS = """
:root{--bg:#fff;--fg:#1a1a1a;--mut:#666;--line:#ddd;--ok:#1a7f37;--bad:#cf222e;--warn:#9a6700;--add:#dafbe1;--del:#ffebe9;--code:#f6f8fa}
@media (prefers-color-scheme:dark){:root{--bg:#111;--fg:#e8e8e8;--mut:#999;--line:#333;--ok:#3fb950;--bad:#f85149;--warn:#d29922;--add:#12261e;--del:#3b1519;--code:#1a1a1a}}
body{font:15px/1.5 system-ui,sans-serif;background:var(--bg);color:var(--fg);max-width:960px;margin:0 auto;padding:20px}
a{color:inherit}
table{border-collapse:collapse;width:100%}
td,th{border-bottom:1px solid var(--line);padding:6px 8px;text-align:left}
.b{padding:2px 8px;border-radius:10px;font-size:13px;border:1px solid currentColor}
.ok{color:var(--ok)}.bad{color:var(--bad)}.warn{color:var(--warn)}
pre{background:var(--code);padding:12px;overflow-x:auto;border-radius:6px;font-size:13px}
.add{background:var(--add)}.del{background:var(--del)}
.mut{color:var(--mut)}
"""

app = Flask(__name__)


def load_runs():
    runs = []
    for i, (label, results, folder) in enumerate(SOURCES):
        if not results.exists():
            continue
        for line in results.read_text().splitlines():
            if line.strip():
                r = json.loads(line)
                r["src"] = i
                runs.append(r)
    return runs


def page(title, body):
    return ("<!doctype html><meta charset=utf-8>"
            "<meta name=viewport content='width=device-width,initial-scale=1'>"
            "<title>" + html.escape(title) + "</title><style>" + CSS + CHART_CSS + "</style>" + body)


def badge(outcome):
    cls = {"verified": "ok", "false_fix": "bad"}.get(outcome, "warn")
    return "<span class='b " + cls + "'>" + html.escape(outcome) + "</span>"


def read(path):
    return path.read_text() if path.exists() else None


DEMO = ROOT / "demo_runs"

CAPTIONS = {
    "single/case01_sqli_super_2": "Verified. The AI's attack test failed on the vulnerable code, the patch passed it, and the hidden oracle confirmed the fix.",
    "single/case03_prefix_traversal_super_2": "False fix. The patch uses a plain startswith check, so a sibling folder such as files_private still passes. The AI's own test only tried ../secret.txt, so it passed, but the hidden oracle failed the patch.",
    "single/case03_prefix_traversal_lightning_1": "Truncated. The model's reasoning hit the 16,000-token output limit before it finished a test, so there is no usable test or patch.",
    "loop/case04_orderby_injection_super_2": "Retry rescued the run. The first test only checked that an unknown column raises ValueError, which is not an injection test, and was rejected. The second attempt used a weaker username-DESC test. The hidden oracle, which tries canary payloads, confirmed the final patch.",
    "loop/case04_orderby_injection_nano_2": "Rejected after a retry. Neither attempt produced a test that failed cleanly on the vulnerable code, so the run stopped before any patch.",
}


def run_dir(src, case, model, idx):
    name = f"{case}_{model}_{idx}"
    d = SOURCES[src][2] / name
    if d.exists():
        return d
    d = DEMO / ("loop" if src == 0 else "single") / name
    return d if d.exists() else None


def featured_html():
    items = []
    for key, text in CAPTIONS.items():
        kind, name = key.split("/")
        case, model, idx = name.rsplit("_", 2)
        src = 0 if kind == "loop" else 1
        url = f"/run/{src}/{case}/{model}/{idx}"
        items.append(f"<li><a href='{url}'>{html.escape(name)}</a> <span class=mut>({kind} agent)</span><br>{html.escape(text)}</li>")
    return "<h2>Featured runs</h2><ul>" + "".join(items) + "</ul>"


def findings_html():
    return (
        "<h2>What this project found</h2><ul>"
        "<li><b>One-shot fixes can hide real flaws.</b> Four NVIDIA Nemotron models patched code "
        "in a single call with no test. On the common flaws (cases 01, 02, 04, 05, 06), 99 of 100 "
        "patches were verified. On open redirect (case 08), all 20 patches passed the ordinary "
        "tests and failed a hidden oracle test.</li>"
        "<li><b>A hidden oracle catches what ordinary tests miss.</b> Across cases 03, 07 and 08 "
        "it flagged patches that looked correct and were not.</li>"
        "<li><b>The retry loop with an AI-written test did not help in these experiments.</b> "
        "Super and Ultra on five cases, five runs each: 33/50 verified against 36/50 one-shot, "
        "with overlapping 95% intervals, at about ten times the tokens.</li>"
        "<li><b>Why:</b> the AI-written attack tests cover attacks the model already knows. "
        "The case 08 tests we inspected did not include the ///evil.test form the oracle uses.</li>"
        "<li><b>What verified means.</b> In this benchmark it means the AI's test, the existing "
        "tests and a hidden oracle all passed. On real code there is no hidden oracle, so a "
        "verdict is only as strong as the AI-written test.</li></ul>"
        "<p class='mut'>Small samples: five runs per cell, eight hand-built cases. "
        "These are measurements of this setup, not a general benchmark.</p>"
    )


def diff_html(a, b):
    out = []
    for line in difflib.unified_diff(a.splitlines(), b.splitlines(),
                                     "vulnerable app.py", "patched app.py", lineterm=""):
        cls = ""
        if line.startswith("+") and not line.startswith("+++"):
            cls = "add"
        elif line.startswith("-") and not line.startswith("---"):
            cls = "del"
        out.append("<div class='" + cls + "'>" + html.escape(line) + "</div>")
    return "<pre>" + "".join(out) + "</pre>"


def summary_html():
    from collections import defaultdict
    stats = defaultdict(lambda: [0, 0, 0])  # verified, valid runs, false fixes
    for r in load_runs():
        if r["outcome"] == "infra_error":
            continue
        k = (r["src"], r["model"])
        stats[k][1] += 1
        stats[k][0] += r["outcome"] == "verified"
        stats[k][2] += r["outcome"] == "false_fix"
    rows = "".join(
        f"<tr><td>{SOURCES[src][0]}</td><td>{model}</td><td>{v}/{n}</td><td>{ff}</td></tr>"
        for (src, model), (v, n, ff) in sorted(stats.items()))
    return ("<h2>Results so far</h2><table><tr><th>agent</th><th>model</th>"
            "<th>verified</th><th>false fixes</th></tr>" + rows + "</table>"
            "<p class=mut>Small samples from a handful of hand-built cases, not a benchmark "
            "leaderboard. The loop agent was only run on one case, so its numbers are not "
            "comparable with the single-shot agent's. A false fix means the AI's own checks "
            "passed but a hidden test showed the flaw remained. Ultra was available when its runs were made but is no longer listed on the account (checked Oct 13, 2026). The two false fixes are one distinct patch returned twice. Truncated means the model hit the 16,000-token output limit set by the test harness.</p><h2>All runs</h2>")


@app.route("/")
def index():
    rows = []
    for r in load_runs():
        url = f"/run/{r['src']}/{r['case']}/{r['model']}/{r['run']}"
        link = f"<a href='{url}'>view</a>" if run_dir(r["src"], r["case"], r["model"], r["run"]) else ""
        rows.append(
            f"<tr><td>{SOURCES[r['src']][0]}</td><td>{r['case']}</td><td>{r['model']}</td>"
            f"<td>{r['run']}</td><td>{badge(r['outcome'])}</td><td>{r['tokens']}</td>"
            f"<td>{link}</td></tr>")
    body = ("<h1>PatchProof</h1><p class=mut>AI fixes that show their receipts. "
            "Runs that produced a patch were judged by a verifier and a hidden oracle test the AI never saw. Runs that ended earlier never reached the oracle.</p>"
            "" + findings_html() + heatmap_html() + comparison_html() + featured_html() + summary_html() + "<table><tr><th>agent</th><th>case</th><th>model</th><th>run</th>"
            "<th>outcome</th><th>tokens</th><th></th></tr>" + "".join(rows) + "</table>")
    return page("PatchProof runs", body)


@app.route("/run/<int:src>/<case>/<model>/<int:idx>")
def detail(src, case, model, idx):
    rec = next((r for r in load_runs() if r["src"] == src and r["case"] == case
                and r["model"] == model and r["run"] == idx), None)
    if rec is None:
        abort(404)
    d = run_dir(src, case, model, idx)
    if d is None:
        abort(404)
    before = read(d / "original" / "app.py")
    after = read(d / "patched" / "app.py")
    ai_test = read(d / "original" / "test_ai_security.py")
    body = (f"<p><a href='/'>&larr; all runs</a></p><h1>{case} / {model} / run {idx}</h1>"
            f"<p>{badge(rec['outcome'])} <span class=mut>{rec['tokens']} tokens, "
            f"{rec['seconds']}s, {SOURCES[src][0]}</span></p>")
    cap = CAPTIONS.get(f"{'loop' if src == 0 else 'single'}/{case}_{model}_{idx}")
    if cap:
        body += "<p>" + html.escape(cap) + "</p>"
    body += "<h2>Attack test written by the AI</h2>"
    body += ("<pre>" + html.escape(ai_test) + "</pre>") if ai_test else "<p class=mut>No test was saved.</p>"
    body += "<h2>Patch</h2>"
    if before and after:
        body += diff_html(before, after)
    else:
        body += "<p class=mut>No patch was produced in this run.</p>"
    return page(f"{case} {model} {idx}", body)


if __name__ == "__main__":
    app.run(port=5050)
