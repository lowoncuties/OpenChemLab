from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True, slots=True)
class Settings:
    host: str
    port: int
    data_dir: Path
    frontend_dist_dir: Path
    cors_origins: list[str]
    max_upload_bytes: int
    upload_rate_limit_count: int
    upload_rate_limit_window_seconds: int


def _split_csv(value: str | None) -> list[str]:
    if not value:
        return []
    return [item.strip() for item in value.split(",") if item.strip()]


def _positive_int(env_name: str, default: str) -> int:
    value = int(os.environ.get(env_name, default))
    if value <= 0:
        raise ValueError(f"{env_name} must be greater than zero.")
    return value


def get_settings() -> Settings:
    base_dir = Path(__file__).resolve().parents[2]
    data_dir = Path(os.environ.get("LCMS_DATA_DIR", base_dir / ".data" / "sessions")).expanduser()
    frontend_dist_dir = Path(
        os.environ.get("LCMS_FRONTEND_DIST_DIR", base_dir / "frontend" / "dist")
    ).expanduser()
    max_upload_mb = _positive_int("LCMS_MAX_UPLOAD_MB", "500")
    cors_origins = _split_csv(
        os.environ.get(
            "LCMS_CORS_ORIGINS",
            "http://127.0.0.1:5173,http://localhost:5173",
        )
    )
    port = int(os.environ.get("PORT", os.environ.get("LCMS_PORT", "8000")))

    return Settings(
        host=os.environ.get("LCMS_HOST", "0.0.0.0"),
        port=port,
        data_dir=data_dir,
        frontend_dist_dir=frontend_dist_dir,
        cors_origins=cors_origins,
        max_upload_bytes=max_upload_mb * 1024 * 1024,
        upload_rate_limit_count=_positive_int("LCMS_UPLOAD_RATE_LIMIT_COUNT", "25"),
        upload_rate_limit_window_seconds=_positive_int(
            "LCMS_UPLOAD_RATE_LIMIT_WINDOW_SECONDS", "600"
        ),
    )


SETTINGS = get_settings()
