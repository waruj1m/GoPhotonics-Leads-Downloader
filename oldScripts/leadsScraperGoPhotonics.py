#!/usr/bin/env python3
"""
GoPhotonics Lead Scraper (Web Scraping Version)
----------------------------------------------

This script demonstrates how you could log into the GoPhotonics website
programmatically, navigate to the manufacturer control panel and scrape the
leads export links without manually copying them from the browser.  It then
downloads the Excel files for each lead type and converts them to CSV.

**IMPORTANT**: This example uses the Python `requests` and `beautifulsoup4`
libraries to perform the login and scraping.  Because GoPhotonics may
implement anti‑scraping measures (such as CSRF tokens, login rate limits
or CAPTCHA), this script may require adjustments to work against the live
site.  It is provided as a starting point.  You should respect the site's
Terms of Service and robots.txt and use this script responsibly.

To use this script:

1. Install dependencies if needed:

       pip install requests beautifulsoup4 pandas openpyxl

2. Set your GoPhotonics credentials in environment variables before running:

       export GOPHOTONICS_EMAIL="your.email@example.com"
       export GOPHOTONICS_PASSWORD="your_password"

3. Run the script.  It will attempt to log in, locate lead export links,
   download the Excel files and write CSVs to the `leads_downloads` folder.

Note: If GoPhotonics uses additional hidden form fields (e.g. CSRF tokens),
you'll need to adjust the login payload accordingly.  You can inspect the
login form HTML manually to identify required fields.
"""
import datetime
import os
import re
from pathlib import Path
from typing import Dict, List, Tuple

import requests  # type: ignore
from bs4 import BeautifulSoup  # type: ignore
import pandas as pd  # type: ignore

# Base URLs used by GoPhotonics
BASE_URL = "https://gophotonics.com"
MANUFACTURER_PANEL_URL = "https://gophotonics.com/manufacturer/control-panel"

# Directory to store downloaded files
DOWNLOAD_DIR = Path(__file__).resolve().parent / "leads_downloads"

# Login credentials from environment variables
EMAIL = os.environ.get("GOPHOTONICS_EMAIL")
PASSWORD = os.environ.get("GOPHOTONICS_PASSWORD")

if not EMAIL or not PASSWORD:
    raise RuntimeError(
        "Missing credentials. Please set GOPHOTONICS_EMAIL and GOPHOTONICS_PASSWORD environment variables."
    )

def login(session: requests.Session) -> None:
    """Perform login and populate the session's cookies.

    Raises:
        Exception if login fails.
    """
    # Step 1: GET the sign‑in page to grab any necessary tokens
    signin_url = f"{BASE_URL}/users/signin"
    resp = session.get(signin_url, timeout=30)
    resp.raise_for_status()

    soup = BeautifulSoup(resp.text, "html.parser")

    # Prepare login payload.  You may need to update field names depending on
    # the actual HTML.  Inspect the login form for accurate names.
    payload = {
        "email": EMAIL,
        "password": PASSWORD,
    }

    # If there are hidden inputs (e.g. CSRF tokens), include them
    for hidden in soup.select("form input[type=hidden]"):
        name = hidden.get("name")
        value = hidden.get("value", "")
        if name and name not in payload:
            payload[name] = value

    # Submit POST to the same sign‑in URL.  Adjust `data` keys if necessary.
    post_resp = session.post(signin_url, data=payload, timeout=30)
    post_resp.raise_for_status()

    # Check if login was successful by looking for the control panel link
    if "manufacturer/control-panel" not in post_resp.text:
        # Some sites redirect after login, follow redirects
        # Try accessing the control panel directly
        panel_check = session.get(MANUFACTURER_PANEL_URL, allow_redirects=True, timeout=30)
        if panel_check.status_code != 200:
            raise Exception("Login failed or control panel inaccessible.")


def scrape_lead_links(session: requests.Session) -> Dict[str, str]:
    """Scrape the manufacturer control panel for lead export links.

    Returns:
        Dictionary mapping lead type to download key.
    """
    resp = session.get(MANUFACTURER_PANEL_URL, timeout=30)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")

    lead_links: Dict[str, str] = {}

    # Look for anchor tags containing /leads?key=... and type=...
    for a in soup.find_all("a", href=True):
        href = a["href"]
        if "/leads?key=" in href:
            # Extract key and type from the query string
            # Example: /leads?key=ABC123&type=Datasheet_Downloads
            match_key = re.search(r"key=([^&]+)", href)
            match_type = re.search(r"type=([^&]+)", href)
            if match_key and match_type:
                key = match_key.group(1)
                lead_type = match_type.group(1)
                lead_links[lead_type] = key
    return lead_links

def download_and_convert(session: requests.Session, lead_links: Dict[str, str]) -> List[Tuple[str, int]]:
    """Download Excel files for each lead type and convert them to CSV.

    Returns:
        A list of tuples containing (lead_type, number_of_rows).
    """
    results: List[Tuple[str, int]] = []
    today = datetime.date.today().isoformat()

    for lead_type, key in lead_links.items():
        url = f"https://mpanel.gophotonics.com/download?key={key}"
        print(f"Fetching {lead_type} leads from {url}")
        resp = session.get(url, timeout=60)
        if resp.status_code != 200:
            print(f"  Failed to download {lead_type} leads (status {resp.status_code})")
            continue

        # Save to XLSX
        xlsx_name = f"{lead_type}_leads_{today}.xlsx"
        xlsx_path = DOWNLOAD_DIR / xlsx_name
        xlsx_path.parent.mkdir(parents=True, exist_ok=True)
        with open(xlsx_path, "wb") as f:
            f.write(resp.content)

        # Convert to CSV
        df = pd.read_excel(xlsx_path)
        csv_path = xlsx_path.with_suffix(".csv")
        df.to_csv(csv_path, index=False)
        print(f"  Saved {len(df)} rows to {csv_path}")
        results.append((lead_type, len(df)))
    return results

def main() -> None:
    with requests.Session() as session:
        # Set a basic User‑Agent to look more like a browser
        session.headers.update({"User-Agent": "Mozilla/5.0 (compatible; GoPhotonicsScraper/1.0)"})

        print("Logging in to GoPhotonics…")
        login(session)
        print("Login successful.")

        print("Scraping lead export links…")
        lead_links = scrape_lead_links(session)
        if not lead_links:
            print("No lead links found. You may need to adjust the scraping logic.")
            return

        print(f"Found {len(lead_links)} lead type(s): {', '.join(lead_links.keys())}")

        summary = download_and_convert(session, lead_links)

        print("\nSummary:")
        for lead_type, count in summary:
            print(f"  {lead_type}: {count} leads downloaded")

if __name__ == "__main__":
    main()

