"""Unit tests for Automation_code.receptor_ligand_prep -- the shared
chain-A-extraction and Open Babel conversion primitives now used by both
Step_03_prepare_receptor_ligand.py (interactive app) and dataset/code.py
(batch dataset generation) instead of each maintaining its own copy.

Pure Python for extract_chain_a (no external tools). convert_to_pdbqt's
command-construction is checked without invoking obabel itself, since obabel
is not guaranteed to be installed in every environment this suite runs in
(see test_docking_smoke.py for the equivalent pattern with vina).
"""
import os
from unittest.mock import patch

import pytest

from Automation_code.receptor_ligand_prep import extract_chain_a, convert_to_pdbqt

FIXTURES = os.path.join(os.path.dirname(__file__), "fixtures")


def test_extract_chain_a_keeps_only_requested_chain_and_end(tmp_path):
    src = tmp_path / "in.pdb"
    src.write_text(
        "ATOM      1  N   ALA A   1       0.000   0.000   0.000  1.00  0.00           N\n"
        "ATOM      2  CA  ALA B   1       1.000   0.000   0.000  1.00  0.00           C\n"
        "HETATM    3  O   HOH A   2       2.000   0.000   0.000  1.00  0.00           O\n"
        "TER\n"
        "END\n"
    )
    dst = tmp_path / "out.pdb"
    extract_chain_a(str(src), str(dst))

    lines = dst.read_text().splitlines()
    assert len(lines) == 3
    assert lines[0].startswith("ATOM") and lines[0][21] == "A"
    assert lines[1].startswith("HETATM") and lines[1][21] == "A"
    assert lines[2] == "END"
    # Chain B and the bare TER record are dropped.
    assert not any(l[21:22] == "B" for l in lines if l.startswith(("ATOM", "HETATM")))


def test_extract_chain_a_respects_chain_id_argument(tmp_path):
    src = tmp_path / "in.pdb"
    src.write_text(
        "ATOM      1  N   ALA B   1       0.000   0.000   0.000  1.00  0.00           N\n"
        "END\n"
    )
    dst = tmp_path / "out.pdb"
    extract_chain_a(str(src), str(dst), chain_id="B")
    assert "ATOM" in dst.read_text()


def test_extract_chain_a_against_real_fixture_matches_reference_loop(tmp_path):
    """Regression check: the shared function must produce byte-identical
    output to the original inline loops it replaced in both Step_03 and
    dataset/code.py."""
    def reference_loop(input_pdb_path, output_pdb_path):
        with open(input_pdb_path) as infile, open(output_pdb_path, "w") as outfile:
            for line in infile:
                if line.startswith(("ATOM", "HETATM")) and line[21] == "A":
                    outfile.write(line)
                elif line.startswith("END"):
                    outfile.write(line)

    src = os.path.join(FIXTURES, "ethanol.pdb")
    shared_out = tmp_path / "shared.pdb"
    reference_out = tmp_path / "reference.pdb"
    extract_chain_a(src, str(shared_out))
    reference_loop(src, str(reference_out))
    assert shared_out.read_text() == reference_out.read_text()


def test_convert_to_pdbqt_receptor_command_matches_both_callers():
    """Both Step_03 (interactive app) and dataset/code.py (batch generator)
    previously built this exact command for receptor conversion; lock it
    down so a future edit can't silently drop -xr or reorder flags."""
    with patch("Automation_code.receptor_ligand_prep.subprocess.run") as mock_run:
        convert_to_pdbqt("obabel", "in.pdb", "out.pdbqt", receptor=True)
        mock_run.assert_called_once_with(
            ["obabel", "in.pdb", "-O", "out.pdbqt", "-xr", "-h", "--partialcharge", "gasteiger"],
            check=True,
            capture_output=False,
        )


def test_convert_to_pdbqt_ligand_command_omits_xr_flag():
    with patch("Automation_code.receptor_ligand_prep.subprocess.run") as mock_run:
        convert_to_pdbqt("obabel", "in.sdf", "out.pdbqt", receptor=False, capture_output=True)
        mock_run.assert_called_once_with(
            ["obabel", "in.sdf", "-O", "out.pdbqt", "-h", "--partialcharge", "gasteiger"],
            check=True,
            capture_output=True,
        )
