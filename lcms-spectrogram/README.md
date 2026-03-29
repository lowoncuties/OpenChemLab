# LCMS Spectrogram

LCMS Spectrogram is a small web app for chemistry and mass spectrometry students who need a simple way to inspect LC-MS data without vendor-only desktop software.

It provides:

- optional Thermo `.raw` upload support through an installed backend converter
- direct `.mzML` upload support
- a TIC view, XIC view, spectrum view, and zoomable LC-MS map
- small chemistry helpers for charge-state `m/z`, isotope spacing, and ppm error
- a built-in demo dataset for quick testing

## Repository layout

- `backend/`: FastAPI API and LC-MS parsing logic
- `frontend/`: React + Vite UI
- `Dockerfile`: single-container production image
- `docker-compose.yml`: Linux deployment entrypoint
- `.tools/`: local, ignored install location for ThermoRawFileParser releases

`ThermoRawFileParser` is intentionally not committed in this repository. If you want RAW conversion, install it separately.

## Quick start

### 1. Clone and enter the app

```bash
cd OpenChemLab/lcms-spectrogram
```

### 2. Backend dependencies

```bash
uv sync --dev
```

### 3. Frontend dependencies

```bash
cd frontend
npm ci
cd ..
```

### 4. Run the app locally

Backend:

```bash
uv run python main.py
```

Frontend:

```bash
cd frontend
npm run dev
```

Open:

- frontend: `http://127.0.0.1:5173`
- backend API: `http://127.0.0.1:8000`

If you do nothing else, the app already works with:

- `.mzML` uploads
- the built-in demo dataset

## Optional Thermo RAW support

RAW conversion is optional. To enable it, install an official ThermoRawFileParser release separately.

Recommended setup:

1. Download the appropriate release for your platform from the official release page:
   <https://github.com/compomics/ThermoRawFileParser/releases>
2. Extract it into:

```bash
.tools/ThermoRawFileParser/
```

3. Make sure the executable ends up somewhere under that directory, for example:

```text
.tools/ThermoRawFileParser/ThermoRawFileParser
```

or:

```text
.tools/ThermoRawFileParser/linux-x64/ThermoRawFileParser
```

Alternative options:

- set `THERMO_RAW_PARSER_BIN` to the executable or DLL path
- set `THERMO_RAW_PARSER_DIR` to the extracted release directory
- install `ThermoRawFileParser` on the system `PATH`

If you already have a local ThermoRawFileParser source checkout, keep it out of git and point this app at the built executable or extracted release instead of committing the source tree.

The app checks for ThermoRawFileParser in this order:

1. `THERMO_RAW_PARSER_BIN`
2. `THERMO_RAW_PARSER_DIR`
3. `.tools/ThermoRawFileParser/` and similar `.tools/ThermoRawFileParser*` directories
4. system `PATH`

If ThermoRawFileParser is not installed, `.raw` uploads fail gracefully and users can still work with `.mzML` or the demo dataset.

## Docker deployment on Linux

### Minimal deployment

```bash
cp .env.example .env
docker compose up --build -d
```

This gives you a working deployment for:

- `.mzML` uploads
- the built-in demo dataset

The app will be available on `http://<server>:8000` unless you change `LCMS_HTTP_PORT` in `.env`.

### Docker deployment with Thermo RAW support

1. Download and extract ThermoRawFileParser into:

```bash
./.tools/ThermoRawFileParser/
```

2. Start the stack:

```bash
cp .env.example .env
docker compose up --build -d
```

`docker-compose.yml` mounts `./.tools` into the container automatically, so the backend can discover the parser without committing it to git.

If the executable lives in a custom location inside the container, set one of these in `.env`:

```dotenv
THERMO_RAW_PARSER_BIN=/app/.tools/ThermoRawFileParser/ThermoRawFileParser
THERMO_RAW_PARSER_DIR=/app/.tools/ThermoRawFileParser
```

Notes:

- the current session store is in-memory, so active sessions reset when the app process restarts
- if you want the least restrictive deployment path, keep RAW conversion optional and rely on `.mzML`

## Runtime configuration

Environment variables used by the backend:

- `LCMS_HOST`: bind host, defaults to `0.0.0.0`
- `LCMS_PORT`: bind port, defaults to `8000`
- `PORT`: optional override for `LCMS_PORT`
- `LCMS_DATA_DIR`: writable session directory, defaults to `.data/sessions`
- `LCMS_FRONTEND_DIST_DIR`: location of the built frontend, defaults to `frontend/dist`
- `LCMS_CORS_ORIGINS`: comma-separated origins for cross-origin API access
- `THERMO_RAW_PARSER_BIN`: explicit ThermoRawFileParser executable or DLL path
- `THERMO_RAW_PARSER_DIR`: directory containing an extracted ThermoRawFileParser release
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

- the app UI includes the RawFileReader attribution notice
- ThermoRawFileParser is not vendored into this repository
- third-party licensing and citation details are documented in [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md)

If you publish scientific work that uses ThermoRawFileParser, cite:

- Hulstaert N, Shofstahl J, Sachsenberg T, Walzer M, Barsnes H, Martens L, Perez-Riverol Y. *ThermoRawFileParser: Modular, Scalable, and Cross-Platform RAW File Conversion*. Journal of Proteome Research. 2020;19(1):537-542. DOI: `10.1021/acs.jproteome.9b00328`

## Open-source housekeeping

This repository currently does not define its own top-level project license. If you plan to publish it as open source, add a root `LICENSE` file before release so downstream users know what they are allowed to do with your code.
