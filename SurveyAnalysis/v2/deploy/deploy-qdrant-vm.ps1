# Deploy Qdrant Vector Database to Google Compute Engine VM (with persistent storage)
# Usage: .\deploy\deploy-qdrant-vm.ps1 -ProjectId "your-project-id" -Region "us-central1"

param(
    [Parameter(Mandatory=$true)]
    [string]$ProjectId,

    [Parameter(Mandatory=$false)]
    [string]$Region = "us-central1",

    [Parameter(Mandatory=$false)]
    [string]$Zone = "us-central1-a",

    [Parameter(Mandatory=$false)]
    [string]$MachineType = "e2-medium"  # 2 vCPU, 4 GB RAM
)

Write-Host "[DEPLOY] Deploying Qdrant Vector DB to Compute Engine VM" -ForegroundColor Green
Write-Host "Project ID: $ProjectId" -ForegroundColor Cyan
Write-Host "Region: $Region" -ForegroundColor Cyan
Write-Host "Zone: $Zone" -ForegroundColor Cyan
Write-Host "Machine Type: $MachineType" -ForegroundColor Cyan
Write-Host ""

# Set the project
Write-Host "[INFO] Setting project..." -ForegroundColor Yellow
gcloud config set project $ProjectId

# Enable Compute Engine API
Write-Host "[INFO] Enabling Compute Engine API..." -ForegroundColor Yellow
gcloud services enable compute.googleapis.com 2>$null

# Step 1: Check if VM already exists
Write-Host "`n[STEP 1] Checking if VM exists..." -ForegroundColor Yellow
$vmExists = gcloud compute instances describe qdrant-vm --zone=$Zone --format=json 2>&1 | Out-String
if ($LASTEXITCODE -eq 0 -and $vmExists -match '"name"') {
    Write-Host "⚠️  VM 'qdrant-vm' already exists in zone $Zone" -ForegroundColor Yellow
    $confirm = Read-Host "Do you want to delete and recreate? (yes/no)"
    if ($confirm -eq "yes") {
        Write-Host "Deleting existing VM..." -ForegroundColor Gray
        gcloud compute instances delete qdrant-vm --zone=$Zone --quiet
        if ($LASTEXITCODE -ne 0) {
            Write-Host "❌ Error: Failed to delete existing VM" -ForegroundColor Red
            exit 1
        }
    } else {
        Write-Host "❌ Cancelled. Exiting." -ForegroundColor Red
        exit 0
    }
}

# Step 2: Create persistent disk for Qdrant storage
Write-Host "`n[STEP 2] Creating persistent disk..." -ForegroundColor Yellow
$diskExists = gcloud compute disks describe qdrant-data --zone=$Zone --format=json 2>&1 | Out-String
if ($LASTEXITCODE -eq 0 -and $diskExists -match '"name"') {
    Write-Host "✅ Disk 'qdrant-data' already exists" -ForegroundColor Green
} else {
    Write-Host "Creating 20GB persistent disk..." -ForegroundColor Gray
    gcloud compute disks create qdrant-data `
        --project=$ProjectId `
        --size=20GB `
        --zone=$Zone `
        --type=pd-standard `
        --description="Qdrant vector database storage"

    if ($LASTEXITCODE -ne 0) {
        Write-Host "❌ Error: Failed to create disk" -ForegroundColor Red
        exit 1
    }
    Write-Host "✅ Disk created successfully" -ForegroundColor Green
}

# Step 3: Create firewall rule for Qdrant port
Write-Host "`n[STEP 3] Creating firewall rule..." -ForegroundColor Yellow
$firewallExists = gcloud compute firewall-rules describe allow-qdrant --format=json 2>&1 | Out-String
if ($LASTEXITCODE -eq 0 -and $firewallExists -match '"name"') {
    Write-Host "✅ Firewall rule 'allow-qdrant' already exists" -ForegroundColor Green
} else {
    Write-Host "Creating firewall rule for port 6333..." -ForegroundColor Gray
    gcloud compute firewall-rules create allow-qdrant `
        --allow tcp:6333 `
        --source-ranges 0.0.0.0/0 `
        --description "Allow Qdrant API access" `
        --target-tags qdrant-server

    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ Firewall rule created" -ForegroundColor Green
    } else {
        Write-Host "⚠️  Firewall rule may already exist" -ForegroundColor Yellow
    }
}

# Step 4: Create startup script for VM
Write-Host "`n[STEP 4] Creating startup script..." -ForegroundColor Yellow
$startupScript = @'
#!/bin/bash
set -e

echo "Installing Docker..."
apt-get update
apt-get install -y apt-transport-https ca-certificates curl gnupg lsb-release

# Install Docker
curl -fsSL https://download.docker.com/linux/debian/gpg | gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg
echo "deb [arch=amd64 signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/debian $(lsb_release -cs) stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null
apt-get update
apt-get install -y docker-ce docker-ce-cli containerd.io

# Format and mount persistent disk
echo "Setting up persistent disk..."
DEVICE="/dev/sdb"
MOUNT_POINT="/mnt/qdrant-data"

# Check if disk is already formatted
if ! blkid $DEVICE; then
    echo "Formatting disk..."
    mkfs.ext4 -F $DEVICE
fi

# Create mount point and mount
mkdir -p $MOUNT_POINT
mount $DEVICE $MOUNT_POINT

