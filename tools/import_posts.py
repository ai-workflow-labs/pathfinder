"""Write src/data/posts.json from a capture of the old WordPress site.

Usage: python3 tools/import_posts.py <old-site-folder>

The folder must hold rest/posts.json, rest/categories.json, rest/media.json and
html/post__<slug>.html (as saved by the migration capture). The image for each
post is the og:image of the live post page, so it matches what search engines
and social cards already show.
"""
import html
import json
import re
import sys
from pathlib import Path

OLD = Path(sys.argv[1])
OUT = Path(__file__).resolve().parent.parent / "src" / "data" / "posts.json"

# Topic filters shown on the knowledge base, and where each comes from in WordPress.
TOPICS = {"Current Events": ("cat", 44), "Financial": ("cat", 43), "Careers": ("cat", 42), "ACT/SAT": ("tag", 85)}

posts = json.loads((OLD / "rest" / "posts.json").read_text(encoding="utf-8"))
media = {m["id"]: m for m in json.loads((OLD / "rest" / "media.json").read_text(encoding="utf-8"))}


def text(s):
    s = re.sub(r"<[^>]+>", " ", s or "")
    return re.sub(r"\s+", " ", html.unescape(s)).strip()


out = []
for p in posts:
    slug = p["slug"]
    page = OLD / "html" / f"post__{slug}.html"
    og = alt = ""
    if page.exists():
        src = page.read_text(encoding="utf-8")
        m = re.search(r'<meta property="og:image" content="([^"]+)"', src)
        og = m.group(1) if m else ""
        m = re.search(r'<meta property="og:image:alt" content="([^"]*)"', src)
        alt = html.unescape(m.group(1)) if m else ""
    fm = media.get(p.get("featured_media"))
    if fm and not alt:
        alt = fm.get("alt_text") or ""
    topics = [name for name, (kind, tid) in TOPICS.items()
              if tid in (p["categories"] if kind == "cat" else p["tags"])]
    excerpt = text(p["excerpt"]["rendered"])
    excerpt = re.sub(r"\s*(\[…\]|\[&hellip;\]|…)$", "", excerpt)
    out.append({"title": text(p["title"]["rendered"]), "slug": slug, "date": p["date"][:10],
                "image": og, "alt": alt or text(p["title"]["rendered"]), "topics": topics,
                "excerpt": excerpt})
out.sort(key=lambda x: x["date"], reverse=True)
OUT.write_text(json.dumps(out, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
print(f"{len(out)} posts -> {OUT}")
print("no image:", [x["slug"] for x in out if not x["image"]])
print("topics:", {t: sum(t in x["topics"] for x in out) for t in TOPICS})
