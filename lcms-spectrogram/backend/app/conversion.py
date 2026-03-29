from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[2]
LOCAL_THERMO_RAW_PARSER_DIR = BASE_DIR / "ThermoRawFileParser"
LOCAL_THERMO_RAW_PARSER_PROJECT = LOCAL_THERMO_RAW_PARSER_DIR / "ThermoRawFileParser.csproj"
LOCAL_THERMO_RAW_PARSER_SCRIPT = BASE_DIR / "scripts" / "run_thermo_raw_parser.sh"


class ConversionError(RuntimeError):
    pass


def _thermo_raw_parser_args(input_path: Path, output_dir: Path) -> list[str]:
    return [
        f"-i={input_path}",
        f"-o={output_dir}",
        "-f=1",
        "-m=2",
    ]


def _thermo_raw_parser_command(input_path: Path, output_dir: Path) -> list[str] | None:
    parser_bin = os.environ.get("THERMO_RAW_PARSER_BIN")
    dotnet_bin = shutil.which("dotnet")
    args = _thermo_raw_parser_args(input_path, output_dir)

    if parser_bin:
        parser_path = Path(parser_bin)
        if parser_path.suffix == ".dll":
            if not dotnet_bin:
                raise ConversionError(
                    "`THERMO_RAW_PARSER_BIN` points to a .dll but `dotnet` is not installed."
                )
            return [dotnet_bin, str(parser_path), *args]
        return [str(parser_path), *args]

    if LOCAL_THERMO_RAW_PARSER_SCRIPT.exists():
        return [
            str(LOCAL_THERMO_RAW_PARSER_SCRIPT),
            str(input_path),
            str(output_dir),
        ]

    if not LOCAL_THERMO_RAW_PARSER_PROJECT.exists():
        return None

    release_dll = (
        LOCAL_THERMO_RAW_PARSER_DIR / "bin" / "Release" / "net8.0" / "ThermoRawFileParser.dll"
    )
    release_binary = LOCAL_THERMO_RAW_PARSER_DIR / "bin" / "Release" / "net8.0" / "ThermoRawFileParser"
    if release_binary.exists():
        return [str(release_binary), *args]
    if release_dll.exists():
        if not dotnet_bin:
            raise ConversionError(
                "A local ThermoRawFileParser build exists but `dotnet` is not installed."
            )
        return [dotnet_bin, str(release_dll), *args]

    if dotnet_bin:
        return [
            dotnet_bin,
            "run",
            "--project",
            str(LOCAL_THERMO_RAW_PARSER_PROJECT),
            "--configuration",
            "Release",
            "--",
            *args,
        ]

    return None


def _local_msconvert_command(input_path: Path, output_dir: Path) -> list[str] | None:
    msconvert_bin = os.environ.get("MSCONVERT_BIN") or shutil.which("msconvert")
    if not msconvert_bin:
        return None
    return [
        msconvert_bin,
        str(input_path),
        "--mzML",
        "--64",
        "--outdir",
        str(output_dir),
    ]


def _docker_msconvert_command(input_path: Path, output_dir: Path) -> list[str] | None:
    docker_image = os.environ.get("MSCONVERT_DOCKER_IMAGE")
    docker_bin = shutil.which("docker")
    if not docker_image or not docker_bin:
        return None

    mount_dir = input_path.parent.resolve()
    input_name = input_path.name
    output_name = output_dir.name
    return [
        docker_bin,
        "run",
        "--rm",
        "-e",
        "WINEDEBUG=-all",
        "-v",
        f"{mount_dir}:/data",
        docker_image,
        "wine",
        "msconvert",
        f"/data/{input_name}",
        "--mzML",
        "--64",
        "--outdir",
        f"/data/{output_name}",
    ]


def _find_mzml_file(output_dir: Path) -> Path | None:
    matches = sorted(output_dir.glob("*.mzML"))
    if matches:
        return matches[0]
    return None


def _run_command(command: list[str], timeout_seconds: int) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        capture_output=True,
        text=True,
        check=False,
        timeout=timeout_seconds,
    )


def convert_raw_to_mzml(input_path: Path, output_dir: Path) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)

    converter_candidates: list[tuple[str, list[str] | None, int]] = [
        ("thermo-raw-parser", _thermo_raw_parser_command(input_path, output_dir), 600),
        ("msconvert", _local_msconvert_command(input_path, output_dir), 180),
        ("msconvert-docker", _docker_msconvert_command(input_path, output_dir), 300),
    ]
    errors: list[str] = []

    for mode, command, timeout_seconds in converter_candidates:
        if not command:
            continue

        completed = _run_command(command, timeout_seconds=timeout_seconds)
        if completed.returncode == 0:
            output_file = _find_mzml_file(output_dir)
            if output_file:
                return output_file

            errors.append(
                f"{mode}: command succeeded but no `.mzML` file was produced in `{output_dir}`."
            )
            continue

        stderr = completed.stderr.strip() or completed.stdout.strip() or "No error output returned."
        errors.append(
            f"{mode}: exit code {completed.returncode}. {stderr}"
        )

    if not errors:
        raise ConversionError(
            "No RAW converter is configured. Use the bundled `ThermoRawFileParser`, set "
            "`THERMO_RAW_PARSER_BIN`, install ProteoWizard `msconvert`, or configure "
            "`MSCONVERT_DOCKER_IMAGE` for Docker mode."
        )

    raise ConversionError("RAW conversion failed. " + " | ".join(errors))
