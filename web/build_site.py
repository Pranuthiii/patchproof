"""Build the PatchProof site into docs/ straight from the result files (no server needed)."""
import difflib
import html
import json
import math
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "docs"
REPO = "https://github.com/Pranuthiii/patchproof"

CASES = [
    ("case01_sqli", "SQL injection"),
    ("case02_path_traversal", "Path traversal"),
    ("case03_prefix_traversal", "Prefix path traversal"),
    ("case04_orderby_injection", "ORDER BY injection"),
    ("case05_command_injection", "Command injection"),
    ("case06_unsafe_eval", "Unsafe eval"),
    ("case07_html_escape", "HTML escaping"),
    ("case08_open_redirect", "Open redirect"),
]
CASE_NAME = dict(CASES)
MODELS = ["lightning", "nano", "super", "ultra"]
MODEL_NAME = {"lightning": "Lightning", "nano": "Nano", "super": "Super", "ultra": "Ultra"}
AGENT_NAME = {"baseline": "one-shot fix", "single": "AI test + patch", "loop": "AI test + retries"}
RESULT_FILES = {
    "loop": "eval/results_loop.jsonl",
    "single": "eval/results.jsonl",
    "baseline": "eval/results_baseline.jsonl",
}

STEPS = [
    ("Finding", "A plain-English description of one vulnerability and the function it affects."),
    ("AI writes an attack test", "A Nemotron model writes a test that must fail on the vulnerable code."),
    ("AI writes the patch", "The model edits app.py only, and may retry using the verifier's output."),
    ("Sandbox verifier", "Plain code runs every test in Docker: no network, read-only files, dropped privileges."),
    ("Hidden oracle", "Benchmark only: a hand-written test the model never sees has the final say."),
]

CURATED = [
    dict(kind="baseline", case="case08_open_redirect", model="super", run=1, label="False fix", cls="bad",
         caption="The patch passed the existing tests. The hidden oracle rejected it because ///evil.test/ was still "
                 "accepted: Python's urlparse reports no host for that form, so the patch treated it as a relative path, "
                 "and browsers commonly resolve it as a link to another site."),
    dict(kind="single", case="case03_prefix_traversal", model="super", run=2, label="False fix", cls="bad",
         caption="The patch uses a plain startswith check, so a sibling folder such as files_private still passes. "
                 "The AI's own test only tried ../secret.txt, so it passed, but the hidden oracle failed the patch."),
    dict(kind="single", case="case01_sqli", model="super", run=2, label="Verified", cls="ok",
         caption="The AI's attack test failed on the vulnerable code, the patch passed it, and the hidden oracle "
                 "confirmed the fix."),
    dict(kind="loop", case="case04_orderby_injection", model="super", run=2, label="Retry rescued", cls="ok",
         caption="The first test only checked that an unknown column raises ValueError, which is not an injection test, "
                 "and was rejected. The second attempt used a weaker username-DESC test. The hidden oracle, which tries "
                 "canary payloads, confirmed the final patch."),
    dict(kind="loop", case="case04_orderby_injection", model="nano", run=2, label="Rejected", cls="warn",
         caption="Neither attempt produced a test that failed cleanly on the vulnerable code, so the run stopped "
                 "before any patch."),
    dict(kind="single", case="case03_prefix_traversal", model="lightning", run=1, label="Truncated", cls="warn",
         caption="The model's reasoning hit the 16,000-token output limit before it finished a test, so there is "
                 "no usable test or patch."),
]


def esc(s):
    return html.escape(str(s))


def jl(rel):
    p = ROOT / rel
    if not p.exists():
        return []
    return [json.loads(x) for x in p.read_text().splitlines() if x.strip()]


SUMMARY = json.loads((ROOT / "eval/summary.json").read_text())
B, L = SUMMARY["baseline"], SUMMARY["loop"]


def case_label(c):
    return f"{c[4:6]} {CASE_NAME.get(c, c)}"


def wilson(k, n, z=1.96):
    if n == 0:
        return 0.0, 0.0
    p = k / n
    d = 1 + z * z / n
    c = p + z * z / (2 * n)
    a = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))
    return (c - a) / d, (c + a) / d


