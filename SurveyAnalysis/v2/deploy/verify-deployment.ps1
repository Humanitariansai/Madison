# Deployment Verification Script
# Checks all components of the Survey Analysis deployment
# Usage: .\deploy\verify-deployment.ps1 -ProjectId "your-project-id"

param(
    [Parameter(Mandatory=$true)]
    [string]$ProjectId,

    [Parameter(Mandatory=$false)]
    [string]$Region = "us-central1"
)

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Survey Analysis - Deployment Verification" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Set project
gcloud config set project $ProjectId | Out-Null

$allGood = $true

# Function to check status
function Check-Status {
    param($name, $condition, $expected, $actual, $details = "")

    if ($condition) {
        Write-Host "✅ $name" -ForegroundColor Green
        if ($details) {
            Write-Host "   $details" -ForegroundColor Gray
        }
    } else {
        Write-Host "❌ $name" -ForegroundColor Red
        Write-Host "   Expected: $expected" -ForegroundColor Yellow
        Write-Host "   Actual: $actual" -ForegroundColor Yellow
        $script:allGood = $false
    }
}

Write-Host "Checking Backend..." -ForegroundColor Yellow
Write-Host ""

# Backend - Service Exists
try {
    $backendStatus = gcloud run services describe survey-analysis-backend --region=$Region --format="get(status.conditions[0].status)" 2>&1
    Check-Status "Backend Service Running" ($backendStatus -eq "True") "True" $backendStatus

    $backendUrl = gcloud run services describe survey-analysis-backend --region=$Region --format="value(status.url)" 2>&1
    Check-Status "Backend URL Configured" ($backendUrl -like "https://*") "https://..." $backendUrl "URL: $backendUrl"
} catch {
    Check-Status "Backend Service" $false "Running" "Not Found"
}

# Backend - Memory
try {
    $backendMemory = gcloud run services describe survey-analysis-backend --region=$Region --format="get(spec.template.spec.containers[0].resources.limits.memory)" 2>&1
    Check-Status "Backend Memory (2Gi)" ($backendMemory -eq "2Gi") "2Gi" $backendMemory
} catch {
    Check-Status "Backend Memory" $false "2Gi" "Unknown"
}

# Backend - VPC Egress
try {
    $vpcEgress = gcloud run services describe survey-analysis-backend --region=$Region --format="get(spec.template.metadata.annotations.'run.googleapis.com/vpc-access-egress')" 2>&1
    Check-Status "VPC Egress Mode" ($vpcEgress -eq "private-ranges-only") "private-ranges-only" $vpcEgress
} catch {
    Check-Status "VPC Egress" $false "private-ranges-only" "Unknown"
}

# Backend - VPC Connector
try {
    $vpcConnector = gcloud run services describe survey-analysis-backend --region=$Region --format="get(spec.template.metadata.annotations.'run.googleapis.com/vpc-access-connector')" 2>&1
    Check-Status "VPC Connector" ($vpcConnector -eq "cloudrun-connector") "cloudrun-connector" $vpcConnector
} catch {
    Check-Status "VPC Connector" $false "cloudrun-connector" "Unknown"
}

# Backend - QDRANT_URL
try {
    $envVars = gcloud run services describe survey-analysis-backend --region=$Region --format="yaml(spec.template.spec.containers[0].env)" 2>&1 | Out-String
    $hasQdrantUrl = $envVars -match "QDRANT_URL.*10\.128\."
    Check-Status "QDRANT_URL Environment Variable" $hasQdrantUrl "http://10.128.0.5:6333" $(if($hasQdrantUrl){"Set"}else{"Not Set or Wrong"})
} catch {
    Check-Status "QDRANT_URL" $false "Set" "Unknown"
}

# Backend - DATABASE_URL (Public IP)
try {
    $envVars = gcloud run services describe survey-analysis-backend --region=$Region --format="yaml(spec.template.spec.containers[0].env)" 2>&1 | Out-String
    $hasPublicIpDb = $envVars -match "DATABASE_URL.*34\."
    Check-Status "DATABASE_URL (Public IP)" $hasPublicIpDb "Public IP (34.*)" $(if($hasPublicIpDb){"Public IP"}else{"Unix Socket or Wrong"})
} catch {
    Check-Status "DATABASE_URL" $false "Public IP" "Unknown"
}

Write-Host ""
Write-Host "Checking Frontend..." -ForegroundColor Yellow
Write-Host ""

# Frontend - Service Exists
try {
    $frontendStatus = gcloud run services describe survey-analysis-frontend --region=$Region --format="get(status.conditions[0].status)" 2>&1
    Check-Status "Frontend Service Running" ($frontendStatus -eq "True") "True" $frontendStatus

    $frontendUrl = gcloud run services describe survey-analysis-frontend --region=$Region --format="value(status.url)" 2>&1
    Check-Status "Frontend URL Configured" ($frontendUrl -like "https://*") "https://..." $frontendUrl "URL: $frontendUrl"
} catch {
    Check-Status "Frontend Service" $false "Running" "Not Found"
}

