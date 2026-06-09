#!/bin/bash
set -e # Exit immediately if any command fails

echo "========================================================"
echo "Deploying Axiom Core to Google Cloud Run..."
echo "========================================================"

echo -e "\n[1/3] Deploying Screener Service..."
mv Dockerfile.screener Dockerfile
gcloud run deploy axiom-screener --source . --port 8080 --allow-unauthenticated --region us-central1 --quiet
mv Dockerfile Dockerfile.screener

echo -e "\n[2/3] Deploying Strategies Service..."
mv Dockerfile.strategies Dockerfile
gcloud run deploy axiom-strategies --source . --port 8080 --allow-unauthenticated --region us-central1 --quiet
mv Dockerfile Dockerfile.strategies

echo -e "\n[3/3] Deploying Frontend Service..."
mv Dockerfile.frontend Dockerfile
gcloud run deploy axiom-frontend --source . --port 8080 --allow-unauthenticated --region us-central1 --quiet
mv Dockerfile Dockerfile.frontend

echo "========================================================"
echo "Deployment Complete!"
echo "Next Steps:"
echo "1. Get the URLs for axiom-screener and axiom-strategies from the output above."
echo "2. Update index.html with those URLs."
echo "3. Run ./deploy.sh one more time to push the updated index.html!"
echo "========================================================"