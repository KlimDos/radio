#!/usr/bin/env python3
"""
Normalize WebVTT from chunked / model exports:

  1. **Loose parse** — cues separated only by a new timing line (no blank line between them).
  2. **Timestamp repair** — e.g. ``00:02:040`` (no dot before ms) → ``00:00:02.040`` (same rules as captions.js).
  3. **Timeline stitch** (file order) — if the next cue jumps backward in time (chunk restart) or
     overlaps the running end of the programme, it is **moved** after the previous cue so the
     track is strictly monotonic (fixes duplicate ``00:00`` segments mid-file).
  4. **Overlap clip** — after sorting by start, trim ``end`` so cues do not cover the next start.
  5. **Dedupe** — identical (start, end, text) removed (optional ``--no-dedupe``).

Usage::

  python3 scripts/normalize_vtt.py src/static/captions/grand-theft-auto-gta-vice-first.vtt \\
    -o src/static/captions/grand-theft-auto-gta-vice-first.normalized.vtt

  python3 scripts/normalize_vtt.py file.vtt --in-place --backup
"""
from __future__ import annotations

import argparse
import re
import shutil
import sys
from dataclasses import dataclass
from pathlib import Path

_SCRIPTS_DIR = Path(__file__).resolve().parent
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))
from repo_paths import resolve_input_path, resolve_output_path  # noqa: E402

EPS = 1e-3
MIN_CUE_SEC = 0.04
# If raw start is this far *behind* the stitched timeline, treat as a new chunk (restart).
RESET_JUMP_SEC = 45.0


@dataclass
class Cue:
    start: float
    end: float
    text: str
    order: int = 0


def parse_timestamp(raw: str) -> float:
    s = raw.strip().replace(",", ".")
    parts = s.split(":")
    if len(parts) == 3:
        last = parts[2]
        has_frac = "." in last or "." in s
        if not has_frac and re.fullmatch(r"\d{3}", last):
            return (int(parts[0]) or 0) * 60 + (int(parts[1]) or 0) + (int(last) or 0) / 1000
        h, m = int(parts[0]) or 0, int(parts[1]) or 0
        sec = float(last) if last else 0.0
        return h * 3600 + m * 60 + sec
    if len(parts) == 2:
        return (int(parts[0]) or 0) * 60 + float(parts[1] or 0)
    return float(parts[0])


