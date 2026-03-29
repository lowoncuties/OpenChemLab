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
TOOLS_DIR="${PROJECT_ROOT}/.tools"
DEFAULT_PARSER_DIR="${TOOLS_DIR}/ThermoRawFileParser"

mkdir -p "${OUTPUT_DIR}"

ARGS=(
  "-i=${INPUT_PATH}"
  "-o=${OUTPUT_DIR}"
  "-f=1"
  "-m=2"
)

run_parser() {
  local target="$1"
  if [[ "${target}" == *.dll ]]; then
    if ! command -v dotnet >/dev/null 2>&1; then
      echo "ThermoRawFileParser DLL found at ${target}, but dotnet is not installed." >&2
      exit 1
    fi
    exec dotnet "${target}" "${ARGS[@]}"
  fi
  exec "${target}" "${ARGS[@]}"
}

try_parser_dir() {
  local parser_dir="$1"
  [ -d "${parser_dir}" ] || return 1

  while IFS= read -r candidate; do
    if [ -x "${candidate}" ]; then
      run_parser "${candidate}"
    fi
  done < <(find "${parser_dir}" -maxdepth 5 -type f -name 'ThermoRawFileParser' | sort)

  while IFS= read -r candidate; do
    if [ -f "${candidate}" ]; then
      run_parser "${candidate}"
    fi
  done < <(find "${parser_dir}" -maxdepth 5 -type f -name 'ThermoRawFileParser.dll' | sort)

  return 1
}

if [ -n "${THERMO_RAW_PARSER_BIN:-}" ]; then
  run_parser "${THERMO_RAW_PARSER_BIN}"
fi

if [ -n "${THERMO_RAW_PARSER_DIR:-}" ]; then
  try_parser_dir "${THERMO_RAW_PARSER_DIR}"
fi

try_parser_dir "${DEFAULT_PARSER_DIR}"

while IFS= read -r candidate_dir; do
  try_parser_dir "${candidate_dir}"
done < <(find "${TOOLS_DIR}" -maxdepth 1 -mindepth 1 -type d -name 'ThermoRawFileParser*' 2>/dev/null | sort)

if command -v ThermoRawFileParser >/dev/null 2>&1; then
  run_parser "$(command -v ThermoRawFileParser)"
fi

cat >&2 <<EOF
ThermoRawFileParser was not found.

Install an official ThermoRawFileParser release into:
  ${DEFAULT_PARSER_DIR}

or set one of:
  THERMO_RAW_PARSER_BIN=/absolute/path/to/ThermoRawFileParser
  THERMO_RAW_PARSER_BIN=/absolute/path/to/ThermoRawFileParser.dll
  THERMO_RAW_PARSER_DIR=/absolute/path/to/extracted-release-directory
EOF

exit 1
