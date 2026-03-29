# syntax=docker/dockerfile:1.7

FROM node:20-bookworm-slim AS frontend-build

ARG VITE_API_BASE_URL=""

WORKDIR /app/frontend

COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci

COPY frontend/ ./
ENV VITE_API_BASE_URL=${VITE_API_BASE_URL}
RUN npm run build


FROM mcr.microsoft.com/dotnet/sdk:8.0 AS thermo-builder

ARG TARGETARCH

WORKDIR /src

COPY ThermoRawFileParser/ ./ThermoRawFileParser/
COPY ThermoRawFileReaderPackages/ ./ThermoRawFileReaderPackages/

RUN set -eux; \
    case "${TARGETARCH:-amd64}" in \
      amd64) runtime_id="linux-x64" ;; \
      arm64) runtime_id="linux-arm64" ;; \
      *) echo "Unsupported TARGETARCH: ${TARGETARCH}" >&2; exit 1 ;; \
    esac; \
    package_source_args=""; \
    if [ -d "/src/ThermoRawFileReaderPackages/Libs/NetCore/Net8" ]; then \
      package_source_args="--source /src/ThermoRawFileReaderPackages/Libs/NetCore/Net8 --source https://api.nuget.org/v3/index.json"; \
    fi; \
    dotnet publish \
      ThermoRawFileParser/ThermoRawFileParser.csproj \
      --configuration Release \
      --runtime "${runtime_id}" \
      --self-contained true \
      ${package_source_args} \
      --output /opt/thermo


FROM python:3.13-slim AS runtime-base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    LCMS_HOST=0.0.0.0 \
    LCMS_PORT=8000 \
    LCMS_DATA_DIR=/app/.data/sessions

WORKDIR /app

COPY pyproject.toml README.md main.py ./
COPY backend/ ./backend/
COPY scripts/ ./scripts/

RUN chmod +x /app/scripts/run_thermo_raw_parser.sh \
    && python -m pip install --upgrade pip \
    && python -m pip install .

COPY --from=frontend-build /app/frontend/dist ./frontend/dist

RUN mkdir -p /app/.data/sessions

EXPOSE 8000
VOLUME ["/app/.data"]

CMD ["python", "main.py"]


FROM runtime-base AS runtime


FROM runtime-base AS runtime-thermo

COPY --from=thermo-builder /opt/thermo /app/.tools/ThermoRawFileParser
COPY ThermoRawFileParser/LICENSE /app/licenses/ThermoRawFileParser-LICENSE
COPY ThermoRawFileParser/THERMO_LICENSE /app/licenses/THERMO_LICENSE

ENV THERMO_RAW_PARSER_BIN=/app/.tools/ThermoRawFileParser/ThermoRawFileParser
