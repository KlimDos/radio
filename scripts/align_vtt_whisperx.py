#!/usr/bin/env python3
"""
Re-align existing WebVTT cues to an audio file using WhisperX forced alignment (wav2vec2).

Each cue keeps its text; timestamps are refined using the audio slice [start, end] from the cue
as the search window. Best when cues are already within ~0.5–2 s of the speech (typical Whisper export).

Install (heavy; GPU recommended):

  pip install whisperx torch torchaudio nltk

Example:

  python3 scripts/align_vtt_whisperx.py src/static/grand-theft-auto-gta-vice.ogg \\
    src/static/captions/grand-theft-auto-gta-vice.vtt \\
    -o src/static/captions/grand-theft-auto-gta-vice.aligned.vtt

Optional: --device cpu  (slow)  |  --language en
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

from normalize_vtt import clip_overlaps_sorted, Cue, emit_vtt, parse_cues_loose  # noqa: E402
from repo_paths import resolve_input_path, resolve_output_path  # noqa: E402


def _segments_from_cues(cues: list[Cue]) -> list[dict]:
    """WhisperX align() expects list of dicts with start, end, text."""
    return [{"start": float(c.start), "end": float(c.end), "text": c.text.strip() or " "} for c in cues]


def _cues_from_aligned(result: dict) -> list[Cue]:
    """Build Cue list from whisperx.align() return value."""
    raw_segs = result.get("segments") or []
    out: list[Cue] = []
    order = 0
    for seg in raw_segs:
        if not isinstance(seg, dict):
            continue
        text = (seg.get("text") or "").strip()
        if not text:
            continue
        try:
            s = float(seg["start"])
            e = float(seg["end"])
        except (KeyError, TypeError, ValueError):
            continue
        if e <= s:
            continue
        out.append(Cue(start=s, end=e, text=text, order=order))
        order += 1
    return out


def main() -> None:
    ap = argparse.ArgumentParser(description="WhisperX forced alignment of WebVTT to audio")
    ap.add_argument("audio", help="Audio path (.ogg, .wav, .mp3, …)")
    ap.add_argument("vtt", help="Input .vtt (approximate timings + final text)")
    ap.add_argument("-o", "--output", required=True, help="Output .vtt")
    ap.add_argument("--language", default="en", help="ISO language code for align model (default: en)")
    ap.add_argument("--device", default=None, help="cuda | cpu (default: cuda if available else cpu)")
    ap.add_argument(
        "--max-cues",
        type=int,
        default=0,
        metavar="N",
        help="If >0, only align the first N cues (smoke test)",
    )
    args = ap.parse_args()

    try:
        import torch
        import whisperx
    except ImportError as e:
        print(
            "Missing dependency. Install with:\n"
            "  pip install whisperx torch torchaudio nltk\n",
            file=sys.stderr,
        )
        raise SystemExit(1) from e

    device = args.device or ("cuda" if torch.cuda.is_available() else "cpu")

    audio_path = resolve_input_path(args.audio)
    vtt_path = resolve_input_path(args.vtt)
    with open(vtt_path, encoding="utf-8") as f:
        cues = parse_cues_loose(f.read())
    if args.max_cues > 0:
        cues = cues[: args.max_cues]
    if not cues:
        print("No cues parsed from VTT", file=sys.stderr)
        raise SystemExit(1)

    segments = _segments_from_cues(cues)
    print(f"Loading audio ({device})…", file=sys.stderr)
    audio = whisperx.load_audio(str(audio_path))

    print("Loading alignment model…", file=sys.stderr)
    model_a, metadata = whisperx.load_align_model(language_code=args.language, device=device)

    print(f"Aligning {len(segments)} segments…", file=sys.stderr)
    result = whisperx.align(
        segments,
        model_a,
        metadata,
        audio,
        device,
        return_char_alignments=False,
        print_progress=True,
    )

    aligned = _cues_from_aligned(result)
    if not aligned:
        print("Aligner returned no segments; check language and audio path.", file=sys.stderr)
        raise SystemExit(2)

    clipped = clip_overlaps_sorted(aligned)

    out_text = emit_vtt(clipped)
    out_path = resolve_output_path(args.output)
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(out_text)
    print(f"Wrote {out_path} ({len(clipped)} cues)", file=sys.stderr)


if __name__ == "__main__":
    main()
