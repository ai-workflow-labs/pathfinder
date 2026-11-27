"""Write src/data/llms.json from the old site's llms.txt (made by Rank Math).

Usage: python tools/import_llms.py <old-site-folder>   (reads <old-site>/files/llms.txt)

Keeps: the site title line, the one-line description used for each post and page
(by path), the old order of the Pages section, and, verbatim, the lines for the
course platform (LearnDash / BuddyBoss pages, courses, lessons, quizzes). Those
pages are not built by this site; they are served by WordPress until the
platform decision, so their lines are copied as they were.
"""
import html
import json
import re
import sys
from pathlib import Path

SITE = "https://www.pathfindersadvisors.com"
OLD = Path(sys.argv[1])
DATA = Path(__file__).resolve().parent.parent / "src" / "data"
text = (OLD / "files" / "llms.txt").read_text(encoding="utf-8")

sections, cur = {}, None
for line in text.splitlines():
    if line.startswith("# "):
        title = line[2:].strip()
    elif line.startswith("## "):
        cur = line[3:].strip()
        sections[cur] = []
    elif cur and line.startswith("- ["):
        sections[cur].append(line)

LINE = re.compile(r"^- \[(.*?)\]\((https?://[^)]+)\)(?::\s*(.*))?$")
desc, names, page_order, lms_pages = {}, {}, [], []
LMS_PATHS = {"/login/", "/members/", "/my-profile/"}
for sec in ("Posts", "Pages"):
    for line in sections.get(sec, []):
        m = LINE.match(line)
        path = m.group(2).replace(SITE, "")
        names[path] = html.unescape(m.group(1)).strip()
        desc[path] = html.unescape(m.group(3) or "").strip()
        if sec == "Pages":
            if path in LMS_PATHS:
                lms_pages.append(line)
            else:
                page_order.append(path)
lms = {k: sections.get(k, []) for k in ("Courses", "Lessons", "Quizzes")}
out = {"_about": "From the old llms.txt (Rank Math), captured 2026-11-27. lms_* lines are pages on the course platform, not built by this site.",
       "title": title, "names": names, "desc": desc, "page_order": page_order, "lms_pages": lms_pages, "lms_sections": lms}
(DATA / "llms.json").write_text(json.dumps(out, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
print(len(desc), "descriptions,", len(page_order), "pages,", len(lms_pages), "platform pages,", {k: len(v) for k, v in lms.items()})
