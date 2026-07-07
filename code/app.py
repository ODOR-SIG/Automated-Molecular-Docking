import io
import re
import os
import sys
import shutil
import threading
import subprocess
import numpy as np
import pandas as pd
from io import BytesIO
import streamlit as st

from Automation_code.config import (
    BASE_DIR, PREPARED_MODELS_DIR, DOCKING_OUTPUT_DIR,
    VINA_EXE, PYMOL_PATH, RECEPTOR_DOWNLOAD_DIR, STD_DEV_RANGES
)
from Automation_code.config import classify_binding_energy

from Automation_code.Step_01_downloading_model_ligands import process_receptor_from_input
from Automation_code.Step_02_validate_model_structure import assess_model
from Automation_code.Step_03_prepare_receptor_ligand import prepare_receptor_and_ligands
from Automation_code.Step_04_config_file import create_all_configs_for_receptor
from Automation_code.Step_05_docking import run_all_dockings_for_receptor
from Automation_code.info_texts import show_binding_energy_info

st.set_page_config(page_title="Molecular Docking UI", page_icon="🧬", layout="centered")

# Top Help Banner
st.markdown("""
<div style='text-align: right;'>
    <span style='font-size: 14px;'>❓ help? Go to the <strong>Help</strong> page.</span>
</div>
""", unsafe_allow_html=True)

st.title("⚛️ Molecular Docking Interface")

# Initialize session state
session_defaults = {
    "plot_bytes": None,
    "csv_data": None,
    "csv_df": None,
    "validation_done": False,
    "prep_done": False,
    "docking_done": False,
    "proceed_to_docking": False,
    "receptor_name": "",
    "ligand_input": "",
    "use_random_seed": True,
    "use_manual_seed": False
}

for key, default in session_defaults.items():
    if key not in st.session_state:
        st.session_state[key] = default

if not st.session_state.proceed_to_docking:
    receptor_name = st.text_input("🔹 Enter Receptor Name", value=st.session_state.receptor_name)
    ligand_input = st.text_input("🔹 Enter Ligand Names (comma-separated)", value=st.session_state.ligand_input)

    if st.button("Submit and Validate"):
        st.session_state.receptor_name = receptor_name
        st.session_state.ligand_input = ligand_input
        st.session_state.validation_done = False
        st.session_state.prep_done = False
        st.session_state.docking_done = False

        if receptor_name and ligand_input:
            ligands = [lig.strip() for lig in ligand_input.split(",") if lig.strip()]

            log_placeholder = st.empty()
            progress_bar = st.progress(0.0, text="🔄 Starting Step 1: Downloading receptor and ligands...")

            def log_callback(msg):
                log_placeholder.text(msg)

            ok, result = process_receptor_from_input(receptor_name, ligands, st_callback=log_callback)
            if not ok:
                progress_bar.empty()
                log_placeholder.empty()
                st.error(f"❌ Download failed: {result}")
                st.stop()

            progress_bar.progress(1 / 3, text="🔍 Step 2: Validating receptor model...")

            ok2, result2 = assess_model(receptor_name, st_callback=log_callback)
            if not ok2:
                progress_bar.empty()
                log_placeholder.empty()
                st.error(f"❌ Validation failed: {result2}")
                st.stop()

            st.session_state.validation_done = True

            vdir = os.path.join(RECEPTOR_DOWNLOAD_DIR, f"{receptor_name}_folder", f"{receptor_name}_validation")
            plot_path = os.path.join(vdir, f"{receptor_name}_Ramachandran_plot.png")
            csv_path = os.path.join(vdir, f"{receptor_name}_Analysis.csv")

            if os.path.isfile(plot_path):
                with open(plot_path, "rb") as f:
                    st.session_state.plot_bytes = f.read()
            if os.path.isfile(csv_path):
                st.session_state.csv_df = pd.read_csv(csv_path)

            progress_bar.progress(2 / 3, text="⚙️ Step 3: Preparing receptor and ligands...")

            ok3, errors = prepare_receptor_and_ligands(receptor_name, st_callback=log_callback)
            if not ok3:
                progress_bar.empty()
                log_placeholder.empty()
                st.error("❌ Preparation failed:")
                for e in errors:
                    st.text(f"- {e}")
                st.stop()

            st.success("✅ Receptor and ligands downloaded and prepared.")
            st.session_state.prep_done = True

            progress_bar.progress(1.0, text="✅ Steps 1–3 completed.")
            progress_bar.empty()
            log_placeholder.empty()

        else:
            st.warning("⚠️ Please enter both receptor and ligands.")

