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

## Automation with Cron

### Daily at 9 AM

```bash
crontab -e
```

Add:
```
0 9 * * * cd /path/to/gophotonics && python3 gophotonics_leads_selenium.py >> /path/to/logs/gophotonics.log 2>&1
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
