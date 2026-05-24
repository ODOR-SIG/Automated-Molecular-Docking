import os
import numpy as np
from Automation_code.config import PREPARED_MODELS_DIR

def extract_protein_coordinates(pdbqt_path):
    coords = []
    with open(pdbqt_path, 'r') as f:
        for line in f:
            if line.startswith("ATOM") or line.startswith("HETATM"):
                x = float(line[30:38])
                y = float(line[38:46])
                z = float(line[46:54])
                coords.append([x, y, z])
    return np.array(coords)

def generate_blind_config(protein_path, ligand_path, config_path, exhaustiveness, num_modes, energy_range=3, buffer=10.0):
    coords = extract_protein_coordinates(protein_path)
    if coords.size == 0:
        print(f"⚠️ No atoms found in {protein_path}")
        return

    center = coords.mean(axis=0)
    min_coords = coords.min(axis=0)
    max_coords = coords.max(axis=0)
    size = (max_coords - min_coords) + buffer

    with open(config_path, 'w') as f:
        f.write(f"receptor = {protein_path}\n")
        f.write(f"ligand = {ligand_path}\n\n")
        f.write(f"center_x = {center[0]:.3f}\n")
        f.write(f"center_y = {center[1]:.3f}\n")
        f.write(f"center_z = {center[2]:.3f}\n\n")
        f.write(f"size_x = {size[0]:.3f}\n")
        f.write(f"size_y = {size[1]:.3f}\n")
        f.write(f"size_z = {size[2]:.3f}\n\n")
        f.write(f"exhaustiveness = {exhaustiveness}\n")
        f.write(f"num_modes = {num_modes}\n")
        f.write(f"energy_range = {energy_range}\n")

    print(f"✅ Config created: {os.path.basename(config_path)}")

def create_all_configs_for_receptor(
    receptor_name,
    base_dir=None,
    mode="blind",
    center=None,
    size=None,
    exhaustiveness=16,
    num_modes=10,
    energy_range=3
):
    model_root = base_dir if base_dir else PREPARED_MODELS_DIR
    model_folder = os.path.join(model_root, f"{receptor_name}_folder")

    if not os.path.isdir(model_folder):
        raise FileNotFoundError(f"Model folder not found: {model_folder}")

    receptor_file = os.path.join(model_folder, f"{receptor_name}.pdbqt")
    if not os.path.isfile(receptor_file):
        raise FileNotFoundError(f"Receptor .pdbqt file not found: {receptor_file}")

    for file in os.listdir(model_folder):
        if file.endswith(".pdbqt") and file != f"{receptor_name}.pdbqt":
            ligand_path = os.path.join(model_folder, file)
            ligand_base = os.path.splitext(file)[0].replace(" ", "")
            config_path = os.path.join(model_folder, f"{ligand_base}_config.txt")

            if mode == "blind":
                generate_blind_config(
                    protein_path=receptor_file,
                    ligand_path=ligand_path,
                    config_path=config_path,
                    exhaustiveness=exhaustiveness,
                    num_modes=num_modes,
                    energy_range=energy_range
                )
            else:
                raise NotImplementedError("Only blind docking is supported right now.")
