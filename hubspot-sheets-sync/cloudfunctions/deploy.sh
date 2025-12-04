#!/bin/bash
# Deploy to Google Cloud Functions

# Configuration - UPDATE THESE
PROJECT_ID="your-gcp-project-id"
REGION="us-central1"
FUNCTION_NAME="sync-hubspot-contacts"
HUBSPOT_API_KEY="your-hubspot-api-key"
GOOGLE_SHEET_ID="your-sheet-id"

echo "Deploying HubSpot Sheets Sync to Google Cloud Functions..."

# Copy sync_contacts.py to cloudfunctions directory
cp ../sync_contacts.py .
cp ../requirements.txt .

# Deploy the function
gcloud functions deploy $FUNCTION_NAME \
  --gen2 \
  --runtime=python311 \
  --region=$REGION \
  --source=. \
  --entry-point=sync_hubspot_contacts \
  --trigger-http \
  --allow-unauthenticated \
  --set-env-vars HUBSPOT_API_KEY=$HUBSPOT_API_KEY,GOOGLE_SHEET_ID=$GOOGLE_SHEET_ID,GOOGLE_SHEET_RANGE="Sheet1!A:M",GOOGLE_CREDENTIALS_FILE="google-credentials.json" \
  --max-instances=1 \
  --timeout=540s \
  --memory=256MB

# Get the function URL
FUNCTION_URL=$(gcloud functions describe $FUNCTION_NAME --region=$REGION --format='value(serviceConfig.uri)')

echo ""
echo "Deployment complete!"
echo "Function URL: $FUNCTION_URL"
echo ""
echo "To set up daily scheduling, run:"
echo ""
echo "gcloud scheduler jobs create http sync-hubspot-daily \\"
echo "  --location=$REGION \\"
echo "  --schedule=\"0 9 * * *\" \\"
echo "  --uri=\"$FUNCTION_URL\" \\"
echo "  --http-method=POST"
