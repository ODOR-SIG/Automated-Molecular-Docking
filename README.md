# 🧬 Automated Molecular Docking Pipeline
[![DOI](https://zenodo.org/badge/1096235543.svg)](https://doi.org/10.5281/zenodo.17814494)

![GitHub License](https://img.shields.io/badge/license-MIT-green.svg)
![GitHub stars](https://img.shields.io/github/stars/ODOR-SIG/Automated-Molecular-Docking?style=social)
![GitHub last commit](https://img.shields.io/github/last-commit/ODOR-SIG/Automated-Molecular-Docking)
![Issues](https://img.shields.io/github/issues/ODOR-SIG/Automated-Molecular-Docking)
![Pull Requests](https://img.shields.io/github/issues-pr/ODOR-SIG/Automated-Molecular-Docking)
![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)
![Framework](https://img.shields.io/badge/Framework-Streamlit-ff4b4b.svg)
![Docking Engine](https://img.shields.io/badge/Engine-AutoDock_Vina-green.svg)
[![Field](https://img.shields.io/badge/Domain-Bioinformatics-lightblue.svg)](#)


---

##  Overview

The **Automated Molecular Docking Pipeline** is a research-focused Python framework developed to automate receptor–ligand retrieval, validation, docking, and visualization using open-source bioinformatics tools.  
The system integrates **AutoDock Vina, Open Babel, PyMOL, RDKit, Biopython**, and a **Streamlit** interface to deliver a fully automated workflow that reduces manual effort by more than **90%**.

Originally developed as part of ongoing PhD research in digital olfaction **IIT Mandi, CHCi Lab**, this pipeline is optimized for reproducibility, accessibility, and high-throughput docking — making it suitable for applications in cheminformatics, drug discovery, and computational olfactory research. 
> **Tagline:**  
> *"From sequence to docking — automated, reproducible, and researcher-friendly."*

---

##  Key Features

- 🔹 **End-to-end automation** of receptor & ligand retrieval, preparation, validation, and docking  
- 🔹 **Direct integration** with NCBI, PubChem & SWISS-MODEL  
- 🔹 **Ramachandran plot–based validation** for receptor reliability  
- 🔹 **Batch docking support** (multiple ligands → one receptor)  
- 🔹 **Streamlit visual interface** (no command line needed)  
- 🔹 **PyMOL visualization** of 3D docking poses  
- 🔹 **Auto-generated Vina configuration files**  
- 🔹 **CSV-based report export**  
- 🔹 **Random/user-defined seed support** for reproducible docking  
- 🔹 **Robust logging and error handling**  

---

##  System Workflow (Architecture)

The pipeline follows a modular, reproducible workflow:

1. **User Input** (Receptor ID, ligand names, seed mode)  
2. **Data Retrieval**  
   - Receptor → NCBI  
   - Ligand → PubChem  
   - Validation → SWISS-MODEL  
3. **Structure Preparation** (Open Babel → `.pdbqt`)  
4. **Model Validation** (Ramachandran plot, QMEAN, GMQE)  
5. **Docking Configuration** (Grid box, exhaustiveness, seed)  
6. **Docking Execution** (AutoDock Vina automation)  
7. **Results Parsing** (binding affinity, RMSD)  
8. **Visualization** (PyMOL 3D pose view)  
9. **Report Export** (CSV + images)

![Workflow Diagram](https://github.com/Atirath-Pal/Automated-Molecular-Docking/blob/397ca159e6a52fec18d65defd79f3d1d216dfaef/flowchart_pipeline.jpg)

---

## 📸 Screenshots

###  User Input Interface  
![User Input Interface](https://github.com/Atirath-Pal/Automated-Molecular-Docking/blob/6c7b229871ed45bdf45398e4c1e4c190f8e8caad/ui_input.jpg)

###  Docking Results  
![Docking Results](https://github.com/Atirath-Pal/Automated-Molecular-Docking/blob/7ad212c99a1face5ec5862c380b18140be485388/output_interface.png)

###  Ramachandran Plot Validation  
![Ramachandran Plot](https://github.com/Atirath-Pal/Automated-Molecular-Docking/blob/534af0b55af7134241c276108938a21acb8df7d2/ramachandran_plot.png)

###  Docking Pose Visualization  
![Docking Pose](https://github.com/Atirath-Pal/Automated-Molecular-Docking/blob/3fd195e811be2cda1528e24eaf16762887232290/pymol_visualization.png)

### 🎬 Demonstration Video  
▶️ https://vimeo.com/1136320708?share=copy&fl=sv&fe=ci

---

## 🧬 Tools & Technologies
| Category | Tool / Library | Version | Purpose |
|--------|----------------|--------|---------|
| **Programming Language** | Python | 3.10+ | Core language for automation, computation, and application logic |
| **Docking Engine** | AutoDock Vina | 1.2.5 | Performs receptor–ligand docking and estimates binding affinities |
| **Structure Conversion** | Open Babel | 3.1.1 | Converts molecular formats and prepares `.pdbqt` files for docking |
| **Visualization** | PyMOL (Open-Source) | 3.1.6.1 | 3D visualization of receptor–ligand binding poses |
| **User Interface** | Streamlit | 1.35+ | Interactive web interface for running docking experiments |
| **Data Retrieval** | Biopython (Entrez) | 1.83+ | Retrieves receptor sequences from NCBI |
|  | Requests | 2.32+ | Handles API calls and file downloads |
|  | BeautifulSoup4 | 4.12+ | Parses biological and validation web data |
| **Molecular Informatics** | RDKit | 2025.03+ | Ligand structure handling and chemical analysis |
| **Automation** | Selenium | 4.23+ | Automates web-based data retrieval |
|  | Subprocess | Built-in | Executes AutoDock Vina & Open Babel commands |
| **Data Processing** | Pandas | 2.2+ | Manages docking results and CSV report generation |
|  | NumPy | 2.0+ | Numerical analysis and statistical calculations |
| **Plotting** | Matplotlib | 3.9+ | Visualization of docking and validation results |
| **System Utilities** | OS, Shutil, Threading | Built-in | File management and task parallelization |
| **Version Control** | Git | 2.45+ | Source code version control |
|  | GitHub | Cloud | Repository hosting and collaboration |


---

### Development Environment

- **Operating System:** Windows 11
- **Python Version:** 3.10 or higher
- **IDE / Editor:** VS Code
- **External Dependencies:** AutoDock Vina, Open Babel, PyMOL

> *All external tools must be correctly installed and their executable paths configured in `config.py` before running the pipeline.*



##  Installation
The **Automated Molecular Docking Pipeline** integrates multiple open-source bioinformatics and cheminformatics tools.  
Follow the steps below to set up your environment and ensure smooth execution.

---

### 1️⃣ System Requirements

| Component | Recommended Specification |
|------------|----------------------------|
| **Operating System** | Windows 11 |
| **Python Version** | 3.9 or above |
| **RAM** | Minimum 8 GB (16 GB preferred) |
| **Storage** | ~2 GB free space |
| **Internet Connection** | Required for data retrieval (NCBI, PubChem, SWISS-MODEL) |

---

### 2️⃣ Prerequisite Software

#### 🧬 AutoDock Vina
- Download: [https://vina.scripps.edu/](https://vina.scripps.edu/)
- Extract and add the `vina` executable to your **PATH**.
  - **Windows:** `C:\Program Files\Vina\vina.exe`
  - **Linux/macOS:** `/usr/local/bin/vina`

####  Open Babel
- Handles structure cleaning and file conversion.
- Download: [https://openbabel.org/wiki/Main_Page](https://openbabel.org/wiki/Main_Page)
- Add `obabel` to your **PATH**.

####  PyMOL
- Used for 3D visualization of receptor–ligand docking results.
- Download: [https://pymol.org/](https://pymol.org/)
- (Optional) Open-source install:
  ```bash
  conda install -c schrodinger pymol





##  Usage

Run the Streamlit interface:

```bash
streamlit run app.py
```

Or run docking directly:

```bash
python run_docking.py --receptor OR1A1 --ligand citral
```

---

##  Example Docking Output

| Pose | Binding Energy (kcal/mol) | RMSD | Notes |
|------|----------------------------|-------|-------|
| 1 | -7.6 | 0.0 | Best pose |
| 2 | -6.9 | 1.2 | Alternative pose |
| 3 | -6.4 | 2.1 | Less stable |

---


##  Citation

If you use this tool in scientific research, please cite:

```bibtex
@software{bajpai2025automateddocking,
  author = {Divyanshu Bajpai,Atirath Pal and shubhajit Roy Chowdhury},
  title = {Automated Molecular Docking Pipeline},
  year = {2025},
  publisher = {ODOR-SIG},
  version = {1.0.0},
  doi = {10.5281/zenodo.17814494},
  url = {https://github.com/ODOR-SIG/Automated-Molecular-Docking},
}
```

---

##  Code Availability 

The complete source code is openly available at:

 **https://github.com/ODOR-SIG/Automated-Molecular-Docking**

A DOI-versioned archival release is available on Zenodo:

**https://doi.org/10.5281/zenodo.17814494**

---

##  License

This project is released under the **MIT License**.  
See the `LICENSE` file for details.

---

## 👤 Author

**Divyanshu Bajpai**  
**Atirath Pal**  
Research Group — Digital Smell, Computational Biology, HCI  
Digital smell Technology Research Group
Indian Institute of Technology-Mandi

