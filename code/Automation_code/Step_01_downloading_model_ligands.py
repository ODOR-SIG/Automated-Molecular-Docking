import os  # For interacting with the operating system (file paths, environment variables)
import time  # For adding delays while web-scraping
import shutil  # For file operations for receptor model downloading and saving
import requests  # For making HTTP requests to download data from web APIs
import subprocess  # For running shell commands and external programs from within Python
from Bio import Entrez  # For accessing NCBI's Entrez system to fetch biological data (Receptor proteins)
from selenium import webdriver  # For automating web browser interaction (web scraping)
from selenium.webdriver.common.by import By  # For selecting HTML elements by tag, class, id, etc.
from selenium.webdriver.support.ui import WebDriverWait  # For waiting until certain conditions are met in the browser
from selenium.webdriver.support import expected_conditions as EC  # For specifying the expected conditions to wait for
from selenium.webdriver.chrome.service import Service  # For managing the ChromeDriver service for Selenium

from Automation_code.config import FASTA_DOWNLOAD_DIR, RECEPTOR_DOWNLOAD_DIR, CHROMEDRIVER
from Automation_code.config import OBABEL_PATH, ENTREZ_EMAIL

Entrez.email = ENTREZ_EMAIL  # Required by NCBI Entrez API to identify the user making requests

if os.path.exists(FASTA_DOWNLOAD_DIR):
    shutil.rmtree(FASTA_DOWNLOAD_DIR)
os.makedirs(FASTA_DOWNLOAD_DIR)

def download_fasta_from_gene(gene_name, organism="Homo sapiens", save_dir=FASTA_DOWNLOAD_DIR):
    try:
        if os.path.exists(save_dir):
            shutil.rmtree(save_dir)
        os.makedirs(save_dir)

        def search_ncbi(term):
            handle = Entrez.esearch(db="protein", term=term, retmax=1)
            record = Entrez.read(handle)
            handle.close()
            return record.get("IdList", [])

        term_refseq = f"{gene_name}[Gene Name] AND {organism}[Organism] AND srcdb_refseq[PROP]"
        id_list = search_ncbi(term_refseq)

        if not id_list:
            term_genbank = f"{gene_name}[Gene Name] AND {organism}[Organism]"
            id_list = search_ncbi(term_genbank)

        if not id_list:
            return None, f"No sequence found for {gene_name}"

        protein_id = id_list[0]
        fetch_handle = Entrez.efetch(db="protein", id=protein_id, rettype="fasta", retmode="text")
        fasta_data = fetch_handle.read()
        fetch_handle.close()

        fasta_path = os.path.join(save_dir, f"{gene_name}.fasta")
        with open(fasta_path, "w") as f:
            f.write(fasta_data)

        return fasta_path, None

    except Exception as e:
        return None, str(e)

def upload_to_swiss_model(fasta_path, save_path, st_callback=None):
    driver = None
    try:
        with open(fasta_path, "r") as f:
            fasta_data = f.read()

        if st_callback:
            st_callback("🔁 Launching SwissModel in browser...")

        # options = webdriver.ChromeOptions()
        # # ❌ No headless mode — browser will be visible
        # options.add_argument("--disable-gpu")
        # options.add_argument("--no-sandbox")
        # options.add_argument("--window-size=1920,1080")

        service = Service(CHROMEDRIVER)
        # driver = webdriver.Chrome(service=service, options=options)
        driver = webdriver.Chrome(service=service)

        driver.get("https://swissmodel.expasy.org/interactive")

        textarea = WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.ID, "id_target")))
        textarea.clear()
        textarea.send_keys(fasta_data)

        build_btn = WebDriverWait(driver, 20).until(EC.element_to_be_clickable((By.ID, "buildButton")))
        driver.execute_script("arguments[0].scrollIntoView(true);", build_btn)
        time.sleep(1)
        build_btn.click()

        if st_callback:
            st_callback("Wait for 2 minutes Receptor Modeling is under progress ...")

        pdb_link = WebDriverWait(driver, 600).until(
            EC.presence_of_element_located((By.XPATH, "//a[contains(@href, '.pdb') and contains(text(), 'PDB format')]"))
        )

        if st_callback:
            st_callback("⏳ Waiting for 30 seconds Receptor is being refined ...")
        time.sleep(30)

        pdb_href = pdb_link.get_attribute("href")
        response = requests.get(pdb_href)

        with open(save_path, "wb") as f:
            f.write(response.content)

        return True, None

    except Exception as e:
        return False, str(e)

    finally:
        if driver:
            driver.quit()

def download_and_convert_ligands(ligands, output_folder, st_callback=None):
    ligand_folder = os.path.join(output_folder, "ligands")

    if os.path.exists(ligand_folder):
        shutil.rmtree(ligand_folder)
    os.makedirs(ligand_folder)

    base_url = "https://pubchem.ncbi.nlm.nih.gov/rest/pug"
    sdf_temp = os.path.join(ligand_folder, "temp_ligand.sdf")
    errors = []

    for ligand in ligands:
        try:
            safe_name = ligand.replace("/", "-").replace("\\", "-").replace(" ", "_")
            if st_callback:
                st_callback(f"🔍 Fetching ligand: {ligand}")

            cid_url = f"{base_url}/compound/name/{ligand}/cids/TXT"
            cid_response = requests.get(cid_url)
            cid_list = cid_response.text.strip().split()
            if not cid_list:
                raise ValueError("CID not found")

            cid = cid_list[0]
            sdf_url = f"{base_url}/compound/cid/{cid}/record/SDF/?record_type=3d&response_type=display"
            sdf_response = requests.get(sdf_url)
            if sdf_response.status_code != 200 or not sdf_response.text.strip():
                raise ValueError("3D SDF not available")

            with open(sdf_temp, "w", encoding="utf-8") as f:
                f.write(sdf_response.text)

            pdb_path = os.path.join(ligand_folder, f"{safe_name}.pdb")
            result = subprocess.run(
                [OBABEL_PATH, sdf_temp, "-O", pdb_path],
                stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
            )
            if result.returncode != 0:
                raise RuntimeError(f"Open Babel error: {result.stderr.strip()}")

            if st_callback:
                st_callback(f"✅ Saved: {pdb_path}")

        except Exception as e:
            errors.append(f"{ligand}: {e}")
            if st_callback:
                st_callback(f"❌ Error for {ligand}: {e}")

    if os.path.exists(sdf_temp):
        os.remove(sdf_temp)

    return errors

def process_receptor_from_input(receptor, ligands, output_root=RECEPTOR_DOWNLOAD_DIR, st_callback=None):
    receptor_folder = os.path.join(output_root, f"{receptor}_folder")
    
    if os.path.exists(receptor_folder):
        shutil.rmtree(receptor_folder)
    os.makedirs(receptor_folder)

    if st_callback:
        st_callback(f"📥 Downloading FASTA for {receptor}...")
    fasta_path, err = download_fasta_from_gene(receptor)
    if not fasta_path:
        return False, f"FASTA error: {err}"

    pdb_save_path = os.path.join(receptor_folder, f"{receptor}_model.pdb")
    success, err = upload_to_swiss_model(fasta_path, pdb_save_path, st_callback)
    if not success:
        return False, f"SwissModel error: {err}"

    errors = download_and_convert_ligands(ligands, receptor_folder, st_callback)
    return True, errors