def totals():
    common = {"case01_sqli", "case02_path_traversal", "case04_orderby_injection",
              "case05_command_injection", "case06_unsafe_eval"}
    hard = {"case03_prefix_traversal", "case07_html_escape", "case08_open_redirect"}
    st = dict(ok=0, n=0, ff8=0, n8=0, ffh=0, bok=0, bn=0, bff=0, btk=0, lok=0, ln=0, lff=0, ltk=0)
    for key, c in B.items():
        case = key.split("|")[0]
        if case in common:
            st["ok"] += c["ok"]; st["n"] += c["n"]
        if case == "case08_open_redirect":
            st["ff8"] += c["ff"]; st["n8"] += c["n"]
        if case in hard:
            st["ffh"] += c["ff"]
    for key, c in L.items():
        b = B.get(key)
        if not b:
            continue
        st["lok"] += c["ok"]; st["ln"] += c["n"]; st["lff"] += c["ff"]; st["ltk"] += c["tokens"]
        st["bok"] += b["ok"]; st["bn"] += b["n"]; st["bff"] += b["ff"]; st["btk"] += b["tokens"]
    st["ratio"] = (st["ltk"] / max(st["ln"], 1)) / max(st["btk"] / max(st["bn"], 1), 1)
    return st


CSS = """
*{box-sizing:border-box}
html{scroll-behavior:smooth}
:root{--bg:#f4f1ea;--paper:#fffdf8;--ink:#17181c;--mut:#5f6470;--line:#e2ddd0;--brand:#1f4fd8;--ok:#0b7a3b;--bad:#c4161c;--warn:#9a6700;--code:#f3efe4;--add:#dff3e4;--del:#fbe3e1;--shadow:0 1px 0 rgba(0,0,0,.04),0 12px 32px rgba(40,30,10,.10)}
@media (prefers-color-scheme:dark){:root{--bg:#0c0f14;--paper:#161a22;--ink:#eceff4;--mut:#9aa3b2;--line:#262d3a;--brand:#7ea2ff;--ok:#43c46a;--bad:#ff6b6b;--warn:#e0a526;--code:#0f1319;--add:#12311f;--del:#3b171b;--shadow:0 12px 32px rgba(0,0,0,.4)}}
body{margin:0;background:var(--bg);color:var(--ink);font:16px/1.65 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif}
.wrap{max-width:1080px;margin:0 auto;padding:0 22px}
a{color:var(--brand);text-decoration:none}
a:hover{text-decoration:underline}
nav{position:sticky;top:0;z-index:20;background:var(--bg);border-bottom:1px solid var(--line)}
.bar{display:flex;align-items:center;justify-content:space-between;height:58px;gap:12px}
.brand{font-weight:800;font-size:18px;color:var(--ink);letter-spacing:-.01em}
.brand:hover{text-decoration:none}
.links{display:flex;gap:18px;font-size:14px;flex-wrap:wrap}
.links a{color:var(--mut)}
.links a:hover{color:var(--ink);text-decoration:none}
.hero{display:grid;grid-template-columns:1.1fr .9fr;gap:44px;align-items:center;padding:64px 0 28px}
.eyebrow{font-size:12.5px;font-weight:700;letter-spacing:.06em;text-transform:uppercase;color:var(--brand);margin:0 0 12px}
h1{font-size:clamp(36px,6vw,58px);line-height:1.04;margin:0 0 18px;letter-spacing:-.025em}
h2{font-size:28px;margin:0 0 6px;letter-spacing:-.015em}
h3{font-size:17px;margin:0 0 6px}
.lead{font-size:19px;color:var(--mut);margin:0 0 26px;max-width:620px}
.mut{color:var(--mut)}
.cta{display:flex;gap:12px;flex-wrap:wrap}
.btn{display:inline-block;padding:11px 20px;border-radius:10px;font-weight:700;font-size:15px;border:1px solid var(--ink);color:var(--ink)}
.btn.primary{background:var(--ink);color:var(--bg)}
.btn:hover{text-decoration:none;opacity:.88}
section{margin:72px 0}
.stats{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:14px;margin:30px 0 0}
.card{background:var(--paper);border:1px solid var(--line);border-radius:14px;padding:20px;box-shadow:var(--shadow);color:var(--ink)}
.stat .num{font-size:32px;font-weight:800;letter-spacing:-.02em;line-height:1.1}
.stat .cap{font-size:14px;color:var(--mut);margin-top:6px}
.grid3{display:grid;grid-template-columns:repeat(auto-fit,minmax(290px,1fr));gap:14px;margin-top:16px}
.grid2{display:grid;grid-template-columns:repeat(auto-fit,minmax(340px,1fr));gap:14px;margin-top:16px}
.card p{margin:0;font-size:15px;color:var(--mut)}
.callout{border:1px solid var(--line);border-left:4px solid var(--brand);background:var(--paper);border-radius:10px;padding:14px 18px;margin-top:14px;font-size:15px}
.flow{display:grid;grid-template-columns:repeat(5,1fr);gap:16px;margin-top:18px;padding:0;list-style:none;counter-reset:s}
.node{position:relative;background:var(--paper);border:1px solid var(--line);border-radius:14px;padding:16px;box-shadow:var(--shadow);counter-increment:s}
.node::before{content:counter(s);display:inline-flex;align-items:center;justify-content:center;width:28px;height:28px;border-radius:50%;background:var(--brand);color:var(--bg);font-weight:800;font-size:14px;margin-bottom:8px}
.node:not(:last-child)::after{content:"\\2192";position:absolute;right:-15px;top:50%;transform:translateY(-50%);color:var(--mut);font-size:18px}
.node p{margin:0;font-size:13.5px;color:var(--mut)}
.node h3{font-size:15px}
.receipt{background:var(--paper);font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;font-size:14px;padding:22px 22px 26px;border-radius:6px;box-shadow:var(--shadow);max-width:390px;margin:0 auto;transform:rotate(1.2deg);border-bottom:3px dashed var(--line)}
.rh{font-weight:800;letter-spacing:.14em;text-align:center}
.rs{text-align:center;color:var(--mut);font-size:12.5px;margin-top:4px}
.rule{border-top:2px dashed var(--line);margin:14px 0}
.line{display:flex;align-items:baseline;gap:6px;margin:6px 0}
.line i{flex:1;border-bottom:2px dotted var(--mut);opacity:.45;transform:translateY(-3px)}
.note{font-size:12.5px;color:var(--mut);margin:-2px 0 6px 12px}
.verdict{display:flex;justify-content:space-between;align-items:center;margin-top:6px}
.foot{margin-top:14px;font-size:11.5px;color:var(--mut);text-align:center}
.stamp{display:inline-block;border:3px solid currentColor;border-radius:6px;padding:2px 10px;font-weight:800;letter-spacing:.06em;transform:rotate(-6deg);text-transform:uppercase}
.tabs{display:flex;gap:8px;justify-content:center;margin:0 0 18px}
.tabs button{font:inherit;font-size:13px;font-weight:700;padding:6px 14px;border-radius:999px;border:1px solid var(--line);background:var(--paper);color:var(--mut);cursor:pointer}
.tabs button.on{background:var(--ink);color:var(--bg);border-color:var(--ink)}
.ok{color:var(--ok)}.bad{color:var(--bad)}.warn{color:var(--warn)}
.badge{display:inline-block;padding:2px 10px;border-radius:999px;font-size:12px;font-weight:700;border:1px solid currentColor;margin-right:8px}
.ledgerwrap{overflow-x:auto}
.ledger{border-collapse:separate;border-spacing:6px;width:100%}
.ledger th{font-size:13px;color:var(--mut);font-weight:600}
.ledger th[scope=row]{text-align:left;color:var(--ink);white-space:nowrap;font-size:14px}
.cell{background:hsl(var(--r) 52% 36%);color:#fff;border-radius:8px;text-align:center;padding:10px 4px;min-width:84px;line-height:1.25}
.cell b{font-size:15px}
.cell small{display:block;font-size:11px;opacity:.92}
.none{text-align:center;color:var(--mut)}
.legend{font-size:13px;color:var(--mut);margin-top:10px}
.bar2{display:grid;grid-template-columns:200px 1fr;gap:6px 18px;align-items:start;margin:20px 0}
.track{position:relative;height:30px;background:var(--code);border-radius:8px;overflow:hidden}
.fill{position:absolute;left:0;top:0;bottom:0;background:var(--brand);opacity:.85}
.whisk{position:absolute;top:50%;height:4px;margin-top:-2px;background:var(--ink);border-radius:2px}
.bt{font-size:13px;color:var(--mut);margin-top:6px}
.feat{display:block;transition:transform .12s,border-color .12s}
.feat:hover{transform:translateY(-3px);border-color:var(--brand);text-decoration:none}
.feat h3{margin-top:10px}
.feat p{margin:6px 0 12px}
.more{font-size:14px;font-weight:700;color:var(--brand)}
.hood{display:grid;grid-template-columns:repeat(auto-fit,minmax(300px,1fr));gap:14px;margin-top:16px}
ul.tight{margin:10px 0 0;padding-left:20px}
ul.tight li{margin:6px 0;color:var(--mut);font-size:15px}
pre{background:var(--code);border:1px solid var(--line);padding:14px;overflow-x:auto;border-radius:10px;font-size:13px;line-height:1.5}
.add{background:var(--add)}.del{background:var(--del)}
.detail h1{font-size:34px;margin-top:6px}
footer{border-top:1px solid var(--line);margin-top:80px;padding:30px 0;color:var(--mut);font-size:14px}
@media (max-width:900px){
.hero{grid-template-columns:1fr;gap:34px;padding-top:36px}
.flow{grid-template-columns:1fr}
.node:not(:last-child)::after{display:none}
.bar2{grid-template-columns:1fr}
.receipt{transform:none}
}
"""

