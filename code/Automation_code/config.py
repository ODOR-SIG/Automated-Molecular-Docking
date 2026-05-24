# config.py

import os

# Base project directory
BASE_DIR = r"C:\Users\atira\OneDrive\Desktop\pipeline\Automated_Molecular_Docking"

# Subdirectories inside the project
UI_AUTOMATION_DIR     = os.path.join(BASE_DIR, "Automation_code")
DOCKING_OUTPUT_DIR    = os.path.join(BASE_DIR, "DockingResults")
PREPARED_MODELS_DIR   = os.path.join(BASE_DIR, "prepared_models")
MODEL_CHAIN_A_ONLY    = os.path.join(BASE_DIR, "model_chain_A_only")
RECEPTOR_DOWNLOAD_DIR = os.path.join(BASE_DIR, "first_stage_model_download")
FASTA_DOWNLOAD_DIR    = os.path.join(BASE_DIR, "fasta_downloads")


# External executable paths
PYMOL_PATH    = r"C:\Users\atira\OneDrive\Desktop\PyMOL.lnk"
CHROMEDRIVER  = r"C:\Users\atira\OneDrive\Desktop\WEB_DRIVER\chromedriver-win64\chromedriver.exe"
VINA_EXE      = r"C:\Users\atira\OneDrive\Desktop\pipeline\vina.exe"
OBABEL_PATH   = r"C:\Users\atira\miniconda3\envs\obabel_env\Library\bin\obabel.exe"

# Biopython Entrez email (required by NCBI)
ENTREZ_EMAIL = "atirathpal@gmail.com"

# Population standard deviation ranges for binding affinity classification
STD_DEV_RANGES = {
    "Consistent Binding": (0.0, 0.2),      # Low variation → consistent binding
    "Medium Consistency": (0.2, 0.5),    # Moderate variation
    "Inconsistent binding": (0.5, float('inf'))  # High variation → inconsistent binding
}

# color coding
BINDING_ENERGY_CLASSES = {
    "Strong Binding Affinity": {"range": (-float('inf'), -6.5), "color": "#0066FF"},   # Blue
    "Moderate Binding Affinity": {"range": (-6.5, -5.4), "color": "#FFFB00"},         # Amber
    "Weak Binding Affinity": {"range": (-5.4, -4.0), "color": "#FF7B00"},             # Orange
    "Very Weak Binding Affinity": {"range": (-4.0, float('inf')), "color": "#818181"} # Gray
}


def classify_binding_energy(energy):
    for label, info in BINDING_ENERGY_CLASSES.items():
        low, high = info["range"]
        if low < energy <= high:
            return label, info["color"]
    return "Unknown", "black"
