# LEGO-API AKS DEPLOYMENT TO cc2526
# Deploys minimal-cost AKS cluster, ACR, and storage to existing resource group
# Region: westeurope (matches existing Cosmos DB location)

# VARIABLES
$resourceGroup = "cc2526"
$location = "northeurope"
$acrName = "legoaci$(Get-Random -Minimum 1000 -Maximum 9999)"
$aksClusterName = "legocluster"
$storageAccountName = "legostorage$(Get-Random -Minimum 100 -Maximum 999)"
$fileShareName = "media"

Write-Host "Lego-API AKS Deployment" -ForegroundColor Cyan
Write-Host "Resource Group: $resourceGroup (northeurope)" -ForegroundColor Yellow
Write-Host "Estimated cost: 2-5 dollars per day for testing" -ForegroundColor Yellow
Write-Host ""

# 1. CREATE CONTAINER REGISTRY
Write-Host "[1/5] Creating ACR (Basic = 5 dollars per month)..." -ForegroundColor Green
az acr create --resource-group $resourceGroup --name $acrName --sku Basic --location $location 2>$null | Out-Null
Write-Host "ACR created: $acrName" -ForegroundColor Green

# 2. CREATE AKS CLUSTER
Write-Host "[2/5] Creating AKS cluster (1 B2s node)..." -ForegroundColor Green
az aks create `
  --resource-group $resourceGroup `
  --name $aksClusterName `
  --location $location `
  --node-count 1 `
  --node-vm-size Standard_B2s `
  --generate-ssh-keys `
  --enable-managed-identity `
  --tier free `
  --network-plugin azure `
  --output none

Write-Host "AKS cluster created: $aksClusterName" -ForegroundColor Green

# 3. ATTACH ACR TO AKS
Write-Host "[3/5] Attaching ACR to AKS..." -ForegroundColor Green
az aks update `
  -n $aksClusterName `
  -g $resourceGroup `
  --attach-acr $acrName `
  --output none

Write-Host "ACR attached to AKS" -ForegroundColor Green

# 4. GET KUBERNETES CREDENTIALS
Write-Host "[4/5] Getting kubectl credentials..." -ForegroundColor Green
az aks get-credentials `
  -g $resourceGroup `
  -n $aksClusterName `
  --overwrite-existing `
  --output none

Write-Host "kubectl configured" -ForegroundColor Green

# 5. CREATE STORAGE ACCOUNT AND FILE SHARE
Write-Host "[5/5] Creating storage account (LRS)..." -ForegroundColor Green
az storage account create `
  -n $storageAccountName `
  -g $resourceGroup `
  -l $location `
  --sku Standard_LRS `
  --access-tier Hot `
  --output none

# Get storage key
$storageKey = (az storage account keys list `
  -g $resourceGroup `
  -n $storageAccountName `
  --query "[0].value" -o tsv)

# Create file share (100 GB quota for media)
az storage share create `
  --account-name $storageAccountName `
  --account-key "$storageKey" `
  --name $fileShareName `
  --quota 100 `
  --output none

Write-Host "Storage account and file share created" -ForegroundColor Green

# SUMMARY
Write-Host ""
Write-Host "DEPLOYMENT COMPLETE!" -ForegroundColor Green
Write-Host "================================"
Write-Host "Resource Group: $resourceGroup"
Write-Host "AKS Cluster: $aksClusterName"
Write-Host "ACR: $acrName"
Write-Host "Storage Account: $storageAccountName"
Write-Host "Storage Key: $storageKey"
Write-Host "File Share: $fileShareName"
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "1. Deploy Redis"
Write-Host "2. Deploy Ingress Controller"
Write-Host "3. Containerize and deploy app"
Write-Host "4. Run artillery tests"
Write-Host ""
Write-Host "CLEANUP (when done):" -ForegroundColor Yellow
Write-Host "az group delete --name $resourceGroup --yes --no-wait"
