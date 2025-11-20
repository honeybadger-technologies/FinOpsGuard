# FinOpsGuard Deployment Guide

This guide covers deploying FinOpsGuard using Docker Compose and Kubernetes.

## Table of Contents

- [Docker Compose Deployment](#docker-compose-deployment)
- [Kubernetes Deployment](#kubernetes-deployment)
- [Production Considerations](#production-considerations)
- [Monitoring Setup](#monitoring-setup)
- [Troubleshooting](#troubleshooting)

---

## Docker Compose Deployment

Docker Compose is ideal for development, testing, and small-scale production deployments.

### Prerequisites

- Docker 20.10+
- Docker Compose 2.0+
- 2GB+ available RAM
- Port 8080 available (or configure a different port)

### Quick Start

1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd FinOpsGuard
   ```

2. **Create environment configuration:**
   ```bash
   cp env.example .env
   # Edit .env with your preferred settings
   vim .env
   ```

3. **Start FinOpsGuard:**
   ```bash
   # Basic deployment (FinOpsGuard only)
   docker-compose up -d

   # With monitoring stack (Prometheus + Grafana)
   docker-compose --profile monitoring up -d

   # With caching (Redis)
   docker-compose --profile caching up -d

   # Full stack
   docker-compose --profile monitoring --profile caching up -d
   ```

4. **Verify deployment:**
   ```bash
   # Check service health
   curl http://localhost:8080/healthz

   # Check cache status (if caching profile enabled)
   curl http://localhost:8080/mcp/cache/info

   # View logs
   docker-compose logs -f finopsguard

   # Access Admin UI
   open http://localhost:8080/

   # Access API documentation
   open http://localhost:8080/docs
   ```

### Docker Compose Profiles

FinOpsGuard supports multiple deployment profiles:

- **Default**: Core FinOpsGuard API only
- **monitoring**: Adds Prometheus (port 9090) and Grafana (port 3000)
- **caching**: Adds Redis (port 6379) for intelligent caching
  - Pricing data cached for 24 hours
  - Analysis results cached for 1 hour
  - 10-100x performance improvement for repeated operations

### Managing the Deployment

```bash
# View running services
docker-compose ps

# Stop services
docker-compose down

# Stop and remove volumes
docker-compose down -v

# Rebuild containers
docker-compose build --no-cache

# View resource usage
docker stats finopsguard

# Update to latest version
git pull
docker-compose pull
docker-compose up -d
```

### Environment Variables

Key environment variables (see `env.example` for full list):

| Variable | Default | Description |
|----------|---------|-------------|
| `FINOPS_PORT` | 8080 | Host port for API |
| `APP_ENV` | production | Environment (development/production) |
| `LOG_LEVEL` | info | Logging level (debug/info/warning/error) |
| `WORKERS` | 4 | Number of worker processes |
| `DEFAULT_BUDGET` | 1000 | Default monthly budget (USD) |
| `ENABLE_BLOCKING` | true | Enable policy blocking mode |
| `REDIS_ENABLED` | false | Enable Redis caching |
| `REDIS_HOST` | redis | Redis host |
| `REDIS_PORT` | 6379 | Redis port |
| `REDIS_DB` | 0 | Redis database index (standalone) |
| `REDIS_CLUSTER_ENABLED` | false | Enable Redis Cluster mode |
| `REDIS_CLUSTER_NODES` | _(empty)_ | Comma-separated `host:port` list for cluster |
| `AWS_REGION` | us-east-1 | Default AWS region |
| `GCP_REGION` | us-central1 | Default GCP region |

### Access Services

After deployment:

- **FinOpsGuard API**: http://localhost:8080
- **Admin UI**: http://localhost:8080/
- **API Docs**: http://localhost:8080/docs
- **Metrics**: http://localhost:8080/metrics
- **Cache Info**: http://localhost:8080/mcp/cache/info
- **Prometheus**: http://localhost:9090 (monitoring profile)
- **Grafana**: http://localhost:3000 (monitoring profile, admin/changeme)
- **Redis**: localhost:6379 (caching profile)

---

## Kubernetes Deployment

Kubernetes deployment is recommended for production environments requiring high availability and scalability.

### Prerequisites

- Kubernetes 1.24+
- kubectl configured
- 4GB+ available cluster resources
- (Optional) Helm 3.0+
- (Optional) Ingress controller (nginx/traefik/AWS ALB/GCP Ingress)
- (Optional) cert-manager for TLS

### Quick Start

1. **Build and push Docker image:**
   ```bash
   # Build image
   docker build -t your-registry/finopsguard:v0.2.0 .

   # Push to registry (Docker Hub, ECR, GCR, etc.)
   docker push your-registry/finopsguard:v0.2.0
   ```

2. **Update image in deployment:**
   ```bash
   # Edit deploy/kubernetes/deployment.yaml
   # Change: image: finopsguard:latest
   # To: image: your-registry/finopsguard:v0.2.0
   ```

3. **Deploy to Kubernetes:**
   ```bash
   # Create namespace and resources
   kubectl apply -f deploy/kubernetes/namespace.yaml
   kubectl apply -f deploy/kubernetes/configmap.yaml
   kubectl apply -f deploy/kubernetes/secret.yaml
   kubectl apply -f deploy/kubernetes/deployment.yaml
   kubectl apply -f deploy/kubernetes/service.yaml
   
   # Optional: High availability features
   kubectl apply -f deploy/kubernetes/hpa.yaml
   kubectl apply -f deploy/kubernetes/pdb.yaml
   
   # Optional: Ingress (configure host first)
   kubectl apply -f deploy/kubernetes/ingress.yaml
   
   # Optional: Prometheus monitoring
   kubectl apply -f deploy/kubernetes/servicemonitor.yaml
   ```

4. **Verify deployment:**
   ```bash
   # Check pod status
   kubectl get pods -n finopsguard
   
   # View logs
   kubectl logs -n finopsguard -l app=finopsguard -f
   
   # Check service
   kubectl get svc -n finopsguard
   
   # Port forward for testing
   kubectl port-forward -n finopsguard svc/finopsguard 8080:8080
   
   # Test health endpoint
   curl http://localhost:8080/healthz
   ```

### Kubernetes Resources

The deployment includes:

- **Namespace**: `finopsguard` - Isolated namespace
- **ConfigMap**: Environment configuration
- **Secret**: Sensitive credentials (API keys, tokens)
- **Deployment**: 3 replicas with rolling updates
- **Service**: ClusterIP and LoadBalancer options
- **Ingress**: External access with TLS support
- **HPA**: Horizontal Pod Autoscaler (3-10 pods)
- **PDB**: Pod Disruption Budget (min 2 available)
- **ServiceMonitor**: Prometheus metrics scraping

### Configuration

#### ConfigMap

Edit `deploy/kubernetes/configmap.yaml` to customize:
- Application settings
- Policy engine defaults
- Cloud provider regions
- Logging and metrics

#### Secrets

Edit `deploy/kubernetes/secret.yaml` to add:
- GitHub/GitLab tokens for PR/MR commenting
- API keys for authentication
- Cloud provider credentials (if needed)

```bash
# Create secrets from files
kubectl create secret generic finopsguard-secrets \
  --from-literal=GITHUB_TOKEN=ghp_xxxxx \
  --from-literal=GITLAB_TOKEN=glpat_xxxxx \
  -n finopsguard
```

#### Ingress Configuration

Edit `deploy/kubernetes/ingress.yaml`:

1. **Set your domain:**
   ```yaml
   rules:
   - host: finopsguard.yourdomain.com
   ```

2. **Choose ingress controller:**
   - Nginx (default)
   - AWS ALB (uncomment AWS annotations)
   - GCP Ingress (uncomment GCP annotations)

3. **Configure TLS:**
   ```bash
   # Using cert-manager
   kubectl apply -f - <<EOF
   apiVersion: cert-manager.io/v1
   kind: Certificate
   metadata:
     name: finopsguard-tls
     namespace: finopsguard
   spec:
     secretName: finopsguard-tls
     issuerRef:
       name: letsencrypt-prod
       kind: ClusterIssuer
     dnsNames:
     - finopsguard.yourdomain.com
   EOF
   ```

### Scaling

#### Manual Scaling
```bash
# Scale deployment
kubectl scale deployment finopsguard -n finopsguard --replicas=5

# Check status
kubectl get hpa -n finopsguard
```

#### Auto-scaling (HPA)

The HPA automatically scales between 3-10 pods based on:
- CPU utilization: 70% target
- Memory utilization: 80% target

Configure in `deploy/kubernetes/hpa.yaml`.

### Updates and Rollbacks

```bash
# Update image
kubectl set image deployment/finopsguard \
  finopsguard=your-registry/finopsguard:v0.3.0 \
  -n finopsguard

# Check rollout status
kubectl rollout status deployment/finopsguard -n finopsguard

# View rollout history
kubectl rollout history deployment/finopsguard -n finopsguard

# Rollback to previous version
kubectl rollout undo deployment/finopsguard -n finopsguard

# Rollback to specific revision
kubectl rollout undo deployment/finopsguard --to-revision=2 -n finopsguard
```

### Resource Management

#### View Resource Usage
```bash
# Pod resource usage
kubectl top pods -n finopsguard

# Node resource usage
kubectl top nodes

# Describe pod for details
kubectl describe pod -n finopsguard -l app=finopsguard
```

#### Adjust Resource Limits

Edit `deploy/kubernetes/deployment.yaml`:
```yaml
resources:
  requests:
    cpu: 500m      # Minimum CPU
    memory: 512Mi  # Minimum memory
  limits:
    cpu: 2000m     # Maximum CPU
    memory: 2Gi    # Maximum memory
```

---

## Production Considerations

### High Availability

1. **Multi-replica Deployment:**
   - Minimum 3 replicas for redundancy
   - Pod anti-affinity for zone distribution
   - Pod Disruption Budget (min 2 available)

2. **Health Checks:**
   - Liveness probe: Restart unhealthy pods
   - Readiness probe: Remove from load balancer

3. **Rolling Updates:**
   - Zero-downtime deployments
   - maxSurge: 1, maxUnavailable: 0

### Security

1. **Secrets Management:**
   ```bash
   # Use Kubernetes secrets
   kubectl create secret generic finopsguard-secrets \
     --from-file=github-token=./token.txt \
     -n finopsguard
   
   # Or use external secret managers (AWS Secrets Manager, GCP Secret Manager)
   ```

2. **Network Policies:**
   ```yaml
   apiVersion: networking.k8s.io/v1
   kind: NetworkPolicy
   metadata:
     name: finopsguard
     namespace: finopsguard
   spec:
     podSelector:
       matchLabels:
         app: finopsguard
     policyTypes:
     - Ingress
     - Egress
     ingress:
     - from:
       - namespaceSelector:
           matchLabels:
             name: ingress-nginx
       ports:
       - protocol: TCP
         port: 8080
   ```

3. **RBAC:**
   ```bash
   # Create service account with minimal permissions
   kubectl create serviceaccount finopsguard -n finopsguard
   ```

4. **Security Context:**
   - Run as non-root user (UID 1000)
   - Read-only root filesystem (future)

### Monitoring and Observability

1. **Prometheus Metrics:**
   - Request rates and latencies
   - Error rates
   - Policy evaluation metrics
   - Cost analysis metrics

2. **Logging:**
   ```bash
   # Stream logs
   kubectl logs -n finopsguard -l app=finopsguard -f
   
   # Export logs to external system (e.g., ELK, Loki)
   # Configure via fluentd/fluent-bit daemonset
   ```

3. **Alerting:**
   - High error rates
   - Pod restarts
   - High memory/CPU usage
   - Policy violations

### Backup and Recovery

1. **Configuration Backup:**
   ```bash
   # Export ConfigMaps and Secrets
   kubectl get configmap -n finopsguard -o yaml > backup-configmap.yaml
   kubectl get secret -n finopsguard -o yaml > backup-secret.yaml
   ```

2. **Policy Backup:**
   ```bash
   # Export policies via API
   curl -sS http://finopsguard/mcp/policies > policies-backup.json
   ```

### Performance Tuning

1. **Worker Processes:**
   - Adjust `WORKERS` env var based on CPU cores
   - Formula: `WORKERS = (2 * CPU_CORES) + 1`

2. **Resource Requests/Limits:**
   - Monitor actual usage with `kubectl top`
   - Adjust based on workload

3. **Caching (Future):**
   - Enable Redis for pricing data caching
   - Reduce API calls and improve response times

---

## Monitoring Setup

### Prometheus + Grafana (Docker Compose)

1. **Start monitoring stack:**
   ```bash
   docker-compose --profile monitoring up -d
   ```

2. **Access Grafana:**
   ```
   URL: http://localhost:3000
   Username: admin
   Password: changeme (from env.example)
   ```

3. **Import dashboards:**
   - Prometheus datasource is auto-configured
   - Create custom dashboards for cost metrics

### Prometheus Operator (Kubernetes)

1. **Install Prometheus Operator:**
   ```bash
   # Using Helm
   helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
   helm install prometheus prometheus-community/kube-prometheus-stack \
     -n monitoring --create-namespace
   ```

2. **Apply ServiceMonitor:**
   ```bash
   kubectl apply -f deploy/kubernetes/servicemonitor.yaml
   ```

3. **Access Grafana:**
   ```bash
   kubectl port-forward -n monitoring svc/prometheus-grafana 3000:80
   ```

### Key Metrics

Monitor these metrics in production:

- `finopsguard_requests_total` - Total API requests
- `finopsguard_request_duration_seconds` - Request latency
- `finopsguard_policy_evaluations_total` - Policy evaluations
- `finopsguard_cost_analyses_total` - Cost analyses performed
- `finopsguard_errors_total` - Error count

---

## Troubleshooting

### Common Issues

#### Docker Compose

**Issue: Port already in use**
```bash
# Solution: Change port in .env
echo "FINOPS_PORT=8081" >> .env
docker-compose up -d
```

**Issue: Container won't start**
```bash
# Check logs
docker-compose logs finopsguard

# Rebuild image
docker-compose build --no-cache
docker-compose up -d
```

#### Kubernetes

**Issue: Pods in CrashLoopBackOff**
```bash
# Check pod logs
kubectl logs -n finopsguard -l app=finopsguard --tail=100

# Describe pod for events
kubectl describe pod -n finopsguard -l app=finopsguard

# Check resource constraints
kubectl top pods -n finopsguard
```

**Issue: ImagePullBackOff**
```bash
# Verify image exists
docker pull your-registry/finopsguard:v0.2.0

# Check image pull secrets
kubectl get secrets -n finopsguard

# Create image pull secret if needed
kubectl create secret docker-registry regcred \
  --docker-server=your-registry \
  --docker-username=your-username \
  --docker-password=your-password \
  -n finopsguard
```

**Issue: Service not accessible**
```bash
# Check service endpoints
kubectl get endpoints -n finopsguard

# Test from within cluster
kubectl run -it --rm debug --image=curlimages/curl --restart=Never -- \
  curl http://finopsguard.finopsguard.svc.cluster.local:8080/healthz

# Check ingress
kubectl describe ingress -n finopsguard
```

### Health Check Failures

1. **Check application logs:**
   ```bash
   docker-compose logs finopsguard
   # or
   kubectl logs -n finopsguard -l app=finopsguard
   ```

2. **Verify port binding:**
   ```bash
   netstat -tuln | grep 8080
   ```

3. **Test health endpoint:**
   ```bash
   curl -v http://localhost:8080/healthz
   ```

### Performance Issues

1. **High CPU usage:**
   - Increase CPU limits
   - Reduce number of workers
   - Check for infinite loops in logs

2. **High memory usage:**
   - Increase memory limits
   - Check for memory leaks in logs
   - Monitor with `kubectl top` or `docker stats`

3. **Slow responses:**
   - Enable caching (Redis profile)
   - Increase worker count
   - Check network latency

### Getting Help

- Check application logs for detailed error messages
- Review metrics in Prometheus/Grafana
- Consult the [GitHub Issues](https://github.com/your-org/finopsguard/issues)
- Review [API documentation](http://localhost:8080/docs)

---

## Next Steps

- **Configure policies**: Use Admin UI or API to create custom policies
- **Integrate with CI/CD**: See [CI/CD Integration Guide](./cicd-integration.md)
- **Set up monitoring**: Configure alerts and dashboards
- **Enable authentication**: Add API keys or OAuth (future)
- **Scale for production**: Adjust replicas and resources based on load

For more information, see:
- [Architecture Documentation](./architecture.md)
- [Requirements Document](./requirements.md)
- [CI/CD Integration Guide](./cicd-integration.md)

