# about.py

import streamlit as st

st.set_page_config(page_title="About", layout="centered")

st.title("About This Project")
st.markdown("""
This project presents a streamlined interface for **automated molecular docking**, designed to simplify the typical multi-step process involved in virtual screening and drug discovery.

---

### 🚀 Features
- Receptor and ligand retrieval from reliable databases
- 3D model validation via Ramachandran plots and structural analysis
- Preparation of docking-ready PDBQT files
- Configuration generation for AutoDock Vina
- Automatic molecular docking and result reporting
- Interactive plots and CSV summaries for validation

---

### 🧠 Technologies Used
- **Python**, **Streamlit** for the interface  
- **Selenium**, **Biopython**, **Pandas**, **NumPy** for backend automation  
- **SwissModel**, **AutoDock Vina**, **PyMOL** for modeling and visualization

---

### 📍 Project Structure
- Modular scripts handle individual pipeline steps
- Logs, progress bars, and validation ensure reliability
- Flexible ligand input supports comma-separated names

---

### 👨‍🔬 Use Case
Designed for researchers, bioinformaticians, and students working in:
- Drug discovery
- Computational biology
- Molecular modeling

---

📄 *Created by [Atirath Pal](https://www.linkedin.com/in/atirath-pal-95163b28a/) as part of a Summer Internship project (2025) at IIT Mandi.*  
*Guided by [Divyanshu Bajpai](https://www.linkedin.com/in/divyanshu-bajpai-8032b092/) and Supervised by [Prof. Dr. Shubhajit Roy Chowdhury](https://www.linkedin.com/in/shubhajit-roy-chowdhury-494196a/?originalSubdomain=in) Chairperson,CHCi,IIT Mandi*

🔗 For help and instructions, visit the Help Page

""")
