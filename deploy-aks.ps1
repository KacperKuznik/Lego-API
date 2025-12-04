# LEGO-API AKS DEPLOYMENT SCRIPT

# This script reads configuration from environment variables or a `.env` file
# and creates a minimal AKS cluster, ACR, and storage account suitable for
# testing the Lego-API. Sensitive values (keys) are NOT checked into git.

function Load-DotEnv {
	param([string]$Path = ".env")
	if (-Not (Test-Path $Path)) { return }
	Get-Content $Path | ForEach-Object {
		$line = $_.Trim()
		if ($line -eq '' -or $line.StartsWith('#')) { return }
		$kv = $line -split('=',2)
		if ($kv.Count -ne 2) { return }
		$key = $kv[0].Trim()
		$val = $kv[1].Trim().Trim('"').Trim("'")
		[System.Environment]::SetEnvironmentVariable($key, $val)
	}
}

Load-DotEnv

# Read config from environment or use sensible defaults
$resourceGroup    = $env:RESOURCE_GROUP    -ne $null ? $env:RESOURCE_GROUP    : "cc2526"
$location         = $env:REGION            -ne $null ? $env:REGION            : "norwayeast"
$acrName          = $env:ACR_NAME         -ne $null ? $env:ACR_NAME         : "legoacr$((Get-Random -Minimum 1000 -Maximum 9999))"
$aksClusterName   = $env:AKS_CLUSTER      -ne $null ? $env:AKS_CLUSTER      : "legocluster"
$storageAccountName = $env:STORAGE_ACCOUNT -ne $null ? $env:STORAGE_ACCOUNT : "legostorage$((Get-Random -Minimum 100 -Maximum 999))"
$fileShareName    = $env:FILE_SHARE       -ne $null ? $env:FILE_SHARE       : "media"

Write-Host "Lego-API AKS Deployment" -ForegroundColor Cyan
Write-Host "Resource Group: $resourceGroup ($location)" -ForegroundColor Yellow
Write-Host "Estimated cost: ~$1.40/day for a single B2s node (testing)" -ForegroundColor Yellow
Write-Host ""

Write-Host "[1/6] Creating or validating ACR (Basic tier)..." -ForegroundColor Green
az acr create --resource-group $resourceGroup --name $acrName --sku Basic --location $location --output none
Write-Host "ACR: $acrName" -ForegroundColor Green

Write-Host "[2/6] Creating AKS cluster (1 B2s node)..." -ForegroundColor Green
az aks create `
  --resource-group $resourceGroup `
  --name $aksClusterName `
  --location $location `
  --node-count 1 `
  --node-vm-size Standard_B2s `
  --enable-managed-identity `
  --network-plugin azure `
  --output none

Write-Host "AKS cluster: $aksClusterName" -ForegroundColor Green

Write-Host "[3/6] Attach ACR to AKS..." -ForegroundColor Green
az aks update -n $aksClusterName -g $resourceGroup --attach-acr $acrName --output none

Write-Host "[4/6] Getting kubectl credentials..." -ForegroundColor Green
az aks get-credentials -g $resourceGroup -n $aksClusterName --overwrite-existing --output none

Write-Host "[5/6] Creating storage account and file share..." -ForegroundColor Green
az storage account create -n $storageAccountName -g $resourceGroup -l $location --sku Standard_LRS --access-tier Hot --output none

# Get storage key (avoid printing secrets).
$storageKey = az storage account keys list -g $resourceGroup -n $storageAccountName --query "[0].value" -o tsv

if ($env:SAVE_SECRETS -eq '1') {
	Write-Host "Saving storage key to local .env (ensure .env is in .gitignore)" -ForegroundColor Yellow
	if (-Not (Test-Path ".env")) { New-Item -Path .env -ItemType File -Force | Out-Null }
	Add-Content -Path .env "STORAGE_ACCOUNT_KEY=$storageKey"
}

az storage share create --account-name $storageAccountName --account-key $storageKey --name $fileShareName --quota 100 --output none

Write-Host "Storage account and file share created" -ForegroundColor Green

Write-Host "[6/6] Deployment finished."
Write-Host "Summary:" -ForegroundColor Cyan
Write-Host "  Resource Group: $resourceGroup"
Write-Host "  AKS Cluster: $aksClusterName"
Write-Host "  ACR: $acrName"
Write-Host "  Storage Account: $storageAccountName"
Write-Host "  File Share: $fileShareName"

Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "  1. Build and push Docker image to ACR"
Write-Host "  2. Create the Cosmos DB secret in Kubernetes (use .env)"
Write-Host "  3. Deploy Redis and app manifests: kubectl apply -f k8s/"
Write-Host "Cleanup (when done): az group delete --name $resourceGroup --yes --no-wait"
*** End Patch
