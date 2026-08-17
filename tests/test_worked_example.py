"""Checks that examples/OR7D4_androstenone/expected_output/ is internally
consistent with the pipeline's own scoring functions.

This does NOT re-run AutoDock Vina (examples/OR7D4_androstenone/run_example.py
does that, and requires `vina` on PATH) -- it recomputes the reproducibility
statistics and interaction analysis from the *already-committed* Vina output
files and checks they match the checked-in summary/CSV. That way the worked
example is verified on every CI run, including on machines without Vina.

Pure Python, no network, no subprocess -- runs in well under a second.
"""
import csv
import importlib.util
import json
import os
import sys

import pytest

FIXTURES = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "examples", "OR7D4_androstenone")
OUT_DIR = os.path.join(FIXTURES, "expected_output")

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "code"))
from Automation_code.reproducibility import reproducibility_stats, classify_std_dev
from Automation_code.config import classify_binding_energy, STD_DEV_RANGES

_spec = importlib.util.spec_from_file_location(
    "odorsig_dataset_code_worked_example",
    os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "dataset", "code.py"),
)
_dataset_code = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_dataset_code)
analyze_interactions = _dataset_code.analyze_interactions


def _best_energy(out_pdbqt):
    energies = [float(l.split()[3]) for l in open(out_pdbqt) if l.startswith("REMARK VINA RESULT")]
    return energies[0]


def test_reproducibility_summary_matches_committed_docking_output():
    with open(os.path.join(OUT_DIR, "reproducibility_summary.json")) as f:
        summary = json.load(f)

    best_energies = [
        _best_energy(os.path.join(OUT_DIR, f"run{i}_seed{seed}_docked.pdbqt"))
        for i, seed in enumerate(summary["seeds"], start=1)
    ]
    # Floating-point summation/division can differ in the last ULP depending
    # on platform/interpreter (e.g. -7.933333333333333 vs
    # -7.933333333333334), so compare with a tolerance rather than exact ==.
    assert best_energies == pytest.approx(summary["best_binding_energies_kcal_per_mol"], abs=1e-9)

    mean, sigma = reproducibility_stats(best_energies)
    assert mean == pytest.approx(summary["delta_g_mean"], abs=1e-9)
    assert sigma == pytest.approx(summary["sigma"], abs=1e-9)

    strength_label, _ = classify_binding_energy(mean)
    assert strength_label == summary["binding_strength"]

    consistency_label = classify_std_dev(sigma, STD_DEV_RANGES)
    assert consistency_label == summary["binding_consistency"]


def test_interaction_analysis_matches_committed_csv():
    receptor = os.path.join(FIXTURES, "receptor.pdbqt")
    docked = os.path.join(OUT_DIR, "run3_seed103_docked.pdbqt")
    csv_path = os.path.join(OUT_DIR, "interaction_analysis_run3.csv")

    results = analyze_interactions(receptor, docked)

    with open(csv_path, newline="") as f:
        rows = list(csv.DictReader(f))

    assert len(rows) == len(results)
    for row, r in zip(rows, results):
        assert int(row["h_bonds"]) == r["h_bonds"]
        assert int(row["hydrophobic_contacts"]) == r["hydrophobic"]
