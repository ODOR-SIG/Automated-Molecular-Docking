# Changelog

All notable changes to OdorSig are documented in this file.
The format is based on [Keep a Changelog](https://keepachangelog.com/).

## [1.0.0] - 2026-07-17

First citable release of the OdorSig pipeline and the accompanying 480-pair
receptor–odorant docking dataset. This release hardens the repository into a
reproducible, testable software artifact.

### Added
- `requirements.txt` with Python dependencies pinned to exact (`==`) versions
  from the verified working environment, replacing the previous unpinned file.
- `environment_lock.txt` recording the external, non-pip tool versions used
  (AutoDock Vina 1.2.7, Open Babel 3.1.1, PyMOL 3.1.0) and noting that
  SWISS-MODEL is an unversioned web service accessed via Selenium.
- `CONTRIBUTORS.md` clarifying contributor roles relative to the shared
  ODOR-SIG account commit history.
- Automated `pytest` test suite (`tests/`): reproducibility-statistics unit
  tests, an Open Babel PDB→PDBQT conversion test, and a hermetic AutoDock Vina
  docking smoke test (with committed fixtures).
- Continuous integration (`.github/workflows/tests.yml`) running the suite on
  Ubuntu with pinned Open Babel and AutoDock Vina 1.2.7.
- `code/Automation_code/reproducibility.py` — a single source of truth for the
  reproducibility-aware scoring (mean ΔG, population σ).
- CI status badge in `README.md`.

### Changed
- `code/app.py` and `dataset/code.py` now import the shared reproducibility
  function instead of each maintaining a separate mean/standard-deviation
  implementation.
- Corrected the README technology table to the actual tool versions
  (AutoDock Vina 1.2.5 → 1.2.7, PyMOL 3.1.6.1 → 3.1.0).
- Repointed installation instructions to the root `requirements.txt`.
- `code/README.md` now shows the correct launch command
  (`streamlit run app.py`) instead of a non-existent `main.py`.

### Removed
- RDKit from the `CITATION.cff` software description — it is not imported or
  used anywhere in the code.
- `code/requirement.txt` — superseded by the root `requirements.txt`.

### Notes
- `environment_lock.txt` documents the *current verified* environment
  (WSL/Ubuntu), which is **not** the original machine that generated the
  deposited 480-pair dataset and Zenodo logs. It reproduces the pipeline's
  functionality but does not guarantee bit-identical output to the original
  dataset.

## [0.1.0] - 2025-12-04

- Initial tagged snapshot of the repository (early README and citation
  metadata), prior to the dataset deposition and the reproducibility hardening
  in 1.0.0.
