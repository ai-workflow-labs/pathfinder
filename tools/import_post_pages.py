"""Write src/data/post_pages.json and src/data/categories.json from the old site capture.

Usage: python3 tools/import_post_pages.py <old-site-folder>

For every post: the body (WordPress content, cleaned to plain semantic HTML), the
old title, description, canonical, robots, share image, dates, author, category and
tags read from the saved live page. For every category archive: its old meta.
"""
import html
import json
import re
import sys
from html.parser import HTMLParser
from pathlib import Path

OLD = Path(sys.argv[1])
DATA = Path(__file__).resolve().parent.parent / "src" / "data"
SITE = "https://www.pathfindersadvisors.com"

KEEP = {"p", "h2", "h3", "h4", "h5", "h6", "ul", "ol", "li", "strong", "b", "em", "i", "u", "a", "br", "hr",
        "blockquote", "table", "thead", "tbody", "tfoot", "tr", "th", "td", "figure", "figcaption", "img", "iframe", "sup", "sub"}
VOID = {"br", "hr", "img"}
ATTRS = {"a": {"href", "target", "rel"}, "img": {"src", "alt", "width", "height"}, "td": {"colspan", "rowspan"},
         "th": {"colspan", "rowspan", "scope"}, "iframe": {"src", "title", "width", "height", "allow", "allowfullscreen"}}
RENAME = {"h1": "h2", "b": "strong", "i": "em"}
DROP = {"script", "style", "form", "button", "svg", "noscript", "input", "select", "textarea"}


class Clean(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=False)
        self.out, self.skip = [], 0

    def handle_starttag(self, tag, attrs):
        if tag in DROP:
            self.skip += 1
            return
        if self.skip:
            return
        tag = RENAME.get(tag, tag)
        if tag not in KEEP:
            return
        keep = ATTRS.get(tag, set())
        a = "".join(f' {k}="{html.escape(v or "", quote=True)}"' for k, v in attrs if k in keep and v is not None)
        if tag == "img":
            a += ' loading="lazy"'
        self.out.append(f"<{tag}{a}>")

    def handle_endtag(self, tag):
        if tag in DROP:
            self.skip = max(0, self.skip - 1)
            return
        if self.skip:
            return
        tag = RENAME.get(tag, tag)
        if tag in KEEP and tag not in VOID:
            self.out.append(f"</{tag}>")

    def handle_data(self, d):
        if not self.skip:
            self.out.append(d)

    def handle_entityref(self, name):
        if not self.skip:
            self.out.append(f"&{name};")

    def handle_charref(self, name):
        if not self.skip:
            self.out.append(f"&#{name};")


OLD_DOMAINS = re.compile(r"https?://(?:www\.)?(?:incollegeplanning|collegeliftoff)\.com/wp-content/uploads/")
_alive = {}


def alive(url):
    """True when the image answers 200. Used only for images on the old brand domains."""
    if url not in _alive:
        import urllib.request
        try:
            req = urllib.request.Request(url, method="HEAD", headers={"User-Agent": "Mozilla/5.0 (site migration)"})
            _alive[url] = urllib.request.urlopen(req, timeout=30).status == 200
        except Exception:  # noqa: BLE001
            _alive[url] = False
    return _alive[url]


def fix_old_images(s):
    """Images hotlinked from the old brand domains: use the same file on this site's
    uploads when it exists there; drop the image when it is gone everywhere (it was
    already broken on the old site)."""
    def one(m):
        tag = m.group(0)
        src = re.search(r'src="([^"]+)"', tag).group(1)
        if not OLD_DOMAINS.match(src):
            return tag
        new = OLD_DOMAINS.sub(SITE + "/wp-content/uploads/", src)
        return tag.replace(src, new) if alive(new) else ""
    return re.sub(r"<img [^>]*>", one, s)


def clean(body):
    c = Clean()
    c.feed(body)
    s = fix_old_images("".join(c.out))
    s = re.sub(r"<p>\s*(&nbsp;| )?\s*</p>", "", s)
    s = re.sub(r"\n{3,}", "\n\n", s)
    return s.strip()


def meta(src):
    def g(pat):
        m = re.search(pat, src, re.S)
        return html.unescape(m.group(1)).strip() if m else ""
    author = g(r'"author":\{"@id":"[^"]*","name":"([^"]*)"')
    return {
        "meta_title": g(r"<title>(.*?)</title>"),
        "desc": g(r'<meta name="description" content="([^"]*)"'),
        "robots": g(r'<meta name="robots" content="([^"]*)"'),
        "canonical": g(r'<link rel="canonical" href="([^"]*)"'),
        "og": g(r'<meta property="og:image" content="([^"]*)"'),
        "og_alt": g(r'<meta property="og:image:alt" content="([^"]*)"'),
        "published": g(r'<meta property="article:published_time" content="([^"]*)"'),
        "modified_time": g(r'<meta property="article:modified_time" content="([^"]*)"'),
        "section": g(r'<meta property="article:section" content="([^"]*)"'),
        "tags": [html.unescape(t) for t in re.findall(r'<meta property="article:tag" content="([^"]*)"', src)],
        "author": author,
        "h1": re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", g(r"<h1[^>]*>(.*?)</h1>"))).strip(),
    }


posts = json.loads((OLD / "rest" / "posts.json").read_text(encoding="utf-8"))
cats = {c["id"]: c for c in json.loads((OLD / "rest" / "categories.json").read_text(encoding="utf-8"))}
out = []
for p in posts:
    page = OLD / "html" / f"post__{p['slug']}.html"
    m = meta(page.read_text(encoding="utf-8")) if page.exists() else {}
    title = html.unescape(re.sub(r"<[^>]+>", "", p["title"]["rendered"])).strip()
    out.append({
        "slug": p["slug"], "path": f"/{p['slug']}/", "title": title,
        "date": p["date"][:10], "modified": p["modified"][:10],
        "categories": [{"slug": cats[c]["slug"], "name": html.unescape(cats[c]["name"])} for c in p["categories"] if c in cats],
        "body": clean(p["content"]["rendered"]), **m,
    })
out.sort(key=lambda x: x["date"], reverse=True)
(DATA / "post_pages.json").write_text(json.dumps(out, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")

catout = []
for f in sorted((OLD / "html").glob("category__category__*.html")):
    slug = f.stem.replace("category__category__", "")
    src = f.read_text(encoding="utf-8")
    c = next((c for c in cats.values() if c["slug"] == slug), None)
    catout.append({"slug": slug, "path": f"/category/{slug}/", "name": html.unescape(c["name"]) if c else slug.title(),
                   "description": html.unescape(re.sub(r"<[^>]+>", "", c.get("description", ""))).strip() if c else "", **meta(src)})
(DATA / "categories.json").write_text(json.dumps(catout, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")

print(len(out), "posts,", sum(1 for x in out if not x.get("title")), "no title,", sum(1 for x in out if not x["body"]), "empty bodies,",
      sum(1 for x in out if "noindex" in x.get("robots", "")), "noindex")
print(len(catout), "categories:", [(c["slug"], c["meta_title"]) for c in catout])
