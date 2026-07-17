"""Test the PDB -> PDBQT ligand conversion (Open Babel), as done in
code/Automation_code/Step_03_prepare_receptor_ligand.py.

Requires the ``obabel`` executable on PATH; skipped otherwise (e.g. local
machines without Open Babel). Exercised in CI, where Open Babel is installed.
"""
import os
import shutil
import subprocess

import pytest

FIXTURES = os.path.join(os.path.dirname(__file__), "fixtures")
OBABEL = os.environ.get("ODORSIG_OBABEL_PATH", "obabel")

pytestmark = pytest.mark.skipif(
    shutil.which(OBABEL) is None,
    reason="Open Babel (obabel) not on PATH; this test runs in CI",
)


def test_ligand_pdb_to_pdbqt_is_well_formed(tmp_path):
    """Replicates OdorSig's ligand conversion command from Step_03:
        obabel <in.pdb> -O <out.pdbqt> -h --partialcharge gasteiger
    and asserts the result is a well-formed AutoDock ligand PDBQT.
    """
    src = os.path.join(FIXTURES, "ethanol.pdb")
    out = str(tmp_path / "ethanol.pdbqt")

    subprocess.run(
        [OBABEL, src, "-O", out, "-h", "--partialcharge", "gasteiger"],
        check=True, capture_output=True, text=True,
    )

    assert os.path.exists(out), "obabel produced no output file"
    text = open(out).read()
    atom_lines = [l for l in text.splitlines() if l.startswith(("ATOM", "HETATM"))]

    # A well-formed AutoDock *ligand* PDBQT carries a torsion tree and a TORSDOF
    # record, and at least ethanol's 3 heavy atoms (C, C, O). The exact atom
    # count depends on Open Babel's hydrogen handling, so we assert a lower
    # bound derived from the input rather than a hard-coded constant.
    assert "ROOT" in text and "ENDROOT" in text, "missing ROOT/ENDROOT torsion tree"
    assert "TORSDOF" in text, "missing TORSDOF record"
    assert len(atom_lines) >= 3, f"expected >= 3 atoms (ethanol heavy atoms), got {len(atom_lines)}"

    # Every atom line must carry an AutoDock atom type in the trailing column.
    for l in atom_lines:
        assert l[77:].strip(), f"atom line missing trailing AutoDock atom type: {l!r}"
