#!/usr/bin/env python3
"""
Transcribe a long audio file via OpenRouter (chat + input_audio), write WebVTT for the radio UI.

Requires:
  - OPENROUTER_API_KEY in the environment (never commit it).
  - ffmpeg and ffprobe on PATH (splits audio into short WAV chunks — full OGG is too large for JSON).

Usage (from repo root):
  export OPENROUTER_API_KEY=sk-or-...
  # optional: export OPENROUTER_MODEL=openai/gpt-audio  # e.g. OpenAI audio-native
  # optional: export CHUNK_SECONDS=90
  python3 scripts/transcribe_openrouter.py

Defaults:
  Input:  src/static/grand-theft-auto-gta-vice.ogg
  Output: src/static/captions/grand-theft-auto-gta-vice.vtt
"""
from __future__ import annotations

import argparse
import base64
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import urllib.error
import urllib.request

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
CHECKPOINT_VERSION = 1
# Strong default on OpenRouter: flagship multimodal with audio (long radio / speech + bed).
DEFAULT_MODEL = "google/gemini-2.5-pro"


def ffprobe_duration(path: str) -> float:
    r = subprocess.run(
        [
            "ffprobe",
            "-v",
            "error",
            "-show_entries",
            "format=duration",
            "-of",
            "default=noprint_wrappers=1:nokey=1",
            path,
        ],
        capture_output=True,
        text=True,
        check=True,
    )
    return float(r.stdout.strip())


def ffmpeg_slice_wav(src: str, start_s: float, dur_s: float, out_wav: str) -> None:
    subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-hide_banner",
            "-loglevel",
            "error",
            "-ss",
            str(start_s),
            "-i",
            src,
            "-t",
            str(dur_s),
            "-ac",
            "1",
            "-ar",
            "16000",
            "-c:a",
            "pcm_s16le",
            out_wav,
        ],
        check=True,
    )


def encode_wav_b64(path: str) -> str:
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode("ascii")


def strip_fences(text: str) -> str:
    t = text.strip()
    t = re.sub(r"^```(?:webvtt|vtt)?\s*", "", t, flags=re.I)
    t = re.sub(r"\s*```\s*$", "", t)
    return t.strip()


def vtt_body_only(raw: str) -> str:
    raw = raw.strip()
    if raw.upper().startswith("WEBVTT"):
        nl = raw.find("\n")
        raw = raw[nl + 1 :] if nl >= 0 else ""
    return raw.lstrip("\n")


def ts_to_sec(ts: str) -> float:
    ts = ts.strip().replace(",", ".")
    parts = ts.split(":")
    if len(parts) == 3:
        return int(parts[0]) * 3600 + int(parts[1]) * 60 + float(parts[2])
    if len(parts) == 2:
        return int(parts[0]) * 60 + float(parts[1])
    return float(parts[0])


