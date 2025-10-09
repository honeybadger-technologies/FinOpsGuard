# FinOpsGuard Deployment Checklist

Use this checklist to ensure a successful deployment of FinOpsGuard.

## Pre-Deployment

### Environment Preparation
- [ ] Choose deployment method (Docker Compose or Kubernetes)
- [ ] Verify system requirements (Docker 20.10+, Kubernetes 1.24+)
- [ ] Review [deployment documentation](../docs/deployment.md)
- [ ] Plan resource allocation (CPU, memory, storage)

### Configuration
- [ ] Copy `env.example` to `.env` (Docker Compose)
- [ ] Review and update environment variables
- [ ] Set default budget limits (`DEFAULT_BUDGET`)
- [ ] Configure cloud regions (`AWS_REGION`, `GCP_REGION`)
- [ ] Set logging level (`LOG_LEVEL`)
- [ ] Configure worker count (`WORKERS`)

### Security
- [ ] Generate strong secrets (API keys, tokens)
- [ ] Configure GitHub/GitLab tokens (if using CI/CD integration)
- [ ] Review secret management strategy
- [ ] Plan TLS/SSL certificate provisioning (for Kubernetes)
- [ ] Review network security requirements

---

## Docker Compose Deployment

### Build & Deploy
- [ ] Build Docker image: `docker build -t finopsguard:latest .`
- [ ] Review `docker-compose.yml` configuration
- [ ] Choose deployment profile (basic/monitoring/caching)
- [ ] Start services: `docker-compose up -d`
- [ ] Verify containers are running: `docker-compose ps`

### Verification
- [ ] Check logs: `docker-compose logs finopsguard`
- [ ] Test health endpoint: `curl http://localhost:8080/healthz`
- [ ] Access Admin UI: http://localhost:8080/
- [ ] Review API documentation: http://localhost:8080/docs
- [ ] Test sample API request
- [ ] Verify metrics endpoint: http://localhost:8080/metrics

### Monitoring (Optional)
- [ ] Start monitoring stack: `docker-compose --profile monitoring up -d`
- [ ] Access Prometheus: http://localhost:9090
- [ ] Access Grafana: http://localhost:3000 (admin/changeme)
- [ ] Configure Grafana datasource
- [ ] Import or create dashboards
- [ ] Set up alerts

---

## Kubernetes Deployment

### Pre-Deployment
- [ ] Build Docker image: `docker build -t your-registry/finopsguard:v0.2.0 .`
- [ ] Push to registry: `docker push your-registry/finopsguard:v0.2.0`
- [ ] Update image in `deploy/kubernetes/deployment.yaml`
- [ ] Review resource requests and limits
- [ ] Configure kubectl context: `kubectl config current-context`

### Namespace & Configuration
- [ ] Create namespace: `kubectl apply -f deploy/kubernetes/namespace.yaml`
- [ ] Review ConfigMap: `deploy/kubernetes/configmap.yaml`
- [ ] Apply ConfigMap: `kubectl apply -f deploy/kubernetes/configmap.yaml`
- [ ] Create secrets: `kubectl apply -f deploy/kubernetes/secret.yaml`
- [ ] Verify configuration: `kubectl get configmap,secret -n finopsguard`

### Core Deployment
- [ ] Apply deployment: `kubectl apply -f deploy/kubernetes/deployment.yaml`
- [ ] Apply service: `kubectl apply -f deploy/kubernetes/service.yaml`
- [ ] Wait for pods: `kubectl wait --for=condition=ready pod -l app=finopsguard -n finopsguard --timeout=300s`
- [ ] Check pod status: `kubectl get pods -n finopsguard`
- [ ] Review pod logs: `kubectl logs -n finopsguard -l app=finopsguard`

### High Availability
- [ ] Apply HPA: `kubectl apply -f deploy/kubernetes/hpa.yaml`
- [ ] Apply PDB: `kubectl apply -f deploy/kubernetes/pdb.yaml`
- [ ] Verify HPA: `kubectl get hpa -n finopsguard`
- [ ] Verify PDB: `kubectl get pdb -n finopsguard`
- [ ] Check pod distribution across nodes

### Ingress (Optional)
- [ ] Verify ingress controller is installed
- [ ] Update domain in `deploy/kubernetes/ingress.yaml`
- [ ] Configure TLS certificates (cert-manager or manual)
- [ ] Apply ingress: `kubectl apply -f deploy/kubernetes/ingress.yaml`
- [ ] Verify ingress: `kubectl get ingress -n finopsguard`
- [ ] Test external access: `curl https://finopsguard.yourdomain.com/healthz`

### Monitoring (Optional)
- [ ] Verify Prometheus Operator is installed
- [ ] Apply ServiceMonitor: `kubectl apply -f deploy/kubernetes/servicemonitor.yaml`
- [ ] Verify metrics scraping in Prometheus
- [ ] Create Grafana dashboards
- [ ] Configure alerts

### Verification
- [ ] Port forward: `kubectl port-forward -n finopsguard svc/finopsguard 8080:8080`
- [ ] Test health endpoint: `curl http://localhost:8080/healthz`
- [ ] Access Admin UI: http://localhost:8080/
- [ ] Review API documentation: http://localhost:8080/docs
- [ ] Test sample API request
- [ ] Verify policy management
- [ ] Test cost analysis

