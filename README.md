# GoPhotonics Lead Scraper

Automated tool for downloading and converting lead data from the GoPhotonics manufacturer control panel.

## Overview

This script automates the process of:
1. Logging into the GoPhotonics manufacturer panel
2. Navigating to the Leads section
3. Exporting all available lead types (Datasheet Downloads, Whitepaper Downloads, Product Quotations, Contact Inquiries)
4. Downloading Excel files
5. Converting them to CSV format

## Why Selenium?

The GoPhotonics control panel uses a complex architecture that requires browser automation:

- **Single Page Application (SPA)**: Content is loaded dynamically via JavaScript
- **Nested iframe**: The dashboard loads in an iframe from `mpanel.gophotonics.com` that requires separate authentication
- **Dynamic download keys**: Export buttons trigger JavaScript actions that generate unique, session-based download URLs
- **No public API**: No documented API for programmatic access

Simple HTTP requests cannot handle these requirements, making Selenium the right choice.

## Prerequisites

### System Requirements
- Python 3.7+
- Google Chrome or Chromium browser
- macOS, Linux, or Windows

### Python Dependencies
```bash
pip install selenium webdriver-manager pandas openpyxl python-dotenv
```

## Installation

1. **Clone or download this repository**

2. **Install dependencies:**
   ```bash
   pip install selenium webdriver-manager pandas openpyxl python-dotenv
   ```

3. **Set up credentials:**

   Create a `.env` file in the script directory:
   ```
   GOPHOTONICS_EMAIL=your.email@example.com
   GOPHOTONICS_PASSWORD=your_password
   ```

   Alternatively, export as environment variables:
   ```bash
   export GOPHOTONICS_EMAIL="your.email@example.com"
   export GOPHOTONICS_PASSWORD="your_password"
   ```

## Usage

### Basic Usage

Run the script:
```bash
python3 gophotonics_leads_selenium.py
```

The script will:
- Open a Chrome browser window (you can minimize it)
- Navigate to the control panel
- Log in automatically
- Export all available lead types
- Download Excel files to `selenium_downloads/`
- Convert Excel files to CSV

### Output

Downloaded files are saved to `selenium_downloads/`:
- `*.xlsx` - Original Excel files from GoPhotonics
- `*.csv` - Converted CSV files

Example output:
```
selenium_downloads/
├── lambda_research_corporation_data_sheet_leads.xlsx
├── lambda_research_corporation_data_sheet_leads.csv
├── lambda_research_corporation_whitepaper_downloads_leads.xlsx
└── lambda_research_corporation_whitepaper_downloads_leads.csv
```

## How It Works

### Architecture Overview

The GoPhotonics control panel has a unique architecture:

1. **Main page** (`gophotonics.com/manufacturer/control-panel`) - Entry point
2. **Dashboard iframe** (`mpanel.gophotonics.com`) - Contains actual dashboard, requires separate login
3. **Lead pages** - Individual pages for each lead type with export buttons

### Script Flow

```
1. Navigate to control panel URL
   └─> Loads page with iframe

2. Switch to iframe context
   └─> Access dashboard content

3. Login to iframe
   └─> Separate authentication required
   └─> Wait for dashboard to load

4. Navigate to Leads menu
   └─> Click "Leads" in sidebar menu

5. Find all lead type links
   └─> Datasheet Downloads
   └─> Whitepaper Downloads
   └─> Product Quotations
   └─> Contact Inquiries

6. For each lead type:
   └─> Navigate to lead type page
   └─> Find "Export to Excel" button
   └─> Click and wait for download
   └─> Return to Leads main page

7. Convert all Excel files to CSV
```

### Technical Details

**Iframe Handling:**
```python
# Wait for iframe and switch context
iframe = WebDriverWait(driver, 30).until(
    EC.presence_of_element_located((By.ID, "myIframe"))
)
driver.switch_to.frame(iframe)
```

**Separate iframe login:**
```python
# The iframe has its own login form
iframe_email = driver.find_element(By.ID, "txtEMailId")
iframe_password = driver.find_element(By.ID, "txtPassword")
# Fill credentials and submit
```

**Download detection:**
```python
# Track files before export
before_files = set(download_dir.glob("*.xlsx"))
export_button.click()
# Wait for new file to appear
while time.time() - start_time < timeout:
    after_files = set(download_dir.glob("*.xlsx"))
    new_files = after_files - before_files
    if new_files:
        # Download complete
        break
```

## Configuration

### Headless Mode

By default, the script runs with a visible browser window. The GoPhotonics SPA has compatibility issues with headless mode, but you can try enabling it:

In `gophotonics_leads_selenium.py`, uncomment line 120:
```python
chrome_options.add_argument("--headless=new")
```

