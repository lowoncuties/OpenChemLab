from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal

import numpy as np

SessionStatus = Literal["uploaded", "ready", "conversion_error", "parse_error"]


@dataclass(slots=True)
class Spectrum:
    scan_id: str
    rt_minutes: float
    ms_level: int
    mz_values: np.ndarray
    intensity_values: np.ndarray


@dataclass(slots=True)
class DatasetSummary:
    scan_count: int
    rt_min: float
    rt_max: float
    mz_min: float
    mz_max: float
    intensity_max: float
    source_name: str
    source_kind: str
    approximate_mass_range: tuple[float, float]

    def to_dict(self) -> dict[str, float | int | str | list[float]]:
        return {
            "scanCount": self.scan_count,
            "rtMin": self.rt_min,
            "rtMax": self.rt_max,
            "mzMin": self.mz_min,
            "mzMax": self.mz_max,
            "intensityMax": self.intensity_max,
            "sourceName": self.source_name,
            "sourceKind": self.source_kind,
            "approximateMassRange": list(self.approximate_mass_range),
        }


@dataclass(slots=True)
class ParsedDataset:
    summary: DatasetSummary
    spectra: list[Spectrum]
    tic: list[dict[str, float]]
    heatmap_points: list[dict[str, float]]
    notes: list[str] = field(default_factory=list)


@dataclass(slots=True)
class SessionRecord:
    session_id: str
    source_path: Path
    filename: str
    source_kind: str
    status: SessionStatus
    message: str
    converted_path: Path | None = None
    dataset: ParsedDataset | None = None
    notes: list[str] = field(default_factory=list)

    def to_response(self) -> dict[str, object]:
        response: dict[str, object] = {
            "sessionId": self.session_id,
            "status": self.status,
            "message": self.message,
            "filename": self.filename,
            "sourceKind": self.source_kind,
            "notes": self.notes,
        }
        if self.dataset:
            response["summary"] = self.dataset.summary.to_dict()
            response["tic"] = self.dataset.tic
            response["heatmapPoints"] = self.dataset.heatmap_points
            response["datasetNotes"] = self.dataset.notes
        return response
