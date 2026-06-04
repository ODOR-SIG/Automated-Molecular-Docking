import os
import re
import subprocess
import time
from Automation_code.config import DOCKING_OUTPUT_DIR, PYMOL_PATH, VINA_EXE


def sanitize_ligand_name(name):
    """Sanitize ligand name to remove problematic characters for file paths."""
    return re.sub(r'[^A-Za-z0-9_-]', '_', name)


def run_docking(vina_exe, config_file, log_file, out_file, seed):
    try:
        cmd = [vina_exe, "--config", config_file, "--out", out_file]

        if seed is not None:
            cmd.extend(["--seed", str(seed)])

        result = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )

        with open(log_file, 'w') as log_f:
            log_f.write(result.stdout)

        return f"✅ Docked ({'seed ' + str(seed) if seed is not None else 'random'}): {os.path.basename(log_file)}"
    except Exception as e:
        return f"❌ Error docking ({'seed ' + str(seed) if seed is not None else 'random'}): {str(e)}"


def run_all_dockings_for_receptor(receptor_name, prepared_base_dir, seed_list, vina_exe=VINA_EXE, progress_bar=None):
    receptor_folder = f"{receptor_name}_folder"
    receptor_path = os.path.join(prepared_base_dir, receptor_folder)

    if not os.path.isdir(receptor_path):
        raise FileNotFoundError(f"Receptor folder not found: {receptor_path}")

    receptor_file = os.path.join(receptor_path, f"{receptor_name}.pdbqt")
    if not os.path.isfile(receptor_file):
        raise FileNotFoundError(f"Receptor file not found: {receptor_file}")

    receptor_result_dir = os.path.join(DOCKING_OUTPUT_DIR, receptor_folder)
    os.makedirs(receptor_result_dir, exist_ok=True)

    docking_jobs = []

    for file in os.listdir(receptor_path):
        if file.endswith(".pdbqt") and file != f"{receptor_name}.pdbqt":
            ligand_name = os.path.splitext(file)[0]
            config_file = os.path.join(receptor_path, f"{ligand_name}_config.txt")
            if not os.path.isfile(config_file):
                print(f"⚠️ Missing config file for ligand: {ligand_name}")
                continue

            ligand_name_clean = sanitize_ligand_name(ligand_name)

            if seed_list is None:
                for i in range(1, 4):
                    log_file = os.path.join(
                        receptor_result_dir,
                        f"{receptor_name}_{ligand_name_clean}_random_{i}_log.txt"
                    )
                    out_file = os.path.join(
                        receptor_result_dir,
                        f"{receptor_name}_{ligand_name_clean}_random_{i}_output.pdbqt"
                    )
                    docking_jobs.append((vina_exe, config_file, log_file, out_file, None))
            else:
                for seed in seed_list:
                    log_file = os.path.join(
                        receptor_result_dir,
                        f"{receptor_name}_{ligand_name_clean}_seed_{seed}_log.txt"
                    )
                    out_file = os.path.join(
                        receptor_result_dir,
                        f"{receptor_name}_{ligand_name_clean}_seed_{seed}_output.pdbqt"
                    )
                    docking_jobs.append((vina_exe, config_file, log_file, out_file, seed))

    total_jobs = len(docking_jobs)
    print(f"🚀 Starting docking for {total_jobs} total jobs...")

    for i, job in enumerate(docking_jobs, 1):
        log_basename = os.path.basename(job[2])
        print(f"[{i}/{total_jobs}] Docking {log_basename.replace('_log.txt', '')}...")

        if progress_bar:
            # Simulate 1/3 of progress before actual docking
            initial = (i - 1) / total_jobs
            interim = initial + (1 / 3) * (1 / total_jobs)
            step = (interim - initial) / 20
            for _ in range(20):
                progress_bar.progress(initial)
                initial += step
                time.sleep(0.05)

        result = run_docking(*job)
        print(result)

        if progress_bar:
            progress_bar.progress(i / total_jobs)

    print("✅ All docking completed.")
    return f"{total_jobs} docking job(s) completed."


def parse_log_file(log_path):
    energies = []
    try:
        with open(log_path, 'r') as f:
            for line in f:
                if line.strip().startswith("REMARK VINA RESULT:"):
                    parts = line.strip().split()
                    if len(parts) >= 4:
                        try:
                            energy = float(parts[3])
                            pose_number = len(energies) + 1
                            energies.append((pose_number, energy))
                        except ValueError:
                            continue
    except Exception as e:
        print(f"Error reading log file {log_path}: {e}")
    return energies


def launch_pymol_for_pose(receptor_file, ligand_file):
    try:
        subprocess.Popen([PYMOL_PATH, receptor_file, ligand_file])
    except Exception as e:
        print(f"❌ Error launching PyMOL: {e}")
