#!/usr/bin/env python3
"""
Remove the 'hdmx' table from a TTF so Firefox stops warning:
  hdmx: the table should not be present when bit 2 and 4 of the head->flags are not set

Requires: pip install fonttools

Usage:
  python3 scripts/strip_ttf_hdmx.py src/static/pricedown-regular/pricedown-regular.ttf
"""
from __future__ import annotations

import argparse
import shutil
import sys


def main() -> None:
    try:
        from fontTools.ttLib import TTFont
    except ImportError:
        print("Install fonttools: pip install fonttools", file=sys.stderr)
        raise SystemExit(1)

    ap = argparse.ArgumentParser(description="Strip hdmx from TTF for cleaner web loading")
    ap.add_argument("font", help="Path to .ttf (overwritten; .bak saved first)")
    args = ap.parse_args()
    path = args.font
    bak = path + ".bak"
    shutil.copy2(path, bak)
    font = TTFont(path)
    if "hdmx" in font:
        del font["hdmx"]
    font.save(path)
    print(f"Updated {path} (backup {bak})")


if __name__ == "__main__":
    main()
