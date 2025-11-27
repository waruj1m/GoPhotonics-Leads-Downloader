#!/usr/bin/env python3
"""
GoPhotonics Leads Downloader
---------------------------

This script automates the retrieval of lead data from the GoPhotonics
manufacturer portal. GoPhotonics provides an "Export to Excel" link for
each type of lead (e.g. datasheet downloads, whitepaper downloads,
product quotations, contact inquiries). The export link looks like:

    https://mpanel.gophotonics.com/download?key=<unique-key>

Where `<unique-key>` is a long token specific to your account and the
lead type. You can obtain this key by visiting the relevant page in your
manufacturer control panel, clicking the chain icon next to the downloaded
file in Chrome's Downloads page, and copying the URL.

To use this script:

1. Replace the placeholder strings in the `LEAD_KEYS` dictionary with
   the actual keys for each lead type you wish to download.

2. Optionally add additional entries for other lead types (for example,
   product quotation or contact inquiry keys) if your account has them.

3. Set up a cron job to run this script at your desired frequency.
   For example, to run daily at 02:00, add a line like this to your
   crontab (edit with `crontab -e`):

       0 2 * * * /usr/bin/python3 /path/to/gophotonics_leads_downloader.py

The script downloads each Excel file, saves it to a local directory,
parses the leads into a pandas DataFrame, writes out a CSV version,
and prints a simple report showing how many leads were retrieved from
each source.

Note: this script uses the `requests` and `pandas` libraries. Install
them with `pip install requests pandas openpyxl` if they are not
already available in your environment.
"""
import datetime
import os
from pathlib import Path
from typing import Dict

import requests  # type: ignore
import pandas as pd  # type: ignore

# Directory to store downloaded Excel and CSV files.
DOWNLOAD_DIR = Path(__file__).resolve().parent / "leads_downloads"

# Mapping of lead type names to their corresponding download keys.
# Replace the placeholder strings with your real keys. You can add more
# types if you have additional export links (e.g. product quotations or
# contact inquiries).
LEAD_KEYS: Dict[str, str] = {
    # "datasheet": "YOUR_ACTUAL_DATASHEET_KEY",
    # "whitepaper": "YOUR_ACTUAL_WHITEPAPER_KEY",
    # "contact_inquiries": "YOUR_CONTACT_INQUIRIES_KEY",
    # "product_quotations": "YOUR_PRODUCT_QUOTATIONS_KEY",
}

def download_excel(url: str) -> bytes:
    """Download the Excel file from the given URL and return its content.

    Args:
        url: The full URL to download.

    Returns:
        The binary content of the downloaded file.

    Raises:
        requests.HTTPError: if the response is not successful.
    """
    resp = requests.get(url, timeout=30)
    resp.raise_for_status()
    return resp.content

def save_file(content: bytes, path: Path) -> None:
    """Write binary content to the given path, ensuring the parent directory exists."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "wb") as f:
        f.write(content)

def parse_and_save_csv(xlsx_path: Path) -> Path:
    """Parse an Excel file into a pandas DataFrame and save as CSV.

    Args:
        xlsx_path: Path to the Excel file.

    Returns:
        Path to the created CSV file.
    """
    df = pd.read_excel(xlsx_path)
    csv_path = xlsx_path.with_suffix(".csv")
    df.to_csv(csv_path, index=False)
    return csv_path

def main() -> None:
    if not LEAD_KEYS:
        print("No lead keys are configured. Please edit the LEAD_KEYS dictionary in the script.")
        return

    today = datetime.date.today().isoformat()
    summary = []  # Collect simple report information

    for lead_type, key in LEAD_KEYS.items():
        url = f"https://mpanel.gophotonics.com/download?key={key}"
        print(f"Retrieving {lead_type} leads from {url}…")

        try:
            content = download_excel(url)
        except requests.HTTPError as e:
            print(f"Failed to download {lead_type} leads: {e}")
            continue

        # Save the XLSX file with a date-coded name
        xlsx_name = f"{lead_type}_leads_{today}.xlsx"
        xlsx_path = DOWNLOAD_DIR / xlsx_name
        save_file(content, xlsx_path)
        print(f"Saved Excel to {xlsx_path}")

        # Parse and save CSV
        csv_path = parse_and_save_csv(xlsx_path)
        print(f"Converted to CSV at {csv_path}")

        # Read DataFrame to count rows for summary
        df = pd.read_csv(csv_path)
        summary.append((lead_type, len(df)))

    # Print a simple report
    print("\nDownload summary:")
    for lead_type, count in summary:
        print(f"  {lead_type}: {count} lead(s) saved")

if __name__ == "__main__":
    main()

