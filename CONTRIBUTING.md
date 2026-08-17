# Contributing to OdorSig

Thanks for your interest in improving OdorSig. This is a small research
codebase, so the process is intentionally lightweight.

## Reporting an issue

Open a GitHub Issue and include:

- What you ran (command / Streamlit page / script) and what you expected.
- The actual output or error, including a traceback if there is one.
- Your environment: Python version, OS, and the versions of AutoDock Vina,
  Open Babel, and PyMOL you have installed (`vina --version`, `obabel -V`,
  `pymol -cq -d "print(cmd.get_version())"`).
- If the bug involves a specific receptor/ligand pair, the pair name(s) and,
  if possible, the input files.

Bugs in the docking or interaction-analysis logic (e.g. PDBQT parsing,
binding-affinity classification, reproducibility statistics) are especially
useful with a minimal reproducing example, since most of that logic is
covered by `tests/` and a failing case can usually become a regression test.

## Submitting a pull request

1. Fork the repo and create a branch off `main`.
2. Keep PRs focused — one logical change per PR is easier to review than a
   mix of unrelated fixes.
3. If you change code under `code/Automation_code/` or `dataset/code.py`,
   add or update a test under `tests/` where the change is testable without
   live network calls (NCBI Entrez, PubChem, SWISS-MODEL, and other
   Selenium-driven steps are intentionally excluded from the test suite —
   mock them if you need to test logic that wraps them).
4. Run the test suite locally before opening the PR:
   ```
   pip install -r requirements.txt
   pip install pytest
   pytest -v
   ```
   Tests that need `vina` or `obabel` on `PATH` skip automatically if those
   tools aren't installed locally; they run in CI (see
   `.github/workflows/ci.yml`), where both are installed.
5. Push and open the PR against `main`. CI (GitHub Actions) runs the same
   test suite automatically; please make sure it's green before requesting
   review.

## Coding style

- Follow the existing style in the file you're editing rather than
  introducing a new one — this codebase doesn't enforce a formatter.
- Prefer clear, descriptive names over abbreviations, matching the existing
  `Step_0N_*.py` / `Automation_code` naming.
- Add a short comment explaining *why*, not *what*, for anything non-obvious
  (e.g. a fixed physical constant, a workaround for a tool quirk, a
  PDBQT column offset).
- New pure-Python logic (parsing, classification, statistics) should be
  factored so it's importable and testable independently of the Streamlit
  UI and Selenium-driven steps, following the pattern in
  `code/Automation_code/reproducibility.py`.

## Questions

For anything not covered here, open an issue — that's fine too.
