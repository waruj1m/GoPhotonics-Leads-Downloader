#!/usr/bin/env python3
"""Debug script to save control panel HTML and inspect download links."""
import os
import sys
from pathlib import Path

import requests
from bs4 import BeautifulSoup

try:
    from dotenv import load_dotenv
    ENV_PATH = Path(__file__).resolve().parent / ".env"
    if ENV_PATH.exists():
        load_dotenv(dotenv_path=ENV_PATH)
except ImportError:
    pass

BASE_URL = "https://gophotonics.com"
MANUFACTURER_PANEL_URL = "https://gophotonics.com/manufacturer/control-panel"

EMAIL = os.environ.get("GOPHOTONICS_EMAIL")
PASSWORD = os.environ.get("GOPHOTONICS_PASSWORD")

if not EMAIL or not PASSWORD:
    sys.exit("Error: Missing credentials")

with requests.Session() as session:
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
    })
    
    # Login
    signin_url = f"{BASE_URL}/users/signin"
    resp = session.get(signin_url, timeout=30)
    soup = BeautifulSoup(resp.text, "html.parser")
    
    payload = {"email": EMAIL, "password": PASSWORD}
    for hidden in soup.select("form input[type=hidden]"):
        name = hidden.get("name")
        value = hidden.get("value", "")
        if name and name not in payload:
            payload[name] = value
    
    session.post(signin_url, data=payload, timeout=30, allow_redirects=True)
    
    # Get control panel
    panel_resp = session.get(MANUFACTURER_PANEL_URL, timeout=30)
    
    # Save HTML
    output_file = Path(__file__).resolve().parent / "control_panel.html"
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(panel_resp.text)
    
    print(f"Saved control panel HTML to: {output_file}")
    
    # Look for links with "key" or "download" or "export" or "leads"
    soup = BeautifulSoup(panel_resp.text, "html.parser")
    print("\nSearching for relevant links...")
    
    for a in soup.find_all("a", href=True):
        href = a["href"]
        text = a.get_text(strip=True)
        if any(keyword in href.lower() for keyword in ["key=", "download", "export", "leads"]):
            print(f"  {text[:50]:50} -> {href[:100]}")
    
    print("\nSearching for buttons with 'export' or 'download'...")
    for btn in soup.find_all(["button", "a"], class_=True):
        text = btn.get_text(strip=True).lower()
        if "export" in text or "download" in text:
            print(f"  Button/Link: {btn.get_text(strip=True)}")
            print(f"    Classes: {btn.get('class')}")
            print(f"    onclick: {btn.get('onclick', 'N/A')}")
            print()
