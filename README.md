# GoPhotonics Lead Scraper

Automated tool for downloading and consolidating lead data from the GoPhotonics manufacturer control panel into a single master file for CRM import.

## Overview

This script automates the complete lead management workflow:
1. Logs into the GoPhotonics manufacturer panel
2. Navigates to the Leads section
3. Exports all available lead types (Datasheet Downloads, Whitepaper Downloads, Product Quotations, Contact Inquiries)
4. Downloads Excel files
5. Converts to CSV format
6. **Consolidates all leads into a single master file** (`gophotonics_master_leads.csv`)
7. **Deduplicates entries** to prevent importing the same lead multiple times
8. **Tracks lead source** (which datasheet/whitepaper was downloaded)
9. **Appends new leads only** - safe to run repeatedly via cron

## New Features ✨

### Master File Consolidation
- All leads are automatically consolidated into `gophotonics_master_leads.csv`
- Includes contact information (email, name, company, phone, location)
- Tracks what content was downloaded (`resource` field)
- Records source type (Datasheet, Whitepaper, Quotation, Contact Inquiry)
- Timestamp when imported

### Google Sheets Integration 🆕
- **Automatic cloud sync** to Google Sheets
- Accessible from anywhere, on any device
- Real-time collaboration with team
- Formatted headers and frozen rows
- Secure service account authentication
- **[Setup Guide](GOOGLE_SHEETS_SETUP.md)** (10 minutes)

### Intelligent Deduplication
- Prevents duplicate entries based on: email + date + resource
- Same person downloading the same content on the same day = one entry
- Different content or different days = separate entries (useful for tracking engagement)

### Cron-Safe Operation
- Appends new leads to existing master file
- Doesn't overwrite or lose historical data
- Can be run daily/weekly without issues

## Master File Format

The consolidated file includes these columns:
- `email` - Contact email (primary identifier)
- `name` - Contact name
- `company` - Company name
- `phone` - Phone number
- `country`, `state`, `city`, `address` - Location information
- `date` - When they downloaded/accessed the content
- `resource` - What they downloaded (e.g., "TracePro", "Accuracy in Optical Design Software")
- `source_type` - Type of lead (Datasheet, Whitepaper, Quotation, Contact Inquiry)
- `source_file` - Original filename (for debugging)
- `imported_at` - When this entry was added to master file

## Prerequisites

### System Requirements
- Python 3.7+
- Google Chrome or Chromium browser
- macOS, Linux, or Windows

### Python Dependencies
```bash
pip install -r requirements.txt
```

## Installation

1. **Clone or download this repository**

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up credentials:**

   Create a `.env` file:
   ```
   GOPHOTONICS_EMAIL=your.email@example.com
   GOPHOTONICS_PASSWORD=your_password
   ```

## Usage

### Basic Usage

Run the script:
```bash
python3 gophotonics_leads_selenium.py
```

The script will:
- Open Chrome browser
- Log in and export all leads
- Consolidate into `gophotonics_master_leads.csv`
- **Sync to Google Sheets** (if configured)

### Google Sheets Setup (Optional but Recommended)

For cloud access and team collaboration:

1. **Install packages:**
   ```bash
   pip install gspread google-auth
   ```

2. **Follow the setup guide:** [GOOGLE_SHEETS_SETUP.md](GOOGLE_SHEETS_SETUP.md)

3. **Add to `.env`:**
   ```
   GOOGLE_SHEET_ID=your_sheet_id_here
   ```

4. **Run script** - leads automatically sync to Google Sheets!

### Output Files

**Master File (Primary Output):**
- `gophotonics_master_leads.csv` - Single file ready for CRM import

**Individual Downloads (in `selenium_downloads/`):**
- `*.xlsx` and `*.csv` - Individual export files

### For CRM Import

1. Run script (manually or via cron)
2. Import `gophotonics_master_leads.csv` into your CRM
3. Map fields: `email`, `name`, `company`, etc.
4. Use `source_type` and `resource` for marketing segmentation

## Automation

### macOS LaunchAgent (Recommended for Mac)

Run automatically every 24 hours at 11 AM and on system reboot:

1. **The LaunchAgent plist should already be created at:**
   ```
   ~/Library/LaunchAgents/com.gophotonics.leads.plist
   ```

