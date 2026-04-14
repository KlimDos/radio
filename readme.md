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

## Environment

| Variable            | Meaning                                      |
|---------------------|----------------------------------------------|
| `ARTEFACT_VERSION`  | Build string shown in the UI (also in CI)   |
| `REPO_URL`          | Git URL for the **repo** row (default: this GitHub repo) |

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
