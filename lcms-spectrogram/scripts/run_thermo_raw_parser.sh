#!/bin/bash
set -euo pipefail

if [ "$#" -lt 2 ]; then
  echo "Usage: $0 <input.raw> <output_dir>" >&2
  exit 2
fi

INPUT_PATH="$1"
OUTPUT_DIR="$2"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
PARSER_DIR="${PROJECT_ROOT}/ThermoRawFileParser"
PARSER_PROJECT="${PARSER_DIR}/ThermoRawFileParser.csproj"
RAW_READER_PACKAGES_DIR="${THERMO_RAW_READER_PACKAGES_DIR:-${PROJECT_ROOT}/ThermoRawFileReaderPackages/Libs/NetCore/Net8}"
RELEASE_DIR="${THERMO_RAW_PARSER_RELEASE_DIR:-${PROJECT_ROOT}/.tools/ThermoRawFileParser-osx-arm64}"
RELEASE_BIN_DIR="${RELEASE_DIR}/osx-arm64"
HOST_ARCH="$(uname -m)"

mkdir -p "${OUTPUT_DIR}"

ARGS=(
  "-i=${INPUT_PATH}"
  "-o=${OUTPUT_DIR}"
  "-f=1"
  "-m=2"
)

if [ -n "${THERMO_RAW_PARSER_BIN:-}" ]; then
  if [[ "${THERMO_RAW_PARSER_BIN}" == *.dll ]]; then
    exec dotnet "${THERMO_RAW_PARSER_BIN}" "${ARGS[@]}"
  fi
  exec "${THERMO_RAW_PARSER_BIN}" "${ARGS[@]}"
fi

run_with_optional_rosetta() {
  local binary="$1"
  local binary_arch="$2"
  if [ "${HOST_ARCH}" = "arm64" ] && [ "${binary_arch}" = "x64" ]; then
    exec arch -x86_64 "${binary}" "${ARGS[@]}"
  fi
  exec "${binary}" "${ARGS[@]}"
}

PARSER_BIN_CANDIDATES=(
  "${PARSER_DIR}/publish/osx-x64/ThermoRawFileParser:x64"
  "${RELEASE_BIN_DIR}/ThermoRawFileParser:arm64"
  "${PARSER_DIR}/publish/osx-arm64/ThermoRawFileParser:arm64"
  "${PARSER_DIR}/bin/arm64/Release/net8.0/osx-arm64/publish/ThermoRawFileParser:arm64"
  "${PARSER_DIR}/bin/Release/net8.0/ThermoRawFileParser:x64"
)

for candidate in "${PARSER_BIN_CANDIDATES[@]}"; do
  IFS=":" read -r binary binary_arch <<< "${candidate}"
  if [ -x "${binary}" ]; then
    run_with_optional_rosetta "${binary}" "${binary_arch}"
  fi
done

PARSER_DLL_CANDIDATES=(
  "${RELEASE_BIN_DIR}/ThermoRawFileParser.dll"
  "${PARSER_DIR}/publish/osx-arm64/ThermoRawFileParser.dll"
  "${PARSER_DIR}/bin/arm64/Release/net8.0/osx-arm64/ThermoRawFileParser.dll"
  "${PARSER_DIR}/bin/Release/net8.0/ThermoRawFileParser.dll"
)

for candidate in "${PARSER_DLL_CANDIDATES[@]}"; do
  if [ -f "${candidate}" ]; then
    exec dotnet "${candidate}" "${ARGS[@]}"
  fi
done

if [ ! -f "${PARSER_PROJECT}" ]; then
  echo "ThermoRawFileParser project not found at ${PARSER_PROJECT}" >&2
  exit 1
fi

DOTNET_RUN_ARGS=(
  dotnet
  run
  --project
  "${PARSER_PROJECT}"
  --configuration
  Release
)

if [ -d "${RAW_READER_PACKAGES_DIR}" ]; then
  DOTNET_RUN_ARGS+=(--source "${RAW_READER_PACKAGES_DIR}")
fi

DOTNET_RUN_ARGS+=(--source "https://api.nuget.org/v3/index.json" -- "${ARGS[@]}")

exec "${DOTNET_RUN_ARGS[@]}"
