"""Unit tests for dataset/code.py's collect_qc_data()/write_qc_report() --
the dataset-level completion aggregation added to make "N/N pairs completed"
a real, checkable statistic instead of something inferred by manually
counting output folders.

Loads dataset/code.py the same way tests/test_worked_example.py already
does (importlib, with ODORSIG_ENTREZ_EMAIL stubbed), and points its
module-level EXCEL_FILE/OUTPUT_ROOT at a synthetic pair list + a synthetic
on-disk output layout built in a tmp_path -- no network, no Vina, no Open
Babel required.
"""
import importlib.util
import json
import os
import sys

import pandas as pd
import pytest

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO_ROOT, "code"))

os.environ.setdefault("ODORSIG_ENTREZ_EMAIL", "odorsig-example@example.com")


def _load_dataset_module():
    spec = importlib.util.spec_from_file_location(
        "odorsig_dataset_code_qc_test", os.path.join(REPO_ROOT, "dataset", "code.py")
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def dataset_code():
    return _load_dataset_module()


def _make_pair_list(path, pairs):
    pd.DataFrame(pairs, columns=["Receptor", "Ligand"]).to_excel(path, index=False)


def _make_completed_run(output_root, receptor, ligand, run_num):
    run_dir = os.path.join(output_root, f"{receptor}_{ligand}", f"docking_{run_num}")
    os.makedirs(run_dir, exist_ok=True)
    with open(os.path.join(run_dir, "pose_analysis.csv"), "w") as f:
        f.write("Pose,Affinity_kcal,H_Bonds,Hydrophobic\n1,-7.0,2,3\n")


def test_all_pairs_and_runs_complete(tmp_path, dataset_code):
    excel = tmp_path / "pairs.xlsx"
    _make_pair_list(excel, [("OR7D4", "Androstenone"), ("OR1A1", "Citral")])
    dataset_code.EXCEL_FILE = str(excel)
    dataset_code.OUTPUT_ROOT = str(tmp_path / "outputs")

    for receptor, ligand in [("OR7D4", "Androstenone"), ("OR1A1", "Citral")]:
        for run_num in range(1, len(dataset_code.DOCKING_SEEDS) + 1):
            _make_completed_run(dataset_code.OUTPUT_ROOT, receptor, ligand, run_num)

    qc = dataset_code.collect_qc_data()
    assert qc["requested_pairs"] == 2
    assert qc["completed_pairs"] == 2
    assert qc["requested_runs"] == 2 * len(dataset_code.DOCKING_SEEDS)
    assert qc["completed_runs"] == qc["requested_runs"]
    assert qc["incomplete_pairs"] == []
    assert qc["completion_summary"] == (
        f"2/2 pairs completed ({qc['completed_runs']}/{qc['requested_runs']} individual docking runs)"
    )


def test_partial_completion_is_reported_by_pair(tmp_path, dataset_code):
    excel = tmp_path / "pairs.xlsx"
    _make_pair_list(excel, [("OR7D4", "Androstenone"), ("OR3A3", "Vanillin")])
    dataset_code.EXCEL_FILE = str(excel)
    dataset_code.OUTPUT_ROOT = str(tmp_path / "outputs")

    # OR7D4-Androstenone: fully completed.
    for run_num in range(1, len(dataset_code.DOCKING_SEEDS) + 1):
        _make_completed_run(dataset_code.OUTPUT_ROOT, "OR7D4", "Androstenone", run_num)
    # OR3A3-Vanillin: only the first run completed.
    _make_completed_run(dataset_code.OUTPUT_ROOT, "OR3A3", "Vanillin", 1)

    qc = dataset_code.collect_qc_data()
    assert qc["completed_pairs"] == 1
    assert qc["incomplete_pairs"] == [{
        "receptor": "OR3A3", "ligand": "Vanillin",
        "completed_runs": 1, "expected_runs": len(dataset_code.DOCKING_SEEDS),
    }]


def test_missing_pair_list_reports_cleanly_without_raising(tmp_path, dataset_code):
    dataset_code.EXCEL_FILE = str(tmp_path / "does_not_exist.xlsx")
    dataset_code.OUTPUT_ROOT = str(tmp_path / "outputs")

    qc = dataset_code.collect_qc_data()
    assert qc["requested_pairs"] == 0
    assert "not found" in qc["completion_summary"]


def test_write_qc_report_persists_valid_json(tmp_path, dataset_code):
    excel = tmp_path / "pairs.xlsx"
    _make_pair_list(excel, [("OR7D4", "Androstenone")])
    dataset_code.EXCEL_FILE = str(excel)
    dataset_code.OUTPUT_ROOT = str(tmp_path / "outputs")
    for run_num in range(1, len(dataset_code.DOCKING_SEEDS) + 1):
        _make_completed_run(dataset_code.OUTPUT_ROOT, "OR7D4", "Androstenone", run_num)

    report_path = tmp_path / "qc_report.json"
    qc = dataset_code.write_qc_report(str(report_path))

    assert report_path.is_file()
    on_disk = json.loads(report_path.read_text())
    assert on_disk == qc
    assert on_disk["completed_pairs"] == 1
