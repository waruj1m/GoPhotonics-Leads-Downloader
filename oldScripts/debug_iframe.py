#!/usr/bin/env python3
"""Debug script to access iframe content directly."""
import os
import re
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
    
    # Get control panel to extract iframe URL
    panel_resp = session.get(MANUFACTURER_PANEL_URL, timeout=30)
    soup = BeautifulSoup(panel_resp.text, "html.parser")
    
    iframe = soup.find("iframe", id="myIframe")
    if not iframe:
        print("Error: Could not find iframe")
        sys.exit(1)
    
    iframe_url = iframe.get("src")
    print(f"Found iframe URL: {iframe_url}")
    
    # Extract the key from iframe URL
    key_match = re.search(r"key=([^&]+)", iframe_url)
    if key_match:
        dashboard_key = key_match.group(1)
        print(f"Dashboard key: {dashboard_key}")
    
    # Try accessing the iframe directly
    print("\nAccessing iframe content...")
    iframe_resp = session.get(iframe_url, timeout=30)
    print(f"Status: {iframe_resp.status_code}")
    
    # Save iframe HTML
    output_file = Path(__file__).resolve().parent / "iframe_dashboard.html"
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(iframe_resp.text)
    print(f"Saved iframe HTML to: {output_file}")
    
    # Look for download links in iframe
    iframe_soup = BeautifulSoup(iframe_resp.text, "html.parser")
    
    print("\nSearching iframe for download/export links...")
    for a in iframe_soup.find_all("a", href=True):
        href = a["href"]
        text = a.get_text(strip=True)
        if any(keyword in href.lower() for keyword in ["key=", "download", "export", "leads"]):
            print(f"  {text[:50]:50} -> {href}")
    
    print("\nSearching iframe for buttons...")
    for btn in iframe_soup.find_all(["button", "a"]):
        text = btn.get_text(strip=True).lower()
        if any(keyword in text for keyword in ["export", "download", "datasheet", "whitepaper", "quotation", "inquiry"]):
            print(f"  Button: {btn.get_text(strip=True)[:60]}")
            print(f"    Tag: {btn.name}")
            print(f"    onclick: {btn.get('onclick', 'N/A')[:100]}")
            print(f"    href: {btn.get('href', 'N/A')[:100]}")
            print()
