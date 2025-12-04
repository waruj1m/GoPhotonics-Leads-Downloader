# HubSpot Integration Setup

Your GoPhotonics lead scraper now automatically syncs to HubSpot CRM! 🎉

## What's New

The script now:
1. ✅ Scrapes leads from GoPhotonics
2. ✅ Consolidates into master CSV file
3. ✅ Syncs to Google Sheets
4. ✅ **NEW: Syncs to HubSpot CRM with active list**

## HubSpot Setup (5 minutes)

### 1. Create HubSpot Private App

1. Log into HubSpot
2. Go to **Settings** (gear icon) → **Integrations** → **Private Apps**
3. Click **Create a private app**
4. Name it: `GoPhotonics Lead Sync`
5. In the **Scopes** tab, enable:
   - `crm.objects.contacts.read`
   - `crm.objects.contacts.write`
6. Click **Create app**
7. Copy the access token (starts with `pat-na1-...`)

### 2. Add API Key to .env File

Add this line to your `.env` file:

```bash
HUBSPOT_API_KEY=pat-na1-your-token-here
```

Your complete `.env` should now have:
```bash
GOPHOTONICS_EMAIL=your_email
GOPHOTONICS_PASSWORD=your_password
GOOGLE_SHEET_ID=your_sheet_id
HUBSPOT_API_KEY=pat-na1-your-token-here
```

### 3. Create Custom Properties in HubSpot

1. Go to **Settings** → **Properties** → **Contact Properties**
2. Click **Create property** for each of these:

   - **Property name:** `google_sheet_sync`
     - **Field type:** Single checkbox
     - **Label:** "Synced from Google Sheets"
   
   - **Property name:** `google_sheet_sync_date`
     - **Field type:** Single-line text
     - **Label:** "Last sync date"
   
   - **Property name:** `google_sheet_resource`
     - **Field type:** Single-line text
     - **Label:** "Downloaded Resource"
   
   - **Property name:** `google_sheet_source_type`
     - **Field type:** Single-line text
     - **Label:** "Lead Source Type"
   
   - **Property name:** `google_sheet_source_file`
     - **Field type:** Single-line text
     - **Label:** "Source File"

### 4. Create Active List in HubSpot

1. Go to **Contacts** → **Lists**
2. Click **Create list**
3. Choose **Active list**
4. Name it: `GoPhotonics Leads`
5. Add filter:
   - Property: `google_sheet_sync`
   - Operator: `is equal to`
   - Value: `true`
6. Click **Save**

**Done!** All contacts synced from GoPhotonics will automatically appear in this list.

## How It Works

1. Script scrapes leads from GoPhotonics
2. Consolidates all leads into `gophotonics_master_leads.csv`
3. Syncs to Google Sheets (existing functionality)
4. **NEW:** Syncs to HubSpot:
   - Creates new contacts if they don't exist
   - Updates existing contacts with latest data
   - Tags all contacts with `google_sheet_sync=true`
   - Contacts automatically appear in your active list

## Usage

Just run the script as normal:

```bash
python3 gophotonics_leads_selenium.py
```

The output will now show:

```
Syncing to Google Sheets...
  ✓ Synced 25 leads to Google Sheets

Syncing to HubSpot CRM...
  Processing 25 contact(s)...
  ✓ HubSpot sync completed
    Created: 15 | Updated: 10 | Errors: 0

  💡 Contacts synced to HubSpot active list 'Google Sheets Contacts'

✓ Done! Master file ready at: gophotonics_master_leads.csv
```

## Install Dependencies

If you don't have the HubSpot SDK installed:

```bash
pip3 install -r requirements.txt
```

Or just:

```bash
pip3 install hubspot-api-client
```

## Features

- ✅ **Automatic deduplication** - Won't create duplicate contacts
- ✅ **Smart updates** - Updates existing contacts with new data
- ✅ **Active list** - Contacts automatically populate your list
- ✅ **Rate limiting** - Handles API rate limits gracefully
- ✅ **Progress tracking** - Shows sync progress for large datasets
- ✅ **Error handling** - Continues syncing even if some contacts fail

## Troubleshooting

### "HubSpot sync skipped"
Make sure `HUBSPOT_API_KEY` is set in your `.env` file

### "HubSpot sync not available"
Run: `pip3 install hubspot-api-client`

### Contacts not appearing in list
1. Verify custom properties were created in HubSpot
2. Check that the active list filter is set correctly
3. Run the script and check for errors in the output

### Rate limit errors
The script automatically waits when rate limits are hit. If you have a large dataset (>100 contacts), the sync may take a few minutes.

## What's Synced to HubSpot

From your master CSV:
- ✅ Email (required)
- ✅ Name (split into first/last name)
- ✅ Company
- ✅ Phone
- ✅ Country
- ✅ State
- ✅ City
- ✅ Address
- ✅ Resource downloaded
- ✅ Source type (Datasheet/Whitepaper/etc)
- ✅ Source file name

## Next Steps

1. Set up automation on your Raspberry Pi (if not already done)
2. Use HubSpot workflows to automatically:
   - Send follow-up emails to new leads
   - Assign leads to sales reps
   - Create deals for qualified leads
   - Track engagement

Enjoy your automated lead pipeline! 🚀
