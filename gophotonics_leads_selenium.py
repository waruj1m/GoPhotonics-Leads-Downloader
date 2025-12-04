#!/usr/bin/env python3
"""
GoPhotonics Lead Scraper with Master File Consolidation
Automates downloading lead data and consolidates into a single master file for CRM import.
"""

import os
import sys
import time
import re
import requests
from pathlib import Path
from typing import List
from datetime import datetime

import pandas as pd  # type: ignore
from selenium import webdriver  # type: ignore
from selenium.webdriver.chrome.options import Options  # type: ignore
from selenium.webdriver.chrome.service import Service  # type: ignore
from selenium.webdriver.common.by import By  # type: ignore
from selenium.webdriver.support.ui import WebDriverWait  # type: ignore
from selenium.webdriver.support import expected_conditions as EC  # type: ignore
from webdriver_manager.chrome import ChromeDriverManager  # type: ignore

try:
    import gspread  # type: ignore
    from google.oauth2.service_account import Credentials  # type: ignore
    GSPREAD_AVAILABLE = True
except ImportError:
    GSPREAD_AVAILABLE = False

try:
    from hubspot import HubSpot  # type: ignore
    from hubspot.crm.contacts import SimplePublicObjectInputForCreate, ApiException  # type: ignore
    HUBSPOT_AVAILABLE = True
except ImportError:
    HUBSPOT_AVAILABLE = False

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

MASTER_FILE = Path(__file__).resolve().parent / "gophotonics_master_leads.csv"


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


