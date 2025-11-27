#!/usr/bin/env python3
"""
GoPhotonics Lead Scraper
Automates downloading and converting lead data from the GoPhotonics manufacturer panel.
"""

import os
import sys
import time
import re
from pathlib import Path
from typing import List

import pandas as pd  # type: ignore
from selenium import webdriver  # type: ignore
from selenium.webdriver.chrome.options import Options  # type: ignore
from selenium.webdriver.chrome.service import Service  # type: ignore
from selenium.webdriver.common.by import By  # type: ignore
from selenium.webdriver.support.ui import WebDriverWait  # type: ignore
from selenium.webdriver.support import expected_conditions as EC  # type: ignore
from webdriver_manager.chrome import ChromeDriverManager  # type: ignore

try:
    from dotenv import load_dotenv  # type: ignore
    ENV_PATH = Path(__file__).resolve().parent / ".env"
    if ENV_PATH.exists():
        load_dotenv(dotenv_path=ENV_PATH)
except ImportError:
    pass

EMAIL = os.environ.get("GOPHOTONICS_EMAIL")
PASSWORD = os.environ.get("GOPHOTONICS_PASSWORD")

if not EMAIL or not PASSWORD:
    sys.exit(
        "Error: GOPHOTONICS_EMAIL or GOPHOTONICS_PASSWORD is missing.\n"
        "Set them in a .env file or export them as environment variables."
    )

BASE_URL = "https://gophotonics.com/manufacturer/control-panel"
DOWNLOAD_DIR = Path(__file__).resolve().parent / "selenium_downloads"
DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)


def setup_driver(download_dir: Path) -> webdriver.Chrome:
    """Configure and return a Selenium Chrome driver with download options."""
    chrome_options = Options()
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")

    prefs = {
        "download.default_directory": str(download_dir),
        "download.prompt_for_download": False,
        "download.directory_upgrade": True,
        "safebrowsing.enabled": True,
    }
    chrome_options.add_experimental_option("prefs", prefs)

    driver_path = ChromeDriverManager().install()
    service = Service(driver_path)
    driver = webdriver.Chrome(service=service, options=chrome_options)
    return driver


def login(driver: webdriver.Chrome) -> None:
    """Navigate to the control panel."""
    print("  Navigating to manufacturer control panel...")
    driver.get(BASE_URL)
    time.sleep(3)
    print(f"  Current URL: {driver.current_url}")
    print(f"  Page title: {driver.title}")