def sec_to_ts(sec: float) -> str:
    sec = max(0.0, sec)
    whole = int(sec)
    ms = int(round((sec - whole) * 1000))
    if ms >= 1000:
        whole += 1
        ms = 0
    s = whole % 60
    m = (whole // 60) % 60
    h = whole // 3600
    return f"{h:02d}:{m:02d}:{s:02d}.{ms:03d}"


def shift_vtt_timestamps(vtt: str, offset_sec: float) -> str:
    """Shift all cue timestamps in a WEBVTT fragment by offset_sec."""
    ts = r"(?:\d{1,2}:\d{2}:\d{2}|\d{1,2}:\d{2})[.,]\d{3}"
    cue_line = re.compile(rf"^({ts})\s*-->\s*({ts})(.*)$")
    lines = []
    for line in vtt.splitlines():
        m = cue_line.match(line)
        if m:
            a = ts_to_sec(m.group(1))
            b = ts_to_sec(m.group(2))
            a += offset_sec
            b += offset_sec
            lines.append(f"{sec_to_ts(a)} --> {sec_to_ts(b)}{m.group(3)}")
        else:
            lines.append(line)
    return "\n".join(lines)


def chunk_plan(duration: float, chunk: float) -> list[tuple[float, float]]:
    """(offset, duration) for each slice, same order as the transcription loop."""
    plan: list[tuple[float, float]] = []
    offset = 0.0
    while offset < duration - 0.01:
        dur = min(chunk, duration - offset)
        plan.append((offset, dur))
        offset += dur
    return plan


def nearly_equal(a: float, b: float, eps: float = 1e-3) -> bool:
    return abs(a - b) <= eps


def checkpoint_paths(out_path: str) -> tuple[str, str]:
    """(json state, human-readable partial WebVTT)."""
    return (out_path + ".progress.json", out_path + ".partial.vtt")


def write_atomic(path: str, text: str) -> None:
    d = os.path.dirname(path) or "."
    fd, tmp = tempfile.mkstemp(prefix=".progress_", suffix=".tmp", dir=d)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(text)
        os.replace(tmp, path)
    except BaseException:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise


def load_checkpoint(
    path: str,
    *,
    source_path: str,
    source_size: int,
    duration: float,
    model: str,
    chunk_seconds: float,
) -> tuple[list[str], float] | None:
    if not os.path.isfile(path):
        return None
    try:
        with open(path, encoding="utf-8") as f:
            cp = json.load(f)
    except (OSError, json.JSONDecodeError):
        return None
    if cp.get("version") != CHECKPOINT_VERSION:
        return None
    if cp.get("source_path") != source_path:
        return None
    if int(cp.get("source_size", -1)) != source_size:
        return None
    if abs(float(cp.get("duration", 0.0)) - duration) > 0.5:
        return None
    if cp.get("model") != model:
        return None
    if not nearly_equal(float(cp.get("chunk_seconds", 0.0)), chunk_seconds):
        return None
    segments = cp.get("segments")
    next_off = float(cp.get("next_offset", -1.0))
    if not isinstance(segments, list) or not all(isinstance(s, str) for s in segments):
        return None
    plan = chunk_plan(duration, chunk_seconds)
    if len(segments) > len(plan):
        return None
    expected_next = sum(plan[i][1] for i in range(len(segments)))
    if abs(expected_next - next_off) > 0.5:
        return None
    return ([str(s) for s in segments], next_off)


def save_progress(
    *,
    json_path: str,
    partial_vtt_path: str,
    source_path: str,
    source_size: int,
    duration: float,
    model: str,
    chunk_seconds: float,
    segments: list[str],
    next_offset: float,
) -> None:
    payload = {
        "version": CHECKPOINT_VERSION,
        "source_path": source_path,
        "source_size": source_size,
        "duration": duration,
        "model": model,
        "chunk_seconds": chunk_seconds,
        "segments": segments,
        "next_offset": next_offset,
    }
    write_atomic(json_path, json.dumps(payload, indent=2, ensure_ascii=False) + "\n")
    partial = "WEBVTT\n\n" + "\n\n".join(segments) + "\n"
    write_atomic(partial_vtt_path, partial)


def transcribe_chunk_wav(
    api_key: str,
    model: str,
    wav_path: str,
    clip_hint: str,
) -> str:
    b64 = encode_wav_b64(wav_path)
    prompt = (
        "You are a transcription engine. Transcribe the speech faithfully (exact wording, "
        "including filler and false starts when audible); do not paraphrase or summarize.\n"
        "This WAV clip is a slice of a longer track; "
        "timestamps in your output must start at 00:00:00.000 relative to THIS clip only.\n\n"
        "Output ONLY valid WebVTT (first line exactly WEBVTT). Use format:\n"
        "HH:MM:SS.mmm --> HH:MM:SS.mmm\n"
        "line of text\n\n"
        "Use short cues (roughly 3–8 seconds) at natural pauses when possible. "
        "No markdown, no code fences, no commentary before or after the WebVTT.\n\n"
        f"Clip context: {clip_hint}"
    )
    body = {
        "model": model,
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {
                        "type": "input_audio",
                        "input_audio": {"data": b64, "format": "wav"},
                    },
                ],
            }
        ],
        "temperature": 0,
        "max_tokens": 8192,
    }
    data = json.dumps(body).encode("utf-8")
    req = urllib.request.Request(
        OPENROUTER_URL,
        data=data,
        method="POST",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://github.com/KlimDos/radio",
            "X-Title": "radio-transcribe",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=600) as resp:
            payload = json.load(resp)
    except urllib.error.HTTPError as e:
        err = e.read().decode("utf-8", errors="replace")
        msg = f"OpenRouter HTTP {e.code}: {err}"
        if e.code == 404 and "input audio" in err.lower():
            msg += (
                "\n\nThis model is not routed for audio on OpenRouter. "
                "Pick one with audio input (e.g. openai/gpt-audio or "
                "google/gemini-2.5-pro): "
                "https://openrouter.ai/models?fmt=cards&input_modalities=audio"
            )
        raise SystemExit(msg) from e

    try:
        content = payload["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError) as e:
        raise SystemExit(f"Unexpected response: {json.dumps(payload)[:2000]}") from e
    return strip_fences(str(content))


def main() -> None:
    ap = argparse.ArgumentParser(description="Transcribe audio → WebVTT via OpenRouter")
    ap.add_argument(
        "--input",
        default="src/static/grand-theft-auto-gta-vice.ogg",
        help="Source audio file",
    )
    ap.add_argument(
        "--output",
        default="src/static/captions/grand-theft-auto-gta-vice.vtt",
        help="Output WebVTT path",
    )
    ap.add_argument(
        "--chunk-seconds",
        type=float,
        default=float(os.environ.get("CHUNK_SECONDS", "90")),
        help="Slice length per API call (smaller = smaller payload)",
    )
    ap.add_argument(
        "--model",
        default=os.environ.get("OPENROUTER_MODEL", DEFAULT_MODEL),
        help="OpenRouter model id (must list audio in input_modalities)",
    )
    ap.add_argument(
        "--fresh",
        action="store_true",
        help="Ignore checkpoint and start from scratch",
    )
    args = ap.parse_args()

    api_key = os.environ.get("OPENROUTER_API_KEY")
    if not api_key:
        print("Set OPENROUTER_API_KEY in the environment.", file=sys.stderr)
        raise SystemExit(1)

    if not shutil.which("ffmpeg") or not shutil.which("ffprobe"):
        print("ffmpeg and ffprobe are required on PATH.", file=sys.stderr)
        raise SystemExit(1)

    src = os.path.abspath(args.input)
    if not os.path.isfile(src):
        raise SystemExit(f"Missing input file: {src}")

    duration = ffprobe_duration(src)
    chunk = max(15.0, min(args.chunk_seconds, 300.0))
    print(f"Duration ~{duration:.1f}s, chunk={chunk:.0f}s, model={args.model!r}")

    out_path = os.path.abspath(args.output)
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    ck_path, partial_path = checkpoint_paths(out_path)
    src_size = os.path.getsize(src)
    plan = chunk_plan(duration, chunk)

    if args.fresh:
        for p in (ck_path, partial_path):
            try:
                os.unlink(p)
            except OSError:
                pass

    merged_body: list[str] = []
    resume_from = load_checkpoint(
        ck_path,
        source_path=src,
        source_size=src_size,
        duration=duration,
        model=args.model,
        chunk_seconds=chunk,
    )
    if resume_from:
        merged_body, _next = resume_from
        print(
            f"Resuming from checkpoint ({len(merged_body)}/{len(plan)} chunks, "
            f"~{100.0 * len(merged_body) / max(len(plan), 1):.0f}% done). "
            f"Use --fresh to restart."
        )
    elif os.path.isfile(ck_path):
        print(
            "Ignoring stale checkpoint (input, duration, model, or chunk size changed).",
            file=sys.stderr,
        )

    with tempfile.TemporaryDirectory() as tmp:
        for idx, (offset, dur) in enumerate(plan, start=1):
            if idx <= len(merged_body):
                continue
            wav = os.path.join(tmp, f"slice_{idx:04d}.wav")
            print(f"  chunk {idx}/{len(plan)}: {offset:.1f}s + {dur:.1f}s → OpenRouter …")
            ffmpeg_slice_wav(src, offset, dur, wav)
            hint = f"part {idx}, global offset {offset:.1f}s, slice duration {dur:.1f}s"
            raw_vtt = transcribe_chunk_wav(api_key, args.model, wav, hint)
            if not raw_vtt.upper().startswith("WEBVTT"):
                raise SystemExit(
                    f"Chunk {idx}: model did not return WEBVTT. First 500 chars:\n{raw_vtt[:500]}"
                )
            body = vtt_body_only(raw_vtt)
            shifted = shift_vtt_timestamps(body, offset) if offset > 0 else body
            merged_body.append(shifted.strip())
            next_offset = sum(plan[i][1] for i in range(len(merged_body)))
            save_progress(
                json_path=ck_path,
                partial_vtt_path=partial_path,
                source_path=src,
                source_size=src_size,
                duration=duration,
                model=args.model,
                chunk_seconds=chunk,
                segments=merged_body,
                next_offset=next_offset,
            )

    final = "WEBVTT\n\n" + "\n\n".join(merged_body) + "\n"
    write_atomic(out_path, final)
    for p in (ck_path, partial_path):
        try:
            os.unlink(p)
        except OSError:
            pass
    print(f"Wrote {out_path} ({len(final)} bytes)")


if __name__ == "__main__":
    main()
