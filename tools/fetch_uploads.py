"""Copy every WordPress upload the built site uses into wp-content/uploads/.

Usage: python3 build.py && python3 tools/fetch_uploads.py

Scans site/ for https://www.pathfindersadvisors.com/wp-content/uploads/... and
downloads each file once, to the same path under this repo. The files keep their
old paths so the old image URLs still work after the domain moves to this site.
"""
import re
import sys
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SITE_DIR = ROOT / "site"
PREFIX = "https://www.pathfindersadvisors.com/wp-content/uploads/"
pat = re.compile(re.escape(PREFIX) + r"""[^"'\s<>)#?]+""")

urls = set()
for f in SITE_DIR.rglob("*.html"):
    urls.update(pat.findall(f.read_text(encoding="utf-8")))
got = skipped = 0
failed = []
for u in sorted(urls):
    dest = ROOT / "wp-content" / "uploads" / u[len(PREFIX):]
    if dest.exists() and dest.stat().st_size > 0:
        skipped += 1
        continue
    dest.parent.mkdir(parents=True, exist_ok=True)
    for attempt in range(3):
        try:
            req = urllib.request.Request(u, headers={"User-Agent": "Mozilla/5.0 (site migration)"})
            with urllib.request.urlopen(req, timeout=60) as r:
                dest.write_bytes(r.read())
            got += 1
            break
        except Exception as ex:  # noqa: BLE001
            if attempt == 2:
                failed.append((u, str(ex)))
            time.sleep(2)
    time.sleep(0.2)
print(f"{len(urls)} uploads referenced, {got} downloaded, {skipped} already here, {len(failed)} failed")
for u, ex in failed:
    print("FAILED", u, ex)
sys.exit(1 if failed else 0)
