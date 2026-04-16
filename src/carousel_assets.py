"""Carousel image paths: serve original bg-art at native resolution."""

from __future__ import annotations

import os

IMAGE_EXT = (".png", ".jpg", ".jpeg", ".webp", ".gif")


def raw_slides(static_dir: str) -> list[str]:
    out: list[str] = []
    for i in range(4):
        fn = f"bg-{i}.jpg"
        if os.path.isfile(os.path.join(static_dir, fn)):
            out.append(fn)
    art_dir = os.path.join(static_dir, "bg-art")
    if os.path.isdir(art_dir):
        for name in sorted(os.listdir(art_dir)):
            if name.lower().endswith(IMAGE_EXT):
                out.append(f"bg-art/{name}")
    return out


def slides_for_flask(app_root: str) -> list[str]:
    """Return slide paths from bg-art at their original resolution."""
    static_dir = os.path.join(app_root, "static")
    return raw_slides(static_dir)
