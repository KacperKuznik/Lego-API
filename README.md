# Lego-API

FastAPI backend for managing Lego collections, users, auctions, and media. Deployed on Azure Kubernetes Service (AKS) with Redis caching and Cosmos DB integration.

```
pip install -r requirements.txt
python -m textblob.download_corpora
python populate_db.py
fastapi dev main.py

```

authors:

Kacper Kuźnik 75267 k.kuznik@campus.fct.unl.pt

Dawid Bogacz 75160 d.bogacz@campus.fct.unl.pt

Mikołaj Nowacki 75231 m.nowacki@campus.fct.unl.pt
## Quick Start - Local Development

```bash
pip install -r requirements.txt
fastapi dev main.py
```

Server runs on `http://localhost:8000`

## Production Deployment on Azure Kubernetes Service (AKS)

### Prerequisites

- Azure CLI (`az`) installed
- Docker Desktop running
- `kubectl` configured to access your AKS cluster
- Azure subscription with appropriate resource group

### Step 1: Set Environment Variables

```powershell
$RESOURCE_GROUP = "cc2526"
$AKS_CLUSTER = "legocluster"
$ACR_NAME = "legoacr2572"
$REGION = "norwayeast"  # Must be in allowed region policy
```

### Step 2: Create Azure Resources

```powershell
# Create resource group (if needed)
az group create --name $RESOURCE_GROUP --location $REGION

# Create Azure Container Registry
az acr create --resource-group $RESOURCE_GROUP --name $ACR_NAME --sku Basic

# Create AKS cluster
az aks create `
	--resource-group $RESOURCE_GROUP `
	--name $AKS_CLUSTER `
	--node-count 1 `
	--vm-set-type VirtualMachineScaleSets `
	--load-balancer-sku standard `
	--enable-managed-identity `
	--network-plugin azure `
	--region $REGION

# Get credentials
az aks get-credentials --resource-group $RESOURCE_GROUP --name $AKS_CLUSTER
```

### Step 3: Build and Push Docker Image

```powershell
# Login to ACR
az acr login --name $ACR_NAME

# Build image
docker build -t "$($ACR_NAME).azurecr.io/lego-api:v1" .

# Push to ACR
docker push "$($ACR_NAME).azurecr.io/lego-api:v1"
```

### Step 4: Deploy to Kubernetes

#### 1. Create Cosmos DB Secret

```powershell
$COSMOS_ENDPOINT = "https://your-cosmos-account.documents.azure.com:443/"
$COSMOS_KEY = "your-cosmos-primary-key"
$DATABASE_NAME = "lego_db"

kubectl create secret generic cosmos-secret `
	--from-literal=COSMOS_ENDPOINT=$COSMOS_ENDPOINT `
	--from-literal=COSMOS_KEY=$COSMOS_KEY `
	--from-literal=DATABASE_NAME=$DATABASE_NAME
```

#### 2. Deploy Redis Cache

```powershell
kubectl apply -f k8s/redis-deploy.yaml
```

#### 3. Deploy Application

```powershell
# Update image in k8s/app-deploy.yaml if using different tag

kubectl apply -f k8s/app-deploy.yaml
```

#### 4. Deploy Ingress Controller

```powershell
# Install NGINX Ingress Controller
helm repo add ingress-nginx https://kubernetes.github.io/ingress-nginx
helm repo update
helm install nginx-ingress ingress-nginx/ingress-nginx `
	--namespace ingress-basic `
	--create-namespace `
	--set controller.service.type=LoadBalancer

# Deploy ingress rules
kubectl apply -f k8s/ingress.yaml
```

### Step 5: Verify Deployment

```powershell
# Check pod status
kubectl get pods

# View application logs
kubectl logs deployment/lego-api --tail 50

# Get ingress IP
kubectl get service -A | Select-String "LoadBalancer"

# Test API endpoint
Invoke-WebRequest -Uri "http://<INGRESS_IP>/rest/user" -Method GET
```

## File Structure

```
.
├── main.py              # FastAPI application with REST endpoints
├── cosmosdb.py          # Cosmos DB client initialization
├── rediscache.py        # Redis cache client
├── models.py            # Pydantic models
├── utils.py             # Utility functions
├── requirements.txt     # Python dependencies
├── Dockerfile           # Container image definition
└── k8s/                 # Kubernetes manifests
		├── redis-deploy.yaml    # Redis in-cluster cache
		├── app-deploy.yaml      # Application deployment
		└── ingress.yaml         # NGINX ingress configuration
```

## Endpoints

- `POST /rest/user` - Create user
- `GET /rest/user` - List all users
- `GET /rest/user/{user_id}` - Get user by ID
- `GET /rest/legoset` - List all Lego sets
- `POST /rest/legoset` - Create Lego set
- `GET /rest/auction` - List all auctions
- `POST /rest/auction` - Create auction
- `POST /rest/bid` - Place bid

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

- **Container Orchestration**: Azure Kubernetes Service (AKS) 1.32
- **Container Registry**: Azure Container Registry (Basic SKU)
- **Database**: Azure Cosmos DB (SQL API)
- **Caching**: Redis 7.2-alpine (in-cluster)
- **Ingress**: NGINX LoadBalancer
- **Cost**: ~$1.40/day (single B2s node)