if st.session_state.validation_done:
    if st.session_state.plot_bytes:
        st.subheader("📈 Ramachandran Plot")
        st.image(BytesIO(st.session_state.plot_bytes), width=500)
    if st.session_state.csv_df is not None:
        st.subheader("📊 Validation Table")
        st.dataframe(st.session_state.csv_df)

if st.session_state.validation_done and st.session_state.prep_done and not st.session_state.proceed_to_docking:
    if st.button("➡️ Proceed to Docking"):
        st.session_state.proceed_to_docking = True
        st.rerun()

# Step: 4
if st.session_state.proceed_to_docking:
    receptor_name = st.session_state.receptor_name
    st.divider()
    st.subheader("🛠️ Docking Configuration")

    # 🔹 Set default state only on first visit
    if "use_random_seed" not in st.session_state:
        st.session_state.use_manual_seed = False
    if "use_manual_seed" not in st.session_state:
        st.session_state.use_random_seed = True  # Default: Random seed ON

    def toggle_random():
        st.session_state.use_random_seed = True
        st.session_state.use_manual_seed = False

    def toggle_manual():
        st.session_state.use_manual_seed = True
        st.session_state.use_random_seed = False

    colx1, colx2 = st.columns(2)
    with colx1:
        st.checkbox("Use User Input Seed Docking", key="use_manual_seed", on_change=toggle_manual)
    with colx2:
        st.checkbox("Use Random Seed Docking", key="use_random_seed", on_change=toggle_random)

    with st.form("docking_config_form"):
        exhaustiveness = st.slider("Exhaustiveness", 1, 32, 8)
        num_modes = st.slider("Number of Poses", 1, 20, 10)
        energy_range = st.slider("Energy Range", 1, 10, 3)
        grid_option = st.selectbox("Grid Option", ["Blind Docking"])

        seed_list = []
        if st.session_state.use_manual_seed:
            st.subheader("🔢 Enter 3 Seed Values")
            c1, c2, c3 = st.columns(3)
            with c1: seed1 = st.text_input("Seed 1", value="123")
            with c2: seed2 = st.text_input("Seed 2", value="456")
            with c3: seed3 = st.text_input("Seed 3", value="789")

        center = size = None
        if grid_option == "User Input":
            center = [st.number_input(f"Center {a}", value=0.0) for a in "XYZ"]
            size = [st.number_input(f"Size {a}", value=20.0) for a in "XYZ"]

        submitted = st.form_submit_button("🚀 Start Docking")

    if submitted:
        show_binding_energy_info()  # 🔔 show binding energy explanation
        
        try:
            if st.session_state.use_manual_seed:
                try:
                    seed_list = [int(seed1), int(seed2), int(seed3)]
                except:
                    st.error("⚠️ Please enter valid integers for all three seeds.")
                    st.stop()
            elif not st.session_state.use_random_seed:
                st.error("❌ Please select a seed strategy.")
                st.stop()

            st.session_state.docking_done = False

            docking_folder = os.path.join(DOCKING_OUTPUT_DIR, f"{receptor_name}_folder")
            if os.path.exists(docking_folder):
                shutil.rmtree(docking_folder)
            os.makedirs(docking_folder)

            create_all_configs_for_receptor(
                receptor_name=receptor_name,
                mode="manual" if grid_option == "User Input" else "blind",
                center=center,
                size=size,
                exhaustiveness=exhaustiveness,
                num_modes=num_modes,
                energy_range=energy_range
            )

            log_placeholder = st.empty()
            progress_bar = st.progress(0, text="Preparing for docking...")

            class LiveLogger:
                def __init__(self, placeholder):
                    self.output = io.StringIO()
                    self.placeholder = placeholder
                    self._lock = threading.Lock()

                def write(self, message):
                    with self._lock:
                        self.output.write(message)
                        lines = self.output.getvalue().splitlines()[-8:]
                        self.placeholder.markdown("```text\n" + "\n".join(lines) + "\n```")

                def flush(self):
                    pass
                
            # 🔄 Redirect stdout
            original_stdout = sys.stdout
            logger = LiveLogger(log_placeholder)
            sys.stdout = logger

            try:
                run_all_dockings_for_receptor(
                    receptor_name=receptor_name,
                    prepared_base_dir=PREPARED_MODELS_DIR,
                    seed_list=seed_list if st.session_state.use_manual_seed else None,
                    vina_exe=VINA_EXE,
                    progress_bar=progress_bar
                )
                st.session_state.docking_done = True
                # ✅ Clear the message block
                progress_bar.empty()
                log_placeholder.empty()
                st.success("✅ Docking completed.")
            except Exception as e:
                st.error(f"❌ Docking failed: {e}")
            finally:
                sys.stdout = original_stdout

        except Exception as e:
            st.error(f"❌ Docking failed: {e}")

