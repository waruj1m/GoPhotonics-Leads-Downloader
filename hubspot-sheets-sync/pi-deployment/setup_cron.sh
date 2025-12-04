#!/bin/bash
# Setup script for Raspberry Pi cron job

# Get the current directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

echo "Setting up HubSpot Sheets Sync cron job..."
echo "Script directory: $SCRIPT_DIR"

# Create log directory if it doesn't exist
mkdir -p "$SCRIPT_DIR/logs"

# Create cron entry
CRON_JOB="0 9 * * * cd $SCRIPT_DIR && /usr/bin/python3 sync_contacts.py >> $SCRIPT_DIR/logs/sync.log 2>&1"

# Check if cron job already exists
(crontab -l 2>/dev/null | grep -v "sync_contacts.py"; echo "$CRON_JOB") | crontab -

echo "Cron job installed successfully!"
echo "The sync will run daily at 9:00 AM"
echo "Logs will be saved to: $SCRIPT_DIR/logs/sync.log"
echo ""
echo "To view current cron jobs: crontab -l"
echo "To test the sync now: python3 $SCRIPT_DIR/sync_contacts.py"