def consolidate_leads(download_dir: Path, master_file: Path) -> None:
    """
    Consolidate all lead CSVs into a single master file with deduplication.
    Tracks source (datasheet/whitepaper) and prevents duplicate entries.
    """
    print("\nConsolidating leads into master file...")
    
    # Load existing master file if it exists
    if master_file.exists():
        print(f"  Loading existing master file: {master_file.name}")
        master_df = pd.read_csv(master_file)
        initial_count = len(master_df)
        print(f"  Existing leads: {initial_count}")
    else:
        print("  Creating new master file...")
        master_df = pd.DataFrame()
        initial_count = 0
    
    # Process all CSV files
    csv_files = list(download_dir.glob("*.csv"))
    print(f"  Processing {len(csv_files)} CSV file(s)...")
    
    all_leads = []
    
    for csv_file in csv_files:
        try:
            # Determine source type from filename
            filename = csv_file.stem
            if "datasheet" in filename.lower() or "data_sheet" in filename.lower():
                source_type = "Datasheet"
            elif "whitepaper" in filename.lower():
                source_type = "Whitepaper"
            elif "quotation" in filename.lower():
                source_type = "Quotation"
            elif "inquiry" in filename.lower() or "contact" in filename.lower():
                source_type = "Contact Inquiry"
            else:
                source_type = "Other"
            
            df = pd.read_csv(csv_file)
            
            # Normalize column names and add source tracking
            normalized_data = []
            
            for _, row in df.iterrows():
                lead = {}
                
                # Helper function to safely extract and clean string values
                def safe_str(value):
                    if pd.isna(value) or value is None:
                        return ''
                    return str(value).strip()
                
                # Extract and normalize contact information
                lead['email'] = safe_str(row.get('User Email', row.get('email', '')))
                lead['name'] = safe_str(row.get('User Name', row.get('name', '')))
                lead['company'] = safe_str(row.get('User Company', row.get('company', '')))
                lead['phone'] = safe_str(row.get('User Telephone', row.get('telephone', row.get('phone', ''))))
                lead['country'] = safe_str(row.get('User Country', row.get('country', '')))
                lead['state'] = safe_str(row.get('User State', row.get('state', '')))
                lead['city'] = safe_str(row.get('User City', row.get('city', '')))
                lead['address'] = safe_str(row.get('User Address', row.get('address', '')))
                
                # Extract download/access date
                downloaded_on = row.get('Downloaded On', row.get('downloaded_on', ''))
                lead['date'] = safe_str(downloaded_on)
                
                # Extract resource information
                if 'Part Number' in row:
                    lead['resource'] = safe_str(row.get('Part Number', ''))
                elif 'White Paper Title' in row:
                    lead['resource'] = safe_str(row.get('White Paper Title', ''))
                elif 'Product Url' in row:
                    url = safe_str(row.get('Product Url', ''))
                    lead['resource'] = url.split('/')[-1] if url else ''
                else:
                    lead['resource'] = ''
                
                lead['source_type'] = source_type
                lead['source_file'] = csv_file.name
                lead['imported_at'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                
                # Only add if email exists
                if lead['email']:
                    normalized_data.append(lead)
            
            if normalized_data:
                all_leads.extend(normalized_data)
                print(f"    ✓ Processed {csv_file.name}: {len(normalized_data)} leads")
            
        except Exception as e:
            print(f"    ✗ Error processing {csv_file.name}: {e}")
    
    if not all_leads:
        print("  No new leads found in CSV files")
        return
    
    # Create DataFrame from new leads
    new_leads_df = pd.DataFrame(all_leads)
    
    # Combine with existing master
    if not master_df.empty:
        combined_df = pd.concat([master_df, new_leads_df], ignore_index=True)
    else:
        combined_df = new_leads_df
    
    # Deduplicate based on email + date + resource (same person downloading same thing on same day)
    # Keep the first occurrence
    print("  Deduplicating leads...")
    before_dedup = len(combined_df)
    combined_df = combined_df.drop_duplicates(subset=['email', 'date', 'resource'], keep='first')
    after_dedup = len(combined_df)
    duplicates_removed = before_dedup - after_dedup
    
    if duplicates_removed > 0:
        print(f"  Removed {duplicates_removed} duplicate(s)")
    
    # Sort by date (most recent first)
    combined_df['date_parsed'] = pd.to_datetime(combined_df['date'], errors='coerce')
    combined_df = combined_df.sort_values('date_parsed', ascending=False)
    combined_df = combined_df.drop('date_parsed', axis=1)
    
    # Save master file
    combined_df.to_csv(master_file, index=False)
    
    new_leads_count = len(combined_df) - initial_count
    print(f"\n  ✓ Master file updated: {master_file.name}")
    print(f"  Total leads: {len(combined_df)}")
    print(f"  New leads added: {new_leads_count}")
    
    # Create summary report
    print("\n  Lead Summary by Source Type:")
    for source_type in combined_df['source_type'].unique():
        count = len(combined_df[combined_df['source_type'] == source_type])
        print(f"    - {source_type}: {count} leads")


def sync_to_google_sheets(master_file: Path) -> None:
    """
    Sync master leads file to Google Sheets.
    Requires google-auth and gspread packages.
    """
    if not GSPREAD_AVAILABLE:
        print("\n⚠ Google Sheets sync not available")
        print("  Install with: pip install gspread google-auth")
        return
    
    # Check for credentials file
    creds_file = Path(__file__).resolve().parent / "google_credentials.json"
    if not creds_file.exists():
        print("\n⚠ Google Sheets sync skipped")
        print("  Create google_credentials.json to enable (see README)")
        return
    
    # Get sheet ID from environment or .env
    sheet_id = os.environ.get("GOOGLE_SHEET_ID")
    if not sheet_id:
        print("\n⚠ Google Sheets sync skipped")
        print("  Set GOOGLE_SHEET_ID in .env file (see README)")
        return
    
    try:
        print("\nSyncing to Google Sheets...")
        
        # Set up credentials
        scopes = [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive"
        ]
        creds = Credentials.from_service_account_file(str(creds_file), scopes=scopes)
        client = gspread.authorize(creds)
        
        # Open the sheet
        sheet = client.open_by_key(sheet_id)
        worksheet = sheet.get_worksheet(0)  # First sheet
        
        # Read master file
        df = pd.read_csv(master_file)
        
        # Replace NaN values with empty strings for JSON compatibility
        df = df.fillna('')
        
        # Clear existing data
        worksheet.clear()
        
        # Update with new data (including headers)
        data = [df.columns.tolist()] + df.values.tolist()
        # Use new API format: values first, then range
        worksheet.update(values=data, range_name='A1')
        
        # Format header row
        worksheet.format('A1:M1', {
            "backgroundColor": {"red": 0.2, "green": 0.2, "blue": 0.2},
            "textFormat": {"foregroundColor": {"red": 1, "green": 1, "blue": 1}, "bold": True}
        })
        
        # Freeze header row
        worksheet.freeze(rows=1)
        
        print(f"  ✓ Synced {len(df)} leads to Google Sheets")
        print(f"  📊 View at: https://docs.google.com/spreadsheets/d/{sheet_id}")
        
    except Exception as e:
        print(f"  ✗ Error syncing to Google Sheets: {e}")
        print("  💡 Check credentials and sheet permissions")


def add_contact_to_static_list(contact_id: str, list_id: str, access_token: str) -> bool:
    """
    Add a contact to a HubSpot static list using the v1 Lists API.
    Returns True if successful, False otherwise.
    """
    try:
        # Ensure contact_id is numeric
        contact_vid = int(contact_id)
        
        url = f"https://api.hubapi.com/contacts/v1/lists/{list_id}/add"
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
        payload = {"vids": [contact_vid]}
        
        response = requests.post(url, json=payload, headers=headers)
        
        if response.status_code in (200, 204):
            return True
        else:
            print(f"    ⚠ List add failed (HTTP {response.status_code}): {response.text}")
            return False
            
    except Exception as e:
        print(f"    ⚠ Error adding to list: {e}")
        return False


def sync_to_hubspot(master_file: Path) -> None:
    """
    Sync master leads file to HubSpot CRM.
    Creates or updates contacts and marks them with google_sheet_sync property.
    Requires hubspot-api-client package.
    """
    if not HUBSPOT_AVAILABLE:
        print("\n⚠ HubSpot sync not available")
        print("  Install with: pip install hubspot-api-client")
        return
    
    # Get HubSpot API key from environment
    hubspot_api_key = os.environ.get("HUBSPOT_API_KEY")
    if not hubspot_api_key:
        print("\n⚠ HubSpot sync skipped")
        print("  Set HUBSPOT_API_KEY in .env file")
        return
    
    # Get HubSpot list ID from environment
    hubspot_list_id = os.environ.get("HUBSPOT_LIST_ID")
    
    try:
        print("\nSyncing to HubSpot CRM...")
        
        # Initialize HubSpot client
        hubspot = HubSpot(access_token=hubspot_api_key)
        
        # Read master file
        df = pd.read_csv(master_file)
        
        # Replace NaN values with empty strings
        df = df.fillna('')
        
        success_count = 0
        update_count = 0
        create_count = 0
        error_count = 0
        list_add_count = 0
        
        print(f"  Processing {len(df)} contact(s)...")
        
        for idx, row in df.iterrows():
            email = str(row.get('email', '')).strip()
            if not email:
                continue
            
            try:
                # Prepare HubSpot properties
                name_parts = str(row.get('name', '')).strip().split()
                firstname = name_parts[0] if name_parts else ''
                lastname = ' '.join(name_parts[1:]) if len(name_parts) > 1 else ''
                
                # US states that HubSpot accepts
                us_states = {
                    'Alabama', 'Alaska', 'Arizona', 'Arkansas', 'California', 'Colorado',
                    'Connecticut', 'Delaware', 'Florida', 'Georgia', 'Hawaii', 'Idaho',
                    'Illinois', 'Indiana', 'Iowa', 'Kansas', 'Kentucky', 'Louisiana',
                    'Maine', 'Maryland', 'Massachusetts', 'Michigan', 'Minnesota',
                    'Mississippi', 'Missouri', 'Montana', 'Nebraska', 'Nevada',
                    'New Hampshire', 'New Jersey', 'New Mexico', 'New York',
                    'North Carolina', 'North Dakota', 'Ohio', 'Oklahoma', 'Oregon',
                    'Pennsylvania', 'Rhode Island', 'South Carolina', 'South Dakota',
                    'Tennessee', 'Texas', 'Utah', 'Vermont', 'Virginia', 'Washington',
                    'West Virginia', 'Wisconsin', 'Wyoming'
                }
                
                state_value = str(row.get('state', '')).strip()
                country_value = str(row.get('country', '')).strip()
                
                hubspot_props = {
                    'email': email,
                    'firstname': firstname,
                    'lastname': lastname,
                    'company': str(row.get('company', '')).strip(),
                    'phone': str(row.get('phone', '')).strip(),
                    'country': country_value,
                    'city': str(row.get('city', '')).strip(),
                    'address': str(row.get('address', '')).strip(),
                }
                
                # Handle state/region based on whether it's a US state or not
                if state_value:
                    if state_value in us_states:
                        # US state - use 'state' field
                        hubspot_props['state'] = state_value
                    else:
                        # Non-US region/province - use 'state_region' field
                        hubspot_props['state_region'] = state_value
                
                # Remove empty values
                hubspot_props = {k: v for k, v in hubspot_props.items() if v}
                
                # Check if contact exists
                try:
                    response = hubspot.crm.contacts.search_api.do_search(
                        public_object_search_request={
                            "filterGroups": [{
                                "filters": [{
                                    "propertyName": "email",
                                    "operator": "EQ",
                                    "value": email
                                }]
                            }],
                            "properties": ["email"],
                            "limit": 1
                        }
                    )
                    
                    if response.results:
                        # Update existing contact
                        contact_id = response.results[0].id
                        hubspot.crm.contacts.basic_api.update(
                            contact_id=contact_id,
                            simple_public_object_input={"properties": hubspot_props}
                        )
                        update_count += 1
                    else:
                        # Create new contact
                        created_contact = hubspot.crm.contacts.basic_api.create(
                            simple_public_object_input_for_create=SimplePublicObjectInputForCreate(
                                properties=hubspot_props
                            )
                        )
                        contact_id = created_contact.id
                        create_count += 1
                    
                    success_count += 1
                    
                    # Add contact to static list if list ID is configured
                    if hubspot_list_id:
                        if add_contact_to_static_list(contact_id, hubspot_list_id, hubspot_api_key):
                            list_add_count += 1
                    
                    # Progress indicator every 10 contacts
                    if (idx + 1) % 10 == 0:
                        print(f"    Processed {idx + 1}/{len(df)} contacts...")
                    
                except Exception as e:
                    error_count += 1
                    if "429" in str(e):  # Rate limit
                        print(f"    ⚠ Rate limit reached, waiting 10s...")
                        time.sleep(10)
                    
            except Exception as e:
                error_count += 1
                print(f"    ✗ Error processing {email}: {e}")
        
        print(f"\n  ✓ HubSpot sync completed")
        print(f"    Created: {create_count} | Updated: {update_count} | Errors: {error_count}")
        if hubspot_list_id:
            print(f"    Added to list: {list_add_count}")
            print(f"\n  💡 Contacts enrolled in HubSpot list ID {hubspot_list_id}")
        else:
            print(f"\n  💡 Note: Set HUBSPOT_LIST_ID in .env to add contacts to a static list")
        
    except Exception as e:
        print(f"  ✗ Error syncing to HubSpot: {e}")
        print("  💡 Check API key and HubSpot account permissions")


def cleanup_old_files(download_dir: Path, keep_days: int = 7) -> None:
    """Remove old downloaded files to save space (optional cleanup)."""
    cutoff_time = time.time() - (keep_days * 24 * 60 * 60)
    removed_count = 0
    
    for file_path in download_dir.glob("*"):
        if file_path.stat().st_mtime < cutoff_time:
            file_path.unlink()
            removed_count += 1
    
    if removed_count > 0:
        print(f"\n  Cleaned up {removed_count} old file(s) (>{keep_days} days)")


def main() -> None:
    driver = setup_driver(DOWNLOAD_DIR)
    try:
        print("Navigating to control panel…")
        login(driver)

        print("\nExporting leads...")
        export_leads(driver, DOWNLOAD_DIR, [])

        print("\nConverting downloads to CSV...")
        convert_downloads_to_csv(DOWNLOAD_DIR)
        
        print("\nConsolidating leads into master file...")
        consolidate_leads(DOWNLOAD_DIR, MASTER_FILE)
        
        # Sync to Google Sheets
        sync_to_google_sheets(MASTER_FILE)
        
        # Sync to HubSpot CRM
        sync_to_hubspot(MASTER_FILE)
        
        # Optional: cleanup old files
        # cleanup_old_files(DOWNLOAD_DIR, keep_days=7)
        
        print(f"\n✓ Done! Master file ready at: {MASTER_FILE.name}")
        
    finally:
        driver.quit()


if __name__ == "__main__":
    main()
