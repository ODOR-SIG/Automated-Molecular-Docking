# Worked example: OR7D4 × Androstenone

A single, concrete, reproducible run through OdorSig's docking and
reproducibility-scoring stages, so a reviewer or CI can check one result
end to end without running the full Selenium-driven modelling pipeline.

**Receptor:** OR7D4 (human olfactory receptor; homology model, chain A only)
**Ligand:** Androstenone

Both input files are genuine, previously-generated OdorSig pipeline outputs
(the same files used as `tests/fixtures/receptor.pdbqt` /
`tests/fixtures/ligand.pdbqt` — see `tests/fixtures/README.md` for their
provenance) — they are not synthetic or hand-written.

## What this example covers

This example starts from the **already-prepared** receptor and ligand
PDBQT files (i.e. Step_01–Step_03 of the pipeline are assumed done — those
steps depend on live NCBI Entrez / PubChem / SWISS-MODEL calls and are
mocked, not run live, in `tests/`). From there it runs the parts of the
pipeline that execute locally with no network dependency:

- **Step_05 (docking):** three independent AutoDock Vina runs (triplicate,
  as OdorSig reports per receptor–ligand pair), each with a different fixed
  seed for reproducibility.
- **Reproducibility scoring** (`code/Automation_code/reproducibility.py`):
  ΔGmean and population σ across the three runs, then binding-strength and
  binding-consistency classification.
- **Interaction analysis** (`dataset/code.py: analyze_interactions`):
  H-bond and hydrophobic-contact counts per docked pose, using the
  AutoDock-atom-type-aware parsing (see `tests/test_interactions.py`).

## Reproducing it

```bash
# from the repo root, with `vina` (AutoDock Vina 1.2.7) on PATH
python examples/OR7D4_androstenone/run_example.py
```

This regenerates everything under `expected_output/` from the two input
files. Vina docking with a fixed `--seed` is deterministic, so re-running
should reproduce the checked-in files' numeric content exactly (up to Vina's
own version/platform-level floating-point behaviour — this is why
`tests/test_docking_smoke.py` asserts determinism per-seed rather than
hard-coding poses as a cross-platform guarantee).

## Checked-in expected output (`expected_output/`)

| File | Contents |
|---|---|
| `run{1,2,3}_seed{101,102,103}_docked.pdbqt` | Full Vina docking output (all poses) for each of the three triplicate runs. |
| `run{1,2,3}_seed{101,102,103}_log.txt` | Vina's stdout for each run. |
| `reproducibility_summary.json` | Best-pose ΔG from each of the 3 runs, ΔGmean, σ, and the resulting binding-strength / binding-consistency classification. |
| `interaction_analysis_run3.csv` | Per-pose H-bond and hydrophobic-contact counts for the seed-103 run (the run with the strongest ΔGmean contribution), from `analyze_interactions`. |

### Result summary (seeds 101/102/103, exhaustiveness 8)

| Run | Seed | Best ΔG (kcal/mol) |
|---|---|---|
| 1 | 101 | -7.2 |
| 2 | 102 | -8.2 |
| 3 | 103 | -8.4 |

- **ΔGmean:** -7.933 kcal/mol
- **σ (population):** 0.525 kcal/mol
- **Binding strength:** Strong Binding Affinity (ΔGmean ≤ -7.0)
- **Binding consistency:** Inconsistent binding (σ ≥ 0.5)

This is a real result for this specific input pair and seed set — it is not
cherry-picked for a "clean" reproducibility story; the point of this example
is that it can be reproduced exactly, not that it is a flattering result.
