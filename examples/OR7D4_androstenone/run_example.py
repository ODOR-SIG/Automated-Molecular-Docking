"""Regenerate this worked example's expected_output/ from scratch.

Docks the receptor.pdbqt / ligand.pdbqt in this folder with AutoDock Vina
across three fixed seeds (triplicate runs, matching how OdorSig scores
reproducibility per receptor-ligand pair), computes the reproducibility
statistics and binding classification via the pipeline's own
Automation_code.reproducibility module, and runs the (atom-type-aware)
interaction analysis from dataset/code.py on the strongest run's poses.

Requires the `vina` executable on PATH (AutoDock Vina 1.2.7, as pinned in
../../environment_lock.txt). No network access is used or required.

Usage (from the repo root):
    python examples/OR7D4_androstenone/run_example.py
"""
import csv
import importlib.util
import json
import os
import subprocess
import sys

EXAMPLE_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(os.path.dirname(EXAMPLE_DIR))
OUT_DIR = os.path.join(EXAMPLE_DIR, "expected_output")

RECEPTOR = os.path.join(EXAMPLE_DIR, "receptor.pdbqt")
LIGAND = os.path.join(EXAMPLE_DIR, "ligand.pdbqt")

# Triplicate seeds. Fixed (not random) so the example is exactly reproducible.
SEEDS = [101, 102, 103]
EXHAUSTIVENESS = 8
NUM_MODES = 9

sys.path.insert(0, os.path.join(REPO_ROOT, "code"))
from Automation_code.reproducibility import reproducibility_stats, classify_std_dev  # noqa: E402
from Automation_code.config import classify_binding_energy, STD_DEV_RANGES  # noqa: E402

# dataset/code.py's module name ("code") collides with the stdlib `code`
# module, and it requires ODORSIG_ENTREZ_EMAIL at import time even though
# this script never calls Entrez -- see tests/conftest.py for the same
# workaround.
os.environ.setdefault("ODORSIG_ENTREZ_EMAIL", "odorsig-example@example.com")
_spec = importlib.util.spec_from_file_location(
    "odorsig_dataset_code", os.path.join(REPO_ROOT, "dataset", "code.py")
)
_dataset_code = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_dataset_code)
analyze_interactions = _dataset_code.analyze_interactions


def _blind_docking_box(pdbqt_path, pad=8.0):
    """Same blind-docking box construction OdorSig's Step_04 uses: centred on
    the receptor's coordinate extent, padded so the whole receptor is inside
    the search box."""
    xs, ys, zs = [], [], []
    for line in open(pdbqt_path):
        if line.startswith(("ATOM", "HETATM")):
            xs.append(float(line[30:38]))
            ys.append(float(line[38:46]))
            zs.append(float(line[46:54]))
    center = lambda a: (min(a) + max(a)) / 2.0
    size = lambda a: (max(a) - min(a)) + 2 * pad
    return (center(xs), center(ys), center(zs)), (size(xs), size(ys), size(zs))


def _run_vina(seed, out_path, log_path):
    (cx, cy, cz), (sx, sy, sz) = _blind_docking_box(RECEPTOR)
    cmd = [
        "vina", "--receptor", RECEPTOR, "--ligand", LIGAND,
        "--center_x", f"{cx:.3f}", "--center_y", f"{cy:.3f}", "--center_z", f"{cz:.3f}",
        "--size_x", f"{sx:.3f}", "--size_y", f"{sy:.3f}", "--size_z", f"{sz:.3f}",
        "--seed", str(seed), "--exhaustiveness", str(EXHAUSTIVENESS), "--num_modes", str(NUM_MODES),
        "--out", out_path,
    ]
    result = subprocess.run(cmd, check=True, capture_output=True, text=True)
    with open(log_path, "w") as f:
        f.write(result.stdout)


def _best_energy(out_pdbqt):
    energies = [float(l.split()[3]) for l in open(out_pdbqt) if l.startswith("REMARK VINA RESULT")]
    return energies[0]


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    best_energies = []
    docked_paths = []

    for i, seed in enumerate(SEEDS, start=1):
        out_path = os.path.join(OUT_DIR, f"run{i}_seed{seed}_docked.pdbqt")
        log_path = os.path.join(OUT_DIR, f"run{i}_seed{seed}_log.txt")
        _run_vina(seed, out_path, log_path)
        best_energies.append(_best_energy(out_path))
        docked_paths.append(out_path)
        print(f"run {i} (seed {seed}): best pose = {best_energies[-1]} kcal/mol")

    mean, sigma = reproducibility_stats(best_energies)
    strength_label, _ = classify_binding_energy(mean)
    consistency_label = classify_std_dev(sigma, STD_DEV_RANGES)

    summary = {
        "receptor": "OR7D4",
        "ligand": "Androstenone",
        "pipeline_stage": "Step_05 docking (Vina) + reproducibility scoring",
        "seeds": SEEDS,
        "best_binding_energies_kcal_per_mol": best_energies,
        "delta_g_mean": mean,
        "sigma": sigma,
        "binding_strength": strength_label,
        "binding_consistency": consistency_label,
    }
    with open(os.path.join(OUT_DIR, "reproducibility_summary.json"), "w") as f:
        json.dump(summary, f, indent=2)
    print(json.dumps(summary, indent=2))

    # Interaction analysis on the run with the strongest (most negative) ΔG.
    best_run_index = min(range(len(best_energies)), key=lambda i: best_energies[i])
    results = analyze_interactions(RECEPTOR, docked_paths[best_run_index])
    csv_path = os.path.join(OUT_DIR, f"interaction_analysis_run{best_run_index + 1}.csv")
    with open(csv_path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["pose", "h_bonds", "hydrophobic_contacts"])
        for pose_i, r in enumerate(results, start=1):
            w.writerow([pose_i, r["h_bonds"], r["hydrophobic"]])
    print(f"wrote {csv_path}")


if __name__ == "__main__":
    main()
