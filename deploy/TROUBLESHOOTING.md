# FinOpsGuard Troubleshooting Guide

Common issues and their solutions when deploying FinOpsGuard.

## Docker Compose Issues

### Port Already Allocated

**Error:**
```
Error response from daemon: failed to set up container networking: 
driver failed programming external connectivity on endpoint finopsguard: 
Bind for 0.0.0.0:8080 failed: port is already allocated
```

**Cause:** Port 8080 (or another required port) is already in use by another container or process.

**Solutions:**

1. **Stop existing containers:**
   ```bash
   docker-compose down
   
   # If running with profiles
   docker-compose --profile monitoring --profile caching down
   ```

2. **Check for duplicate port definitions in .env:**
   ```bash
   # Look for duplicate PORT variables
   grep -E "PORT=" .env | sort
   
   # Fix: Remove or comment out duplicates
   # Each port should only be defined once
   ```

3. **Check what's using the port:**
   ```bash
   # macOS/Linux
   lsof -i :8080
   
   # Kill the process (if safe to do so)
   lsof -ti :8080 | xargs kill -9
   ```

4. **Change the port in .env:**
   ```bash
   # Edit .env file
   FINOPS_PORT=8081  # Use a different port
   
   # Restart
   docker-compose down && docker-compose up -d
   ```

---

### Container Keeps Restarting

**Symptom:** Container status shows "Restarting" or "Unhealthy"

**Diagnosis:**
```bash
# Check container status
docker ps -a | grep finopsguard

# View logs
docker logs finopsguard --tail 50

# Follow logs in real-time
docker logs finopsguard -f
```

**Common Causes:**

1. **Missing static directory:**
   ```
   RuntimeError: Directory 'static' does not exist
   ```
   
   **Fix:** Ensure Dockerfile includes:
   ```dockerfile
   COPY static/ ./static/
   ```
   
   Rebuild: `docker-compose build --no-cache`

2. **Missing environment variables:**
   ```bash
   # Check if .env exists
   ls -la .env
   
   # If not, copy from example
   cp env.example .env
   ```

3. **Port conflict (see above)**

4. **Insufficient resources:**
   ```bash
   # Check Docker resource limits
   docker stats finopsguard
   
   # Increase limits in docker-compose.yml if needed
   ```

---

### Health Check Failing

**Error:** `curl http://localhost:8080/healthz` returns error or times out

**Solutions:**

1. **Wait for startup:**
   ```bash
   # Container may still be starting
   docker ps | grep finopsguard  # Check status
   sleep 10  # Wait a bit
   curl http://localhost:8080/healthz
   ```

2. **Check container logs:**
   ```bash
   docker logs finopsguard
   ```

3. **Verify container is running:**
   ```bash
   docker ps | grep finopsguard
   # Should show "Up" status, not "Restarting"
   ```

4. **Check port mapping:**
   ```bash
   docker ps | grep finopsguard
   # Should show: 0.0.0.0:8080->8080/tcp
   ```

5. **Test from inside container:**
   ```bash
   docker exec finopsguard curl http://localhost:8080/healthz
   ```

---

### Network Errors

**Error:** `Network finopsguard_finopsguard-network Resource is still in use`

**Solution:**
```bash
# Force remove all containers using the network
docker-compose down --remove-orphans

# Or manually remove the network
docker network rm finopsguard_finopsguard-network

# Then restart
docker-compose up -d
```

---

### Permission Denied

**Error:** Permission errors when accessing volumes or files

**Solution:**
```bash
# Fix ownership of volumes
docker-compose down
sudo chown -R $(whoami):$(whoami) .

# Or run with sudo (not recommended for production)
sudo docker-compose up -d
```

---

### Build Failures

**Error:** Docker build fails

**Solutions:**

1. **Clear Docker cache:**
   ```bash
   docker-compose build --no-cache
   ```

2. **Clean up Docker system:**
   ```bash
   docker system prune -a
   docker volume prune
   ```

3. **Check disk space:**
   ```bash
   df -h
   docker system df
   ```

---

