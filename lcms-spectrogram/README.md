# LCMS Spectrogram

LCMS Spectrogram is a small web app for chemistry and mass spectrometry students who need a simple way to inspect LC-MS data without vendor-only desktop software.

It provides:

- Thermo `.raw` upload support through an optional backend converter
- direct `.mzML` upload support
- a TIC view, XIC view, spectrum view, and zoomable LC-MS map
- small chemistry helpers for charge-state `m/z`, isotope spacing, and ppm error
- a built-in demo dataset for quick testing

## Stack

- `backend/`: FastAPI API and LC-MS parsing logic
- `frontend/`: React + Vite UI
- `Dockerfile`: single-container production build that serves frontend and API from the same origin
- `docker-compose.yml`: Linux deployment entrypoint
- `ThermoRawFileParser/`: vendored ThermoRawFileParser source

In production, the backend serves the built frontend directly. That removes the hardcoded localhost dependency and makes reverse-proxy or Docker deployment much simpler.

## Local development

### Backend

```bash
uv sync --dev
uv run python main.py
```

The API starts on `http://127.0.0.1:8000`.

### Frontend

```bash
cd frontend
npm ci
npm run dev
```

The frontend starts on `http://127.0.0.1:5173`.

## Production deployment on Linux

### Default deployment

The default Docker target ships the web app without Thermo RAW conversion. Students can still use:

- direct `.mzML` uploads
- the built-in demo dataset

Steps:

```bash
cp .env.example .env
docker compose up --build -d
```

The app will be available on `http://<server>:8000` unless you change `LCMS_HTTP_PORT` in `.env`.

### Deployment with Thermo RAW conversion

The repo includes an opt-in Docker build target called `runtime-thermo`. It builds a Linux ThermoRawFileParser binary and wires it into the backend automatically.

To enable it:

```bash
cp .env.example .env
```

Set this in `.env`:

```dotenv
DOCKER_BUILD_TARGET=runtime-thermo
```

Then build and start:

```bash
docker compose up --build -d
```

Notes:

- This target is meant for Linux servers.
- Docker build will produce the correct Linux parser variant for `amd64` or `arm64`.
- Thermo RAW conversion is intentionally not the default target because the Thermo RawFileReader terms are more restrictive than the ThermoRawFileParser Apache-2.0 source license.
- The current session store is in-memory, so active sessions reset when the app process restarts.

## Runtime configuration

Environment variables used by the backend:

- `LCMS_HOST`: bind host, defaults to `0.0.0.0`
- `LCMS_PORT`: bind port, defaults to `8000`
- `PORT`: optional override for `LCMS_PORT`
- `LCMS_DATA_DIR`: writable session directory, defaults to `.data/sessions`
- `LCMS_FRONTEND_DIST_DIR`: location of the built frontend, defaults to `frontend/dist`
- `LCMS_CORS_ORIGINS`: comma-separated origins for cross-origin API access
- `THERMO_RAW_PARSER_BIN`: optional explicit path to ThermoRawFileParser
- `MSCONVERT_BIN`: optional explicit path to ProteoWizard `msconvert`
- `MSCONVERT_DOCKER_IMAGE`: optional Docker image for `msconvert`

## Validation

Backend:

```bash
uv run pytest
.venv/bin/python -m compileall backend main.py
```

Frontend:

```bash
cd frontend
npm run lint
npm run build
```

CI is defined in [`.github/workflows/ci.yml`](.github/workflows/ci.yml).

## ThermoRawFileParser licensing and citation

ThermoRawFileParser itself is distributed under Apache-2.0, but the RAW conversion path also relies on Thermo Fisher's RawFileReader license. That means the RAW-conversion feature has stricter distribution rules than the rest of the app.

Project notes:

- the app UI now includes the RawFileReader attribution notice
- the Docker setup keeps Thermo support behind the explicit `runtime-thermo` target
- third-party licensing and citation details are documented in [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md)

If you publish scientific work that uses ThermoRawFileParser, cite:

- Hulstaert N, Shofstahl J, Sachsenberg T, Walzer M, Barsnes H, Martens L, Perez-Riverol Y. *ThermoRawFileParser: Modular, Scalable, and Cross-Platform RAW File Conversion*. Journal of Proteome Research. 2020;19(1):537-542. DOI: `10.1021/acs.jproteome.9b00328`

## Open-source housekeeping

This repository currently does not define its own top-level project license. If you plan to publish it as open source, add a root `LICENSE` file before release so downstream users know what they are allowed to do with your code.
