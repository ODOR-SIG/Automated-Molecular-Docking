# config.py
#
# All machine-specific settings are read from environment variables so that a
# fresh `git clone` runs on any machine without editing source. Sensible
# defaults are provided:
#   - Data directories default to a "runs/" folder next to the project root.
#   - External executables (vina, obabel) default to the bare command name and
#     are resolved via PATH, matching the installation instructions in README.md.
#   - CHROMEDRIVER is optional: if unset, Selenium Manager (built into
#     Selenium >= 4.6) auto-downloads and manages the correct driver.
#
# To override any of these, set the corresponding environment variable, e.g.:
#   export ODORSIG_ENTREZ_EMAIL="you@example.com"
#   export ODORSIG_VINA_EXE="/opt/homebrew/bin/vina"
# or copy .env.example to .env and load it before running the app.

import os

# Base project directory: defaults to the repository's "code" folder's parent,
# so all working directories live inside the cloned repo by default.
BASE_DIR = os.environ.get(
    "ODORSIG_BASE_DIR",
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)
RUNS_DIR = os.path.join(BASE_DIR, "runs")

# Subdirectories inside the project (auto-created on import)
UI_AUTOMATION_DIR     = os.path.dirname(os.path.abspath(__file__))
DOCKING_OUTPUT_DIR    = os.environ.get("ODORSIG_DOCKING_OUTPUT_DIR", os.path.join(RUNS_DIR, "DockingResults"))
PREPARED_MODELS_DIR   = os.environ.get("ODORSIG_PREPARED_MODELS_DIR", os.path.join(RUNS_DIR, "prepared_models"))
MODEL_CHAIN_A_ONLY    = os.environ.get("ODORSIG_MODEL_CHAIN_A_DIR", os.path.join(RUNS_DIR, "model_chain_A_only"))
RECEPTOR_DOWNLOAD_DIR = os.environ.get("ODORSIG_RECEPTOR_DOWNLOAD_DIR", os.path.join(RUNS_DIR, "first_stage_model_download"))
FASTA_DOWNLOAD_DIR    = os.environ.get("ODORSIG_FASTA_DOWNLOAD_DIR", os.path.join(RUNS_DIR, "fasta_downloads"))

for _dir in (DOCKING_OUTPUT_DIR, PREPARED_MODELS_DIR, MODEL_CHAIN_A_ONLY, RECEPTOR_DOWNLOAD_DIR, FASTA_DOWNLOAD_DIR):
    os.makedirs(_dir, exist_ok=True)

# External executable paths. Defaults assume the tools are on PATH, per the
# installation steps in README.md. Set an env var only if you need to point
# at a specific install (e.g. a non-PATH location on Windows).
PYMOL_PATH   = os.environ.get("ODORSIG_PYMOL_PATH", "pymol")
VINA_EXE     = os.environ.get("ODORSIG_VINA_EXE", "vina")
OBABEL_PATH  = os.environ.get("ODORSIG_OBABEL_PATH", "obabel")

# ChromeDriver: optional. If set and the path exists, Selenium uses it
# directly; otherwise Selenium Manager (Selenium >= 4.6) resolves and caches
# the correct driver automatically on first use.
CHROMEDRIVER = os.environ.get("ODORSIG_CHROMEDRIVER", "")

# Biopython Entrez email — REQUIRED by NCBI to identify API callers.
# No default is provided; the app/scripts should fail fast with a clear
# message if this is not set, rather than silently using someone else's email.
ENTREZ_EMAIL = os.environ.get("ODORSIG_ENTREZ_EMAIL", "")


def require_entrez_email():
    """Raise a clear error if ODORSIG_ENTREZ_EMAIL was never configured."""
    if not ENTREZ_EMAIL:
        raise RuntimeError(
            "ODORSIG_ENTREZ_EMAIL is not set. NCBI Entrez requires a real "
            "contact email for API requests. Set it via:\n"
            '  export ODORSIG_ENTREZ_EMAIL="you@example.com"\n'
            "or add it to a .env file (see .env.example)."
        )


# Population standard deviation ranges used to describe docking-run
# consistency (reproducibility), independent of binding-strength classification.
STD_DEV_RANGES = {
    "Consistent Binding": (0.0, 0.2),            # Low variation -> consistent binding
    "Medium Consistency": (0.2, 0.5),             # Moderate variation
    "Inconsistent binding": (0.5, float('inf'))   # High variation -> inconsistent binding
}

# Binding-strength classification, aligned with the thresholds reported in the
# manuscript (Hsin et al.-informed cutoffs used throughout Methods/Results):
#   strong   : dG <= -7.0 kcal/mol
#   moderate : -7.0 < dG <= -5.0 kcal/mol
#   weak     : dG > -5.0 kcal/mol
BINDING_ENERGY_CLASSES = {
    "Strong Binding Affinity":   {"range": (-float('inf'), -7.0), "color": "#0066FF"},  # Blue
    "Moderate Binding Affinity": {"range": (-7.0, -5.0), "color": "#FFFB00"},           # Amber
    "Weak Binding Affinity":     {"range": (-5.0, float('inf')), "color": "#FF7B00"},   # Orange
}


def classify_binding_energy(energy):
    for label, info in BINDING_ENERGY_CLASSES.items():
        low, high = info["range"]
        if low < energy <= high:
            return label, info["color"]
    return "Unknown", "black"
