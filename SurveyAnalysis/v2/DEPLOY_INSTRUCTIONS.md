# Deployment Instructions for Google Cloud

## Quick Deploy (Recommended)

Since you've already deployed before, use the `connect-frontend-backend.ps1` script to redeploy just the frontend with the fixes:

### Step 1: Open PowerShell in the project root

### Step 2: Run the deployment script

```powershell
.\deploy\connect-frontend-backend.ps1 -ProjectId "YOUR_PROJECT_ID" -Region "us-central1"
```

Replace `YOUR_PROJECT_ID` with your actual Google Cloud Project ID.

**Example:**
```powershell
.\deploy\connect-frontend-backend.ps1 -ProjectId "my-survey-analysis-project" -Region "us-central1"
```

### What this script does:
1. ✅ Checks if backend is deployed (deploys if needed)
2. ✅ Gets the backend URL automatically
3. ✅ Creates `.env.production` file with correct `VITE_API_BASE_URL`
4. ✅ Builds the frontend Docker image with the updated code
5. ✅ Deploys to Cloud Run

---

## Full Deployment (If starting fresh)

If you need to deploy everything from scratch, use:

```powershell
.\deploy\deploy-gcp.ps1 -ProjectId "YOUR_PROJECT_ID" -Region "us-central1"
```

Or for minimal resources (lower cost):

```powershell
.\deploy\deploy-gcp-minimal.ps1 -ProjectId "YOUR_PROJECT_ID" -Region "us-central1"
```

---

## Prerequisites

Make sure you have:
- ✅ Google Cloud SDK installed (`gcloud` command)
- ✅ Authenticated: `gcloud auth login`
- ✅ Project set: `gcloud config set project YOUR_PROJECT_ID`
- ✅ Required APIs enabled (script will enable them automatically)

---

## After Deployment

The script will output:
- Frontend URL (e.g., `https://survey-analysis-frontend-xxx-uc.a.run.app`)
- Backend URL (e.g., `https://survey-analysis-backend-xxx-uc.a.run.app`)

Visit the Frontend URL to test your application!

---

## Troubleshooting

### If you get "gcloud not found":
1. Install Google Cloud SDK: https://cloud.google.com/sdk/docs/install
2. Restart PowerShell after installation

### If deployment fails:
- Check that your project has billing enabled
- Verify you have the necessary permissions (Owner or Editor role)
- Check the Cloud Build logs: `gcloud builds list --limit=5`

### To check deployment status:
```powershell
gcloud run services list --region us-central1
```