---

## Post-Deployment

### Configuration
- [ ] Create default policies via Admin UI or API
- [ ] Configure budget rules
- [ ] Test policy evaluation
- [ ] Set up environment-specific policies (dev/staging/prod)

### Integration
- [ ] Configure CI/CD integration (GitHub Actions, GitLab CI)
- [ ] Test automated cost checks
- [ ] Verify PR/MR commenting
- [ ] Update team documentation

### Monitoring
- [ ] Set up log aggregation (if not using default)
- [ ] Configure metric collection
- [ ] Create custom dashboards
- [ ] Set up alerting rules
- [ ] Define SLOs/SLIs

### Security
- [ ] Review and rotate secrets
- [ ] Configure network policies (Kubernetes)
- [ ] Enable authentication (if required)
- [ ] Review RBAC permissions (Kubernetes)
- [ ] Audit access logs

### Performance
- [ ] Monitor resource usage
- [ ] Adjust replicas/workers if needed
- [ ] Enable caching (Redis) if performance is an issue
- [ ] Review and optimize policies

### Backup
- [ ] Document configuration
- [ ] Export policies: `curl http://localhost:8080/mcp/policies > policies-backup.json`
- [ ] Backup ConfigMaps/Secrets (Kubernetes)
- [ ] Document deployment process

---

## Validation Tests

### Health & Availability
```bash
# Health check
curl -f http://localhost:8080/healthz || echo "FAILED"

# Metrics endpoint
curl -f http://localhost:8080/metrics | grep -q finopsguard || echo "FAILED"

# Admin UI
curl -f http://localhost:8080/ | grep -q "FinOpsGuard" || echo "FAILED"
```

### API Functionality
```bash
# List policies
curl -f http://localhost:8080/mcp/policies || echo "FAILED"

# Get price catalog
curl -f -X POST http://localhost:8080/mcp/getPriceCatalog \
  -H 'Content-Type: application/json' \
  -d '{"cloud":"aws"}' || echo "FAILED"

# Cost analysis (basic)
PAYLOAD=$(echo 'resource "aws_instance" "test" { instance_type = "t3.small" } provider "aws" { region="us-east-1" }' | base64)
curl -f -X POST http://localhost:8080/mcp/checkCostImpact \
  -H 'Content-Type: application/json' \
  -d "{\"iac_type\":\"terraform\",\"iac_payload\":\"$PAYLOAD\"}" || echo "FAILED"
```

### Kubernetes Specific
```bash
# Pod health
kubectl get pods -n finopsguard -o json | jq '.items[].status.conditions[] | select(.type=="Ready") | .status' | grep -q "True" || echo "FAILED"

# Service endpoints
kubectl get endpoints -n finopsguard finopsguard -o json | jq '.subsets[].addresses | length' | grep -qv "^0$" || echo "FAILED"

# HPA status
kubectl get hpa -n finopsguard finopsguard -o json | jq '.status.currentReplicas' | grep -qv "^0$" || echo "FAILED"
```

---

## Rollback Plan

### Docker Compose
```bash
# Stop current version
docker-compose down

# Restore previous configuration
git checkout HEAD~1 docker-compose.yml env.example

# Restore previous image
docker pull finopsguard:previous-version
docker tag finopsguard:previous-version finopsguard:latest

# Restart
docker-compose up -d
```

### Kubernetes
```bash
# Rollback deployment
kubectl rollout undo deployment/finopsguard -n finopsguard

# Or rollback to specific revision
kubectl rollout history deployment/finopsguard -n finopsguard
kubectl rollout undo deployment/finopsguard --to-revision=<N> -n finopsguard

# Verify rollback
kubectl rollout status deployment/finopsguard -n finopsguard
```

---

## Troubleshooting

### Common Issues

**Issue: Service not starting**
- Check logs: `docker-compose logs` or `kubectl logs -n finopsguard -l app=finopsguard`
- Verify port availability
- Check resource constraints
- Review configuration

**Issue: High memory/CPU usage**
- Reduce worker count (`WORKERS` env var)
- Increase resource limits
- Enable caching
- Review policy complexity

**Issue: Slow responses**
- Check network connectivity
- Enable Redis caching
- Increase workers
- Review resource allocation

**Issue: Authentication failures**
- Verify secrets are properly set
- Check token expiration
- Review API key configuration

---

## Support

- **Documentation**: [docs/deployment.md](../docs/deployment.md)
- **Quick Start**: [deploy/QUICK_START.md](QUICK_START.md)
- **CI/CD Guide**: [docs/cicd-integration.md](../docs/cicd-integration.md)
- **Makefile**: Run `make help` for available commands
- **API Docs**: http://localhost:8080/docs

---

## Sign-Off

- [ ] All deployment steps completed successfully
- [ ] All verification tests passed
- [ ] Monitoring and alerting configured
- [ ] Team members notified and trained
- [ ] Documentation updated
- [ ] Rollback plan tested and documented

**Deployed by**: _________________  
**Date**: _________________  
**Version**: v0.2.0  
**Environment**: _________________  

---

**Deployment Status**: ⬜ In Progress | ⬜ Completed | ⬜ Failed

**Notes**:
```
[Add any deployment-specific notes, issues encountered, or customizations made]
```