### Download Directory

Change the download location by modifying:
```python
DOWNLOAD_DIR = Path(__file__).resolve().parent / "selenium_downloads"
```

### Timeouts

Adjust wait times if your connection is slow:
```python
# Iframe login wait (line 100)
time.sleep(8)  # Increase if dashboard doesn't load

# Export wait timeout (line 173)
timeout = 60  # Increase if downloads are slow
```

## Troubleshooting

### Script fails at login
- Verify credentials in `.env` file
- Check that you have active GoPhotonics manufacturer access
- Look for error messages in console output

### No export buttons found
- Some lead types may not have export functionality if there are no leads
- Check saved debug file: `selenium_debug_leads_page.html`
- Verify your account has permission to export leads

### Downloads timeout
- Increase timeout value (default: 60 seconds)
- Check your internet connection
- Verify Chrome can access the download directory

### Iframe login fails
- Increase wait time after iframe login (default: 8 seconds)
- Check if GoPhotonics updated their login form

### Debug files
The script saves HTML snapshots when errors occur:
- `selenium_debug_error.html` - Saved when navigation fails
- `selenium_debug_leads_page.html` - Saved when export buttons not found

## Automation

### Schedule with Cron (Linux/macOS)

Run daily at 9 AM:
```bash
crontab -e
```

Add:
```
0 9 * * * cd /path/to/gophotonics && python3 gophotonics_leads_selenium.py >> /path/to/logs/gophotonics.log 2>&1
```

### Schedule with Task Scheduler (Windows)

1. Open Task Scheduler
2. Create Basic Task
3. Set trigger (daily/weekly)
4. Action: Start a program
   - Program: `python`
   - Arguments: `gophotonics_leads_selenium.py`
   - Start in: `C:\path\to\gophotonics`

### Using a wrapper script

Create `run_scraper.sh`:
```bash
#!/bin/bash
cd /path/to/gophotonics
source .venv/bin/activate  # if using virtual environment
python3 gophotonics_leads_selenium.py
```

Make executable and schedule:
```bash
chmod +x run_scraper.sh
```

## Project Structure

```
gophotonics/
├── .env                                    # Credentials (not in git)
├── gophotonics_leads_selenium.py           # Main script
├── README.md                               # This file
├── selenium_downloads/                     # Downloaded files
│   ├── *.xlsx                             # Excel files
│   └── *.csv                              # Converted CSV files
└── selenium_debug_*.html                   # Debug files (when errors occur)
```

## Dependencies Explained

- **selenium**: Browser automation framework
- **webdriver-manager**: Automatic ChromeDriver installation and management
- **pandas**: Excel to CSV conversion and data manipulation
- **openpyxl**: Excel file reading support for pandas
- **python-dotenv**: Load credentials from `.env` file (optional)

## Security Notes

- **Never commit `.env` file** to version control (add to `.gitignore`)
- **Credentials** are only stored locally and sent directly to GoPhotonics
- **No data is sent to third parties**
- Script runs entirely on your machine

## Limitations

- **Visible browser required**: Headless mode has compatibility issues with the GoPhotonics SPA
- **Chrome only**: Script is designed for Chrome/Chromium (can be adapted for other browsers)
- **Session-based**: Each run creates a new session; doesn't maintain persistent login
- **Export availability**: Only lead types with export buttons can be downloaded

## Contributing

Feel free to submit issues or pull requests if you encounter problems or have improvements.

## License

This project is provided as-is for personal/commercial use. Respect GoPhotonics' terms of service when using this tool.

## FAQ

**Q: Can I run this in Docker?**  
A: Yes, but you'll need a Docker image with Chrome and X11 support. The visible browser requirement makes Docker more complex.

**Q: Can I export specific lead types only?**  
A: Yes, modify the script to skip certain lead types in the `export_leads()` function.

**Q: How often should I run this?**  
A: Depends on your needs. Daily is common for active manufacturers.

**Q: Does this violate GoPhotonics terms of service?**  
A: This tool automates manual tasks you could perform in the browser. Always review and comply with GoPhotonics' terms of service.

**Q: Can I use this with multiple accounts?**  
A: Yes, create separate `.env` files or pass different credentials via environment variables.

## Support

For issues specific to:
- **This script**: Open a GitHub issue
- **GoPhotonics platform**: Contact GoPhotonics support
- **Selenium**: See [Selenium documentation](https://www.selenium.dev/documentation/)

## Changelog

### Version 1.0.0 (2025-11-27)
- Initial release
- Support for all lead types
- Automatic Excel to CSV conversion
- Iframe authentication handling
- Error debugging with HTML snapshots
