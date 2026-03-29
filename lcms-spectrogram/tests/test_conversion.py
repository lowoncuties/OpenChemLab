from __future__ import annotations

from pathlib import Path

from backend.app import conversion


def test_thermo_raw_parser_command_prefers_explicit_binary(
    monkeypatch,
    tmp_path: Path,
) -> None:
    parser_bin = tmp_path / "ThermoRawFileParser"
    parser_bin.write_text("", encoding="utf-8")
    parser_bin.chmod(0o755)
    monkeypatch.setenv("THERMO_RAW_PARSER_BIN", str(parser_bin))

    command = conversion._thermo_raw_parser_command(Path("input.raw"), Path("out"))

    assert command == [
        str(parser_bin),
        "-i=input.raw",
        "-o=out",
        "-f=1",
        "-m=2",
    ]


def test_thermo_raw_parser_command_falls_back_to_wrapper(monkeypatch) -> None:
    monkeypatch.delenv("THERMO_RAW_PARSER_BIN", raising=False)
    monkeypatch.setattr(conversion.shutil, "which", lambda _: None)

    command = conversion._thermo_raw_parser_command(Path("input.raw"), Path("out"))

    assert command == [
        str(conversion.THERMO_RAW_PARSER_SCRIPT),
        "input.raw",
        "out",
    ]