2. **If not, create it with this content:**
   ```xml
   <?xml version="1.0" encoding="UTF-8"?>
   <!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
   <plist version="1.0">
   <dict>
       <key>Label</key>
       <string>com.gophotonics.leads</string>
       
       <key>ProgramArguments</key>
       <array>
           <string>/path/to/gophotonics/.venv/bin/python</string>
           <string>/path/to/gophotonics/gophotonics_leads_selenium.py</string>
       </array>
       
       <key>WorkingDirectory</key>
       <string>/path/to/gophotonics</string>
       
       <key>StartCalendarInterval</key>
       <dict>
           <key>Hour</key>
           <integer>11</integer>
           <key>Minute</key>
           <integer>0</integer>
       </dict>
       
       <key>StandardOutPath</key>
       <string>/path/to/gophotonics/logs/gophotonics_leads.log</string>
       
       <key>StandardErrorPath</key>
       <string>/path/to/gophotonics/logs/gophotonics_leads.error.log</string>
       
       <key>EnvironmentVariables</key>
       <dict>
           <key>PATH</key>
           <string>/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin</string>
           <key>GOPHOTONICS_EMAIL</key>
           <string>your.email@example.com</string>
           <key>GOPHOTONICS_PASSWORD</key>
           <string>your_password</string>
           <!-- Add other env vars from .env file -->
       </dict>
       
       <key>RunAtLoad</key>
       <false/>
       
       <key>KeepAlive</key>
       <false/>
   </dict>
   </plist>
   ```

3. **Load the service:**
   ```bash
   launchctl load ~/Library/LaunchAgents/com.gophotonics.leads.plist
   ```

4. **Useful commands:**
   ```bash
   # Check service status
   launchctl list | grep gophotonics
   
   # View detailed status
   launchctl list com.gophotonics.leads
   
   # Manually trigger now (for testing)
   launchctl start com.gophotonics.leads
   
   # View logs
   tail -f logs/gophotonics_leads.log
   tail -f logs/gophotonics_leads.error.log
   
   # Stop service
   launchctl stop com.gophotonics.leads
   
   # Disable completely
   launchctl unload ~/Library/LaunchAgents/com.gophotonics.leads.plist
   
   # Reload after making changes
   launchctl unload ~/Library/LaunchAgents/com.gophotonics.leads.plist
   launchctl load ~/Library/LaunchAgents/com.gophotonics.leads.plist
   ```

**Important Notes:**
- Uses your virtual environment's Python (`.venv/bin/python`)
- All environment variables from `.env` must be added to the plist
- Service persists across reboots
- Logs are stored in `logs/` directory

### Linux/Unix Cron (Alternative)

**Daily at 9 AM:**

```bash
crontab -e
```

Add:
```
0 9 * * * cd /path/to/gophotonics && /path/to/gophotonics/.venv/bin/python gophotonics_leads_selenium.py >> /path/to/logs/gophotonics.log 2>&1
```

The script safely appends new leads without losing historical data.

## How It Works

1. Logs into GoPhotonics control panel
2. Switches to dashboard iframe
3. Navigates to Leads section
4. Exports each lead type (Datasheets, Whitepapers, etc.)
5. Converts Excel files to CSV
6. Consolidates all CSVs into single master file:
   - Normalizes column names
   - Tracks source type and resource
   - Deduplicates (email + date + resource)
   - Sorts by date (newest first)
   - Appends to existing master file

## Deduplication Logic

Duplicates are removed based on three fields:
- **Email**: Same person
- **Date**: Same day
- **Resource**: Same content

**Examples:**
- ✅ Keeps both: Person downloads TracePro on Nov 15 AND Nov 20
- ❌ Removes duplicate: Person downloads TracePro twice on Nov 15
- ✅ Keeps both: Person downloads TracePro AND Whitepaper on Nov 15

This tracks engagement while preventing noise from re-exports.

## Configuration

### Master File Location

Edit in script:
```python
MASTER_FILE = Path(__file__).resolve().parent / "gophotonics_master_leads.csv"
```

### Optional File Cleanup

Uncomment to auto-delete old downloads:
```python
cleanup_old_files(DOWNLOAD_DIR, keep_days=7)
```

## Troubleshooting

### No new leads added
- Normal if no new leads since last run
- Check "New leads added: 0" in output

### Duplicates in master file
- Only duplicate if same email + date + resource
- Different dates/resources are intentional (tracks engagement)

### CSV import issues
- File is UTF-8 encoded
- Compatible with Excel, Google Sheets, most CRMs

## Project Structure

```
gophotonics/
├── .env                              # Credentials
├── gophotonics_leads_selenium.py     # Main script
├── gophotonics_master_leads.csv      # Master file ← Import this
├── requirements.txt                  # Dependencies
└── selenium_downloads/               # Individual exports
```

## Security

- `.env` and master file excluded from git
- Credentials only sent to GoPhotonics
- No third-party data sharing
- Runs entirely on your machine

## Changelog

### Version 2.0.0 (2025-11-27)
- ✨ Master file consolidation
- ✨ Automatic deduplication
- ✨ Source tracking
- ✨ Cron-safe appending

### Version 1.0.0 (2025-11-27)
- Initial release

## License

MIT License - free for personal/commercial use.
