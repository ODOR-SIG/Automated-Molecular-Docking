"""Hermetic docking smoke test for AutoDock Vina.

Runs Vina on a fixed prepared receptor + ligand with a fixed seed and asserts
the docking machinery behaves as expected: it returns docking modes, a finite
best binding energy, and — crucially for a *reproducibility-aware* pipeline —
the identical result when re-run with the same seed.

Scope: this exercises the docking step ONLY. It deliberately does not run
homology modelling (SWISS-MODEL is a live web service driven by Selenium and
cannot run hermetically in CI), and it makes no claim about the biological
relevance of this particular receptor-ligand pair — it is a technical smoke
test chosen for speed and determinism.

Requires the ``vina`` executable; skipped otherwise. In CI this runs against the
pinned AutoDock Vina 1.2.7 (see environment_lock.txt).

Reference-value note: absolute Vina binding energies are engine-version- and
platform-dependent, so this test asserts *determinism* and structural validity
rather than a hard-coded kcal/mol value. If an exact-value regression guard is
wanted later, generate and lock the reference from a CI run and record it here
as, e.g.: "best-energy reference locked from CI run <YYYY-MM-DD>, Ubuntu +
Vina 1.2.7 — platform-specific, not a cross-platform guarantee."
"""
import os
import shutil
import subprocess

import pytest

FIXTURES = os.path.join(os.path.dirname(__file__), "fixtures")
VINA = os.environ.get("ODORSIG_VINA_EXE", "vina")

pytestmark = pytest.mark.skipif(
    shutil.which(VINA) is None,
    reason="AutoDock Vina not on PATH; this test runs in CI",
)

RECEPTOR = os.path.join(FIXTURES, "receptor.pdbqt")
LIGAND = os.path.join(FIXTURES, "ligand.pdbqt")
SEED = 42
NUM_MODES = 10


def _box_from_receptor(pdbqt, pad=8.0):
    """Blind-docking box covering the whole receptor (centre + padded extent),
    mirroring OdorSig's blind-docking strategy but computed from the fixture so
    the box always contains the receptor regardless of its coordinates."""
    xs, ys, zs = [], [], []
    for ln in open(pdbqt):
        if ln.startswith(("ATOM", "HETATM")):
            xs.append(float(ln[30:38])); ys.append(float(ln[38:46])); zs.append(float(ln[46:54]))
    def c(a): return (min(a) + max(a)) / 2.0
    def s(a): return (max(a) - min(a)) + 2 * pad
    return (c(xs), c(ys), c(zs)), (s(xs), s(ys), s(zs))


def _run_vina(out_path):
    (cx, cy, cz), (sx, sy, sz) = _box_from_receptor(RECEPTOR)
    cmd = [
        VINA, "--receptor", RECEPTOR, "--ligand", LIGAND,
        "--center_x", f"{cx:.3f}", "--center_y", f"{cy:.3f}", "--center_z", f"{cz:.3f}",
        "--size_x", f"{sx:.3f}", "--size_y", f"{sy:.3f}", "--size_z", f"{sz:.3f}",
        "--seed", str(SEED), "--exhaustiveness", "1", "--num_modes", str(NUM_MODES),
        "--out", out_path,
    ]
    subprocess.run(cmd, check=True, capture_output=True, text=True)


def _energies(out_pdbqt):
    return [float(l.split()[3]) for l in open(out_pdbqt)
            if l.startswith("REMARK VINA RESULT")]


def test_docking_runs_and_is_deterministic(tmp_path):
    out1 = str(tmp_path / "dock1.pdbqt")
    out2 = str(tmp_path / "dock2.pdbqt")
    _run_vina(out1)
    _run_vina(out2)

    e1 = _energies(out1)
    e2 = _energies(out2)

    # Vina returns UP TO num_modes poses (it may return fewer if it cannot find
    # that many distinct ones); require at least one and no more than requested.
    assert 1 <= len(e1) <= NUM_MODES, f"unexpected number of modes: {len(e1)}"

    best = e1[0]
    assert best == best, "best energy is NaN"                 # finite
    assert -50.0 < best < 10.0, f"best energy not physically plausible: {best}"

    # Same seed -> identical run: the core reproducibility guarantee.
    assert e1 == e2, f"fixed seed was not deterministic:\n{e1}\n{e2}"
