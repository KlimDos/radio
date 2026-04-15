# Radio (Vice City style)

Flask app that serves a Vice City–styled in-browser radio UI: carousel backgrounds, menu navigation, volume (0–10), and keyboard controls.

## Requirements

- Python 3.12+ (matches the Docker image)
- Optional: Docker

## Run locally

```bash
cd src
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
export ARTEFACT_VERSION=dev   # optional; shown in the corner overlay
flask --app app run --debug
```

Open `http://127.0.0.1:5000/` for the radio. `/bank` is the landing page from `index.html`.

## Carousel backgrounds (uniform 1920×1080)

If `src/static/bg-normalized/` contains JPEGs (see below), the app uses **only** those so every slide matches **1920×1080** and the same aspect ratio. Otherwise it falls back to `bg-*.jpg` and `bg-art/*` as before.

Regenerate after adding images under `src/static/bg-art/`:

```bash
pip install Pillow
python3 scripts/normalize_backgrounds.py
```

## Captions (WebVTT) via OpenRouter

The radio page loads `static/captions/<same-name-as-audio>.vtt` for `audio2`. The transcription script uses the chat API with **`input_audio`** (base64 WAV per chunk). Only models that list **audio** under `input_modalities` on OpenRouter work; plain **`openai/gpt-4o`** does not and returns HTTP 404.

**Accuracy vs catalog:** OpenAI’s dedicated STT IDs **`gpt-4o-transcribe`** / **`gpt-4o-mini-transcribe`** (often best WER on OpenAI’s side) are **not** always exposed on OpenRouter—check the [models filter (audio input)](https://openrouter.ai/models?fmt=cards&input_modalities=audio). When they appear as e.g. `openai/gpt-4o-transcribe`, set `OPENROUTER_MODEL` to that. Until then, strong choices on OpenRouter include:

| Priority | Model (OpenRouter id) | Notes |
|----------|------------------------|--------|
| **Default (script)** | **`google/gemini-2.5-pro`** | Flagship multimodal with audio: long tracks, speech over music, mixed radio. |
| OpenAI audio-native | `openai/gpt-audio` / `openai/gpt-audio-mini` | Strong chat+audio; mini is cheaper. |
| Other | `mistralai/voxtral-small-24b-2507` | Voxtral-style ASR + reasoning. |

1. Install **ffmpeg** / **ffprobe** (required: the full `.ogg` is too large to send as one base64 payload; the script slices it into WAV chunks).
2. Set **`OPENROUTER_API_KEY`** (never commit it). Optionally **`OPENROUTER_MODEL`** (default **`google/gemini-2.5-pro`**) and **`CHUNK_SECONDS`** (default `90`, smaller = smaller requests).

**Resume:** after each successful chunk the script writes **`your.vtt.progress.json`** and **`your.vtt.partial.vtt`** next to **`your.vtt`**. Run the same command again to continue; an existing checkpoint is skipped if the source file size, duration, model, or chunk length no longer matches. **`--fresh`** clears checkpoint files and starts from the beginning. When the full file is done, the `.progress.json` and `.partial.vtt` files are deleted automatically.

```bash
export OPENROUTER_API_KEY=sk-or-v1-...
# optional: export OPENROUTER_MODEL=openai/gpt-audio
# optional: export CHUNK_SECONDS=60
python3 scripts/transcribe_openrouter.py
# same command again after a crash → resumes
```

Output: `src/static/captions/grand-theft-auto-gta-vice.vtt`. Costs follow OpenRouter pricing for the chosen model and total audio length.

## Environment

| Variable            | Meaning                                      |
|---------------------|----------------------------------------------|
| `ARTEFACT_VERSION`  | Build string shown in the UI (also in CI)   |
| `REPO_URL`          | Git URL for the **repo** row (default: this GitHub repo) |
| `OPENROUTER_API_KEY` | Only for local script `scripts/transcribe_openrouter.py` (not used by Flask in production unless you wire it in) |
| `OPENROUTER_MODEL`   | Optional; default `google/gemini-2.5-pro` (must support audio input on OpenRouter) |
| `CHUNK_SECONDS`      | Optional; slice length for that script (default `90`) |

If unset, the template shows `local` for the version label.

## Controls (radio page)

Click the page so the body has focus, then:

- **Arrow Up / Down** — move menu highlight
- On **volume**: **Arrow Left / Right** or **`[` / `]`** — decrease / increase volume (0–10)
- **Enter** — **radio** toggles play/stop; **repo** (last row) opens the Git link in a new tab
- Mouse: click **off/on** to toggle the radio

## Test (quick)

```bash
cd src
source .venv/bin/activate
pip install -r requirements.txt
ARTEFACT_VERSION=test python3 -c "
from app import app
c = app.test_client()
assert c.get('/').status_code == 200
assert c.get('/bank').status_code == 200
print('ok')
"
```

## Docker

From the repository root:

```bash
docker build --build-arg Build=my-tag -t radio:local .
docker run --rm -p 8080:8080 radio:local
```

Open `http://127.0.0.1:8080/`. The app listens on port **8080** inside the container.

## CI

On push to `main`, GitHub Actions (`.github/workflows/build.yml`) builds the image, writes `src/.env` with `ARTEFACT_VERSION`, and pushes to Docker Hub when `DOCKERHUB_USERNAME` and `DOCKERHUB_TOKEN` secrets are set.
