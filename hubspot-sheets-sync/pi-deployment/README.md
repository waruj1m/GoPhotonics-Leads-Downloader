# HubSpot Google Sheets Contact Sync

Automatically sync contacts from Google Sheets to HubSpot and maintain an active list.

## Features

- ✅ Syncs contacts from Google Sheets to HubSpot
- ✅ Creates new contacts or updates existing ones
- ✅ Marks synced contacts with custom property for active list filtering
- ✅ Can run on Raspberry Pi or Google Cloud Functions
- ✅ Daily scheduling support

## Setup Instructions

### 1. HubSpot Setup

#### Create a Private App in HubSpot:
1. Go to HubSpot Settings → Integrations → Private Apps
2. Click "Create a private app"
3. Name it "Google Sheets Contact Sync"
4. In the **Scopes** tab, enable:
   - `crm.objects.contacts.read`
   - `crm.objects.contacts.write`
5. Click "Create app" and copy the access token
6. Save this token - you'll use it as `HUBSPOT_API_KEY`

#### Create Custom Properties (if they don't exist):
1. Go to Settings → Properties → Contact Properties
2. Create the following custom properties:
   - **google_sheet_sync** (Single checkbox) - "Synced from Google Sheets"
   - **google_sheet_sync_date** (Single-line text) - "Last sync date"
   - **google_sheet_resource** (Single-line text) - "Resource from sheet"
   - **google_sheet_source_type** (Single-line text) - "Source type"
   - **google_sheet_source_file** (Single-line text) - "Source file"

#### Create Active List:
1. Go to Contacts → Lists → Create list
2. Choose "Active list"
3. Name it "Google Sheets Contacts"
4. Set filter: `google_sheet_sync` is equal to `true`
5. Save the list

Now any contact synced from Google Sheets will automatically appear in this active list!

### 2. Google Sheets API Setup

#### Enable Google Sheets API:
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project (or select existing)
3. Enable "Google Sheets API"
4. Go to "Credentials" → Create Credentials → Service Account
5. Create a service account (name it "hubspot-sheets-sync")
6. Click on the service account → Keys → Add Key → Create new key → JSON
7. Download the JSON file and save it as `google-credentials.json` in your project folder

#### Share your Google Sheet:
1. Open your Google Sheet
2. Click "Share"
3. Add the service account email (from the JSON file: `client_email` field)
4. Give it "Viewer" access
5. Copy the Sheet ID from the URL: `https://docs.google.com/spreadsheets/d/[SHEET_ID]/edit`

### 3. Installation

#### On Raspberry Pi:

```bash
# Navigate to your project directory
cd /home/pi/hubspot-sheets-sync

# Install Python dependencies
pip3 install -r requirements.txt

# Copy environment template
cp .env.example .env

# Edit .env with your credentials
nano .env
```

Add your credentials to `.env`:
```
HUBSPOT_API_KEY=pat-na1-xxxxx-xxxx
GOOGLE_SHEET_ID=1abc123xyz
GOOGLE_SHEET_RANGE=Sheet1!A:M
GOOGLE_CREDENTIALS_FILE=/home/pi/hubspot-sheets-sync/google-credentials.json
```

#### Test the sync:

```bash
python3 sync_contacts.py
```

#### Set up daily cron job:

```bash
crontab -e
```

Add this line to run daily at 9 AM:
```
0 9 * * * cd /home/pi/hubspot-sheets-sync && /usr/bin/python3 sync_contacts.py >> /home/pi/hubspot-sheets-sync/sync.log 2>&1
```

### 4. Google Cloud Functions (Alternative)

If you prefer to run on Google Cloud Functions:

#### Create `main.py`:
```python
from sync_contacts import ContactSyncer
import os

def sync_hubspot_contacts(request):
    """HTTP Cloud Function entry point"""
    try:
        syncer = ContactSyncer()
        syncer.sync()
        return 'Sync completed successfully', 200
    except Exception as e:
        return f'Sync failed: {str(e)}', 500
```

#### Deploy:
```bash
gcloud functions deploy sync-hubspot-contacts \
  --runtime python311 \
  --trigger-http \
  --allow-unauthenticated \
  --entry-point sync_hubspot_contacts \
  --set-env-vars HUBSPOT_API_KEY=your_key,GOOGLE_SHEET_ID=your_id
```

#### Set up Cloud Scheduler:
```bash
gcloud scheduler jobs create http sync-hubspot-daily \
  --schedule="0 9 * * *" \
  --uri="https://YOUR_REGION-YOUR_PROJECT.cloudfunctions.net/sync-hubspot-contacts" \
  --http-method=GET
```

## Usage

### Manual run:
```bash
python3 sync_contacts.py
```

### Check logs:
```bash
tail -f sync.log
```

## How It Works

1. Script reads all contacts from your Google Sheet
2. For each contact:
   - Maps sheet columns to HubSpot properties
   - Checks if contact exists (by email)
   - Creates new contact or updates existing one
   - Sets `google_sheet_sync=true` property
3. HubSpot active list automatically updates based on this property
4. New contacts appear in the list immediately
5. If you remove a contact from the sheet, they'll still exist in HubSpot but won't be updated

## Troubleshooting

### "HUBSPOT_API_KEY environment variable not set"
- Make sure your `.env` file exists and contains the API key
- Or export it: `export HUBSPOT_API_KEY=your_key`

### "Failed to initialize Google Sheets client"
- Verify `google-credentials.json` exists and path is correct
- Ensure the service account email has access to your sheet

### Contacts not appearing in active list
- Check that custom properties were created in HubSpot
- Verify the active list filter is set to `google_sheet_sync = true`
- Run the script with verbose logging to see if contacts are being synced

## Next Steps

- Monitor the first few syncs to ensure data is mapping correctly
- Consider adding webhook notifications for sync failures
- Add email deduplication logic if needed
- Extend with additional HubSpot properties as needed
