"""Reproducibility-aware scoring — single source of truth.

OdorSig quantifies docking reproducibility by reporting, for each
receptor-ligand pair, the mean binding energy (Delta-G mean) and the
*population* standard deviation (sigma, ddof=0) across repeated docking runs.

Both the interactive app (code/app.py) and the batch dataset generator
(dataset/code.py) import these functions, so the calculation is defined
exactly once rather than reimplemented independently.

Example:
    reproducibility_stats([-7.0, -7.2, -6.8]) -> (-7.0, 0.16329931618554522)
"""
from math import sqrt


def reproducibility_stats(values):
    """Return (mean, population_std_dev) for a sequence of docking Delta-G values.

    The standard deviation is the *population* standard deviation (ddof = 0),
    matching numpy.std()'s default and the sigma definition used throughout the
    OdorSig manuscript.

    Raises:
        ValueError: if ``values`` is empty.
    """
    vals = [float(v) for v in values]
    n = len(vals)
    if n == 0:
        raise ValueError("reproducibility_stats() requires at least one value")
    mean_val = sum(vals) / n
    variance = sum((x - mean_val) ** 2 for x in vals) / n
    return mean_val, sqrt(variance)


def classify_std_dev(value, ranges):
    """Classify a population sigma into a consistency label.

    ``ranges`` maps a label to a half-open ``(low, high)`` interval ``[low, high)``.
    Returns ``"Unknown"`` if no interval matches.
    """
    for label, (low, high) in ranges.items():
        if low <= value < high:
            return label
    return "Unknown"
