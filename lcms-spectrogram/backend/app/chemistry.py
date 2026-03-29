from __future__ import annotations

PROTON_MASS = 1.007276466812


def neutral_mass_to_mz(neutral_mass: float, charge: int) -> float:
    if charge == 0:
        raise ValueError("Charge must be non-zero.")
    absolute_charge = abs(charge)
    return (neutral_mass + absolute_charge * PROTON_MASS) / absolute_charge


def ppm_error(observed_mz: float, theoretical_mz: float) -> float:
    if theoretical_mz == 0:
        raise ValueError("Theoretical m/z must be non-zero.")
    return ((observed_mz - theoretical_mz) / theoretical_mz) * 1_000_000


def isotope_spacing_hint(charge: int) -> float:
    if charge == 0:
        raise ValueError("Charge must be non-zero.")
    return 1 / abs(charge)