Write-Host ""
Write-Host "Checking Qdrant..." -ForegroundColor Yellow
Write-Host ""

# Qdrant VM - Running
try {
    $qdrantStatus = gcloud compute instances describe qdrant-vm --zone=us-central1-a --format="get(status)" 2>&1
    Check-Status "Qdrant VM Status" ($qdrantStatus -eq "RUNNING") "RUNNING" $qdrantStatus

    $qdrantIp = gcloud compute instances describe qdrant-vm --zone=us-central1-a --format="get(networkInterfaces[0].networkIP)" 2>&1
    Check-Status "Qdrant Internal IP" ($qdrantIp -eq "10.128.0.5") "10.128.0.5" $qdrantIp "IP: $qdrantIp"
} catch {
    Check-Status "Qdrant VM" $false "RUNNING" "Not Found"
}

Write-Host ""
Write-Host "Checking Cloud SQL..." -ForegroundColor Yellow
Write-Host ""

# Cloud SQL - Running
try {
    $sqlStatus = gcloud sql instances describe survey-analysis-db --format="get(state)" 2>&1
    Check-Status "Cloud SQL Status" ($sqlStatus -eq "RUNNABLE") "RUNNABLE" $sqlStatus

    $sqlIp = gcloud sql instances describe survey-analysis-db --format="get(ipAddresses[0].ipAddress)" 2>&1
    Check-Status "Cloud SQL Public IP" ($sqlIp -like "34.*") "34.*.*.* (Public IP)" $sqlIp "IP: $sqlIp"
} catch {
    Check-Status "Cloud SQL" $false "RUNNABLE" "Not Found"
}

Write-Host ""
Write-Host "Checking VPC Networking..." -ForegroundColor Yellow
Write-Host ""

# VPC Connector - Ready
try {
    $connectorStatus = gcloud compute networks vpc-access connectors describe cloudrun-connector --region=$Region --format="get(state)" 2>&1
    Check-Status "VPC Connector Status" ($connectorStatus -eq "READY") "READY" $connectorStatus

    $connectorRange = gcloud compute networks vpc-access connectors describe cloudrun-connector --region=$Region --format="get(ipCidrRange)" 2>&1
    Check-Status "VPC Connector IP Range" ($connectorRange -eq "10.8.0.0/28") "10.8.0.0/28" $connectorRange
} catch {
    Check-Status "VPC Connector" $false "READY" "Not Found"
}

Write-Host ""
Write-Host "Checking Secrets..." -ForegroundColor Yellow
Write-Host ""

# OpenAI API Key
try {
    $openaiSecret = gcloud secrets describe openai-api-key --format="get(name)" 2>&1
    Check-Status "OpenAI API Key Secret" ($openaiSecret -like "*openai-api-key") "Exists" $(if($openaiSecret -like "*openai-api-key"){"Exists"}else{"Not Found"})
} catch {
    Check-Status "OpenAI API Key" $false "Exists" "Not Found"
}

# JWT Secret
try {
    $jwtSecret = gcloud secrets describe jwt-secret --format="get(name)" 2>&1
    Check-Status "JWT Secret" ($jwtSecret -like "*jwt-secret") "Exists" $(if($jwtSecret -like "*jwt-secret"){"Exists"}else{"Not Found"})
} catch {
    Check-Status "JWT Secret" $false "Exists" "Not Found"
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan

if ($allGood) {
    Write-Host "✅ ALL CHECKS PASSED" -ForegroundColor Green
    Write-Host ""
    Write-Host "Your deployment is correctly configured!" -ForegroundColor Green
    Write-Host ""
    Write-Host "Next steps:" -ForegroundColor Yellow
    Write-Host "1. Test backend health: curl $backendUrl/health" -ForegroundColor White
    Write-Host "2. Open frontend: $frontendUrl" -ForegroundColor White
    Write-Host "3. Check logs: gcloud run services logs tail survey-analysis-backend --region=$Region" -ForegroundColor White
} else {
    Write-Host "❌ SOME CHECKS FAILED" -ForegroundColor Red
    Write-Host ""
    Write-Host "Please review the errors above and fix the issues." -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Common fixes:" -ForegroundColor Yellow
    Write-Host "1. Redeploy: .\deploy\redeploy-code-only.ps1 -ProjectId '$ProjectId'" -ForegroundColor White
    Write-Host "2. Check TROUBLESHOOTING.md for specific issues" -ForegroundColor White
    Write-Host "3. View logs: gcloud run services logs tail survey-analysis-backend --region=$Region" -ForegroundColor White
}

Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

