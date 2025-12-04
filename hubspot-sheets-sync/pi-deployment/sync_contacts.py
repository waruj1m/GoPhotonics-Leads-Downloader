#!/usr/bin/env python3
"""
HubSpot Google Sheets Contact Sync
Syncs contacts from Google Sheets to HubSpot and maintains an active list
"""

import os
import sys
from datetime import datetime
from typing import List, Dict, Optional
import logging

from google.oauth2 import service_account
from googleapiclient.discovery import build
from hubspot import HubSpot
from hubspot.crm.contacts import SimplePublicObjectInputForCreate, ApiException

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configuration
GOOGLE_SHEET_ID = os.environ.get('GOOGLE_SHEET_ID')
GOOGLE_SHEET_RANGE = os.environ.get('GOOGLE_SHEET_RANGE', 'Sheet1!A:M')
HUBSPOT_API_KEY = os.environ.get('HUBSPOT_API_KEY')
GOOGLE_CREDENTIALS_FILE = os.environ.get('GOOGLE_CREDENTIALS_FILE', 'google-credentials.json')


class ContactSyncer:
    def __init__(self):
        """Initialize the syncer with Google Sheets and HubSpot clients"""
        self.hubspot = HubSpot(access_token=HUBSPOT_API_KEY)
        self.sheets_service = self._init_google_sheets()
        
    def _init_google_sheets(self):
        """Initialize Google Sheets API client"""
        try:
            credentials = service_account.Credentials.from_service_account_file(
                GOOGLE_CREDENTIALS_FILE,
                scopes=['https://www.googleapis.com/auth/spreadsheets.readonly']
            )
            return build('sheets', 'v4', credentials=credentials)
        except Exception as e:
            logger.error(f"Failed to initialize Google Sheets client: {e}")
            raise
    
    def get_sheet_contacts(self) -> List[Dict[str, str]]:
        """Fetch contacts from Google Sheets"""
        try:
            result = self.sheets_service.spreadsheets().values().get(
                spreadsheetId=GOOGLE_SHEET_ID,
                range=GOOGLE_SHEET_RANGE
            ).execute()
            
            rows = result.get('values', [])
            if not rows:
                logger.warning("No data found in sheet")
                return []
            
            # First row is headers
            headers = [h.lower().strip() for h in rows[0]]
            contacts = []
            
            for row in rows[1:]:
                # Pad row if it's shorter than headers
                row = row + [''] * (len(headers) - len(row))
                contact = dict(zip(headers, row))
                
                # Only process if email exists
                if contact.get('email'):
                    contacts.append(contact)
            
            logger.info(f"Retrieved {len(contacts)} contacts from Google Sheets")
            return contacts
            
        except Exception as e:
            logger.error(f"Error fetching sheet data: {e}")
            raise
    
    def map_sheet_to_hubspot(self, sheet_contact: Dict[str, str]) -> Dict[str, str]:
        """Map Google Sheets columns to HubSpot properties"""
        hubspot_props = {
            'email': sheet_contact.get('email', '').strip(),
            'firstname': sheet_contact.get('name', '').strip().split()[0] if sheet_contact.get('name') else '',
            'lastname': ' '.join(sheet_contact.get('name', '').strip().split()[1:]) if sheet_contact.get('name') and len(sheet_contact.get('name', '').split()) > 1 else '',
            'company': sheet_contact.get('company', '').strip(),
            'phone': sheet_contact.get('phone', '').strip(),
            'country': sheet_contact.get('country', '').strip(),
            'state': sheet_contact.get('state', '').strip(),
            'city': sheet_contact.get('city', '').strip(),
            'address': sheet_contact.get('address', '').strip(),
            # Custom property to identify contacts synced from Google Sheets
            'google_sheet_sync': 'true',
            'google_sheet_sync_date': datetime.utcnow().isoformat(),
            'google_sheet_resource': sheet_contact.get('resource', '').strip(),
            'google_sheet_source_type': sheet_contact.get('source_type', '').strip(),
            'google_sheet_source_file': sheet_contact.get('source_file', '').strip(),
        }
        
        # Remove empty values
        return {k: v for k, v in hubspot_props.items() if v}
    
    def get_existing_contact(self, email: str) -> Optional[str]:
        """Check if contact already exists in HubSpot by email"""
        try:
            # Search for contact by email
            response = self.hubspot.crm.contacts.search_api.do_search(
                public_object_search_request={
                    "filterGroups": [{
                        "filters": [{
                            "propertyName": "email",
                            "operator": "EQ",
                            "value": email
                        }]
                    }],
                    "properties": ["email"],
                    "limit": 1
                }
            )
            
            if response.results:
                return response.results[0].id
            return None
            
        except Exception as e:
            logger.error(f"Error searching for contact {email}: {e}")
            return None
    
    def create_or_update_contact(self, sheet_contact: Dict[str, str]) -> bool:
        """Create or update a contact in HubSpot"""
        email = sheet_contact.get('email', '').strip()
        if not email:
            logger.warning("Skipping contact without email")
            return False
        
        try:
            hubspot_props = self.map_sheet_to_hubspot(sheet_contact)
            existing_id = self.get_existing_contact(email)
            
            if existing_id:
                # Update existing contact
                self.hubspot.crm.contacts.basic_api.update(
                    contact_id=existing_id,
                    simple_public_object_input={"properties": hubspot_props}
                )
                logger.info(f"Updated contact: {email}")
            else:
                # Create new contact
                self.hubspot.crm.contacts.basic_api.create(
                    simple_public_object_input_for_create=SimplePublicObjectInputForCreate(
                        properties=hubspot_props
                    )
                )
                logger.info(f"Created contact: {email}")
            
            return True
            
        except ApiException as e:
            logger.error(f"HubSpot API error for {email}: {e}")
            return False
        except Exception as e:
            logger.error(f"Error processing contact {email}: {e}")
            return False
    
    def sync(self):
        """Main sync process"""
        logger.info("Starting contact sync...")
        
        # Get contacts from sheet
        sheet_contacts = self.get_sheet_contacts()
        
        if not sheet_contacts:
            logger.warning("No contacts to sync")
            return
        
        # Process each contact
        success_count = 0
        error_count = 0
        
        for contact in sheet_contacts:
            if self.create_or_update_contact(contact):
                success_count += 1
            else:
                error_count += 1
        
        logger.info(f"Sync completed: {success_count} successful, {error_count} errors")


def main():
    """Main entry point"""
    # Validate environment variables
    if not HUBSPOT_API_KEY:
        logger.error("HUBSPOT_API_KEY environment variable not set")
        sys.exit(1)
    
    if not GOOGLE_SHEET_ID:
        logger.error("GOOGLE_SHEET_ID environment variable not set")
        sys.exit(1)
    
    try:
        syncer = ContactSyncer()
        syncer.sync()
    except Exception as e:
        logger.error(f"Sync failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