## Kubernetes Issues

### ImagePullBackOff

**Error:** Pods show `ImagePullBackOff` status

**Diagnosis:**
```bash
kubectl describe pod -n finopsguard -l app=finopsguard
```

**Solutions:**

1. **Image doesn't exist:**
   ```bash
   # Build and push image
   docker build -t your-registry/finopsguard:v0.2.0 .
   docker push your-registry/finopsguard:v0.2.0
   ```

2. **Missing image pull secret:**
   ```bash
   # Create secret for private registry
   kubectl create secret docker-registry regcred \
     --docker-server=your-registry \
     --docker-username=your-username \
     --docker-password=your-password \
     -n finopsguard
   
   # Add to deployment.yaml
   spec:
     imagePullSecrets:
     - name: regcred
   ```

3. **Wrong image name:**
   ```bash
   # Check deployment
   kubectl get deployment -n finopsguard finopsguard -o yaml | grep image:
   
   # Update if needed
   kubectl set image deployment/finopsguard \
     finopsguard=your-registry/finopsguard:v0.2.0 \
     -n finopsguard
   ```

---

### CrashLoopBackOff

**Error:** Pods in `CrashLoopBackOff` state

**Diagnosis:**
```bash
# Check logs
kubectl logs -n finopsguard -l app=finopsguard --tail=100

# Check events
kubectl get events -n finopsguard --sort-by='.lastTimestamp'

# Describe pod
kubectl describe pod -n finopsguard -l app=finopsguard
```

**Solutions:**

1. **Application errors:** Fix based on logs

2. **Missing ConfigMap/Secret:**
   ```bash
   # Check resources exist
   kubectl get configmap,secret -n finopsguard
   
   # Apply if missing
   kubectl apply -f deploy/kubernetes/configmap.yaml
   kubectl apply -f deploy/kubernetes/secret.yaml
   ```

3. **Resource limits too low:**
   ```bash
   # Check resource usage
   kubectl top pods -n finopsguard
   
   # Increase limits in deployment.yaml
   ```

---

### Service Not Accessible

**Error:** Cannot access service externally

**Diagnosis:**
```bash
# Check service
kubectl get svc -n finopsguard

# Check endpoints
kubectl get endpoints -n finopsguard finopsguard

# Check ingress (if used)
kubectl get ingress -n finopsguard
kubectl describe ingress -n finopsguard
```

**Solutions:**

1. **Port forward for testing:**
   ```bash
   kubectl port-forward -n finopsguard svc/finopsguard 8080:8080
   curl http://localhost:8080/healthz
   ```

2. **Check LoadBalancer:**
   ```bash
   # Wait for external IP
   kubectl get svc -n finopsguard -w
   
   # Get external IP
   EXTERNAL_IP=$(kubectl get svc -n finopsguard finopsguard-loadbalancer -o jsonpath='{.status.loadBalancer.ingress[0].ip}')
   curl http://$EXTERNAL_IP/healthz
   ```

3. **Check Ingress controller:**
   ```bash
   # Verify ingress controller is installed
   kubectl get pods -n ingress-nginx
   
   # Check ingress rules
   kubectl describe ingress -n finopsguard
   ```

---

### Pods Not Ready

**Error:** Pods show "0/1 READY" status

**Diagnosis:**
```bash
# Check readiness probe
kubectl describe pod -n finopsguard -l app=finopsguard | grep -A5 "Readiness"

# Check logs
kubectl logs -n finopsguard -l app=finopsguard
```

**Solutions:**

1. **Application not starting:**
   ```bash
   # Increase initialDelaySeconds in deployment.yaml
   readinessProbe:
     initialDelaySeconds: 30  # Increase this
   ```

2. **Health endpoint failing:**
   ```bash
   # Test from pod
   kubectl exec -it -n finopsguard \
     $(kubectl get pod -n finopsguard -l app=finopsguard -o name | head -1) \
     -- curl http://localhost:8080/healthz
   ```

---

## Application Issues

### API Returns 500 Errors

