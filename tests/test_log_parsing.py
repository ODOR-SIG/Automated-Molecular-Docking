"""Unit tests for Step_05_docking.parse_log_file, which extracts per-pose
binding energies from a Vina "REMARK VINA RESULT:" block.

Pure Python, no external tools, no network -- runs in well under a second.

Note on scope: parse_log_file's own docstring-free implementation reads
"REMARK VINA RESULT:" lines, which is the format Vina writes into its
*docked-pose PDBQT* (the --out file), not into the plain-text stdout capture
that run_docking() calls "log_file" in this same module (that stdout instead
contains a "mode | affinity | ..." table, which is what code/app.py's own
inline parser matches). parse_log_file is exercised here against genuine
Vina output content for the contract it actually implements; see the repo
notes for the naming mismatch.
"""
import os

from Automation_code.Step_05_docking import parse_log_file

FIXTURES = os.path.join(os.path.dirname(__file__), "fixtures")


def test_parses_genuine_vina_output_result_lines():
    """tests/fixtures/sample_vina_output.pdbqt is genuine AutoDock Vina 1.2.7
    output (produced locally, seed 42) docking the same OR7D4 receptor /
    androstenone ligand pair used by test_docking_smoke.py."""
    path = os.path.join(FIXTURES, "sample_vina_output.pdbqt")
    energies = parse_log_file(path)

    assert len(energies) == 4
    # (pose_number, energy) pairs, 1-indexed, in file order.
    assert energies[0] == (1, -7.2)
    assert energies[1] == (2, -6.3)
    assert energies[2] == (3, -5.4)
    assert energies[3] == (4, -4.4)
    # Best pose (Vina always lists poses best-first) is the lowest energy.
    assert energies[0][1] == min(e for _, e in energies)


def test_ignores_non_result_lines(tmp_path):
    log = tmp_path / "log.txt"
    log.write_text(
        "MODEL 1\n"
        "REMARK VINA RESULT:      -8.1      0.000      0.000\n"
        "ATOM      1  C   LIG A   1       0.000   0.000   0.000  0.00  0.00     0.000 C\n"
        "ENDMDL\n"
    )
    energies = parse_log_file(str(log))
    assert energies == [(1, -8.1)]


def test_malformed_result_line_is_skipped(tmp_path):
    log = tmp_path / "log.txt"
    log.write_text(
        "REMARK VINA RESULT:      -8.1      0.000      0.000\n"
        "REMARK VINA RESULT:      not_a_number      0.000      0.000\n"
        "REMARK VINA RESULT:      -7.9      0.000      0.000\n"
    )
    energies = parse_log_file(str(log))
    # The malformed row is dropped, not raised; the pose numbering is
    # sequential over the *successfully parsed* rows (matches current
    # implementation: pose_number = len(energies) + 1 at append time).
    assert energies == [(1, -8.1), (2, -7.9)]


def test_missing_file_returns_empty_list_without_raising():
    assert parse_log_file("/nonexistent/path/does-not-exist.txt") == []


def test_empty_file_returns_empty_list(tmp_path):
    log = tmp_path / "empty.txt"
    log.write_text("")
    assert parse_log_file(str(log)) == []
