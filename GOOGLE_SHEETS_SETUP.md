# Google Sheets Integration Setup

This guide walks you through setting up automatic sync to Google Sheets for your GoPhotonics leads.

## Overview

The script will automatically:
- Create/update a Google Sheet with all your leads
- Format headers with dark background
- Freeze the header row
- Provide a direct link to view the sheet

## Prerequisites

- Google Account
- Google Cloud Project (free)
- 10 minutes for setup

## Step 1: Install Required Packages

```bash
pip install gspread google-auth
```

Or use the updated requirements:
```bash
pip install -r requirements.txt
```

## Step 2: Create Google Cloud Project

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Click **"Create Project"** or select existing project
3. Name it something like "GoPhotonics Leads"
4. Click **"Create"**

## Step 3: Enable Google Sheets API

1. In Google Cloud Console, go to **"APIs & Services" → "Library"**
2. Search for **"Google Sheets API"**
3. Click on it and press **"Enable"**
4. Also search for and enable **"Google Drive API"**

## Step 4: Create Service Account

1. Go to **"APIs & Services" → "Credentials"**
2. Click **"Create Credentials" → "Service Account"**
3. Fill in:
   - **Service account name**: `gophotonics-leads-sync`
   - **Service account ID**: (auto-generated)
   - **Description**: `Syncs GoPhotonics leads to Google Sheets`
4. Click **"Create and Continue"**
5. **Role**: Select **"Editor"** (or just **"Basic → Editor"**)
6. Click **"Continue"** then **"Done"**

## Step 5: Create Service Account Key

1. In **"Credentials"**, find your service account in the list
2. Click on the service account email
3. Go to **"Keys"** tab
4. Click **"Add Key" → "Create new key"**
5. Choose **JSON** format
6. Click **"Create"**
7. A JSON file will download - this is your credentials file

## Step 6: Save Credentials File

1. Rename the downloaded file to `google_credentials.json`
2. Move it to your gophotonics project directory:
   ```bash
   mv ~/Downloads/your-project-xxxxx.json /path/to/gophotonics/google_credentials.json
   ```
3. **Important**: This file is excluded from git (in `.gitignore`)

## Step 7: Create Google Sheet

1. Go to [Google Sheets](https://sheets.google.com)
2. Click **"Blank"** to create a new sheet
3. Name it **"GoPhotonics Leads"** (or whatever you prefer)
4. **Important**: Copy the **Sheet ID** from the URL

   URL format: `https://docs.google.com/spreadsheets/d/YOUR_SHEET_ID/edit`
   
   Example:
   ```
   https://docs.google.com/spreadsheets/d/1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms/edit
                                         ↑_______THIS PART IS THE SHEET ID_______↑
   ```

## Step 8: Share Sheet with Service Account

1. In your Google Sheet, click **"Share"** button (top right)
2. Paste the **service account email** (from step 4)
   - Format: `gophotonics-leads-sync@your-project-xxxxx.iam.gserviceaccount.com`
   - You can find this in the credentials JSON file under `"client_email"`
3. Give it **"Editor"** permissions
4. Uncheck **"Notify people"**
5. Click **"Share"** or **"Send"**

## Step 9: Configure Environment Variables

Add to your `.env` file:
```
GOOGLE_SHEET_ID=1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms
```
(Use your actual sheet ID from Step 7)

## Step 10: Test the Integration

Run the script:
```bash
python3 gophotonics_leads_selenium.py
```

You should see:
```
Syncing to Google Sheets...
  ✓ Synced 13 leads to Google Sheets
  📊 View at: https://docs.google.com/spreadsheets/d/YOUR_SHEET_ID
```

## Verification Checklist

- [ ] Google Sheets API enabled
- [ ] Google Drive API enabled
- [ ] Service account created
- [ ] `google_credentials.json` file in project directory
- [ ] Google Sheet created
- [ ] Sheet shared with service account email
- [ ] `GOOGLE_SHEET_ID` added to `.env` file
- [ ] Packages installed (`gspread`, `google-auth`)
- [ ] Test run successful

## Troubleshooting

### Error: "Insufficient Permission"
- **Cause**: Sheet not shared with service account
- **Fix**: Share the sheet with the service account email (Step 8)

### Error: "API has not been used in project"
- **Cause**: Google Sheets API or Drive API not enabled
- **Fix**: Enable both APIs in Google Cloud Console (Step 3)

### Error: "File google_credentials.json not found"
- **Cause**: Credentials file in wrong location or wrong name
- **Fix**: Ensure file is named exactly `google_credentials.json` and in project root

### Error: "Invalid authentication credentials"
- **Cause**: Credentials file corrupted or wrong project
- **Fix**: Download a fresh key from Google Cloud Console (Step 5)

### Sync Skipped: "Set GOOGLE_SHEET_ID in .env file"
- **Cause**: Sheet ID not configured
- **Fix**: Add `GOOGLE_SHEET_ID=your_id_here` to `.env` file (Step 9)

## Security Best Practices

1. **Never commit credentials**: `google_credentials.json` is in `.gitignore`
2. **Use service account**: Don't use your personal Google account
3. **Limit permissions**: Service account only has access to shared sheets
4. **Rotate keys**: Consider rotating service account keys periodically
5. **Share carefully**: Only share sheet with service account, not publicly

## Optional: Multiple Sheets

To sync to multiple sheets (e.g., production and staging):

1. Create multiple sheets
2. Share all with same service account
3. Use different sheet IDs based on environment:

```python
# In script, you could add logic like:
if os.environ.get('ENVIRONMENT') == 'production':
    sheet_id = os.environ.get('GOOGLE_SHEET_ID_PROD')
else:
    sheet_id = os.environ.get('GOOGLE_SHEET_ID_DEV')
```

## Cost

**All free** under Google Cloud's free tier:
- Google Sheets API: 500 requests/100 seconds (plenty for this use case)
- Google Drive API: 1 billion requests/day (way more than needed)
- Service accounts: Unlimited

## Disabling Google Sheets Sync

If you want to disable sync without uninstalling packages:

1. Remove or comment out `GOOGLE_SHEET_ID` from `.env`
2. Or delete `google_credentials.json`
3. Script will skip sync and just create local CSV

## Advanced: Programmatic Access

Your team can access the sheet programmatically:

```python
import gspread
from google.oauth2.service_account import Credentials

creds = Credentials.from_service_account_file('google_credentials.json')
client = gspread.authorize(creds)
sheet = client.open_by_key('YOUR_SHEET_ID')
worksheet = sheet.get_worksheet(0)

# Get all values
data = worksheet.get_all_values()

# Or use pandas
import pandas as pd
df = pd.DataFrame(data[1:], columns=data[0])
```

## Support

- [gspread Documentation](https://docs.gspread.org/)
- [Google Sheets API Documentation](https://developers.google.com/sheets/api)
- [Google Cloud Console](https://console.cloud.google.com/)

## Next Steps

Once set up, the sheet will automatically update every time you run the script. Set up cron for automated daily syncs!

```bash
# Daily at 9 AM
0 9 * * * cd /path/to/gophotonics && python3 gophotonics_leads_selenium.py
```