JS = """
document.querySelectorAll('[data-tab]').forEach(function(b){
  b.addEventListener('click',function(){
    document.querySelectorAll('[data-tab]').forEach(function(x){x.classList.toggle('on',x===b)});
    document.querySelectorAll('[data-pane]').forEach(function(p){p.hidden=p.getAttribute('data-pane')!==b.getAttribute('data-tab')});
  });
});
"""


def receipt_html(sub, rows, verdict, cls, foot):
    lines = ""
    for label, status, note in rows:
        c = "ok" if status == "PASS" else "bad"
        lines += (f"<div class='line'><span>{esc(label)}</span><i></i><b class='{c}'>{status}</b></div>"
                  + (f"<div class='note'>{esc(note)}</div>" if note else ""))
    return ("<div class='receipt'><div class='rh'>PATCHPROOF RECEIPT</div>"
            f"<div class='rs'>{esc(sub)}</div><div class='rule'></div>{lines}<div class='rule'></div>"
            f"<div class='verdict'><span>VERDICT</span><b class='stamp {cls}'>{esc(verdict)}</b></div>"
            f"<div class='foot'>{esc(foot)}</div></div>")


def ledger_html():
    head = "".join(f"<th>{MODEL_NAME[m]}</th>" for m in MODELS)
    rows = []
    for case, _ in CASES:
        cells = []
        for m in MODELS:
            c = B.get(f"{case}|{m}")
            if not c or not c["n"]:
                cells.append("<td class='none'>-</td>")
                continue
            rate = c["ok"] / c["n"]
            ff = ""
            if c["ff"]:
                ff = "<small>" + str(c["ff"]) + (" false fix" if c["ff"] == 1 else " false fixes") + "</small>"
            tip = f"{c['ok']} of {c['n']} verified, {c['ff']} false fixes"
            cells.append(f"<td><div class='cell' style='--r:{int(120 * rate)}' title='{esc(tip)}'>"
                         f"<b>{c['ok']}/{c['n']}</b>{ff}</div></td>")
        rows.append(f"<tr><th scope='row'>{esc(case_label(case))}</th>{''.join(cells)}</tr>")
    return ("<div class='ledgerwrap'><table class='ledger'><thead><tr><th></th>" + head
            + "</tr></thead><tbody>" + "".join(rows) + "</tbody></table></div>"
            "<p class='legend'>Verified runs out of five. Green is all verified, red is none. "
            "A false fix passed the existing tests and failed the hidden oracle.</p>")


