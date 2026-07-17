"""Unit tests for OdorSig's reproducibility-aware scoring and classification.

Pure Python: no external tools, no network, no heavy dependencies — runs on any
machine (this is the test that must be green locally as well as in CI).
"""
import pytest

from Automation_code.reproducibility import reproducibility_stats, classify_std_dev


def test_reproducibility_stats_hand_computed():
    # dG = [-7.0, -7.2, -6.8]  ->  mean = -21.0/3 = -7.0
    # population variance = (0^2 + (-0.2)^2 + (0.2)^2) / 3 = 0.08/3 = 0.0266667
    # population sigma = sqrt(0.0266667) = 0.1632993...
    mean, sigma = reproducibility_stats([-7.0, -7.2, -6.8])
    assert mean == pytest.approx(-7.0, abs=1e-12)
    assert sigma == pytest.approx(0.16329931618554522, abs=1e-12)


def test_population_not_sample_std():
    # Classic example: values [2,4,4,4,5,5,7,9] -> mean 5.0
    # population sigma (ddof=0) = 2.0 ; sample sigma (ddof=1) = 2.1381...
    # Guards against an accidental switch to sample standard deviation.
    mean, sigma = reproducibility_stats([2, 4, 4, 4, 5, 5, 7, 9])
    assert mean == pytest.approx(5.0)
    assert sigma == pytest.approx(2.0, abs=1e-12)


def test_identical_runs_zero_sigma():
    mean, sigma = reproducibility_stats([-8.47, -8.47, -8.47])
    assert mean == pytest.approx(-8.47)
    assert sigma == pytest.approx(0.0, abs=1e-12)


def test_single_value():
    mean, sigma = reproducibility_stats([-6.3])
    assert mean == pytest.approx(-6.3)
    assert sigma == pytest.approx(0.0)


def test_empty_raises():
    with pytest.raises(ValueError):
        reproducibility_stats([])


def test_accepts_strings_like_the_app_passes():
    # app.py builds seed_vals via float(...) already, but the function must be
    # robust to numeric strings too.
    mean, sigma = reproducibility_stats(["-7.0", "-7.2", "-6.8"])
    assert mean == pytest.approx(-7.0)
    assert sigma == pytest.approx(0.16329931618554522, abs=1e-12)


def test_classify_std_dev_half_open_intervals():
    ranges = {
        "Consistent Binding": (0.0, 0.2),
        "Medium Consistency": (0.2, 0.5),
        "Inconsistent binding": (0.5, float("inf")),
    }
    assert classify_std_dev(0.10, ranges) == "Consistent Binding"
    assert classify_std_dev(0.20, ranges) == "Medium Consistency"   # [low, high): 0.2 -> Medium
    assert classify_std_dev(0.49, ranges) == "Medium Consistency"
    assert classify_std_dev(0.50, ranges) == "Inconsistent binding"
    assert classify_std_dev(3.00, ranges) == "Inconsistent binding"
    assert classify_std_dev(-1.0, ranges) == "Unknown"


def test_classify_binding_energy_thresholds():
    # config.py owns the binding-strength thresholds; verify the manuscript
    # cutoffs (strong <= -7, moderate (-7,-5], weak > -5), including boundaries.
    from Automation_code.config import classify_binding_energy
    assert classify_binding_energy(-8.0)[0] == "Strong Binding Affinity"
    assert classify_binding_energy(-7.0)[0] == "Strong Binding Affinity"    # boundary
    assert classify_binding_energy(-6.0)[0] == "Moderate Binding Affinity"
    assert classify_binding_energy(-5.0)[0] == "Moderate Binding Affinity"  # boundary
    assert classify_binding_energy(-4.0)[0] == "Weak Binding Affinity"
