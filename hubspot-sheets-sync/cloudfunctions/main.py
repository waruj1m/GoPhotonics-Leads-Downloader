"""
Google Cloud Functions entry point for HubSpot contact sync
"""

import sys
import os

# Add parent directory to path to import sync_contacts module
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sync_contacts import ContactSyncer
import logging

logger = logging.getLogger(__name__)


def sync_hubspot_contacts(request):
    """
    HTTP Cloud Function entry point for syncing contacts
    
    Args:
        request (flask.Request): The request object
        
    Returns:
        tuple: Response message and HTTP status code
    """
    try:
        logger.info("Cloud Function triggered - starting sync")
        syncer = ContactSyncer()
        syncer.sync()
        return {'status': 'success', 'message': 'Sync completed successfully'}, 200
    except Exception as e:
        logger.error(f"Sync failed: {e}")
        return {'status': 'error', 'message': str(e)}, 500


def scheduled_sync(event, context):
    """
    Cloud Scheduler entry point for syncing contacts
    
    Args:
        event (dict): Event payload
        context (google.cloud.functions.Context): Metadata for the event
        
    Returns:
        str: Success message
    """
    try:
        logger.info("Scheduled sync triggered")
        syncer = ContactSyncer()
        syncer.sync()
        return "Sync completed successfully"
    except Exception as e:
        logger.error(f"Scheduled sync failed: {e}")
        raise