def compare_html(st):
    out = ""
    for label, ok, n, ff, tk in (("One-shot fix (no test)", st["bok"], st["bn"], st["bff"], st["btk"]),
                                 ("AI test + retries", st["lok"], st["ln"], st["lff"], st["ltk"])):
        if not n:
            continue
        lo, hi = wilson(ok, n)
        out += (f"<div class='bar2'><div><b>{esc(label)}</b></div><div><div class='track'>"
                f"<div class='fill' style='width:{100 * ok / n:.1f}%'></div>"
                f"<div class='whisk' style='left:{100 * lo:.1f}%;width:{100 * (hi - lo):.1f}%'></div></div>"
                f"<div class='bt'>{ok}/{n} verified ({100 * ok / n:.0f}%). 95% interval {100 * lo:.0f}% to "
                f"{100 * hi:.0f}% (the black line). {ff} false fixes, about {tk // n} tokens per run.</div></div></div>")
    return out


def featured_cards():
    items = ""
    for c in CURATED:
        d = ROOT / "demo_runs" / c["kind"] / f"{c['case']}_{c['model']}_{c['run']}"
        if not d.exists():
            continue
        href = f"run/{c['kind']}/{c['case']}/{c['model']}/{c['run']}/index.html"
        items += (f"<a class='card feat' href='{href}'><div><span class='badge {c['cls']}'>{esc(c['label'])}</span>"
                  f"<span class='mut'>{esc(case_label(c['case']))}</span></div>"
                  f"<h3>{esc(MODEL_NAME[c['model']])} &middot; run {c['run']} &middot; {esc(AGENT_NAME[c['kind']])}</h3>"
                  f"<p>{esc(c['caption'])}</p><span class='more'>Open the receipt &rarr;</span></a>")
    return items


