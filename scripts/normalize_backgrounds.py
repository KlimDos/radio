#!/usr/bin/env python3
"""
Resize all carousel sources to 1920×1080 (cover crop) as JPEG in static/bg-normalized/.
Run from repo root:  python3 scripts/normalize_backgrounds.py
Requires: pip install Pillow
"""
from __future__ import annotations

import os
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(REPO, "src")
STATIC = os.path.join(SRC, "static")

sys.path.insert(0, SRC)

from carousel_assets import raw_slides  # noqa: E402

try:
    from PIL import Image, ImageOps
except ImportError as e:
    print("Install Pillow: pip install Pillow", file=sys.stderr)
    raise SystemExit(1) from e

OUT_W, OUT_H = 1920, 1080
OUT_DIR = os.path.join(STATIC, "bg-normalized")


def main() -> None:
    slides = raw_slides(STATIC)
    if not slides:
        print("No source slides found under", STATIC)
        raise SystemExit(1)

    os.makedirs(OUT_DIR, exist_ok=True)
    for old in os.listdir(OUT_DIR):
        os.remove(os.path.join(OUT_DIR, old))

    for idx, rel in enumerate(slides):
        src_path = os.path.join(STATIC, *rel.split("/"))
        if not os.path.isfile(src_path):
            print("skip missing:", src_path)
            continue
        im = Image.open(src_path)
        im = ImageOps.exif_transpose(im)
        if im.mode in ("RGBA", "P"):
            rgba = im.convert("RGBA")
            bg = Image.new("RGB", rgba.size, (0, 0, 0))
            bg.paste(rgba, mask=rgba.split()[3])
            im = bg
        elif im.mode != "RGB":
            im = im.convert("RGB")

        fitted = ImageOps.fit(im, (OUT_W, OUT_H), method=Image.Resampling.LANCZOS)
        out_name = f"slide-{idx:04d}.jpg"
        out_path = os.path.join(OUT_DIR, out_name)
        fitted.save(out_path, "JPEG", quality=88, optimize=True)
        print(out_name, "<-", rel)

    print("Wrote", len(slides), "slides to", OUT_DIR)


if __name__ == "__main__":
    main()
