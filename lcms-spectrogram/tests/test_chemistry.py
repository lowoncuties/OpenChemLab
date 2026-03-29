from __future__ import annotations

import pytest

from backend.app.chemistry import isotope_spacing_hint, neutral_mass_to_mz, ppm_error


def test_neutral_mass_to_mz_supports_positive_and_negative_charge() -> None:
    assert neutral_mass_to_mz(500.0, 2) == pytest.approx(251.007276466812)
    assert neutral_mass_to_mz(500.0, -2) == pytest.approx(251.007276466812)


def test_ppm_error_raises_when_theoretical_mz_is_zero() -> None:
    with pytest.raises(ValueError, match="non-zero"):
        ppm_error(100.0, 0.0)


def test_isotope_spacing_hint_uses_absolute_charge() -> None:
    assert isotope_spacing_hint(4) == pytest.approx(0.25)
    assert isotope_spacing_hint(-4) == pytest.approx(0.25)