**Diagnosis:**
```bash
# Check logs
docker logs finopsguard --tail=100
# or
kubectl logs -n finopsguard -l app=finopsguard --tail=100
```

**Common Causes:**

1. **Missing dependencies:** Check requirements.txt is complete
2. **Configuration errors:** Verify environment variables
3. **Static files missing:** Ensure static/ directory is copied in Dockerfile

---

### Slow Performance

**Diagnosis:**
```bash
# Check resource usage
docker stats finopsguard
# or
kubectl top pods -n finopsguard
```

**Solutions:**

1. **Increase worker count:**
   ```bash
   # In .env or ConfigMap
   WORKERS=8  # Increase based on CPU cores
   ```

2. **Enable caching:**
   ```bash
   # Docker Compose
   docker-compose --profile caching up -d
   ```

3. **Increase resources:**
   ```yaml
   # In docker-compose.yml or deployment.yaml
   resources:
     limits:
       cpu: "4.0"
       memory: 4Gi
   ```

---

### Admin UI Not Loading

**Symptoms:** Blank page or 404 errors at http://localhost:8080/

**Solutions:**

1. **Check static files are copied:**
   ```bash
   # Docker
   docker exec finopsguard ls -la /app/static/
   
   # Should show: css/, js/, index.html
   ```

2. **Check logs for errors:**
   ```bash
   docker logs finopsguard | grep static
   ```

3. **Rebuild with static files:**
   ```bash
   # Ensure Dockerfile has:
   # COPY static/ ./static/
   
   docker-compose build --no-cache
   docker-compose up -d
   ```

---

## Debugging Commands

### Docker Compose

```bash
# View all logs
docker-compose logs -f

# View specific service logs
docker-compose logs -f finopsguard

# Check configuration
docker-compose config

# Validate docker-compose.yml
docker-compose config --quiet

# Shell into container
docker exec -it finopsguard /bin/bash

# Check environment variables
docker exec finopsguard env

# Restart specific service
docker-compose restart finopsguard

# Rebuild and restart
docker-compose up -d --build
```

### Kubernetes

```bash
# Get all resources
kubectl get all -n finopsguard

# Describe deployment
kubectl describe deployment -n finopsguard finopsguard

# Get detailed pod info
kubectl describe pod -n finopsguard -l app=finopsguard

# Shell into pod
kubectl exec -it -n finopsguard \
  $(kubectl get pod -n finopsguard -l app=finopsguard -o name | head -1) \
  -- /bin/bash

# Check environment variables
kubectl exec -n finopsguard \
  $(kubectl get pod -n finopsguard -l app=finopsguard -o name | head -1) \
  -- env

# View events
kubectl get events -n finopsguard --sort-by='.lastTimestamp' | tail -20

# Check resource usage
kubectl top pods -n finopsguard
kubectl top nodes
```

---

## Getting Help

If you're still experiencing issues:

1. **Check logs:** Always start with application logs
2. **Review configuration:** Verify environment variables and config files
3. **Check documentation:** 
   - [Deployment Guide](../docs/deployment.md)
   - [Quick Start](./QUICK_START.md)
   - [README](../README.md)
4. **Search issues:** Check GitHub Issues for similar problems
5. **Create an issue:** Provide logs, configuration, and steps to reproduce

---

## Quick Reset

If all else fails, complete reset:

### Docker Compose
```bash
# Stop everything
docker-compose --profile monitoring --profile caching down -v

# Clean up
docker system prune -a
docker volume prune

# Remove .env and recreate
rm .env
cp env.example .env
# Edit .env as needed

# Rebuild and start
docker-compose build --no-cache
docker-compose up -d
```

### Kubernetes
```bash
# Delete everything
kubectl delete namespace finopsguard

# Reapply
kubectl apply -f deploy/kubernetes/namespace.yaml
kubectl apply -f deploy/kubernetes/configmap.yaml
kubectl apply -f deploy/kubernetes/secret.yaml
kubectl apply -f deploy/kubernetes/deployment.yaml
kubectl apply -f deploy/kubernetes/service.yaml
```

