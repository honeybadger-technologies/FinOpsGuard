# FinOpsGuard Quick Start Guide

## 🚀 Docker Compose (Fastest)

### 1. Start FinOpsGuard
```bash
# Basic deployment
docker-compose up -d

# With monitoring (Prometheus + Grafana)
docker-compose --profile monitoring up -d
```

### 2. Verify
```bash
# Check health
curl http://localhost:8080/healthz

# Open Admin UI
open http://localhost:8080/

# Open API docs
open http://localhost:8080/docs
```

### 3. Stop
```bash
docker-compose down
```

---

## ☸️ Kubernetes

### 1. Build and Push Image
```bash
# Build
docker build -t your-registry/finopsguard:v0.2.0 .

# Push
docker push your-registry/finopsguard:v0.2.0

# Update image in deploy/kubernetes/deployment.yaml
```

### 2. Deploy
```bash
# Using kubectl
make k8s-deploy

# Or manually
kubectl apply -f deploy/kubernetes/namespace.yaml
kubectl apply -f deploy/kubernetes/configmap.yaml
kubectl apply -f deploy/kubernetes/secret.yaml
kubectl apply -f deploy/kubernetes/deployment.yaml
kubectl apply -f deploy/kubernetes/service.yaml
kubectl apply -f deploy/kubernetes/hpa.yaml
kubectl apply -f deploy/kubernetes/pdb.yaml

# Using Kustomize
kubectl apply -k deploy/kubernetes/
```

### 3. Verify
```bash
# Check status
kubectl get pods -n finopsguard

# Port forward
kubectl port-forward -n finopsguard svc/finopsguard 8080:8080

# Test
curl http://localhost:8080/healthz
```

### 4. Deploy Ingress (Optional)
```bash
# Edit deploy/kubernetes/ingress.yaml (set your domain)
kubectl apply -f deploy/kubernetes/ingress.yaml
```

---

## 🛠️ Makefile Commands

### Development
```bash
make install          # Install dependencies
make test            # Run tests
make run             # Run dev server
```

### Docker
```bash
make docker-build    # Build image
make docker-run      # Run container
```

### Docker Compose
```bash
make docker-compose-up              # Start services
make docker-compose-up-monitoring   # Start with monitoring
make docker-compose-logs            # View logs
make docker-compose-down            # Stop services
```

### Kubernetes
```bash
make k8s-deploy      # Deploy to cluster
make k8s-status      # Check status
make k8s-logs        # View logs
make k8s-port-forward # Port forward
make k8s-delete      # Delete deployment
```

---

## 📊 Access Services

### Docker Compose
- **FinOpsGuard**: http://localhost:8080
- **Prometheus**: http://localhost:9090 (monitoring profile)
- **Grafana**: http://localhost:3000 (monitoring profile, admin/changeme)

### Kubernetes
- **Internal**: http://finopsguard.finopsguard.svc.cluster.local:8080
- **Port Forward**: `kubectl port-forward -n finopsguard svc/finopsguard 8080:8080`
- **Ingress**: Configure in `deploy/kubernetes/ingress.yaml`

---

## 🧪 Test the API

```bash
# Health check
curl http://localhost:8080/healthz

# Get price catalog
curl -X POST http://localhost:8080/mcp/getPriceCatalog \
  -H 'Content-Type: application/json' \
  -d '{"cloud":"aws"}'

# List policies
curl http://localhost:8080/mcp/policies

# Check cost impact
PAYLOAD=$(echo 'resource "aws_instance" "test" { 
  instance_type = "t3.medium"
}
provider "aws" { region="us-east-1" }' | base64)

curl -X POST http://localhost:8080/mcp/checkCostImpact \
  -H 'Content-Type: application/json' \
  -d "{\"iac_type\":\"terraform\",\"iac_payload\":\"$PAYLOAD\"}"
```

---

## 📚 Documentation

- **Full Deployment Guide**: [docs/deployment.md](../docs/deployment.md)
- **CI/CD Integration**: [docs/cicd-integration.md](../docs/cicd-integration.md)
- **Architecture**: [docs/architecture.md](../docs/architecture.md)
- **Requirements**: [docs/requirements.md](../docs/requirements.md)
- **API Docs**: http://localhost:8080/docs (after starting)

---

## 🆘 Troubleshooting

### Docker Compose Issues
```bash
# View logs
docker-compose logs -f finopsguard

# Rebuild
docker-compose build --no-cache
docker-compose up -d

# Reset everything
docker-compose down -v
```

### Kubernetes Issues
```bash
# View logs
kubectl logs -n finopsguard -l app=finopsguard -f

# Describe pod
kubectl describe pod -n finopsguard -l app=finopsguard

# Check events
kubectl get events -n finopsguard --sort-by='.lastTimestamp'

# Restart deployment
kubectl rollout restart deployment/finopsguard -n finopsguard
```

### Common Issues

**Port 8080 already in use:**
```bash
# Docker Compose: Change port in .env
echo "FINOPS_PORT=8081" >> .env

# Or kill process
lsof -ti:8080 | xargs kill -9
```

**Permission denied:**
```bash
# Docker Compose
sudo docker-compose up -d

# Kubernetes
kubectl auth can-i create deployments -n finopsguard
```

---

## 🎯 Next Steps

1. ✅ **Deploy** using Docker Compose or Kubernetes
2. ✅ **Access** Admin UI at http://localhost:8080/
3. ✅ **Create** custom policies via UI or API
4. ✅ **Integrate** with CI/CD (see [cicd-integration.md](../docs/cicd-integration.md))
5. ✅ **Monitor** with Prometheus/Grafana (optional)

Happy cost optimizing! 💰

