"""PatchProof viewer: browse recorded agent runs."""
import difflib
import html
import json
from pathlib import Path

from flask import Flask, abort

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
            "<title>" + html.escape(title) + "</title><style>" + CSS + "</style>" + body)


def badge(outcome):
    cls = {"verified": "ok", "false_fix": "bad"}.get(outcome, "warn")
    return "<span class='b " + cls + "'>" + html.escape(outcome) + "</span>"


def read(path):
    return path.read_text() if path.exists() else None


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


@app.route("/")
def index():
    rows = []
    for r in load_runs():
        url = f"/run/{r['src']}/{r['case']}/{r['model']}/{r['run']}"
        rows.append(
            f"<tr><td>{SOURCES[r['src']][0]}</td><td>{r['case']}</td><td>{r['model']}</td>"
            f"<td>{r['run']}</td><td>{badge(r['outcome'])}</td><td>{r['tokens']}</td>"
            f"<td><a href='{url}'>view</a></td></tr>")
    body = ("<h1>PatchProof</h1><p class=mut>AI fixes that show their receipts. "
            "Every run below was judged by a verifier and a hidden oracle test.</p>"
            "<table><tr><th>agent</th><th>case</th><th>model</th><th>run</th>"
            "<th>outcome</th><th>tokens</th><th></th></tr>" + "".join(rows) + "</table>")
    return page("PatchProof runs", body)


@app.route("/run/<int:src>/<case>/<model>/<int:idx>")
def detail(src, case, model, idx):
    rec = next((r for r in load_runs() if r["src"] == src and r["case"] == case
                and r["model"] == model and r["run"] == idx), None)
    if rec is None:
        abort(404)
    d = SOURCES[src][2] / f"{case}_{model}_{idx}"
    if not d.exists():
        abort(404)
    before = read(d / "original" / "app.py")
    after = read(d / "patched" / "app.py")
    ai_test = read(d / "original" / "test_ai_security.py")
    body = (f"<p><a href='/'>&larr; all runs</a></p><h1>{case} / {model} / run {idx}</h1>"
            f"<p>{badge(rec['outcome'])} <span class=mut>{rec['tokens']} tokens, "
            f"{rec['seconds']}s, {SOURCES[src][0]}</span></p>")
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
