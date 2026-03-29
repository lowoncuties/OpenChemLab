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


def _split_csv(value: str | None) -> list[str]:
    if not value:
        return []
    return [item.strip() for item in value.split(",") if item.strip()]


def get_settings() -> Settings:
    base_dir = Path(__file__).resolve().parents[2]
    data_dir = Path(os.environ.get("LCMS_DATA_DIR", base_dir / ".data" / "sessions")).expanduser()
    frontend_dist_dir = Path(
        os.environ.get("LCMS_FRONTEND_DIST_DIR", base_dir / "frontend" / "dist")
    ).expanduser()
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
    )


SETTINGS = get_settings()
