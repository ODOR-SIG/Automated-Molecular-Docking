"""Unit tests for code/cli.py -- argument parsing and dispatch only.

These tests do not invoke the network, Selenium, or AutoDock Vina; they
check that the CLI wires arguments through to the right subcommand handler
with the right defaults, matching the values documented in cli.py's
docstrings (exhaustiveness=8/num_modes=10/energy_range=3 for `run`, the
interactive app's own defaults; dataset/code.py's own constants for
`batch`).
"""
import os
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "code"))

import cli  # noqa: E402


def test_run_defaults_match_interactive_app():
    parser = cli.build_parser()
    args = parser.parse_args(["run", "--receptor", "OR7D4", "--ligands", "Androstenone"])
    assert args.exhaustiveness == 8
    assert args.num_modes == 10
    assert args.energy_range == 3
    assert args.seed is None
    assert args.func is cli._cmd_run


def test_run_accepts_multiple_seeds_and_comma_separated_ligands():
    parser = cli.build_parser()
    args = parser.parse_args([
        "run", "--receptor", "OR1A1", "--ligands", "Citral,Carvone",
        "--seed", "111", "222", "333",
    ])
    assert args.ligands == "Citral,Carvone"
    assert args.seed == [111, 222, 333]


def test_batch_dispatches_to_batch_handler():
    parser = cli.build_parser()
    args = parser.parse_args(["batch", "--input", "pairs.xlsx"])
    assert args.input == "pairs.xlsx"
    assert args.func is cli._cmd_batch


def test_reproduce_requires_example_dir_argument():
    parser = cli.build_parser()
    args = parser.parse_args(["reproduce", "examples/OR7D4_androstenone"])
    assert args.example_dir == "examples/OR7D4_androstenone"
    assert args.func is cli._cmd_reproduce


def test_missing_command_is_an_error():
    parser = cli.build_parser()
    with pytest.raises(SystemExit):
        parser.parse_args([])


def test_reproduce_invokes_run_example_py_for_real_worked_example():
    """Confirms the CLI locates the actual, existing worked example's
    run_example.py without needing vina installed -- subprocess.call itself
    is mocked so this test doesn't require the vina executable."""
    example_dir = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "examples", "OR7D4_androstenone",
    )
    parser = cli.build_parser()
    args = parser.parse_args(["reproduce", example_dir])

    with patch("cli.subprocess.call", return_value=0) as mock_call:
        rc = cli._cmd_reproduce(args)

    assert rc == 0
    called_script = Path(mock_call.call_args[0][0][1])
    assert called_script.name == "run_example.py"
    assert called_script.parent == Path(example_dir).resolve()


def test_reproduce_reports_missing_run_example(tmp_path):
    parser = cli.build_parser()
    args = parser.parse_args(["reproduce", str(tmp_path)])
    assert cli._cmd_reproduce(args) == 1
