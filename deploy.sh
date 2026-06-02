@echo off
echo ========================================================
echo Deploying Axiom Core to Google Cloud Run...
echo ========================================================

echo.
echo [1/3] Deploying Screener Service...
rename Dockerfile.screener Dockerfile
call gcloud run deploy axiom-screener --source . --port 8080 --allow-unauthenticated --region us-central1 --quiet
rename Dockerfile Dockerfile.screener

echo.
echo [2/3] Deploying Strategies Service...
rename Dockerfile.strategies Dockerfile
call gcloud run deploy axiom-strategies --source . --port 8080 --allow-unauthenticated --region us-central1 --quiet
rename Dockerfile Dockerfile.strategies

echo.
echo [3/3] Deploying Frontend Service...
rename Dockerfile.frontend Dockerfile
call gcloud run deploy axiom-frontend --source . --port 8080 --allow-unauthenticated --region us-central1 --quiet
rename Dockerfile Dockerfile.frontend

echo.
echo ========================================================
echo Deployment Complete!
echo Next Steps:
echo 1. Get the URLs for axiom-screener and axiom-strategies from the output above.
echo 2. Update index.html with those URLs.
echo 3. Run deploy.bat one more time to push the updated index.html!
echo ========================================================
