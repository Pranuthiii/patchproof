"""HTML fragments (heat map and comparison bars) built from eval/summary.json."""
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MODELS = ["lightning", "nano", "super", "ultra"]
LABEL = {
    "case01_sqli": "01 SQL injection",
    "case02_path_traversal": "02 Path traversal",
    "case03_prefix_traversal": "03 Prefix path traversal",
    "case04_orderby_injection": "04 ORDER BY injection",
    "case05_command_injection": "05 Command injection",
    "case06_unsafe_eval": "06 Unsafe eval",
    "case07_html_escape": "07 HTML escaping",
    "case08_open_redirect": "08 Open redirect",
}

CHART_CSS = """
.heat{border-collapse:separate;border-spacing:4px;width:100%}
.heat th{font-weight:600;font-size:13px;color:var(--mut,#666);text-align:center;padding:4px}
.heat th.row{text-align:left}
.heat td.cell{text-align:center;padding:10px 4px;border-radius:6px;color:#fff;font-weight:600;min-width:84px}
.heat td.cell small{display:block;font-weight:400;opacity:.9;font-size:11px}
.heat td.none{text-align:center;color:var(--mut,#666)}
.bars .row{display:flex;align-items:center;gap:12px;margin:10px 0}
.bars .name{width:200px;font-size:14px}
.bars .track{flex:1;background:var(--code,#f1f1f1);border-radius:6px;height:26px;position:relative}
.bars .fill{height:100%;border-radius:6px;background:var(--ok,#1a7f37)}
.bars .val{width:200px;font-size:13px;color:var(--mut,#666)}
"""


def wilson(k, n, z=1.96):
    if n == 0:
        return 0.0, 0.0
    p = k / n
    d = 1 + z * z / n
    c = p + z * z / (2 * n)
    a = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))
    return (c - a) / d, (c + a) / d


def load():
    p = ROOT / "eval/summary.json"
    return json.loads(p.read_text()) if p.exists() else {"baseline": {}, "loop": {}}


def heatmap_html(data=None):
    data = data or load()
    base = data["baseline"]
    head = "".join(f"<th>{m}</th>" for m in MODELS)
    rows = []
    for case, label in LABEL.items():
        cells = []
        for m in MODELS:
            c = base.get(f"{case}|{m}")
            if not c or not c["n"]:
                cells.append("<td class='none'>-</td>")
                continue
            rate = c["ok"] / c["n"]
            ff = f"<small>{c['ff']} false fix{'es' if c['ff'] != 1 else ''}</small>" if c["ff"] else ""
            cells.append(
                f"<td class='cell' style='background:hsl({int(120 * rate)} 55% 36%)'>"
                f"{c['ok']}/{c['n']}{ff}</td>")
        rows.append(f"<tr><th class='row'>{label}</th>{''.join(cells)}</tr>")
    return ("<h2>One-shot fixes by case</h2>"
            "<p class='mut'>Verified runs out of 5 when a model patches the code in one call with no test. "
            "Judged by the normal tests plus a hidden oracle test the model never sees.</p>"
            f"<table class='heat'><tr><th></th>{head}</tr>{''.join(rows)}</table>")


def comparison_html(data=None):
    data = data or load()
    tot = {"baseline": [0, 0, 0, 0], "loop": [0, 0, 0, 0]}
    for key, c in data["loop"].items():
        b = data["baseline"].get(key)
        if not b:
            continue
        for name, cell in (("baseline", b), ("loop", c)):
            t = tot[name]
            t[0] += cell["ok"]; t[1] += cell["n"]; t[2] += cell["ff"]; t[3] += cell["tokens"]
    out = []
    for name, label in (("baseline", "One-shot fix, no test"), ("loop", "Loop agent (AI test + retries)")):
        ok, n, ff, tk = tot[name]
        if not n:
            continue
        lo, hi = wilson(ok, n)
        out.append(
            f"<div class='row'><div class='name'>{label}</div>"
            f"<div class='track'><div class='fill' style='width:{100 * ok / n:.0f}%'></div></div>"
            f"<div class='val'>{ok}/{n} verified ({100 * ok / n:.0f}%), 95% interval "
            f"{100 * lo:.0f}% to {100 * hi:.0f}%, {ff} false fixes, ~{tk // n} tokens per run</div></div>")
    return ("<h2>Does the retry loop help?</h2>"
            "<p class='mut'>Super and Ultra on five cases, five runs each. "
            "The intervals overlap, so this data does not show a difference.</p>"
            f"<div class='bars'>{''.join(out)}</div>")