def export_leads(driver: webdriver.Chrome, download_dir: Path, lead_pages: List[str]) -> None:
    """Navigate to Leads section and export all available lead types."""
    print("  Waiting for dashboard iframe...")
    try:
        iframe = WebDriverWait(driver, 30).until(
            EC.presence_of_element_located((By.ID, "myIframe"))
        )
        driver.switch_to.frame(iframe)
        print("  ✓ Switched to iframe")
        time.sleep(2)
    except Exception as e:
        print(f"  ✗ Could not find or switch to iframe: {e}")
        return

    try:
        iframe_email = driver.find_element(By.ID, "txtEMailId")
        print("  Iframe requires separate login...")
        iframe_password = driver.find_element(By.ID, "txtPassword")
        iframe_email.clear()
        iframe_email.send_keys(EMAIL)
        iframe_password.clear()
        iframe_password.send_keys(PASSWORD)
        
        login_btn = driver.find_element(By.ID, "lnkLogIn")
        login_btn.click()
        print("  ✓ Logged into iframe")
        time.sleep(8)
    except:
        time.sleep(3)

    try:
        print("  Waiting for menu to load...")
        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.CLASS_NAME, "sidebar-menu"))
        )
        time.sleep(2)
        
        print("  Navigating to Leads...")
        leads_link = WebDriverWait(driver, 20).until(
            EC.element_to_be_clickable((By.XPATH,
                "//a[contains(text(), 'Leads') and not(contains(@href, 'type='))] | "
                "//span[contains(text(), 'Leads') and not(ancestor::a[contains(@href, 'type=')])]/parent::a | "
                "//button[contains(., 'Leads')] | "
                "//*[contains(@class, 'menu') or contains(@class, 'nav')]//a[normalize-space(.)='Leads']"
            ))
        )
        driver.execute_script("arguments[0].click();", leads_link)
        time.sleep(3)
        print("  ✓ Opened Leads section")
        
        print("  Looking for lead type links...")
        lead_type_links = driver.find_elements(By.XPATH,
            "//a[contains(@href, 'leads?key=') and contains(@href, 'type=')]")
        
        if not lead_type_links:
            print("  ✗ No lead type links found")
            debug_file = Path(__file__).resolve().parent / "selenium_debug_leads_page.html"
            with open(debug_file, "w", encoding="utf-8") as f:
                f.write(driver.page_source)
            print(f"  Saved page source to {debug_file}")
            return
        
        lead_types = {}
        for link in lead_type_links:
            href = link.get_attribute("href")
            text = link.text.strip()
            if text and "type=" in href:
                type_match = re.search(r"type=([^&]+)", href)
                if type_match:
                    lead_type = type_match.group(1)
                    if lead_type not in lead_types:
                        lead_types[lead_type] = (text, href)
        
        print(f"  Found {len(lead_types)} lead type(s): {', '.join([v[0] for v in lead_types.values()])}")
        
        for lead_type, (display_name, href) in lead_types.items():
            try:
                print(f"\n  Processing {display_name}...")
                driver.get(href)
                time.sleep(3)
                
                try:
                    export_button = WebDriverWait(driver, 10).until(
                        EC.element_to_be_clickable((By.XPATH,
                            "//button[contains(., 'Export to Excel')] | "
                            "//a[contains(., 'Export to Excel')] | "
                            "//button[contains(., 'Export') and contains(., 'Excel')] | "
                            "//a[contains(., 'Export') and contains(., 'Excel')]"
                        ))
                    )
                except:
                    print(f"    ✗ No export button found for {display_name}")
                    continue
                
                before_files = set(download_dir.glob("*.xlsx"))
                export_button.click()
                print(f"    Clicked export, waiting for download...")
                time.sleep(2)
                
                timeout = 60
                start_time = time.time()
                new_file = None
                while time.time() - start_time < timeout:
                    after_files = set(download_dir.glob("*.xlsx"))
                    new_files = after_files - before_files
                    if new_files:
                        new_file = new_files.pop()
                        break
                    time.sleep(1)
                
                if not new_file:
                    print(f"    ✗ No file detected within timeout")
                else:
                    print(f"    ✓ Downloaded {new_file.name}")
                
                driver.back()
                time.sleep(2)
                    
            except Exception as e:
                print(f"    ✗ Error processing {display_name}: {e}")
                
    except Exception as e:
        print(f"  ✗ Error during navigation: {e}")
        debug_file = Path(__file__).resolve().parent / "selenium_debug_error.html"
        with open(debug_file, "w", encoding="utf-8") as f:
            f.write(driver.page_source)
        print(f"  Saved page source to {debug_file}")


def convert_downloads_to_csv(download_dir: Path) -> None:
    """Convert all Excel files in the download directory to CSV."""
    for xlsx_path in download_dir.glob("*.xlsx"):
        try:
            df = pd.read_excel(xlsx_path)
            csv_path = xlsx_path.with_suffix(".csv")
            df.to_csv(csv_path, index=False)
            print(f"  Converted {xlsx_path.name} -> {csv_path.name} ({len(df)} rows)")
        except Exception as exc:
            print(f"  Failed to convert {xlsx_path.name}: {exc}")


def main() -> None:
    driver = setup_driver(DOWNLOAD_DIR)
    try:
        print("Navigating to control panel…")
        login(driver)

        print("\nExporting leads...")
        export_leads(driver, DOWNLOAD_DIR, [])

        print("\nConverting downloads to CSV...")
        convert_downloads_to_csv(DOWNLOAD_DIR)
        
        print("\n✓ Done! Check the selenium_downloads folder for your files.")
    finally:
        driver.quit()


if __name__ == "__main__":
    main()