def format_timestamp(t: float) -> str:
    t = max(0.0, t)
    whole = int(t)
    ms = int(round((t - whole) * 1000))
    if ms >= 1000:
        whole += 1
        ms = 0
    s = whole % 60
    m = (whole // 60) % 60
    h = whole // 3600
    return f"{h:02d}:{m:02d}:{s:02d}.{ms:03d}"


def parse_timing_line(line: str) -> tuple[float, float] | None:
    if "-->" not in line:
        return None
    left, right = line.strip().split("-->", 1)
    rtoks = right.strip().split()
    if not rtoks:
        return None
    ltoks = left.strip().split()
    if not ltoks:
        return None
    start_tok, end_tok = ltoks[-1], rtoks[0]
    try:
        return parse_timestamp(start_tok), parse_timestamp(end_tok)
    except ValueError:
        return None


def is_timing_line(line: str) -> bool:
    return parse_timing_line(line) is not None


def split_timing_line(line: str) -> tuple[float, float]:
    r = parse_timing_line(line)
    if r is None:
        raise ValueError(f"bad timing line: {line!r}")
    return r


def parse_cues_loose(text: str) -> list[Cue]:
    lines = text.replace("\ufeff", "").splitlines()
    cues: list[Cue] = []
    i = 0
    n = len(lines)

    def skip_header() -> None:
        nonlocal i
        while i < n:
            s = lines[i].strip()
            if s == "WEBVTT" or s.startswith("Kind:") or s.startswith("Language:"):
                i += 1
                continue
            if s.startswith("NOTE"):
                while i < n and lines[i].strip() != "":
                    i += 1
                while i < n and lines[i].strip() == "":
                    i += 1
                continue
            break

    skip_header()
    while i < n:
        while i < n and not lines[i].strip():
            i += 1
        if i >= n:
            break
        raw = lines[i]
        if not is_timing_line(raw):
            i += 1
            continue
        try:
            start, end = split_timing_line(raw)
        except ValueError:
            i += 1
            continue
        i += 1
        text_lines: list[str] = []
        while i < n:
            nxt = lines[i]
            stripped = nxt.strip()
            if stripped == "":
                i += 1
                break
            if is_timing_line(nxt):
                break
            text_lines.append(nxt.rstrip("\n"))
            i += 1
        body = "\n".join(text_lines).strip()
        oid = len(cues)
        cues.append(Cue(start=start, end=end, text=body, order=oid))
    return cues


def stitch_monotonic_file_order(cues: list[Cue], *, reset_jump_sec: float = RESET_JUMP_SEC) -> list[Cue]:
    """Place cues in file order onto one non-decreasing timeline."""
    reset_jump_sec = max(5.0, reset_jump_sec)
    ordered = sorted(cues, key=lambda c: (c.order, c.start, c.end))
    max_seen = 0.0
    out: list[Cue] = []
    for c in ordered:
        dur = max(c.end - c.start, MIN_CUE_SEC)
        s, e = c.start, c.end
        if s < max_seen - reset_jump_sec:
            s = max_seen + EPS
            e = s + dur
        elif s < max_seen + EPS:
            s = max_seen + EPS
            e = s + dur
        if e <= s:
            e = s + MIN_CUE_SEC
        max_seen = max(max_seen, e)
        out.append(Cue(start=s, end=e, text=c.text, order=c.order))
    return out


def clip_overlaps_sorted(cues: list[Cue]) -> list[Cue]:
    if not cues:
        return []
    out = sorted(cues, key=lambda c: (c.start, c.end, c.order))
    for i in range(len(out) - 1):
        nxt_start = out[i + 1].start
        if out[i].end > nxt_start - EPS:
            out[i].end = max(out[i].start + MIN_CUE_SEC, nxt_start - EPS)
    return [c for c in out if c.end > c.start + EPS and c.text]


def dedupe(cues: list[Cue]) -> list[Cue]:
    seen: set[tuple[float, float, str]] = set()
    out: list[Cue] = []
    for c in cues:
        key = (round(c.start, 3), round(c.end, 3), c.text)
        if key in seen:
            continue
        seen.add(key)
        out.append(c)
    return out


def emit_vtt(cues: list[Cue]) -> str:
    parts = ["WEBVTT", ""]
    for c in sorted(cues, key=lambda x: (x.start, x.end, x.order)):
        parts.append(f"{format_timestamp(c.start)} --> {format_timestamp(c.end)}")
        if c.text:
            parts.append(c.text)
        parts.append("")
    return "\n".join(parts).rstrip() + "\n"


def main() -> None:
    ap = argparse.ArgumentParser(description="Normalize WebVTT (timestamps, stitch, overlaps)")
    ap.add_argument("input", help="Input .vtt path")
    ap.add_argument("-o", "--output", help="Output .vtt (default: stdout)")
    ap.add_argument("--in-place", action="store_true", help="Overwrite input (use with --backup)")
    ap.add_argument("--backup", action="store_true", help="With --in-place, save copy as .bak")
    ap.add_argument("--no-dedupe", action="store_true", help="Keep duplicate cues")
    ap.add_argument(
        "--no-stitch",
        action="store_true",
        help="Do not run file-order stitch (only parse + clip + dedupe; may break on chunk restarts)",
    )
    ap.add_argument(
        "--reset-gap",
        type=float,
        default=RESET_JUMP_SEC,
        metavar="SEC",
        help=f"Backward jump vs stitched tail treated as chunk restart (default {RESET_JUMP_SEC})",
    )
    args = ap.parse_args()

    reset_gap = max(5.0, float(args.reset_gap))

    path = resolve_input_path(args.input)
    with open(path, encoding="utf-8") as f:
        raw = f.read()

    cues = parse_cues_loose(raw)
    n_raw = len(cues)
    if not args.no_stitch:
        cues = stitch_monotonic_file_order(cues, reset_jump_sec=reset_gap)
    cues = clip_overlaps_sorted(cues)
    if not args.no_dedupe:
        cues = dedupe(cues)

    out_text = emit_vtt(cues)
    n_out = len(cues)

    if args.in_place:
        if args.backup:
            shutil.copy2(path, str(path) + ".bak")
        out_path = path
    else:
        out_path = resolve_output_path(args.output) if args.output else None

    if not out_path:
        sys.stdout.write(out_text)
        print(f"# cues: {n_raw} parsed → {n_out} after normalize", file=sys.stderr)
        return

    with open(out_path, "w", encoding="utf-8") as f:
        f.write(out_text)
    print(f"Wrote {out_path} ({n_raw} cues parsed → {n_out} kept)")


if __name__ == "__main__":
    main()
