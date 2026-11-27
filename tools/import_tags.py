"""Write src/data/tags.json from the old site capture.

Usage: python tools/import_tags.py <old-site-folder>

Every WordPress tag (rest/tags.json) with its old archive URL /tag/<slug>/, its
name, and the slugs of the posts that carry it (rest/posts.json), newest first.
The old tag archives were "follow, noindex" with no description and no
canonical, and their title was "<name> - Pathfinders Advisors".
"""
import html
import json
import sys
from pathlib import Path

OLD = Path(sys.argv[1])
DATA = Path(__file__).resolve().parent.parent / "src" / "data"

tags = json.loads((OLD / "rest" / "tags.json").read_text(encoding="utf-8"))
posts = sorted(json.loads((OLD / "rest" / "posts.json").read_text(encoding="utf-8")), key=lambda p: p["date"], reverse=True)
out = []
for t in sorted(tags, key=lambda t: t["slug"]):
    name = html.unescape(t["name"])
    out.append({"slug": t["slug"], "name": name, "path": f"/tag/{t['slug']}/", "meta_title": f"{name} - Pathfinders Advisors",
                "posts": [p["slug"] for p in posts if t["id"] in p.get("tags", [])]})
(DATA / "tags.json").write_text(json.dumps(out, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
print(len(out), "tags,", sum(len(t["posts"]) for t in out), "post links,", [t["slug"] for t in out if not t["posts"]], "empty")
