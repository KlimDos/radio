"""
Resolve CLI paths whether you run from repo root or from scripts/.

Input files: try cwd first, then repository root.
Output files: prefer cwd if parent exists, else repo root, else repo/src (for paths like static/captions/…).
"""
from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent


def resolve_input_path(raw: str) -> Path:
    """Return path to an existing file (cwd, then repo root)."""
    p = Path(raw)
    if p.is_absolute():
        if not p.is_file():
            raise FileNotFoundError(str(p))
        return p
    a = Path.cwd() / p
    if a.is_file():
        return a.resolve()
    b = REPO_ROOT / p
    if b.is_file():
        return b.resolve()
    raise FileNotFoundError(f"{raw!r} not found (cwd={Path.cwd()}, repo={REPO_ROOT})")


def resolve_output_path(raw: str) -> Path:
    """Path for writing; parents are created. Works for static/captions/… from scripts/."""
    p = Path(raw)
    if p.is_absolute():
        p.parent.mkdir(parents=True, exist_ok=True)
        return p
    candidates: list[Path] = []
    for base in (Path.cwd(), REPO_ROOT, REPO_ROOT / "src"):
        cand = base / p
        if cand.parent.exists():
            candidates.append(cand)
    if candidates:
        out = candidates[0]
    else:
        # e.g. run from scripts/: -o static/captions/foo.vtt → src/static/…
        if p.parts and p.parts[0] == "static":
            out = REPO_ROOT / "src" / p
        else:
            out = REPO_ROOT / p
    out.parent.mkdir(parents=True, exist_ok=True)
    return out
