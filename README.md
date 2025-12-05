# Lego-API

FastAPI backend for managing Lego collections, users, auctions, and media. Fully deployed on Azure Kubernetes Service (AKS) with Redis caching, Cosmos DB, and NGINX ingress.

**Note:** All deployment-specific values (IPs, resource names, credentials) are stored in `.env` file. See `.env.example` for required variables.

## Authors

- Kacper Kuźnik 75267 - k.kuznik@campus.fct.unl.pt
- Dawid Bogacz 75160 - d.bogacz@campus.fct.unl.pt
- Mikołaj Nowacki 75231 - m.nowacki@campus.fct.unl.pt

## Quick Start - Local Development

```bash
pip install -r requirements.txt
python -m textblob.download_corpora
python populate_db.py
fastapi dev main.py
```

Server runs on `http://localhost:8000`

## Production Deployment on Azure Kubernetes Service (AKS)

### Automated Deployment

Use the deployment script for automated resource provisioning:

```powershell
# Ensure .env file exists with required credentials
.\deploy-aks.ps1
```

The script will:
- Create resource group, ACR, AKS cluster, and storage
- Attach ACR to AKS for seamless image pulling
- Configure kubectl context automatically

### Prerequisites

- Azure CLI (`az`) installed and logged in
- Docker Desktop running
- `kubectl` installed
- Azure subscription with appropriate permissions
- `.env` file with secrets (see `.env.example`)

### Manual Deployment Steps

#### Step 1: Set Environment Variables

```powershell
$RESOURCE_GROUP = "<your-resource-group>"
$AKS_CLUSTER = "<your-aks-cluster>"
$ACR_NAME = "<your-acr-name>"
$REGION = "<your-region>"  # Must be in allowed region policy (e.g., norwayeast, westeurope)
```

#### Step 2: Create Azure Resources

```powershell
# Create resource group
az group create --name $RESOURCE_GROUP --location $REGION

# Create Azure Container Registry
az acr create --resource-group $RESOURCE_GROUP --name $ACR_NAME --sku Basic

# Create AKS cluster
az aks create `
    --resource-group $RESOURCE_GROUP `
    --name $AKS_CLUSTER `
    --node-count 1 `
    --node-vm-size Standard_B2s `
    --enable-managed-identity `
    --network-plugin azure `
    --location $REGION `
    --attach-acr $ACR_NAME

# Create Cosmos DB
az cosmosdb create `
    --name <your-cosmos-name> `
    --resource-group $RESOURCE_GROUP `
    --locations regionName=$REGION `
    --kind GlobalDocumentDB `
    --default-consistency-level Session

# Get AKS credentials
az aks get-credentials --resource-group $RESOURCE_GROUP --name $AKS_CLUSTER
```

#### Step 3: Build and Push Docker Image

```powershell
# Login to ACR
az acr login --name $ACR_NAME

# Build image
docker build -t "$($ACR_NAME).azurecr.io/lego-api:v4" .

# Push to ACR
docker push "$($ACR_NAME).azurecr.io/lego-api:v4"
```

#### Step 4: Deploy to Kubernetes

**1. Create Cosmos DB Secret**

Get your Cosmos DB credentials:
```powershell
$COSMOS_NAME = "<your-cosmos-name>"
$COSMOS_ENDPOINT = az cosmosdb show --name $COSMOS_NAME --resource-group $RESOURCE_GROUP --query documentEndpoint -o tsv
$COSMOS_KEY = az cosmosdb keys list --name $COSMOS_NAME --resource-group $RESOURCE_GROUP --query primaryMasterKey -o tsv
```

Create the secret:
```powershell
kubectl create secret generic cosmos-secret `
    --from-literal=COSMOS_ENDPOINT=$COSMOS_ENDPOINT `
    --from-literal=COSMOS_KEY=$COSMOS_KEY `
    --from-literal=DATABASE_NAME=legodb
```

**2. Deploy Redis Cache (in-cluster)**

```powershell
kubectl apply -f k8s/redis-deploy.yaml
```

**3. Deploy Application**

Update the image reference in `k8s/app-deploy.yaml` or use kubectl:
```powershell
kubectl apply -f k8s/app-deploy.yaml
kubectl set image deployment/lego-api lego-api=$ACR_NAME.azurecr.io/lego-api:v4
kubectl set env deployment/lego-api REDIS_HOST=redis REDIS_PORT=6379 REDIS_KEY=''
```

**4. Install NGINX Ingress Controller**

```powershell
# Apply the official manifest
kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/controller-v1.8.2/deploy/static/provider/cloud/deploy.yaml

# Deploy ingress rules
kubectl apply -f k8s/ingress.yaml

# Wait for external IP assignment
kubectl get service -n ingress-nginx ingress-nginx-controller --watch
```