# Add to fstab for auto-mount on reboot
UUID=$(blkid -s UUID -o value $DEVICE)
if ! grep -q $UUID /etc/fstab; then
    echo "UUID=$UUID $MOUNT_POINT ext4 defaults,nofail 0 2" >> /etc/fstab
fi

# Set permissions
chmod 777 $MOUNT_POINT

# Pull and run Qdrant
echo "Starting Qdrant container..."
docker pull qdrant/qdrant:v1.7.4

# Stop and remove existing container if any
docker stop qdrant 2>/dev/null || true
docker rm qdrant 2>/dev/null || true

# Run Qdrant with persistent storage
docker run -d \
    --name qdrant \
    --restart always \
    -p 6333:6333 \
    -v $MOUNT_POINT:/qdrant/storage \
    qdrant/qdrant:v1.7.4

echo "Qdrant started successfully!"
echo "Dashboard available at: http://$(curl -s http://metadata.google.internal/computeMetadata/v1/instance/network-interfaces/0/access-configs/0/external-ip -H "Metadata-Flavor: Google"):6333/dashboard"
'@

$tempScriptPath = [System.IO.Path]::GetTempFileName()
$startupScript | Out-File -FilePath $tempScriptPath -Encoding utf8
Write-Host "✅ Startup script created" -ForegroundColor Green

# Step 5: Create VM instance
Write-Host "`n[STEP 5] Creating VM instance..." -ForegroundColor Yellow
Write-Host "This will take 2-3 minutes..." -ForegroundColor Gray

gcloud compute instances create qdrant-vm `
    --project=$ProjectId `
    --zone=$Zone `
    --machine-type=$MachineType `
    --image-family=debian-11 `
    --image-project=debian-cloud `
    --boot-disk-size=10GB `
    --boot-disk-type=pd-standard `
    --disk "name=qdrant-data,device-name=qdrant-data" `
    --tags=qdrant-server `
    --metadata-from-file=startup-script=$tempScriptPath `
    --scopes=https://www.googleapis.com/auth/cloud-platform

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Error: Failed to create VM" -ForegroundColor Red
    Remove-Item $tempScriptPath -Force
    exit 1
}

Remove-Item $tempScriptPath -Force
Write-Host "✅ VM created successfully" -ForegroundColor Green

# Step 6: Get VM external IP
Write-Host "`n[STEP 6] Getting VM details..." -ForegroundColor Yellow
Start-Sleep -Seconds 10  # Wait for VM to initialize

$externalIp = gcloud compute instances describe qdrant-vm --zone=$Zone --format='get(networkInterfaces[0].accessConfigs[0].natIP)'
$internalIp = gcloud compute instances describe qdrant-vm --zone=$Zone --format='get(networkInterfaces[0].networkIP)'

Write-Host ""
Write-Host "[SUCCESS] Qdrant VM Deployed Successfully!" -ForegroundColor Green
Write-Host ""
Write-Host "VM Details:" -ForegroundColor Cyan
Write-Host "   Name: qdrant-vm" -ForegroundColor White
Write-Host "   Zone: $Zone" -ForegroundColor White
Write-Host "   Machine Type: $MachineType" -ForegroundColor White
Write-Host "   External IP: $externalIp" -ForegroundColor White
Write-Host "   Internal IP: $internalIp" -ForegroundColor White
Write-Host ""
Write-Host "Qdrant URLs:" -ForegroundColor Cyan
Write-Host "   API (External): http://$externalIp:6333" -ForegroundColor White
Write-Host "   Dashboard: http://$externalIp:6333/dashboard" -ForegroundColor White
Write-Host "   API (Internal - from Cloud Run): http://$internalIp:6333" -ForegroundColor White
Write-Host ""
Write-Host "[WAIT] Waiting for Qdrant to start (30 seconds)..." -ForegroundColor Yellow
Start-Sleep -Seconds 30

Write-Host ""
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host ""
Write-Host "1. Test Qdrant connection:" -ForegroundColor White
Write-Host "   curl http://$externalIp:6333/collections" -ForegroundColor Gray
Write-Host ""
Write-Host "2. Update backend environment variable:" -ForegroundColor White
Write-Host "   QDRANT_URL=http://$internalIp:6333" -ForegroundColor Gray
Write-Host "   (Use internal IP if backend is also on GCP)" -ForegroundColor Gray
Write-Host ""
Write-Host "3. Update deploy-gcp.ps1 to add QDRANT_URL to backend deployment" -ForegroundColor White
Write-Host ""
Write-Host "4. SSH into VM (optional):" -ForegroundColor White
Write-Host "   gcloud compute ssh qdrant-vm --zone=$Zone" -ForegroundColor Gray
Write-Host ""
Write-Host "5. View Qdrant logs:" -ForegroundColor White
Write-Host "   gcloud compute ssh qdrant-vm --zone=$Zone --command='docker logs qdrant'" -ForegroundColor Gray
Write-Host ""
Write-Host "Storage:" -ForegroundColor Cyan
Write-Host "   Persistent disk: qdrant-data (20GB)" -ForegroundColor White
Write-Host "   Mounted at: /mnt/qdrant-data" -ForegroundColor White
Write-Host "   Auto-starts on VM reboot" -ForegroundColor White
Write-Host ""
Write-Host "Cost estimate: ~`$25-30/month (e2-medium + 20GB disk)" -ForegroundColor Yellow
Write-Host ""
