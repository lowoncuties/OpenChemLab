from __future__ import annotations

from math import ceil
from pathlib import Path

import numpy as np
from pyteomics import mzml

from .models import DatasetSummary, ParsedDataset, Spectrum


def _normalize_rt_minutes(scan_start_time: float) -> float:
    if scan_start_time > 120:
        return scan_start_time / 60
    return scan_start_time


def _peak_pick(mz_values: np.ndarray, intensity_values: np.ndarray, max_peaks: int) -> list[dict[str, float]]:
    if mz_values.size == 0 or intensity_values.size == 0:
        return []

    if intensity_values.size < 3:
        ranked = np.argsort(intensity_values)[::-1][:max_peaks]
    else:
        local_maxima = np.where(
            (intensity_values[1:-1] >= intensity_values[:-2])
            & (intensity_values[1:-1] >= intensity_values[2:])
        )[0] + 1
        if local_maxima.size == 0:
            local_maxima = np.argsort(intensity_values)[::-1][:max_peaks]

        threshold = np.percentile(intensity_values, 75)
        ranked = local_maxima[intensity_values[local_maxima] >= threshold]
        if ranked.size == 0:
            ranked = local_maxima
        ranked = ranked[np.argsort(intensity_values[ranked])[::-1][:max_peaks]]

    ranked = ranked[np.argsort(mz_values[ranked])]
    return [
        {
            "mz": float(mz_values[index]),
            "intensity": float(intensity_values[index]),
        }
        for index in ranked
    ]


def _spectrum_from_reader_entry(entry: dict[str, object], fallback_scan_id: int) -> Spectrum | None:
    mz_values = np.asarray(entry.get("m/z array", []), dtype=float)
    intensity_values = np.asarray(entry.get("intensity array", []), dtype=float)
    if mz_values.size == 0 or intensity_values.size == 0:
        return None

    ms_level = int(entry.get("ms level", 1))
    scan_list = entry.get("scanList", {})
    scan_data = scan_list.get("scan", [{}])[0] if isinstance(scan_list, dict) else {}
    scan_start_time = float(scan_data.get("scan start time", 0.0))
    rt_minutes = _normalize_rt_minutes(scan_start_time)
    scan_id = str(entry.get("id", f"scan={fallback_scan_id}"))

    return Spectrum(
        scan_id=scan_id,
        rt_minutes=rt_minutes,
        ms_level=ms_level,
        mz_values=mz_values,
        intensity_values=intensity_values,
    )


def parse_mzml_file(path: Path) -> ParsedDataset:
    spectra: list[Spectrum] = []
    skipped_ms_levels = 0
    with mzml.MzML(str(path)) as reader:
        for index, entry in enumerate(reader):
            spectrum = _spectrum_from_reader_entry(entry, fallback_scan_id=index)
            if not spectrum:
                continue
            if spectrum.ms_level != 1:
                skipped_ms_levels += 1
                continue
            spectra.append(spectrum)

    if not spectra:
        raise ValueError("No MS1 spectra were found in the mzML file.")

    tic = [
        {
            "rt": float(spectrum.rt_minutes),
            "intensity": float(np.sum(spectrum.intensity_values)),
        }
        for spectrum in spectra
    ]

    heatmap_points: list[dict[str, float]] = []
    stride = max(1, ceil(len(spectra) / 220))
    for spectrum in spectra[::stride]:
        for peak in _peak_pick(spectrum.mz_values, spectrum.intensity_values, max_peaks=10):
            heatmap_points.append(
                {
                    "rt": float(spectrum.rt_minutes),
                    "mz": peak["mz"],
                    "intensity": peak["intensity"],
                }
            )

    mz_min = min(float(np.min(spectrum.mz_values)) for spectrum in spectra)
    mz_max = max(float(np.max(spectrum.mz_values)) for spectrum in spectra)
    intensity_max = max(float(np.max(spectrum.intensity_values)) for spectrum in spectra)
    rt_min = min(spectrum.rt_minutes for spectrum in spectra)
    rt_max = max(spectrum.rt_minutes for spectrum in spectra)

    notes = [
        "Heatmap points are peak-picked and downsampled for responsive navigation.",
        "TIC and extracted ion chromatograms are based on MS1 scans only.",
    ]
    if skipped_ms_levels:
        notes.append(f"Ignored {skipped_ms_levels} non-MS1 spectra in the overview.")

    summary = DatasetSummary(
        scan_count=len(spectra),
        rt_min=rt_min,
        rt_max=rt_max,
        mz_min=mz_min,
        mz_max=mz_max,
        intensity_max=intensity_max,
        source_name=path.name,
        source_kind=path.suffix.lower().lstrip(".") or "unknown",
        approximate_mass_range=(mz_min, mz_max),
    )

    return ParsedDataset(
        summary=summary,
        spectra=spectra,
        tic=tic,
        heatmap_points=heatmap_points,
        notes=notes,
    )


def nearest_spectrum(dataset: ParsedDataset, rt_minutes: float) -> Spectrum:
    return min(dataset.spectra, key=lambda spectrum: abs(spectrum.rt_minutes - rt_minutes))


def serialize_spectrum(spectrum: Spectrum, max_points: int = 2500) -> dict[str, object]:
    point_count = spectrum.mz_values.size
    stride = max(1, ceil(point_count / max_points))
    mz_values = spectrum.mz_values[::stride]
    intensity_values = spectrum.intensity_values[::stride]

    return {
        "scanId": spectrum.scan_id,
        "rt": float(spectrum.rt_minutes),
        "msLevel": spectrum.ms_level,
        "mz": [float(value) for value in mz_values],
        "intensity": [float(value) for value in intensity_values],
        "peakLabels": _peak_pick(spectrum.mz_values, spectrum.intensity_values, max_peaks=18),
    }


def build_xic(dataset: ParsedDataset, target_mz: float, ppm_tolerance: float) -> list[dict[str, float]]:
    tolerance = target_mz * ppm_tolerance / 1_000_000
    lower = target_mz - tolerance
    upper = target_mz + tolerance
    trace: list[dict[str, float]] = []
    for spectrum in dataset.spectra:
        window = (spectrum.mz_values >= lower) & (spectrum.mz_values <= upper)
        intensity = float(np.sum(spectrum.intensity_values[window])) if np.any(window) else 0.0
        trace.append({"rt": float(spectrum.rt_minutes), "intensity": intensity})
    return trace
