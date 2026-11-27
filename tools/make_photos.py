"""Make the web copies of the licensed iStock photos listed in src/data/photos.json.

Usage: python tools/make_photos.py <folder with iStock-<id>.jpg originals>

For every entry: a 1200x800 copy (post and page heroes) and a 768x512 copy
(article cards), both cropped to 3:2 from the centre, saved as progressive JPEG
under assets/img/photos/<name>.jpg and <name>-768x512.jpg. Camera and IPTC
metadata are not carried over. Existing files are overwritten.
"""
import json
import sys
from pathlib import Path

from PIL import Image, ImageOps

ROOT = Path(__file__).resolve().parent.parent
SRC = Path(sys.argv[1])
OUT = ROOT / "assets" / "img" / "photos"
OUT.mkdir(parents=True, exist_ok=True)
data = json.loads((ROOT / "src" / "data" / "photos.json").read_text(encoding="utf-8"))

made = 0
for group in ("pages", "posts"):
    for key, x in data[group].items():
        im = ImageOps.exif_transpose(Image.open(SRC / f"iStock-{x['istock']}.jpg")).convert("RGB")
        for (w, h), suffix in (((1200, 800), ""), ((768, 512), "-768x512")):
            ImageOps.fit(im, (w, h), Image.LANCZOS).save(
                OUT / f"{x['name']}{suffix}.jpg", "JPEG", quality=80, optimize=True, progressive=True)
        made += 1
print(made, "photos written to", OUT)
