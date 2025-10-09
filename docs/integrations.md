# FinOpsGuard Integration Guide

This guide provides detailed examples for integrating FinOpsGuard with various tools and platforms.

## Table of Contents

- [MCP Agent Overview](#mcp-agent-overview)
- [REST API Integration](#rest-api-integration)
- [Python SDK](#python-sdk)
- [CI/CD Platforms](#cicd-platforms)
- [GitOps Tools](#gitops-tools)
- [Monitoring & Observability](#monitoring--observability)
- [Custom Integrations](#custom-integrations)
- [Best Practices](#best-practices)

---

## MCP Agent Overview

FinOpsGuard is an MCP (Model Context Protocol) agent that provides cost-aware guardrails for infrastructure changes. It exposes standard MCP endpoints via REST API that can be consumed by any tool or platform.

### Core MCP Methods

| Method | Endpoint | Purpose |
|--------|----------|---------|
| `checkCostImpact` | `POST /mcp/checkCostImpact` | Analyze cost impact of IaC changes |
| `evaluatePolicy` | `POST /mcp/evaluatePolicy` | Evaluate specific policy |
| `suggestOptimizations` | `POST /mcp/suggestOptimizations` | Get cost optimization suggestions |
| `getPriceCatalog` | `POST /mcp/getPriceCatalog` | Retrieve cloud pricing data |
| `listRecentAnalyses` | `POST /mcp/listRecentAnalyses` | List historical analyses |

### MCP Compliance

- ✅ Stateless request/response model
- ✅ JSON-based payloads
- ✅ Standard HTTP/REST protocol
- ✅ Async-capable operations
- ✅ Comprehensive error handling
- ✅ OpenAPI 3.0 specification

---

## REST API Integration

### Direct API Calls

Use any HTTP client to interact with FinOpsGuard:

**cURL Example:**
```bash
# Prepare Terraform payload
PAYLOAD=$(cat main.tf | base64)

# Check cost impact
curl -X POST http://finopsguard:8080/mcp/checkCostImpact \
  -H 'Content-Type: application/json' \
  -d "{
    \"iac_type\": \"terraform\",
    \"iac_payload\": \"$PAYLOAD\",
    \"environment\": \"prod\",
    \"budget_rules\": {\"monthly_budget\": 1000}
  }"
```

**Response:**
```json
{
  "estimated_monthly_cost": 243.50,
  "estimated_first_week_cost": 56.25,
  "breakdown_by_resource": [...],
  "risk_flags": [],
  "recommendations": [...],
  "policy_eval": {
    "status": "pass",
    "policy_id": "all_policies",
    "reason": "All policies satisfied"
  },
  "pricing_confidence": "high",
  "duration_ms": 45
}
```

### JavaScript/Node.js Example

```javascript
const axios = require('axios');
const fs = require('fs');

async function analyzeCost(tfFile, budget) {
    const tfContent = fs.readFileSync(tfFile, 'utf8');
    const payload = Buffer.from(tfContent).toString('base64');
    
    const response = await axios.post(
        'http://finopsguard:8080/mcp/checkCostImpact',
        {
            iac_type: 'terraform',
            iac_payload: payload,
            environment: 'prod',
            budget_rules: { monthly_budget: budget }
        }
    );
    
    const result = response.data;
    console.log(`Monthly Cost: $${result.estimated_monthly_cost}`);
    
    if (result.risk_flags.includes('over_budget')) {
        console.error('❌ Budget exceeded!');
        process.exit(1);
    }
    
    return result;
}

// Usage
analyzeCost('infrastructure/main.tf', 1000);
```

---

## Python SDK

### Using the CLI Module as Library

```python
from finopsguard.cli.main import FinOpsGuardCLI
import sys

# Initialize client
client = FinOpsGuardCLI(api_url="http://finopsguard:8080")

# Check cost impact
result = client.check_cost(
    file_path="main.tf",
    environment="prod",
    budget=1000
)

# Handle result
if result.get('risk_flags') and 'over_budget' in result['risk_flags']:
    print(f"❌ Over budget: ${result['estimated_monthly_cost']:.2f}")
    sys.exit(1)
else:
    print(f"✅ Within budget: ${result['estimated_monthly_cost']:.2f}")
```

### Direct API Client

```python
import httpx
import base64
from pathlib import Path

class FinOpsClient:
    def __init__(self, base_url: str):
        self.client = httpx.Client(base_url=base_url, timeout=30.0)
    
    def check_cost(self, tf_file: str, environment: str = "dev", budget: float = None):
        """Check cost impact of Terraform file."""
        content = Path(tf_file).read_text()
        payload = base64.b64encode(content.encode()).decode()
        
        request = {
            "iac_type": "terraform",
            "iac_payload": payload,
            "environment": environment
        }
        
        if budget:
            request["budget_rules"] = {"monthly_budget": budget}
        
        response = self.client.post("/mcp/checkCostImpact", json=request)
        response.raise_for_status()
        return response.json()
    
    def list_policies(self):
        """List all policies."""
        response = self.client.get("/mcp/policies")
        response.raise_for_status()
        return response.json()
    
    def get_pricing(self, cloud: str, region: str = None):
        """Get pricing catalog."""
        request = {"cloud": cloud}
        if region:
            request["region"] = region
        
        response = self.client.post("/mcp/getPriceCatalog", json=request)
        response.raise_for_status()
        return response.json()

# Usage
client = FinOpsClient("http://finopsguard:8080")
cost_analysis = client.check_cost("main.tf", environment="prod", budget=1000)
policies = client.list_policies()
pricing = client.get_pricing("aws", region="us-east-1")
```

---

## CI/CD Platforms

### GitHub Actions

**Option 1: Pre-built Workflow**

Copy `.github/workflows/finopsguard-check.yml` to your repository and customize:

```yaml
name: Cost Check
on: [pull_request]

jobs:
  cost-analysis:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: FinOpsGuard Cost Check
        env:
          FINOPSGUARD_URL: ${{ secrets.FINOPSGUARD_URL }}
        run: |
          ./scripts/finopsguard-cicd.sh \
            --environment ${{ github.ref == 'refs/heads/main' && 'prod' || 'dev' }} \
            --budget 1000 \
            --format github
```

**Option 2: Custom Action**

```yaml
- name: Analyze Infrastructure Cost
  id: cost-check
  run: |
    PAYLOAD=$(base64 -w0 terraform/main.tf)
    RESULT=$(curl -X POST ${{ secrets.FINOPSGUARD_URL }}/mcp/checkCostImpact \
      -H 'Content-Type: application/json' \
      -d "{
        \"iac_type\": \"terraform\",
        \"iac_payload\": \"$PAYLOAD\",
        \"environment\": \"prod\",
        \"budget_rules\": {\"monthly_budget\": 1000}
      }")
    
    echo "cost_result=$RESULT" >> $GITHUB_OUTPUT
    
    # Check for violations
    if echo "$RESULT" | jq -e '.risk_flags[] | select(. == "policy_blocked")'; then
      echo "::error::Policy violation detected"
      exit 1
    fi

- name: Comment PR
  uses: actions/github-script@v7
  with:
    script: |
      const result = JSON.parse('${{ steps.cost-check.outputs.cost_result }}');
      const comment = `
      ## 💰 Cost Analysis
      
      **Estimated Monthly Cost:** $${result.estimated_monthly_cost.toFixed(2)}
      **First Week Cost:** $${result.estimated_first_week_cost.toFixed(2)}
      
      ${result.risk_flags.length > 0 ? '⚠️ **Risk Flags:** ' + result.risk_flags.join(', ') : '✅ No risks detected'}
      `;
      
      github.rest.issues.createComment({
        issue_number: context.issue.number,
        owner: context.repo.owner,
        repo: context.repo.repo,
        body: comment
      });
```

### GitLab CI

**Option 1: Include Template**

```yaml
include:
  - local: '.gitlab/ci-templates/finopsguard.yml'

cost-check:
  extends: .finopsguard-check
  stage: validate
  variables:
    ENVIRONMENT: $CI_COMMIT_BRANCH == "main" ? "prod" : "dev"
    BUDGET: "1000"
  rules:
    - if: $CI_PIPELINE_SOURCE == "merge_request_event"
    - if: $CI_COMMIT_BRANCH == "main"
```

**Option 2: Custom Job**

```yaml
cost-analysis:
  stage: validate
  image: curlimages/curl:latest
  script:
    - apk add --no-cache jq bash
    - |
      PAYLOAD=$(base64 -w0 terraform/main.tf)
      RESULT=$(curl -X POST $FINOPSGUARD_URL/mcp/checkCostImpact \
        -H 'Content-Type: application/json' \
        -d "{
          \"iac_type\": \"terraform\",
          \"iac_payload\": \"$PAYLOAD\",
          \"environment\": \"$ENVIRONMENT\"
        }")
      
      # Save result
      echo "$RESULT" > cost-report.json
      
      # Check for violations
      if echo "$RESULT" | jq -e '.risk_flags[] | select(. == "policy_blocked")'; then
        echo "Cost policy violation"
        exit 1
      fi
  artifacts:
    reports:
      junit: cost-report.xml
    paths:
      - cost-report.json
```

### CircleCI

```yaml
version: 2.1

jobs:
  cost-check:
    docker:
      - image: cimg/python:3.11
    steps:
      - checkout
      
      - run:
          name: Install FinOpsGuard CLI
          command: |
            pip install httpx
            curl -O https://raw.githubusercontent.com/your-org/FinOpsGuard/main/src/finopsguard/cli/main.py
      
      - run:
          name: Analyze Cost
          command: |
            python main.py check-cost \
              --file terraform/main.tf \
              --environment prod \
              --budget 1000 \
              --output cost-report.json
      
      - store_artifacts:
          path: cost-report.json

workflows:
  version: 2
  build-and-test:
    jobs:
      - cost-check
```

### Azure DevOps

```yaml
trigger:
  - main

pool:
  vmImage: 'ubuntu-latest'

steps:
- task: Bash@3
  displayName: 'FinOpsGuard Cost Check'
  inputs:
    targetType: 'inline'
    script: |
      PAYLOAD=$(base64 -w0 terraform/main.tf)
      
      RESULT=$(curl -X POST $(FINOPSGUARD_URL)/mcp/checkCostImpact \
        -H 'Content-Type: application/json' \
        -d "{
          \"iac_type\": \"terraform\",
          \"iac_payload\": \"$PAYLOAD\",
          \"environment\": \"prod\",
          \"budget_rules\": {\"monthly_budget\": 1000}
        }")
      
      echo "Cost Analysis Result:"
      echo "$RESULT" | jq .
      
      # Check for violations
      if echo "$RESULT" | jq -e '.risk_flags[] | select(. == "policy_blocked")'; then
        echo "##vso[task.logissue type=error]Cost policy violation detected"
        exit 1
      fi
```

---

## GitOps Tools

### ArgoCD

**PreSync Hook for Cost Validation:**

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: finopsguard-presync-hook
  namespace: argocd
data:
  check-cost.sh: |
    #!/bin/bash
    set -e
    
    # Get the application manifests
    kubectl get app $ARGOCD_APP_NAME -n argocd -o json > app.json
    
    # Extract manifests and encode
    MANIFESTS=$(kubectl get app $ARGOCD_APP_NAME -n argocd -o jsonpath='{.spec.source}')
    PAYLOAD=$(echo "$MANIFESTS" | base64 -w0)
    
    # Call FinOpsGuard
    RESULT=$(curl -f -X POST $FINOPSGUARD_URL/mcp/checkCostImpact \
      -H 'Content-Type: application/json' \
      -d "{
        \"iac_type\": \"k8s\",
        \"iac_payload\": \"$PAYLOAD\",
        \"environment\": \"$ARGOCD_ENV_ENVIRONMENT\"
      }")
    
    # Parse result
    MONTHLY_COST=$(echo "$RESULT" | jq -r '.estimated_monthly_cost')
    echo "Estimated monthly cost: \$$MONTHLY_COST"
    
    # Check for blocking violations
    if echo "$RESULT" | jq -e '.risk_flags[] | select(. == "policy_blocked")'; then
      echo "❌ Cost policy violation - blocking deployment"
      exit 1
    fi
    
    echo "✅ Cost check passed"
---
apiVersion: batch/v1
kind: Job
metadata:
  generateName: finopsguard-presync-
  annotations:
    argocd.argoproj.io/hook: PreSync
    argocd.argoproj.io/hook-delete-policy: BeforeHookCreation
spec:
  template:
    spec:
      serviceAccountName: argocd-application-controller
      containers:
      - name: cost-check
        image: bitnami/kubectl:latest
        command: ["/bin/bash", "/scripts/check-cost.sh"]
        env:
        - name: FINOPSGUARD_URL
          value: "http://finopsguard.finopsguard.svc.cluster.local:8080"
        - name: ARGOCD_APP_NAME
          valueFrom:
            fieldRef:
              fieldPath: metadata.labels['app.kubernetes.io/instance']
        volumeMounts:
        - name: scripts
          mountPath: /scripts
      volumes:
      - name: scripts
        configMap:
          name: finopsguard-presync-hook
          defaultMode: 0755
      restartPolicy: Never
  backoffLimit: 1
```

### Flux CD

**Notification Provider:**

```yaml
apiVersion: notification.toolkit.fluxcd.io/v1beta1
kind: Provider
metadata:
  name: finopsguard
  namespace: flux-system
spec:
  type: generic
  address: http://finopsguard.finopsguard.svc.cluster.local:8080/mcp/checkCostImpact
---
apiVersion: notification.toolkit.fluxcd.io/v1beta1
kind: Alert
metadata:
  name: cost-check
  namespace: flux-system
spec:
  providerRef:
    name: finopsguard
  eventSeverity: info
  eventSources:
    - kind: Kustomization
      name: '*'
  suspend: false
```

---

## Monitoring & Observability

### Prometheus

**Scrape Configuration:**

```yaml
# prometheus.yml
scrape_configs:
  - job_name: 'finopsguard'
    static_configs:
      - targets: ['finopsguard:8080']
    metrics_path: '/metrics'
    scrape_interval: 30s
    scrape_timeout: 10s
```

**Alert Rules:**

```yaml
# alert-rules.yml
groups:
  - name: finopsguard
    interval: 1m
    rules:
      - alert: HighCostDetected
        expr: finops_checks_total{result="over_budget"} > 10
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High number of over-budget deployments"
          description: "{{ $value }} deployments exceeded budget in the last 5 minutes"
      
      - alert: PolicyBlocksIncreasing
        expr: rate(finops_blocks_total[5m]) > 1
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "Policy blocks increasing"
          description: "Policy blocks are occurring at {{ $value }} per second"
      
      - alert: CacheMissRateHigh
        expr: |
          (sum(rate(finops_cache_misses_total[5m])) / 
           (sum(rate(finops_cache_hits_total[5m])) + sum(rate(finops_cache_misses_total[5m])))) > 0.5
        for: 10m
        labels:
          severity: warning
        annotations:
          summary: "High cache miss rate"
          description: "Cache miss rate is {{ $value | humanizePercentage }}"
```

### Grafana Dashboards

**Cost Analysis Dashboard:**

```json
{
  "dashboard": {
    "title": "FinOpsGuard - Cost Analysis",
    "panels": [
      {
        "title": "Total Cost Checks",
        "targets": [{
          "expr": "sum(finops_checks_total)"
        }],
        "type": "stat"
      },
      {
        "title": "Average Cost per Check",
        "targets": [{
          "expr": "avg(finops_checks_duration_seconds)"
        }],
        "type": "gauge"
      },
      {
        "title": "Policy Blocks Over Time",
        "targets": [{
          "expr": "rate(finops_blocks_total[5m])"
        }],
        "type": "graph"
      },
      {
        "title": "Cache Hit Rate",
        "targets": [{
          "expr": "sum(finops_cache_hits_total) / (sum(finops_cache_hits_total) + sum(finops_cache_misses_total))"
        }],
        "type": "gauge"
      }
    ]
  }
}
```

### Datadog

**Custom Metric Integration:**

```python
from datadog import initialize, api
import requests

# Initialize Datadog
initialize(api_key='YOUR_API_KEY', app_key='YOUR_APP_KEY')

# Get FinOpsGuard metrics
response = requests.get('http://finopsguard:8080/metrics')
metrics_text = response.text

# Parse and send to Datadog
for line in metrics_text.split('\n'):
    if line.startswith('finops_'):
        # Parse Prometheus format and send to Datadog
        # (implementation depends on your parsing logic)
        pass
```

---

## Custom Integrations

### Slack Bot

**Cost Analysis Bot:**

```python
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler
import httpx
import base64

app = App(token="xoxb-your-token")

@app.command("/cost-check")
def handle_cost_check(ack, command, say):
    ack()
    
    # Get Terraform file from command
    tf_file = command['text']
    
    try:
        # Read file and encode
        with open(tf_file, 'r') as f:
            content = f.read()
        payload = base64.b64encode(content.encode()).decode()
        
        # Call FinOpsGuard
        client = httpx.Client()
        response = client.post(
            'http://finopsguard:8080/mcp/checkCostImpact',
            json={
                "iac_type": "terraform",
                "iac_payload": payload,
                "environment": "dev"
            }
        )
        result = response.json()
        
        # Format response
        blocks = [
            {
                "type": "header",
                "text": {"type": "plain_text", "text": "💰 Cost Analysis"}
            },
            {
                "type": "section",
                "fields": [
                    {"type": "mrkdwn", "text": f"*Monthly:* ${result['estimated_monthly_cost']:.2f}"},
                    {"type": "mrkdwn", "text": f"*First Week:* ${result['estimated_first_week_cost']:.2f}"}
                ]
            }
        ]
        
        if result['risk_flags']:
            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"⚠️ *Risks:* {', '.join(result['risk_flags'])}"
                }
            })
        
        say(blocks=blocks)
        
    except Exception as e:
        say(f"❌ Error: {str(e)}")

if __name__ == "__main__":
    handler = SocketModeHandler(app, "xapp-your-token")
    handler.start()
```

### Pre-commit Hook

**Local Cost Validation:**

```bash
#!/bin/bash
# .git/hooks/pre-commit

# Check if Terraform files changed
TF_FILES=$(git diff --cached --name-only --diff-filter=ACM | grep '.tf$')

if [ -z "$TF_FILES" ]; then
    exit 0
fi

echo "🔍 Checking cost impact..."

# Combine all Terraform files
COMBINED_TF=$(cat $TF_FILES)
PAYLOAD=$(echo "$COMBINED_TF" | base64)

# Call FinOpsGuard
RESULT=$(curl -s -X POST http://localhost:8080/mcp/checkCostImpact \
  -H 'Content-Type: application/json' \
  -d "{
    \"iac_type\": \"terraform\",
    \"iac_payload\": \"$PAYLOAD\",
    \"environment\": \"dev\"
  }")

# Parse result
COST=$(echo "$RESULT" | jq -r '.estimated_monthly_cost')
RISKS=$(echo "$RESULT" | jq -r '.risk_flags | join(", ")')

echo "💰 Estimated monthly cost: \$$COST"

if [ -n "$RISKS" ]; then
    echo "⚠️  Risk flags: $RISKS"
fi

# Check for blocking violations
if echo "$RESULT" | jq -e '.risk_flags[] | select(. == "policy_blocked")' > /dev/null; then
    echo "❌ Cost policy violation - commit blocked"
    exit 1
fi

echo "✅ Cost check passed"
exit 0
```

Make executable:
```bash
chmod +x .git/hooks/pre-commit
```

### Terraform Module

**Cost Check Module:**

```hcl
# modules/cost-check/main.tf
terraform {
  required_providers {
    http = {
      source = "hashicorp/http"
      version = "~> 3.0"
    }
  }
}

variable "finopsguard_url" {
  description = "FinOpsGuard API URL"
  type        = string
}

variable "terraform_plan" {
  description = "Base64-encoded Terraform plan"
  type        = string
}

variable "environment" {
  description = "Environment name"
  type        = string
  default     = "dev"
}

data "http" "cost_check" {
  url    = "${var.finopsguard_url}/mcp/checkCostImpact"
  method = "POST"
  
  request_headers = {
    Content-Type = "application/json"
  }
  
  request_body = jsonencode({
    iac_type    = "terraform"
    iac_payload = var.terraform_plan
    environment = var.environment
  })
}

locals {
  cost_result = jsondecode(data.http.cost_check.response_body)
}

output "monthly_cost" {
  value = local.cost_result.estimated_monthly_cost
}

output "policy_status" {
  value = local.cost_result.policy_eval.status
}
```

---

## Best Practices

### 1. Error Handling

Always handle API errors gracefully:

```python
import httpx

try:
    response = client.post('/mcp/checkCostImpact', json=payload)
    response.raise_for_status()
    result = response.json()
except httpx.HTTPStatusError as e:
    if e.response.status_code == 400:
        print(f"Invalid request: {e.response.json()['detail']}")
    elif e.response.status_code == 500:
        print(f"Server error: {e.response.json()['detail']}")
    sys.exit(1)
except httpx.RequestError as e:
    print(f"Connection error: {e}")
    sys.exit(1)
```

### 2. Timeout Configuration

Set appropriate timeouts for large analyses:

```python
client = httpx.Client(
    base_url="http://finopsguard:8080",
    timeout=60.0  # 60 seconds for large Terraform files
)
```

### 3. Caching Strategy

For repeated analyses, use request IDs:

```python
# First request
result1 = client.post('/mcp/checkCostImpact', json=payload)
request_id = result1.json()['duration_ms']  # Use timestamp as ID

# Check if already analyzed
analyses = client.post('/mcp/listRecentAnalyses', json={"limit": 10})
# Compare against recent analyses to avoid duplicates
```

### 4. Policy Management

Manage policies programmatically:

```python
# Create policy via API
policy = {
    "name": "Production Budget Limit",
    "description": "Enforce $5000 monthly budget for production",
    "budget": 5000,
    "on_violation": "block",
    "enabled": True
}

response = client.post('/mcp/policies', json=policy)
policy_id = response.json()['id']

# Update policy
updated_policy = {**policy, "budget": 6000}
client.put(f'/mcp/policies/{policy_id}', json=updated_policy)
```

### 5. Monitoring Integration

Track FinOpsGuard usage:

```python
import prometheus_client as prom

# Custom metrics
cost_checks = prom.Counter('app_cost_checks_total', 'Total cost checks')
cost_savings = prom.Gauge('app_cost_savings_usd', 'Estimated cost savings')

# After each check
cost_checks.inc()
if recommendations:
    savings = sum(r.get('estimated_savings', 0) for r in recommendations)
    cost_savings.set(savings)
```

### 6. Multi-Environment Strategy

Use different policies per environment:

```bash
# Development
curl -X POST http://finopsguard:8080/mcp/checkCostImpact \
  -d '{"environment": "dev", "budget_rules": {"monthly_budget": 500}}'

# Staging
curl -X POST http://finopsguard:8080/mcp/checkCostImpact \
  -d '{"environment": "staging", "budget_rules": {"monthly_budget": 2000}}'

# Production
curl -X POST http://finopsguard:8080/mcp/checkCostImpact \
  -d '{"environment": "prod", "budget_rules": {"monthly_budget": 10000}}'
```

---

## Troubleshooting Integrations

### Common Issues

**Issue: Connection refused**
```bash
# Check FinOpsGuard is running
curl http://finopsguard:8080/healthz

# Check network connectivity
ping finopsguard

# Check DNS resolution
nslookup finopsguard
```

**Issue: 400 Bad Request**
```bash
# Validate payload encoding
echo "test content" | base64 -d  # Should decode properly

# Check JSON format
echo '{"iac_type": "terraform"}' | jq .  # Should parse
```

**Issue: Slow responses**
```bash
# Enable Redis caching
export REDIS_ENABLED=true

# Check cache status
curl http://finopsguard:8080/mcp/cache/info
```

**Issue: Policy not evaluating**
```bash
# List available policies
curl http://finopsguard:8080/mcp/policies

# Check policy is enabled
curl http://finopsguard:8080/mcp/policies/policy_id | jq '.enabled'
```

---

## Security Considerations

### 1. Authentication (Future)

When authentication is enabled:

```bash
# Using API key
curl -X POST http://finopsguard:8080/mcp/checkCostImpact \
  -H 'X-API-Key: your-api-key' \
  -H 'Content-Type: application/json' \
  -d '{...}'
```

### 2. Network Security

**Kubernetes Network Policy:**

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: finopsguard-ingress
  namespace: finopsguard
spec:
  podSelector:
    matchLabels:
      app: finopsguard
  policyTypes:
    - Ingress
  ingress:
    - from:
        - namespaceSelector:
            matchLabels:
              name: ci-runners
        - namespaceSelector:
            matchLabels:
              name: argocd
      ports:
        - protocol: TCP
          port: 8080
```

### 3. TLS/HTTPS

Always use HTTPS in production:

```bash
# Production URL
FINOPSGUARD_URL=https://finopsguard.company.com

# Verify certificate
curl --cacert /path/to/ca.crt https://finopsguard.company.com/healthz
```

---

## Additional Resources

- **API Documentation**: http://localhost:8080/docs
- **Architecture**: [docs/architecture.md](./architecture.md)
- **Requirements**: [docs/requirements.md](./requirements.md)
- **CI/CD Integration**: [docs/cicd-integration.md](./cicd-integration.md)
- **Deployment Guide**: [docs/deployment.md](./deployment.md)

---

## Support

For integration support:
- Check API documentation at `/docs`
- Review example scripts in `/scripts`
- See GitHub Issues for common integration patterns
- Consult the troubleshooting guide

**FinOpsGuard is designed to be integration-friendly - if you can make HTTP requests, you can integrate with FinOpsGuard!** 🚀

