"""Unit tests for Automation_code.provenance -- per-run manifest generation.

Pure Python, no network. Tool-version lookups use the real `python`/a
guaranteed-missing executable rather than mocking subprocess, so the
"tool not found" path is exercised for real, not just asserted.
"""
import hashlib
import json
import os
import sys

from Automation_code.provenance import build_manifest, write_run_manifest, _sha256_of_file, _tool_version


def test_tool_version_returns_first_nonempty_line_for_a_real_executable():
    version = _tool_version([sys.executable, "--version"])
    assert version is not None
    assert "Python" in version


def test_tool_version_returns_none_for_missing_executable():
    assert _tool_version(["definitely-not-a-real-executable-xyz"]) is None


def test_sha256_of_file_matches_hashlib_reference(tmp_path):
    f = tmp_path / "sample.txt"
    f.write_bytes(b"OdorSig provenance test content")
    expected = hashlib.sha256(b"OdorSig provenance test content").hexdigest()
    assert _sha256_of_file(str(f)) == expected


def test_sha256_of_file_returns_none_for_missing_file():
    assert _sha256_of_file("/nonexistent/path/does-not-exist.pdbqt") is None
    assert _sha256_of_file(None) is None


def test_build_manifest_records_receptor_ligand_seeds_and_params():
    manifest = build_manifest(
        receptor="OR7D4",
        ligand="Androstenone",
        seeds=[101, 102, 103],
        docking_params={"exhaustiveness": 8, "num_modes": 10, "energy_range": 3},
        vina_exe="definitely-not-installed",
        obabel_exe="definitely-not-installed",
    )
    assert manifest["receptor"] == "OR7D4"
    assert manifest["ligand"] == "Androstenone"
    assert manifest["seeds"] == [101, 102, 103]
    assert manifest["docking_params"] == {"exhaustiveness": 8, "num_modes": 10, "energy_range": 3}
    assert manifest["vina_version"] is None  # executable genuinely not found
    assert "timestamp_utc" in manifest
    assert manifest["python_version"] == sys.version.split()[0]


def test_build_manifest_hashes_input_and_output_files(tmp_path):
    receptor_file = tmp_path / "receptor.pdbqt"
    receptor_file.write_text("dummy receptor content")

    manifest = build_manifest(
        receptor="OR7D4", ligand="Androstenone", seeds=[101],
        input_files={"receptor_pdbqt": str(receptor_file)},
        output_files={"docked_pdbqt": str(tmp_path / "does_not_exist.pdbqt")},
    )
    assert manifest["input_files"]["receptor_pdbqt"]["path"] == str(receptor_file)
    assert manifest["input_files"]["receptor_pdbqt"]["sha256"] == hashlib.sha256(
        b"dummy receptor content"
    ).hexdigest()
    # Output file doesn't exist yet (e.g. a run that hasn't completed) -- no hash, no crash.
    assert manifest["output_files"]["docked_pdbqt"]["sha256"] is None


def test_write_run_manifest_writes_valid_json(tmp_path):
    manifest_path = tmp_path / "run_manifest.json"
    returned = write_run_manifest(
        str(manifest_path), receptor="OR1A1", ligand="Citral", seeds=[100, 200, 300],
    )
    assert manifest_path.is_file()
    on_disk = json.loads(manifest_path.read_text())
    assert on_disk == returned
    assert on_disk["receptor"] == "OR1A1"


def test_manifest_is_json_serialisable_end_to_end(tmp_path):
    """Guards against accidentally putting a non-JSON-serialisable value
    (e.g. a raw datetime object) into the manifest."""
    manifest_path = tmp_path / "run_manifest.json"
    write_run_manifest(
        str(manifest_path), receptor="OR3A3", ligand="Vanillin", seeds=100,
        extra={"note": "single random-seed run"},
    )
    with open(manifest_path) as f:
        json.load(f)  # raises if the file isn't valid JSON
