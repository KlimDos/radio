#!/usr/bin/env python3
"""
Shift every WebVTT cue start/end by a constant (seconds). Use for a fixed global desync.

  python3 scripts/shift_vtt.py src/static/captions/grand-theft-auto-gta-vice.vtt \\
    -o src/static/captions/grand-theft-auto-gta-vice.shifted.vtt --seconds -0.35

  python3 scripts/shift_vtt.py file.vtt --in-place --backup --seconds 0.2
"""
from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

from normalize_vtt import MIN_CUE_SEC, Cue, emit_vtt, parse_cues_loose  # noqa: E402
from repo_paths import resolve_input_path, resolve_output_path  # noqa: E402


def shift_cues(cues: list[Cue], delta: float) -> list[Cue]:
    out: list[Cue] = []
    for c in cues:
        ns = max(0.0, c.start + delta)
        ne = c.end + delta
        if ne <= ns:
            ne = ns + MIN_CUE_SEC
        out.append(Cue(start=ns, end=ne, text=c.text, order=c.order))
    return out


def main() -> None:
    ap = argparse.ArgumentParser(description="Shift all VTT timestamps by DELTA seconds")
    ap.add_argument("input", help="Input .vtt")
    ap.add_argument("-o", "--output", help="Output .vtt (required unless --in-place)")
    ap.add_argument(
        "--seconds",
        type=float,
        required=True,
        metavar="DELTA",
        help="Added to every start and end (negative pulls cues earlier)",
    )
    ap.add_argument("--in-place", action="store_true", help="Overwrite input")
    ap.add_argument("--backup", action="store_true", help="With --in-place, save .bak first")
    args = ap.parse_args()

    if not args.in_place and not args.output:
        ap.error("pass -o/--output or --in-place")

    path = resolve_input_path(args.input)
    with open(path, encoding="utf-8") as f:
        raw = f.read()

    cues = parse_cues_loose(raw)
    shifted = shift_cues(cues, args.seconds)
    out_text = emit_vtt(shifted)

    if args.in_place:
        if args.backup:
            shutil.copy2(path, str(path) + ".bak")
        out_path = path
    else:
        out_path = resolve_output_path(args.output)

    with open(out_path, "w", encoding="utf-8") as f:
        f.write(out_text)
    print(f"Wrote {out_path} ({len(shifted)} cues, delta={args.seconds:+.3f}s)")


if __name__ == "__main__":
    main()