# === Step 5: Docking Results ===
if st.session_state.docking_done:
    st.divider()
    st.header("📁 Docking Results")

    def parse_binding_energies(log_file):
        energies = []
        try:
            with open(log_file, 'r') as f:
                for line in f:
                    if re.match(r'\s*\d+\s+[-\d.]+\s+[-\d.]+\s+[-\d.]+', line):
                        parts = line.split()
                        energies.append(float(parts[1]))
        except:
            pass
        return energies

    def launch_pymol(receptor_path, output_path):
        try:
            if os.name == "nt":
                subprocess.run(["start", "", PYMOL_PATH, receptor_path, output_path], shell=True)
            else:
                subprocess.Popen([PYMOL_PATH, receptor_path, output_path])
        except Exception as e:
            st.error(f"PyMOL launch failed: {e}")

    receptor_dir = os.path.join(DOCKING_OUTPUT_DIR, f"{receptor_name}_folder")
    receptor_path = os.path.join(PREPARED_MODELS_DIR, f"{receptor_name}_folder", f"{receptor_name}.pdbqt")

    ligand_rows = {}
    for file in sorted(os.listdir(receptor_dir)):
        if file.endswith("_log.txt"):
            log_path = os.path.join(receptor_dir, file)
            match = re.match(f"{receptor_name}_(.+?)_log\\.txt", file)
            if not match:
                continue
            ligand_id = match.group(1)
            parts = ligand_id.split("_")

            if "seed" in parts:
                seed_type = "Seed"
                seed_name = parts[-1]
                ligand_base = "_".join(parts[:-2])
            elif "random" in parts:
                seed_type = "Random"
                seed_name = parts[-1]
                ligand_base = "_".join(parts[:-2])
            else:
                seed_type = "Seed"
                seed_name = "default"
                ligand_base = ligand_id

            energies = parse_binding_energies(log_path)
            if ligand_base not in ligand_rows:
                ligand_rows[ligand_base] = {}
            ligand_rows[ligand_base][f"{seed_type}_{seed_name}"] = {
                "energies": energies,
                "log": log_path,
                "pdbqt": os.path.join(receptor_dir, f"{receptor_name}_{ligand_id}_output.pdbqt")
            }

    for ligand_name, seeds in ligand_rows.items():
        mode_count = max(len(data["energies"]) for data in seeds.values())
        table_data = []
        seed_names = sorted(seeds.keys())

        for i in range(mode_count):
            row = {"Ligand": ligand_name, "Mode": str(i + 1)}
            for seed in seed_names:
                e = seeds[seed]["energies"]
                val = e[i] if i < len(e) else ""
                row[seed] = f"{val:.4f}" if val != "" else ""
            try:
                avg = np.mean([float(row[s]) for s in seed_names if row[s]])
                row["Average Affinity"] = f"{avg:.4f}"
            except:
                row["Average Affinity"] = ""
            table_data.append(row)

        df = pd.DataFrame(table_data)
        first_avg_affinity = df["Average Affinity"].iloc[0]

        col1, col2 = st.columns([0.75, 0.25])
        with col1:
            st.subheader(f"🧪 Docking: `{receptor_name}+{ligand_name}`")
        with col2:
            csv_buf = BytesIO()
            df.to_csv(csv_buf, index=False)
            csv_buf.seek(0)
            st.download_button("⬇️ Download CSV", csv_buf, f"{ligand_name}_docking.csv", "text/csv", key=f"dl_{ligand_name}")

        st.dataframe(df.drop(columns=["Ligand"]).style.hide(axis="index"), use_container_width=True)

        cols = st.columns(len(seed_names))
        for i, seed in enumerate(seed_names):
            with cols[i]:
                if st.button(f"See Pose {seed}", key=f"{ligand_name}_{seed}"):
                    launch_pymol(receptor_path, seeds[seed]["pdbqt"])

        # Show the best binding energy line
        best_score = float("inf")
        best_seed = None
        for seed in seed_names:
            energies = seeds[seed]["energies"]
            if energies:
                min_energy = min(energies)
                if min_energy < best_score:
                    best_score = min_energy
                    best_seed = seed

        def classify_std_dev(value, ranges):
            for label, (low, high) in ranges.items():
                if low <= value < high:
                    return label
            return "Unknown"

        if best_seed is not None:
            first_row = df.iloc[0]
            seed_vals = [float(first_row[seed]) for seed in seed_names if first_row[seed] != ""]
            n = len(seed_vals)
            if n > 0:
                mean_val = sum(seed_vals) / n
                variance = sum((x - mean_val) ** 2 for x in seed_vals) / n
                pop_std_dev = variance ** 0.5
                std_dev_class = classify_std_dev(pop_std_dev, STD_DEV_RANGES)
            else:
                pop_std_dev = None
                std_dev_class = "N/A"

            class_color = {
                "Consistent Binding": "#00A100",     # Green
                "Medium Consistency": "#FFB833",         # Orange
                "Inconsistent binding": "#EF0000",   # Red
                "N/A": "#808080",                    # Gray
                "Unknown": "#000000"                 # Black
            }.get(std_dev_class, "#000000")
            

            # ✅ NEW: Binding energy class and color
            binding_class, binding_color = classify_binding_energy(best_score)

            suggestion = ""
            if std_dev_class == "Medium Consistency":
                suggestion = "For Vina slight variation across the results is expected</b>."
            elif std_dev_class == "Inconsistent binding":
                suggestion = "Consistency of the binding can be increased by increasing the <b>Exhaustiveness</b> or try <b>Fixed seed Docking</b>."

            st.markdown(
                f"""
                <div style='padding-top: 8px; font-weight: bold;'>
                    Best binding energy is: {best_score:.4f} (minimum)<br>
                    Average binding affinity: {float(first_avg_affinity):.4f}<br>
                    <span style='color:{binding_color}'>{binding_class}</span><br>
                    <span style='color:{class_color}'>{std_dev_class}</span><br>
                    <div style='color: gray; font-weight: normal; padding-top: 5px;'>{suggestion}</div>
                </div>
                """,
                unsafe_allow_html=True
            )
