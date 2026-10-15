"""Render the viewer to static HTML in docs/ (for GitHub Pages)."""
import re
import shutil
import sys
from pathlib import Path

sys.path.insert(0, "web")
import server

# Only curated runs in demo_runs/ get detail pages in the static copy.
server.SOURCES = [(label, results, Path("/nonexistent")) for (label, results, _) in server.SOURCES]

out = Path("docs")
if out.exists():
    shutil.rmtree(out)
out.mkdir()
(out / ".nojekyll").write_text("")
client = server.app.test_client()

html = client.get("/").get_data(as_text=True)
pages = sorted(set(re.findall(r"href='/run/([^']+)'", html)))
index = re.sub(r"href='/run/([^']+)'", r"href='run/\1/index.html'", html)
(out / "index.html").write_text(index)

count = 0
for p in pages:
    r = client.get("/run/" + p)
    if r.status_code != 200:
        print("skipped", p, r.status_code)
        continue
    d = out / "run" / p
    d.mkdir(parents=True, exist_ok=True)
    page = r.get_data(as_text=True).replace("href='/'", "href='../../../../../index.html'")
    (d / "index.html").write_text(page)
    count += 1
print("index.html written;", count, "run pages")
