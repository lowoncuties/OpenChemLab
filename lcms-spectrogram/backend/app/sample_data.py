from __future__ import annotations

import math

import numpy as np

from .models import DatasetSummary, ParsedDataset, Spectrum
from .parser import _peak_pick


def generate_demo_dataset() -> ParsedDataset:
    rng = np.random.default_rng(42)
    mz_axis = np.linspace(100, 900, 900)
    rt_axis = np.linspace(0.3, 18.0, 180)
    compounds = [
        {"mz": 152.071, "center": 3.2, "width": 0.7, "height": 220_000},
        {"mz": 245.114, "center": 6.8, "width": 1.0, "height": 360_000},
        {"mz": 377.219, "center": 10.4, "width": 0.9, "height": 420_000},
        {"mz": 523.288, "center": 14.2, "width": 1.3, "height": 300_000},
    ]

    spectra: list[Spectrum] = []
    tic: list[dict[str, float]] = []
    heatmap_points: list[dict[str, float]] = []

    for index, rt in enumerate(rt_axis):
        intensities = rng.uniform(0, 1200, mz_axis.shape[0])
        for compound in compounds:
            chromatographic_gain = math.exp(-((rt - compound["center"]) ** 2) / (2 * compound["width"] ** 2))
            profile = np.exp(-((mz_axis - compound["mz"]) ** 2) / (2 * 0.22**2))
            intensities += chromatographic_gain * compound["height"] * profile
            intensities += chromatographic_gain * compound["height"] * 0.18 * np.exp(
                -((mz_axis - (compound["mz"] + 0.5)) ** 2) / (2 * 0.18**2)
            )

        spectrum = Spectrum(
            scan_id=f"demo-scan-{index + 1}",
            rt_minutes=float(rt),
            ms_level=1,
            mz_values=mz_axis.copy(),
            intensity_values=intensities,
        )
        spectra.append(spectrum)
        tic.append({"rt": float(rt), "intensity": float(np.sum(intensities))})
        for peak in _peak_pick(mz_axis, intensities, max_peaks=8):
            heatmap_points.append({"rt": float(rt), "mz": peak["mz"], "intensity": peak["intensity"]})

    summary = DatasetSummary(
        scan_count=len(spectra),
        rt_min=float(rt_axis.min()),
        rt_max=float(rt_axis.max()),
        mz_min=float(mz_axis.min()),
        mz_max=float(mz_axis.max()),
        intensity_max=float(max(np.max(spectrum.intensity_values) for spectrum in spectra)),
        source_name="demo-lcms.mzML",
        source_kind="demo",
        approximate_mass_range=(float(mz_axis.min()), float(mz_axis.max())),
    )
    notes = [
        "Demo dataset is synthetic and useful for UI testing when vendor RAW conversion is unavailable.",
        "Peak labels mark local maxima in each spectrum for quick inspection.",
    ]

    return ParsedDataset(
        summary=summary,
        spectra=spectra,
        tic=tic,
        heatmap_points=heatmap_points,
        notes=notes,
    )
