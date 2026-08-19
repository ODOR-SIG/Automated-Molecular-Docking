"""Per-run provenance manifest generation.

Makes "reproducible" a demonstrated, per-run, machine-readable fact rather
than only an assertion in the manuscript: for a given docking run, this
records exactly what produced it -- tool versions actually present on the
machine that ran it (not just the static, project-level requirements.txt /
environment_lock.txt), the seeds and parameters used, timestamps, and file
paths/hashes of the inputs and outputs involved.

Every field here is either already known to the caller (receptor/ligand
names, seeds, docking parameters, file paths) or trivially queryable from the
running environment (tool --version output, the Python interpreter version,
a file's own SHA-256) -- nothing here is invented or inferred.
"""
import hashlib
import json
import os
import subprocess
import sys
from datetime import datetime, timezone


def _tool_version(cmd_args, timeout=10):
    """Run e.g. ['vina', '--version'] and return the first non-empty line of
    its combined stdout+stderr, or None if the executable isn't found or
    doesn't respond in time. Never raises."""
    try:
        result = subprocess.run(
            cmd_args, capture_output=True, text=True, timeout=timeout
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    combined = (result.stdout or "") + (result.stderr or "")
    for line in combined.splitlines():
        if line.strip():
            return line.strip()
    return None


def _sha256_of_file(path, chunk_size=1 << 20):
    """SHA-256 of a file's contents, or None if the file doesn't exist or
    can't be read (e.g. a run that failed before writing that output)."""
    if not path or not os.path.isfile(path):
        return None
    digest = hashlib.sha256()
    try:
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(chunk_size), b""):
                digest.update(chunk)
    except OSError:
        return None
    return digest.hexdigest()


def build_manifest(
    receptor,
    ligand,
    seeds,
    input_files=None,
    output_files=None,
    docking_params=None,
    vina_exe="vina",
    obabel_exe="obabel",
    extra=None,
):
    """Build a provenance manifest dict for one receptor-ligand docking run.

    Args:
        receptor: receptor identifier (e.g. "OR7D4").
        ligand: ligand identifier (e.g. "Androstenone").
        seeds: the seed(s) actually used for this run (list of ints, or a
            single int for a one-seed run).
        input_files: optional {label: path} of input files to hash
            (e.g. {"receptor_pdbqt": ..., "ligand_pdbqt": ..., "config": ...}).
        output_files: optional {label: path} of output files to hash
            (e.g. {"docked_pdbqt": ..., "log": ...}).
        docking_params: optional dict of docking parameters actually used
            (exhaustiveness, num_modes, energy_range, etc.) -- recorded
            verbatim, not recomputed or validated here.
        vina_exe: the Vina executable/path actually configured for this run
            (so the manifest reflects what would really execute, matching
            config.py's ODORSIG_VINA_EXE convention).
        obabel_exe: same, for Open Babel.
        extra: optional dict of any additional caller-supplied fields.

    Returns:
        A JSON-serialisable dict. Does not write anything to disk --
        see write_run_manifest() for that.
    """
    manifest = {
        "receptor": receptor,
        "ligand": ligand,
        "seeds": seeds,
        "timestamp_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "python_version": sys.version.split()[0],
        "vina_version": _tool_version([vina_exe, "--version"]),
        "obabel_version": _tool_version([obabel_exe, "-V"]),
        "docking_params": docking_params or {},
        "input_files": {
            label: {"path": path, "sha256": _sha256_of_file(path)}
            for label, path in (input_files or {}).items()
        },
        "output_files": {
            label: {"path": path, "sha256": _sha256_of_file(path)}
            for label, path in (output_files or {}).items()
        },
    }
    if extra:
        manifest["extra"] = extra
    return manifest


def write_run_manifest(manifest_path, **kwargs):
    """Build a manifest (see build_manifest() for kwargs) and write it as
    indented JSON to manifest_path. Returns the manifest dict."""
    manifest = build_manifest(**kwargs)
    with open(manifest_path, "w") as f:
        json.dump(manifest, f, indent=2)
        f.write("\n")
    return manifest