def page(title, body, depth):
    base = "" if depth == 0 else "../" * depth + "index.html"
    nav = (f"<nav><div class='wrap bar'><a class='brand' href='{base or '#top'}'>PatchProof</a><div class='links'>"
           f"<a href='{base}#findings'>Findings</a><a href='{base}#how'>How it works</a>"
           f"<a href='{base}#ledger'>Ledger</a><a href='{base}#receipts'>Receipts</a>"
           f"<a href='{base}#hood'>Under the hood</a><a href='{REPO}'>GitHub</a></div></div></nav>")
    foot = ("<footer><div class='wrap'>PatchProof &middot; built for the Nebius x NVIDIA Global AI Hackathon "
            "(Coding and Agentic Engineering). NVIDIA Nemotron models served through Nebius Token Factory, plus "
            f"Tavily web search. MIT licensed. <a href='{REPO}'>Source code</a></div></footer>")
    return ("<!doctype html><html lang='en'><head><meta charset='utf-8'>"
            "<meta name='viewport' content='width=device-width,initial-scale=1'>"
            f"<title>{esc(title)}</title><style>{CSS}</style></head>"
            f"<body id='top'>{nav}<main class='wrap'>{body}</main>{foot}<script>{JS}</script></body></html>")


def index_page(st):
    lm = sorted({k.split("|")[1] for k in L}, key=MODELS.index)
    lc = {k.split("|")[0] for k in L}
    b_lo, b_hi = wilson(st["bok"], st["bn"])
    l_lo, l_hi = wilson(st["lok"], st["ln"])
    overlap = b_lo <= l_hi and l_lo <= b_hi
    names = ", ".join(MODEL_NAME[m] for m in lm)
    if overlap:
        loop_title = "An AI-written test and retries did not measurably help"
        loop_text = (f"{names} on {len(lc)} cases: {st['lok']}/{st['ln']} verified with the loop against "
                     f"{st['bok']}/{st['bn']} one-shot. The 95% intervals overlap, at about {st['ratio']:.0f}x the tokens.")
    else:
        more = st["lok"] / max(st["ln"], 1) > st["bok"] / max(st["bn"], 1)
        loop_title = "The retry loop verified " + ("more" if more else "fewer") + " patches"
        loop_text = (f"{names} on {len(lc)} cases: {st['lok']}/{st['ln']} verified with the loop against "
                     f"{st['bok']}/{st['bn']} one-shot, at about {st['ratio']:.0f}x the tokens.")

    bad = receipt_html("Open redirect | Nemotron Super | one-shot fix",
                       [("Existing tests", "PASS", ""),
                        ("Hidden oracle test", "FAIL", "still accepted ///evil.test/")],
                       "FALSE FIX", "bad", "recorded run, the oracle is never shown to the model")
    good = receipt_html("SQL injection | Nemotron Super | AI test + patch",
                        [("AI attack test fails on old code", "PASS", ""),
                         ("AI attack test passes on patch", "PASS", ""),
                         ("Existing tests", "PASS", ""),
                         ("Hidden oracle test", "PASS", "")],
                        "VERIFIED", "ok", "recorded run, the oracle is never shown to the model")

    stats = [(f"{st['ok']}/{st['n']}", "patches verified on five common flaw types"),
             (f"{st['ff8']}/{st['n8']}", "open-redirect patches passed the existing tests and failed the hidden oracle"),
             (str(st["ffh"]), "false fixes caught across the three subtle cases"),
             (f"{st['bok']}/{st['bn']} vs {st['lok']}/{st['ln']}", "verified: one-shot fix vs retry loop")]
    stat_html = "".join(f"<div class='card stat'><div class='num'>{esc(n)}</div><div class='cap'>{esc(c)}</div></div>"
                        for n, c in stats)
    find = [("One-shot fixes pass easy cases and fail subtle ones",
             f"{st['ok']} of {st['n']} patches were verified on five common flaw types. On open redirect, "
             f"{st['ff8']} of {st['n8']} passed the existing tests and failed the hidden oracle."),
            ("A hidden oracle catches what ordinary tests miss",
             f"On the prefix-traversal, HTML-escaping and open-redirect cases it flagged {st['ffh']} patches "
             "that looked correct and were not."),
            (loop_title, loop_text)]
    find_html = "".join(f"<div class='card'><h3>{esc(t)}</h3><p>{esc(x)}</p></div>" for t, x in find)
    flow = "".join(f"<li class='node'><h3>{esc(t)}</h3><p>{esc(d)}</p></li>" for t, d in STEPS)

    hood = [
        ("Models", ["NVIDIA Nemotron Lightning, Nano, Super and Ultra, through the Nebius Token Factory API.",
                    "Tool calling worked on all four. Reasoning tokens count against the output cap."]),
        ("Sandbox", ["Docker with no network, a read-only root filesystem, dropped Linux capabilities and a non-root user.",
                     "Memory, CPU and process limits, plus a 45 second timeout inside the container."]),
        ("Verifier", ["Plain code decides pass or fail, never the model.",
                      "Test files are hash-checked so a patch cannot edit the tests it is judged by."]),
        ("Tavily", ["A runtime web search adds advisory context to the test-writer in one agent variant.",
                    "In a 12-run test on one case the results were mixed, so we report no measured benefit."]),
        ("Evidence", ["Every result file, the eight cases and their reference fixes are in the repository.",
                      f"<a href='{REPO}/blob/main/eval/summary.md'>Read the full summary table</a>."]),
    ]
    hood_html = ""
    for title, lines in hood:
        hood_html += (f"<div class='card'><h3>{esc(title)}</h3><ul class='tight'>"
                      + "".join(f"<li>{x if '<a ' in x else esc(x)}</li>" for x in lines) + "</ul></div>")

    limits = [
        "Small samples: five runs per cell and eight hand-built cases. These measure this setup and are not a general benchmark.",
        "In the benchmark, verified means the AI's test, the existing tests and a hidden oracle all passed. On real code there is no hidden oracle, so a verdict is only as strong as the AI-written test.",
        "Ultra was available when its runs were made but was no longer listed on the account when checked on Oct 13, 2026.",
        "The early experiments used the API's default temperature, where Super sometimes returned identical replies. The main evaluation used temperature 0.7.",
        "Truncated means the model hit the 16,000-token output limit set by the test harness.",
        "This page shows recorded runs. The agent itself runs locally with Docker.",
    ]
    limits_html = "<ul class='tight'>" + "".join(f"<li>{esc(x)}</li>" for x in limits) + "</ul>"

    body = (
        "<header class='hero'><div>"
        "<p class='eyebrow'>Nebius x NVIDIA Global AI Hackathon &middot; Coding and Agentic Engineering</p>"
        "<h1>AI fixes that show their receipts.</h1>"
        "<p class='lead'>PatchProof runs AI-written security patches in a locked-down sandbox and judges them against a "
        "test the model never saw. We measured four NVIDIA Nemotron models on eight hand-built vulnerabilities. "
        "Patches that look fine are sometimes still wrong.</p>"
        f"<div class='cta'><a class='btn primary' href='#findings'>See what we found</a>"
        f"<a class='btn' href='{REPO}'>Source on GitHub</a></div></div>"
        "<div><div class='tabs'><button class='on' data-tab='bad'>False fix</button>"
        "<button data-tab='good'>Verified</button></div>"
        f"<div data-pane='bad'>{bad}</div><div data-pane='good' hidden>{good}</div></div></header>"
        f"<div class='stats'>{stat_html}</div>"
        f"<section id='findings'><h2>What we found</h2><div class='grid3'>{find_html}</div>"
        "<div class='callout'><b>Why the AI-written test is the weak link.</b> It covers attacks the model already knows. "
        "The open-redirect tests we inspected did not include the ///evil.test form the oracle uses.</div>"
        "<div class='callout'><b>A negative result we kept.</b> We also tried asking the model to red-team its own patch. "
        "In the one run we inspected it invented bypasses that were really the allowed host, so we did not pursue it.</div></section>"
        f"<section id='how'><h2>How it works</h2><p class='mut'>Every run follows the same pipeline.</p>"
        f"<ol class='flow'>{flow}</ol></section>"
        f"<section id='ledger'><h2>The ledger</h2><p class='mut'>One-shot fixes: four models, eight cases.</p>"
        f"<div class='card'>{ledger_html()}</div>"
        f"<h2 style='margin-top:40px'>Does the retry loop help?</h2>"
        f"<p class='mut'>The black line is the 95% interval. Overlapping lines mean this data cannot separate the two.</p>"
        f"<div class='card'>{compare_html(st)}</div></section>"
        f"<section id='receipts'><h2>Receipts</h2><p class='mut'>Real runs, saved as recorded. Open one to see the "
        f"AI's test and the patch.</p><div class='grid2'>{featured_cards()}</div></section>"
        f"<section id='hood'><h2>Under the hood</h2><div class='hood'>{hood_html}</div></section>"
        f"<section id='limits'><h2>Limits</h2>{limits_html}</section>"
    )
    return page("PatchProof: AI fixes that show their receipts", body, 0)


