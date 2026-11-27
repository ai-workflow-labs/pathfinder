"""Write src/data/locations.json from the old site's city pages and locations hub.

Usage: python3 tools/import_locations.py <old-site-folder>

Reads <old-site>/html/page__<slug>.html (as saved by the migration capture), keeps
every heading, paragraph, quote, stat and FAQ in page order, and records the old
title, description and og:image so the new pages can carry them unchanged.
"""
import html
import json
import re
import sys
from html.parser import HTMLParser
from pathlib import Path

OLD = Path(sys.argv[1])
OUT = Path(__file__).resolve().parent.parent / "src" / "data" / "locations.json"
CITIES = ["columbus-oh", "cincinnati-oh", "raleigh-nc", "charlotte-nc", "pittsburgh-pa",
          "cleveland-oh", "dallas-tx", "nashville-tn", "denver-co"]
BLOCK = {"h1", "h2", "h3", "h4", "h5", "h6", "p", "a", "li", "summary", "div", "span"}
SKIP = {"script", "style", "noscript", "svg", "template", "head", "header", "footer", "form", "select"}


class Outline(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.stack, self.lines, self.buf, self.cur = [], [], [], None

    def skipping(self):
        return any(s for _, s in self.stack)

    def flush(self):
        t = re.sub(r"\s+", " ", "".join(self.buf)).strip()
        if t and self.cur:
            self.lines.append((self.cur, t))
        self.buf = []

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        cls = a.get("class") or ""
        skip = (tag in SKIP or (a.get("data-elementor-type") or "") in ("header", "footer", "popup")
                or "elementor-location-" in cls)
        if tag in ("br", "img", "input", "meta", "link", "hr", "source"):
            return
        if tag in BLOCK and not self.skipping():
            self.flush()
            if tag in ("h1", "h2", "h3", "h4", "h5", "h6", "p", "a", "li", "summary"):
                self.cur = tag
        self.stack.append((tag, skip))

    def handle_endtag(self, tag):
        if tag in ("br", "img", "input", "meta", "link", "hr", "source"):
            return
        while self.stack:
            t, _ = self.stack.pop()
            if t == tag:
                break
        if tag in BLOCK:
            self.flush()

    def handle_data(self, d):
        if not self.skipping():
            self.buf.append(d)


def outline(src):
    p = Outline()
    p.feed(src[src.find("<body"):])
    p.flush()
    out = []
    for x in p.lines:
        if not out or out[-1] != x:
            out.append(x)
    return [x for x in out if x[1].lower() != "skip to content"]


def meta(src):
    g = lambda pat: (lambda m: html.unescape(m.group(1)).strip() if m else "")(re.search(pat, src, re.S))
    return {"title": g(r"<title>(.*?)</title>"), "desc": g(r'<meta name="description" content="([^"]*)"'),
            "og": g(r'<meta property="og:image" content="([^"]*)"')}


CAPS = re.compile(r"^[A-Z0-9 ?!&'’.,-]{6,}$")
STARS = re.compile(r"^★+$")
ATTRIB = re.compile(r"^[-–—]\s*")


def city(slug):
    src = (OLD / "html" / f"page__college-career-planning-{slug}.html").read_text(encoding="utf-8")
    lines = outline(src)
    page = {"slug": slug, "path": f"/college-career-planning-{slug}/", **meta(src)}
    h1 = next(i for i, (t, _) in enumerate(lines) if t == "h1")
    page["h1"] = lines[h1][1]
    rest = lines[h1 + 1:]
    page["lead"] = rest[0][1] if rest and rest[0][0] == "p" else ""
    # Split into sections at each h2; remember an all-caps eyebrow just before it.
    sections, cur, eyebrow = [], None, ""
    for t, txt in rest[1:] if page["lead"] else rest:
        if t in ("p", "a") and CAPS.match(txt) and not txt.startswith(("“", '"')):
            eyebrow = txt
            continue
        if t == "h2" and STARS.match(txt):
            continue
        if t == "h2":
            if cur and cur["heading"] == txt:
                continue  # Charlotte and Raleigh repeat the FAQ heading
            cur = {"heading": txt, "eyebrow": eyebrow, "lines": []}
            eyebrow = ""
            sections.append(cur)
            continue
        if cur is None:
            page.setdefault("hero_links", []).append(txt)
            continue
        cur["lines"].append([t, txt])
    page["sections"] = [classify(s) for s in sections]
    return page


def classify(s):
    h, L = s["heading"].lower(), s["lines"]
    out = {"heading": s["heading"], "eyebrow": s["eyebrow"]}
    if "question" in h:
        qa = [x[1] for x in L if x[0] in ("a", "summary", "h3", "h4", "p")]
        out["kind"] = "faq"
        out["items"] = [{"q": qa[i], "a": qa[i + 1]} for i in range(0, len(qa) - 1, 2)]
        return out
    if "say" in h or "saying" in h:
        out["kind"] = "quotes"
        quotes, extra, i = [], [], 0
        texts = [x for x in L if not STARS.match(x[1])]
        while i < len(texts):
            t, txt = texts[i]
            if t in ("h3",) and "ready" in txt.lower():
                break
            if txt.startswith(("“", '"')):
                q = {"text": txt.strip("“”\""), "by": "", "where": ""}
                if i + 1 < len(texts) and ATTRIB.match(texts[i + 1][1]):
                    q["by"] = ATTRIB.sub("", texts[i + 1][1]); i += 1
                    if i + 1 < len(texts) and texts[i + 1][0] == "p" and not texts[i + 1][1].startswith(("“", '"')) \
                            and len(texts[i + 1][1]) < 60 and not ATTRIB.match(texts[i + 1][1]):
                        q["where"] = texts[i + 1][1]; i += 1
                quotes.append(q)
            i += 1
        rest = texts[i:]
        out["items"] = quotes
        # "Ready to Start Planning?" box, then the stats that follow it.
        if rest:
            out["ready"] = {"heading": rest[0][1], "text": rest[1][1] if len(rest) > 1 else "",
                            "button": next((x[1] for x in rest[2:3] if x[0] == "a"), "")}
            stats_lines = rest[3:] if out["ready"]["button"] else rest[2:]
            out["stats"] = pair_stats(stats_lines)
        return out
    if "by the numbers" in h:
        out["kind"] = "stats"
        out["items"] = pair_stats(L)
        return out
    items, intro, cta = [], [], None
    i = 0
    while i < len(L):
        t, txt = L[i]
        if t in ("h3", "h4"):
            nxt = L[i + 1][1] if i + 1 < len(L) and L[i + 1][0] == "p" else ""
            items.append({"title": txt, "text": nxt}); i += 2 if nxt else 1
            continue
        if t == "a":
            cta = txt
        elif t == "p":
            (intro if not items else items[-1].setdefault("more", [])).append(txt)
        i += 1
    out["intro"], out["items"] = intro, items
    if cta:
        out["button"] = cta
    if "top college" in h:
        out["kind"] = "colleges"
    elif not items:
        out["kind"] = "text"
    else:
        out["kind"] = "cards"
    return out


def pair_stats(L):
    stats, i = [], 0
    while i < len(L):
        t, txt = L[i]
        if t in ("h3", "h2") and re.match(r"^[$\d]", txt):
            label = L[i + 1][1] if i + 1 < len(L) and L[i + 1][0] in ("h4", "p") else ""
            stats.append({"value": txt, "label": label}); i += 2 if label else 1
        else:
            i += 1
    return stats


def hub():
    src = (OLD / "html" / "page__college-planning-locations.html").read_text(encoding="utf-8")
    L = outline(src)
    page = {"path": "/college-planning-locations/", **meta(src)}
    page["lines"] = L
    return page


data = {"hub": hub(), "cities": [city(c) for c in CITIES]}
OUT.write_text(json.dumps(data, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
for c in data["cities"]:
    print(c["slug"], [(s["kind"], len(s.get("items", []))) for s in c["sections"]])
