# syntax=docker/dockerfile:1.7

FROM node:20-bookworm-slim AS frontend-build

ARG VITE_API_BASE_URL=""

WORKDIR /app/frontend

COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci

COPY frontend/ ./
ENV VITE_API_BASE_URL=${VITE_API_BASE_URL}
RUN npm run build


FROM python:3.13-slim-bookworm AS runtime

# ThermoRawFileParser (.NET) needs ICU at runtime; slim images omit it.
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    LCMS_HOST=0.0.0.0 \
    LCMS_PORT=8000 \
    LCMS_DATA_DIR=/app/.data/sessions

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends libicu72 \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml README.md main.py ./
COPY backend/ ./backend/
COPY scripts/ ./scripts/

RUN chmod +x /app/scripts/run_thermo_raw_parser.sh \
    && python -m pip install --upgrade pip \
    && python -m pip install .

COPY --from=frontend-build /app/frontend/dist ./frontend/dist

RUN mkdir -p /app/.data/sessions /app/.tools

EXPOSE 8000
VOLUME ["/app/.data", "/app/.tools"]

CMD ["python", "main.py"]