def find_run(c):
    for r in jl(RESULT_FILES[c["kind"]]):
        if r["case"] == c["case"] and r["model"] == c["model"] and r["run"] == c["run"]:
            return r
    return {}


def diff_html(a, b):
    out = ""
    for line in difflib.unified_diff(a.splitlines(), b.splitlines(), "vulnerable app.py", "patched app.py", lineterm=""):
        cls = ""
        if line.startswith("+") and not line.startswith("+++"):
            cls = "add"
        elif line.startswith("-") and not line.startswith("---"):
            cls = "del"
        out += f"<div class='{cls}'>{esc(line)}</div>"
    return "<pre>" + out + "</pre>"


def detail_page(c, d):
    rec = find_run(c)

    def rd(rel):
        p = d / rel
        return p.read_text() if p.exists() else None

    before, after, ai_test = rd("original/app.py"), rd("patched/app.py"), rd("original/test_ai_security.py")
    meta = f"{MODEL_NAME[c['model']]} &middot; run {c['run']} &middot; {esc(AGENT_NAME[c['kind']])}"
    if rec:
        meta += f" &middot; {rec['tokens']} tokens &middot; {rec['seconds']}s"
    body = ("<div class='detail'><p style='margin-top:28px'><a href='../../../../../index.html'>&larr; All results</a></p>"
            f"<h1>{esc(case_label(c['case']))}</h1>"
            f"<p><span class='badge {c['cls']}'>{esc(c['label'])}</span><span class='mut'>{meta}</span></p>"
            f"<div class='callout'>{esc(c['caption'])}</div>")
    body += "<h2 style='margin-top:30px'>Attack test written by the AI</h2>"
    if ai_test:
        body += "<pre>" + esc(ai_test) + "</pre>"
    elif c["kind"] == "baseline":
        body += "<p class='mut'>None. The one-shot baseline writes the patch directly, with no test.</p>"
    else:
        body += "<p class='mut'>No test was saved for this run.</p>"
    body += "<h2 style='margin-top:30px'>Patch</h2>"
    body += diff_html(before, after) if (before and after) else "<p class='mut'>No patch was produced in this run.</p>"
    body += "</div>"
    return page(f"{case_label(c['case'])} | PatchProof", body, 5)


def main():
    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir()
    (OUT / ".nojekyll").write_text("")
    (OUT / "index.html").write_text(index_page(totals()), encoding="utf-8")
    n = 0
    for c in CURATED:
        d = ROOT / "demo_runs" / c["kind"] / f"{c['case']}_{c['model']}_{c['run']}"
        if not d.exists():
            print("missing demo run:", d)
            continue
        out = OUT / "run" / c["kind"] / c["case"] / c["model"] / str(c["run"])
        out.mkdir(parents=True)
        (out / "index.html").write_text(detail_page(c, d), encoding="utf-8")
        n += 1
    print(f"docs/index.html written, {n} run pages")


if __name__ == "__main__":
    main()