#### Step 5: Verify Deployment

```powershell
# Check pod status
kubectl get pods -A

# View application logs
kubectl logs deployment/lego-api --tail 50

# Get ingress external IP
kubectl get ingress -A

# Test API endpoint
$INGRESS_IP = kubectl get service -n ingress-nginx ingress-nginx-controller -o jsonpath='{.status.loadBalancer.ingress[0].ip}'
Invoke-WebRequest -Uri "http://$INGRESS_IP/docs"
Invoke-WebRequest -Uri "http://$INGRESS_IP/rest/user"
```

### Testing Your Deployment

After deployment, get your ingress IP:
```powershell
$INGRESS_IP = kubectl get service -n ingress-nginx ingress-nginx-controller -o jsonpath='{.status.loadBalancer.ingress[0].ip}'
Write-Host "Your API is available at: http://$INGRESS_IP"
```

**Test Endpoints:**
```powershell
# List users
curl http://$INGRESS_IP/rest/user

# Create user
curl -X POST http://$INGRESS_IP/rest/user `
  -H "Content-Type: application/json" `
  -d '{"nickname":"john","name":"John Doe","password":"pass123"}'

# Access API documentation
curl http://$INGRESS_IP/docs
```

## File Structure

```
.
├── main.py               # FastAPI application with REST endpoints
├── cosmosdb.py           # Cosmos DB client initialization with error handling
├── rediscache.py         # Redis cache client
├── blobstorage.py        # Azure Blob Storage for media files
├── models.py             # Pydantic models for validation
├── utils.py              # Utility functions (password hashing, etc.)
├── requirements.txt      # Python dependencies
├── Dockerfile            # Optimized container image definition
├── deploy-aks.ps1        # Automated deployment script
├── .env.example          # Environment variable template
└── k8s/                  # Kubernetes manifests
    ├── redis-deploy.yaml    # Redis in-cluster cache deployment
    ├── app-deploy.yaml      # Application deployment with secrets
    └── ingress.yaml         # NGINX ingress configuration
```

## API Endpoints

**User Management:**
- `POST /rest/user` - Create new user
- `GET /rest/user` - List all users (with Redis caching, 60s TTL)
- `GET /rest/user/{user_id}` - Get user by ID
- `PUT /rest/user/{user_id}` - Update user
- `DELETE /rest/user/{user_id}` - Delete user

**Lego Sets:**
- `GET /rest/legoset` - List all Lego sets
- `POST /rest/legoset` - Create Lego set (with image upload)

**Auctions:**
- `GET /rest/auction` - List all auctions
- `POST /rest/auction` - Create auction
- `GET /rest/auction/{auction_id}` - Get auction details

**Bidding:**
- `POST /rest/bid` - Place bid on auction

**Media:**
- `GET /rest/media/{blob_name}` - Get media URL

**Documentation:**
- `GET /docs` - Swagger UI (interactive API documentation)
- `GET /openapi.json` - OpenAPI schema

## Load Testing

Run performance tests with Artillery:

```bash
npm install -g artillery
artillery run artillery-test.yml --output results.json
```

## Cleanup

To delete all Azure resources and avoid ongoing charges:

```powershell
az group delete --name cc2526 --yes --no-wait
```

## Architecture

**Cloud Infrastructure:**
- **Container Orchestration**: Azure Kubernetes Service (AKS) v1.32
- **Container Registry**: Azure Container Registry (Basic SKU)
- **Database**: Azure Cosmos DB (SQL API, Session consistency)
- **Caching**: Redis 7.2-alpine (in-cluster deployment)
- **Ingress**: NGINX Ingress Controller (LoadBalancer)
- **Storage**: Azure Blob Storage (for media files)

**Application Stack:**
- **Framework**: FastAPI 0.118.0
- **Server**: Uvicorn (async ASGI)
- **Python**: 3.12-slim
- **Dependencies**: 
  - azure-cosmos 4.9.0
  - azure-storage-blob 12.19.0
  - redis 4.5.5
  - pydantic 2.11.10
  - passlib + argon2 (password hashing)

**Cost Estimate**: ~$1.40/day (single Standard_B2s node, minimal throughput)

**Features:**
- ✅ Graceful error handling (DB/cache failures non-blocking)
- ✅ Redis caching with TTL (60s for user lists)
- ✅ Password hashing with Argon2
- ✅ Sentiment analysis via TextBlob
- ✅ Image upload to Azure Blob Storage
- ✅ Comprehensive logging
- ✅ Health check ready endpoints
