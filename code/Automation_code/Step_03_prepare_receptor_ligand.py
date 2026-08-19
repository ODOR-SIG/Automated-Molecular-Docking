import os
import shutil
import subprocess
from Automation_code.config import (
    RECEPTOR_DOWNLOAD_DIR,
    PREPARED_MODELS_DIR,
    MODEL_CHAIN_A_ONLY,
    OBABEL_PATH
)
from Automation_code.receptor_ligand_prep import extract_chain_a, convert_to_pdbqt

def prepare_receptor_and_ligands(receptor, base_dir=None, st_callback=print):
    input_root = base_dir if base_dir else RECEPTOR_DOWNLOAD_DIR
    output_root = PREPARED_MODELS_DIR
    chainA_dir = MODEL_CHAIN_A_ONLY

    os.makedirs(chainA_dir, exist_ok=True)
    os.makedirs(output_root, exist_ok=True)

    errors = []
    receptor_folder = f"{receptor}_folder"
    receptor_input_dir = os.path.join(input_root, receptor_folder)
    receptor_output_dir = os.path.join(output_root, receptor_folder)

    # 🔄 Reset receptor output folder if it already exists
    if os.path.exists(receptor_output_dir):
        shutil.rmtree(receptor_output_dir)
    os.makedirs(receptor_output_dir, exist_ok=True)

    for root, _, files in os.walk(receptor_input_dir):
        for file in files:
            if file.endswith(".pdb"):
                input_path = os.path.join(root, file)

                if "ligands" in input_path.lower():
                    # Ligand processing
                    ligand_name = os.path.splitext(file)[0]
                    output_path = os.path.join(receptor_output_dir, f"{ligand_name}.pdbqt")
                    convert_source = input_path
                    is_receptor = False
                    tag = "[Ligand]"
                else:
                    # Receptor processing
                    tag = "[Protein]"
                    chainA_path = os.path.join(chainA_dir, f"{receptor}.pdb")

                    try:
                        extract_chain_a(input_path, chainA_path)
                    except Exception as e:
                        errors.append(f"{tag} Error processing {file}: {e}")
                        continue

                    output_path = os.path.join(receptor_output_dir, f"{receptor}.pdbqt")
                    convert_source = chainA_path
                    is_receptor = True

                # Run the Open Babel command (log message still refers to the
                # original input_path, matching pre-refactor behaviour, even
                # though the receptor branch converts from chainA_path).
                st_callback(f"{tag} Processing: {input_path}")
                try:
                    convert_to_pdbqt(OBABEL_PATH, convert_source, output_path, receptor=is_receptor)
                    st_callback(f"    ✔ Saved: {output_path}\n")
                except subprocess.CalledProcessError:
                    errors.append(f"{tag} ❌ Failed to convert: {input_path}")

    return (len(errors) == 0), errors
