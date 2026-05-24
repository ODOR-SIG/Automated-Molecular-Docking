import os
import time
import glob
import shutil
import pandas as pd
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from Automation_code.config import RECEPTOR_DOWNLOAD_DIR, CHROMEDRIVER

def assess_model(receptor, st_callback=None):
    def log(msg):
        if st_callback:
            st_callback(msg)
        else:
            print(msg)

    receptor_folder = os.path.join(RECEPTOR_DOWNLOAD_DIR, f"{receptor}_folder")
    pdb_file = os.path.join(receptor_folder, f"{receptor}_model.pdb")

    if not os.path.isfile(pdb_file):
        return False, f"❌ PDB file not found for {receptor}: {pdb_file}"

    if not os.path.exists(CHROMEDRIVER):
        return False, f"❌ chromedriver.exe not found at: {CHROMEDRIVER}"

    # Configure download folder and options
    chrome_options = Options()
    chrome_options.add_experimental_option("prefs", {
        "download.default_directory": receptor_folder,
        "download.prompt_for_download": False,
        "safebrowsing.enabled": True
    })

    # Start ChromeDriver
    driver = webdriver.Chrome(service=Service(CHROMEDRIVER), options=chrome_options)

    try:
        driver.get("https://swissmodel.expasy.org/")
        WebDriverWait(driver, 10).until(lambda d: d.execute_script("return document.readyState") == "complete")

        tools_dropdown = WebDriverWait(driver, 30).until(
            EC.element_to_be_clickable((By.XPATH, "//a[contains(@class, 'dropdown-toggle') and text()='Tools']"))
        )
        ActionChains(driver).move_to_element(tools_dropdown).click().perform()

        try:
            structure_assessment_link = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//a[@href='/assess']"))
            )
        except:
            structure_assessment_link = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//a[contains(text(), 'Structure Assessment')]"))
            )
        structure_assessment_link.click()

        file_input = WebDriverWait(driver, 30).until(
            EC.presence_of_element_located((By.XPATH, "//input[@type='file']"))
        )
        file_input.send_keys(os.path.abspath(pdb_file))
        log(f"📤 Uploaded: {receptor}_model.pdb")

        WebDriverWait(driver, 30).until(
            EC.presence_of_element_located((By.XPATH, f"//*[contains(text(), '{receptor}_model.pdb')]"))
        )

        # Select analysis options
        sequence_input = WebDriverWait(driver, 30).until(
            EC.presence_of_element_located((By.NAME, "sequenceSearch"))
        )
        molprobity_input = WebDriverWait(driver, 30).until(
            EC.presence_of_element_located((By.NAME, "molprobity"))
        )
        if not sequence_input.is_selected():
            driver.execute_script("arguments[0].click();", sequence_input)
        if not molprobity_input.is_selected():
            driver.execute_script("arguments[0].click();", molprobity_input)

        # Start validation
        start_button = WebDriverWait(driver, 30).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "button.css-110xwq5"))
        )
        driver.execute_script("arguments[0].click();", start_button)
        log("🧪 Running validation...")

        # Wait for download button
        download_btn = WebDriverWait(driver, 120).until(
            EC.element_to_be_clickable((By.XPATH, "//button[@title='Save as PNG']"))
        )
        download_btn.click()
        time.sleep(5)

        # Save plot
        validation_dir = os.path.join(receptor_folder, f"{receptor}_validation")
        os.makedirs(validation_dir, exist_ok=True)

        png_files = glob.glob(os.path.join(receptor_folder, "*.png"))
        if not png_files:
            return False, "❌ PNG not found after assessment."

        latest_png = max(png_files, key=os.path.getctime)
        shutil.move(latest_png, os.path.join(validation_dir, f"{receptor}_Ramachandran_plot.png"))
        log(f"🖼️ Plot saved to: {validation_dir}")

        # Save validation table
        molprobity_table = WebDriverWait(driver, 60).until(
            EC.presence_of_element_located((By.ID, "molprobityResults"))
        )
        soup = BeautifulSoup(molprobity_table.get_attribute("outerHTML"), "html.parser")

        validation_data = {"Metric": [], "Value": [], "Outliers": []}
        for row in soup.find_all("tr"):
            cells = row.find_all("td")
            if len(cells) >= 2:
                metric = cells[0].text.strip()
                value = cells[1].text.strip()
                outliers = ""
                if row.get("class") == ["outlierContainer"]:
                    outliers = cells[0].text.strip()
                validation_data["Metric"].append(metric)
                validation_data["Value"].append(value)
                validation_data["Outliers"].append(outliers)

        df = pd.DataFrame(validation_data)
        df.to_csv(os.path.join(validation_dir, f"{receptor}_Analysis.csv"), index=False)
        log(f"✅ Validation CSV saved to: {validation_dir}")
        return True, None

    except Exception as e:
        return False, str(e)

    finally:
        driver.quit()
