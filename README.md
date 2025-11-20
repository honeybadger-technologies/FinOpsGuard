# FinOpsGuard

MCP agent providing cost-aware guardrails for IaC in CI/CD with advanced policy enforcement.

## Overview
- **Cost Analysis**: Analyzes IaC changes and provides accurate cost projections
- **Policy Engine**: Enforces budget rules and resource constraints with blocking/advisory modes
- **Multi-Cloud Support**: AWS, GCP, and Azure pricing adapters with support for multiple resource types
- **CI/CD Integration**: Seamless integration with GitHub/GitLab CI for automated cost governance
- **FastAPI Server**: Modern Python API with auto-generated OpenAPI documentation

## Current Status (MVP+ Complete) ✅

### Core MCP Endpoints
- **POST** `/mcp/checkCostImpact` - Cost analysis with integrated policy evaluation
- **POST** `/mcp/evaluatePolicy` - Dedicated policy evaluation with blocking mode
- **POST** `/mcp/suggestOptimizations` - Cost optimization recommendations
- **POST** `/mcp/getPriceCatalog` - Cloud pricing information
- **POST** `/mcp/listRecentAnalyses` - Historical analysis tracking
- **GET** `/healthz` - Health check endpoint
- **GET** `/metrics` - Prometheus metrics

### Policy Management API
- **GET** `/mcp/policies` - List all policies
- **GET** `/mcp/policies/{id}` - Get specific policy
- **POST** `/mcp/policies` - Create new policy
- **PUT** `/mcp/policies/{id}` - Update existing policy
- **DELETE** `/mcp/policies/{id}` - Delete policy

### Usage Integration API
- **GET** `/usage/availability` - Check cloud provider availability
- **POST** `/usage/resource` - Get resource metrics (CloudWatch, Cloud Monitoring, Azure Monitor)
- **POST** `/usage/cost` - Get historical cost data (Cost Explorer, Cloud Billing, Cost Management)
- **POST** `/usage/summary` - Generate comprehensive usage summary
- **GET** `/usage/example/{provider}` - Get example usage data
- **DELETE** `/usage/cache` - Clear usage data cache

### Webhook Management API
- **GET** `/webhooks` - List all webhook configurations
- **POST** `/webhooks` - Create new webhook configuration
- **GET** `/webhooks/{id}` - Get specific webhook configuration
- **PUT** `/webhooks/{id}` - Update webhook configuration
- **DELETE** `/webhooks/{id}` - Delete webhook configuration
- **GET** `/webhooks/{id}/deliveries` - List webhook delivery attempts
- **GET** `/webhooks/stats` - Get webhook delivery statistics

### Admin UI
- **GET** `/` - Modern web interface for policy and analysis management
- **Dashboard**: Real-time metrics and activity overview
- **Policy Management**: Visual policy builder with rule editor
- **Analysis History**: Detailed cost analysis results and trends
- **Settings**: Configuration management and system settings

### CI/CD Integration
- **GitHub Actions**: Ready-to-use workflow for automated cost checking
- **GitLab CI**: Reusable job template for GitLab pipelines
- **CLI Tool**: Command-line interface for any CI/CD platform
- **Universal Script**: Cross-platform bash script for CI/CD integration
- **PR/MR Comments**: Automated posting of cost analysis results

### Features
- ✅ **Terraform Parser**: Modular HCL parsing with 60+ resource types across AWS (24), GCP (18), and Azure (18)
- ✅ **Ansible Parser**: Comprehensive YAML parsing with 58+ module types across AWS (20), GCP (18), and Azure (20)
- ✅ **Cost Simulation**: Accurate monthly/weekly cost projections for multi-cloud infrastructure
- ✅ **Policy Engine**: Budget and rule-based policies with DSL support
- ✅ **Blocking Mode**: Policy violations can block deployments
- ✅ **Real-time Pricing**: Live pricing APIs for AWS, GCP, and Azure with intelligent fallback
- ✅ **Usage Integration**: Historical usage data from CloudWatch, Cloud Monitoring, and Azure Monitor
  - **AWS**: CloudWatch metrics and Cost Explorer for actual resource usage and billing
  - **GCP**: Cloud Monitoring metrics and BigQuery billing export for usage analytics
  - **Azure**: Azure Monitor metrics and Cost Management for cost and usage tracking
- ✅ **Webhooks**: Event-driven notifications for cost anomalies and policy changes
  - **Cost Anomalies**: Automatic alerts for budget violations, cost spikes, and high-cost resources
  - **Policy Events**: Notifications for policy creation, updates, and deletions
  - **Retry Logic**: Robust delivery with configurable retry attempts and timeouts
  - **HMAC Signatures**: Secure webhook verification with cryptographic signatures
  - **Background Processing**: Asynchronous delivery with proper error handling
- ✅ **Authentication**: API keys, JWT tokens, OAuth2 (GitHub/Google/Azure), mTLS support
- ✅ **RBAC**: Role-based access control (admin, user, viewer, api)
- ✅ **PostgreSQL Storage**: Persistent policies and analysis history
- ✅ **Redis Caching**: Intelligent caching for pricing data and analysis results with automatic TTL management
- ✅ **Multi-Cloud Support**: 
  - **AWS**: EC2, RDS, EKS, ElastiCache, DynamoDB, Redshift, OpenSearch, Load Balancers
  - **GCP**: Compute Engine, Cloud SQL, GKE, Cloud Run, Cloud Functions, Load Balancers, Redis, BigQuery
  - **Azure**: Virtual Machines, SQL Database, Storage, AKS, App Service, Functions, Load Balancer, Redis, Cosmos DB
- ✅ **Auto-generated OpenAPI**: Complete API documentation at `/docs`
- ✅ **Admin UI**: Modern web interface for management and monitoring
- ✅ **CI/CD Integration**: Seamless integration with GitHub Actions and GitLab CI

## Repo Structure
```
src/finopsguard/
  api/                 # FastAPI server and MCP endpoints
  adapters/
    pricing/           # Cloud pricing adapters (static + live APIs for AWS/GCP/Azure)
    usage/             # Historical usage adapters (CloudWatch, Monitoring, Cost Management)
  auth/                # Authentication & authorization (API keys, JWT, OAuth2, mTLS)
  audit/               # Audit logging and compliance reporting
  cache/               # Redis caching layer (pricing, analysis, policies)
  database/            # PostgreSQL persistent storage (policies, analyses, audit logs)
  engine/              # Cost simulation and policy evaluation
  parsers/             # Infrastructure parsers (Terraform HCL + Ansible YAML)
    terraform.py       # Terraform orchestrator (93 lines)
    aws_tf_parser.py   # AWS Terraform parsing (24 types)
    gcp_tf_parser.py   # GCP Terraform parsing (18 types)
    azure_tf_parser.py # Azure Terraform parsing (18 types)
    ansible.py         # Ansible orchestrator (210 lines)
    aws_ansible_parser.py   # AWS Ansible parsing (20 types)
    gcp_ansible_parser.py   # GCP Ansible parsing (18 types)
    azure_ansible_parser.py # Azure Ansible parsing (20 types)
  storage/             # Hybrid storage (in-memory + database)
  types/               # Pydantic models and policy definitions
  webhooks/            # Webhook system for event-driven notifications
    storage.py         # Webhook configuration storage
    delivery.py        # Webhook delivery service with retry logic
    events.py          # Event generation and cost anomaly detection
    tasks.py           # Background task processing
  integrations/        # CI/CD integration helpers
    github/            # GitHub Actions and PR commenting
    gitlab/            # GitLab CI and MR commenting
  cli/                 # Command-line interface tools
  metrics/             # Prometheus metrics
  
tests/
  unit/                # Unit tests (260+ tests: auth, cache, database, pricing, policies, usage, parsers, audit, webhooks)
  integration/         # Integration tests (25+ tests)

examples/              # Example scripts and infrastructure definitions
  usage_integration_example.py  # Complete usage integration examples
  aws-infrastructure.tf         # AWS Terraform example
  gcp-infrastructure.tf         # GCP Terraform example
  azure-infrastructure.tf       # Azure Terraform example
  aws-infrastructure.yml        # AWS Ansible example
  gcp-infrastructure.yml        # GCP Ansible example
  azure-infrastructure.yml      # Azure Ansible example

static/                # Admin UI static files
  css/                 # Stylesheets
  js/                  # JavaScript application
  assets/              # Images and other assets

scripts/               # CI/CD integration scripts
  finopsguard-cicd.sh  # Universal CI/CD integration script

examples/              # Example configurations and templates
  .github/
    workflows/         # GitHub Actions workflow examples
      finopsguard-check.yml
      finopsguard-pr-comment.yml
  .gitlab/
    ci-templates/      # GitLab CI job template examples
      finopsguard.yml
    ci-example.yml     # Example GitLab CI configuration

docs/
  requirements.md      # Detailed requirements and specifications
  architecture.md      # System architecture documentation
  cicd-integration.md  # CI/CD integration guide
  deployment.md        # Deployment guide (Docker Compose & Kubernetes)
  integrations.md      # MCP agent integration examples (12+ platforms)
  database.md          # PostgreSQL configuration and management
  authentication.md    # Authentication & authorization guide (API keys, JWT, OAuth2, mTLS)
  pricing.md           # Real-time and static pricing configuration
  usage-integration.md # Usage integration guide (CloudWatch, Cloud Monitoring, Cost Management)
  terraform-parsing.md # Terraform HCL parsing guide
  ansible-parsing.md   # Ansible YAML parsing guide

deploy/
  kubernetes/          # Kubernetes manifests
  prometheus/          # Prometheus configuration
  grafana/            # Grafana dashboards and datasources
  QUICK_START.md      # Quick deployment guide
```

## Quick Start

### Prerequisites
- Python 3.11+
- pip

### Install Dependencies
```bash
# Create virtual environment (recommended)
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Run Development Server
```bash
# Set Python path and run
PYTHONPATH=src python -m finopsguard.main

# Server will be available at http://localhost:8080
```

### Verify Installation
```bash
# Health check
curl -sS http://localhost:8080/healthz

# View metrics
curl -sS http://localhost:8080/metrics | head

# API documentation
open http://localhost:8080/docs

# Admin UI
open http://localhost:8080/
```

### Docker Compose Deployment

**Fastest way to get started:**

```bash
# Start FinOpsGuard
docker-compose up -d

# With monitoring (Prometheus + Grafana)
docker-compose --profile monitoring up -d

# With caching (Redis)
docker-compose --profile caching up -d

# Full stack (monitoring + caching)
docker-compose --profile monitoring --profile caching up -d

# Verify deployment
curl http://localhost:8080/healthz
curl http://localhost:8080/mcp/cache/info  # Check cache status
open http://localhost:8080/

# Stop services
docker-compose down
```

### Kubernetes Deployment

**For production environments:**

```bash
# Using Makefile
make k8s-deploy

# Or using kubectl
kubectl apply -k deploy/kubernetes/

# Verify
kubectl get pods -n finopsguard
kubectl port-forward -n finopsguard svc/finopsguard 8080:8080
```

**See [deploy/QUICK_START.md](deploy/QUICK_START.md) for detailed deployment instructions.**

## API Usage Examples

### Cost Impact Analysis
Analyze Terraform changes for cost impact and policy compliance:

```bash
# Encode Terraform configuration
PAYLOAD=$(printf 'resource "aws_instance" "example" { 
  instance_type = "t3.medium" 
  tags = { Environment = "dev" }
}
provider "aws" { region="us-east-1" }' | base64)

# Check cost impact with budget rules
curl -sS -X POST "http://localhost:8080/mcp/checkCostImpact" \
  -H 'Content-Type: application/json' \
  -d '{
    "iac_type":"terraform",
    "iac_payload":"'"$PAYLOAD"'",
    "environment":"dev",
    "budget_rules": {"monthly_budget": 25}
  }'
```

### Policy Management
Create and manage cost policies:

```bash
# Create a policy to block large instances in dev
curl -sS -X POST "http://localhost:8080/mcp/policies" \
  -H 'Content-Type: application/json' \
  -d '{
    "name": "No Large Instances in Dev",
    "description": "Prevent large instances in development environment",
    "rules": [
      {
        "name": "max_instance_size_dev",
        "description": "Block instances larger than t3.medium in dev",
        "expression": {
          "field": "resource.size",
          "operator": "in",
          "value": ["t3.large", "t3.xlarge", "m5.large", "m5.xlarge"]
        },
        "action": "block"
      }
    ],
    "enabled": true
  }'

# List all policies
curl -sS http://localhost:8080/mcp/policies
```

### Usage Integration & Historical Data
Get actual usage metrics and billing data from cloud providers:

```bash
# Check if usage integration is available
curl -sS http://localhost:8080/usage/availability

# Get CloudWatch metrics for an EC2 instance (last 7 days)
curl -sS -X POST "http://localhost:8080/usage/resource" \
  -H 'Content-Type: application/json' \
  -d '{
    "cloud_provider": "aws",
    "resource_id": "i-1234567890abcdef0",
    "resource_type": "ec2",
    "start_time": "2024-01-01T00:00:00Z",
    "end_time": "2024-01-31T23:59:59Z",
    "region": "us-east-1",
    "metrics": ["CPUUtilization", "NetworkIn", "NetworkOut"]
  }'

# Get historical cost data from AWS Cost Explorer
curl -sS -X POST "http://localhost:8080/usage/cost" \
  -H 'Content-Type: application/json' \
  -d '{
    "cloud_provider": "aws",
    "start_time": "2024-01-01T00:00:00Z",
    "end_time": "2024-01-31T23:59:59Z",
    "granularity": "DAILY",
    "group_by": ["service", "region"]
  }'

# Get usage example for last 7 days
curl -sS http://localhost:8080/usage/example/aws?days=7
```

### Webhook Management
Configure webhooks for event-driven notifications:

```bash
# Create a webhook for cost anomaly notifications
curl -sS -X POST "http://localhost:8080/webhooks" \
  -H 'Content-Type: application/json' \
  -d '{
    "name": "Cost Anomaly Alerts",
    "description": "Notify when cost anomalies are detected",
    "url": "https://your-app.com/webhooks/finopsguard",
    "events": ["cost.anomaly.detected", "budget.exceeded", "cost.spike"],
    "secret": "your-webhook-secret",
    "enabled": true,
    "verify_ssl": true,
    "timeout_seconds": 30,
    "retry_attempts": 3,
    "retry_delay_seconds": 5
  }'

# List all webhooks
curl -sS http://localhost:8080/webhooks

# Get webhook delivery history
curl -sS http://localhost:8080/webhooks/{webhook_id}/deliveries

# Get webhook statistics
curl -sS http://localhost:8080/webhooks/stats
```

### GCP Cost Analysis
Analyze GCP infrastructure changes:

```bash
# Encode GCP Terraform configuration
PAYLOAD=$(printf 'resource "google_compute_instance" "web_server" { 
  machine_type = "e2-standard-4"
  zone = "us-central1-a"
}
resource "google_sql_database_instance" "main_db" {
  database_version = "POSTGRES_13"
  settings {
    tier = "db-n1-standard-2"
  }
}
provider "google" { region="us-central1" }' | base64)

# Check cost impact for GCP resources
curl -sS -X POST "http://localhost:8080/mcp/checkCostImpact" \
  -H 'Content-Type: application/json' \
  -d '{
    "iac_type":"terraform",
    "iac_payload":"'"$PAYLOAD"'",
    "environment":"prod",
    "budget_rules": {"monthly_budget": 100}
  }'
```

### Response Fields
- `estimated_monthly_cost`, `estimated_first_week_cost` - Cost projections
- `breakdown_by_resource[]` - Per-resource cost breakdown
- `risk_flags[]` - Risk indicators (e.g., `over_budget`, `policy_violation`)
- `recommendations[]` - Optimization suggestions
- `policy_eval` - Policy evaluation results with blocking status
- `pricing_confidence`, `duration_ms` - Metadata

### Error Handling
- `400` `{ "detail": { "error": "invalid_request|invalid_payload_encoding" } }`
- `500` `{ "detail": { "error": "internal_error" } }`

## Testing

### Run All Tests
```bash
# Activate virtual environment first
source venv/bin/activate

# Run with Python path set
PYTHONPATH=src pytest tests/ -v
```

### Test Categories
- **Unit Tests** (245+ tests): Core business logic, policy engine, cost simulation, AWS pricing, GCP pricing, caching layer, authentication, database, webhooks
- **Integration Tests** (25+ tests): HTTP endpoints, API workflows, error handling, webhook integration

### Test Coverage
- ✅ Policy engine evaluation and blocking logic
- ✅ Cost simulation with AWS and GCP resources
- ✅ Terraform parser with comprehensive AWS and GCP resource support
- ✅ AWS pricing adapter with static pricing data
- ✅ GCP pricing adapter with comprehensive static pricing data
- ✅ Redis caching layer (pricing, analysis, TTL management)
- ✅ PostgreSQL database layer (policies, analyses, hybrid storage)
- ✅ Authentication (API keys, JWT, OAuth2, mTLS)
- ✅ RBAC and authorization
- ✅ API endpoints with request/response validation
- ✅ Error handling and edge cases
- ✅ Admin UI functionality and policy management
- ✅ CI/CD integration scripts and workflows
- ✅ Webhook system (storage, delivery, events, background processing)

## Policy Engine Features

### Supported Policy Types
- **Budget Policies**: Monthly spending limits with advisory/blocking modes
- **Resource Rules**: Instance size restrictions, region controls, tag requirements
- **Environment-Specific**: Different policies per environment (dev/staging/prod)

### Policy Actions
- **Block**: Prevent deployment if policy is violated
- **Advisory**: Log violations but allow deployment
- **Warning**: Generate warnings for policy violations

### Policy Evaluation Context
- Resource attributes (size, type, region, tags)
- Environment information
- Cost projections and budget comparisons
- Historical analysis data

## CI/CD Integration

FinOpsGuard provides comprehensive CI/CD integration for automated cost governance:

### GitHub Actions
```yaml
# Copy examples/.github/workflows/finopsguard-check.yml to your repository
name: FinOpsGuard Cost Check
on: [pull_request, push]
```

### GitLab CI
```yaml
# Copy examples/.gitlab/ci-templates/finopsguard.yml to .gitlab/ci-templates/
# Then include in your .gitlab-ci.yml
include:
  - local: '.gitlab/ci-templates/finopsguard.yml'
```

### CLI Tool
```bash
# Use the CLI for any CI/CD platform
python -m finopsguard.cli.main check-cost --environment prod --budget 1000
```

### Universal Script
```bash
# Cross-platform script for any CI/CD system
./scripts/finopsguard-cicd.sh --format json --output results.json
```

For detailed CI/CD integration instructions, see [docs/cicd-integration.md](docs/cicd-integration.md).

## MCP Agent Integration

FinOpsGuard is a Model Context Protocol (MCP) agent that can be integrated with various tools and platforms for cost-aware infrastructure governance.

### MCP Architecture

FinOpsGuard exposes standard MCP endpoints that follow the request/response pattern:

```
┌─────────────────┐
│   MCP Client    │  (GitHub Actions, GitLab CI, CLI, Custom Tools)
└────────┬────────┘
         │ HTTP/JSON
         ▼
┌─────────────────┐
│  FinOpsGuard    │  MCP Endpoints:
│   MCP Agent     │  - checkCostImpact
│                 │  - evaluatePolicy
│                 │  - suggestOptimizations
│                 │  - getPriceCatalog
└────────┬────────┘
         │
    ┌────┴────┬──────────┬────────┐
    ▼         ▼          ▼        ▼
 Parsers   Engine    Adapters  Storage
```

### Integration Options

#### 1. **REST API Integration**

Direct API calls from any HTTP client:

```bash
# Cost analysis
curl -X POST http://finopsguard:8080/mcp/checkCostImpact \
  -H 'Content-Type: application/json' \
  -d '{
    "iac_type": "terraform",
    "iac_payload": "'$(base64 < main.tf)'",
    "environment": "prod",
    "budget_rules": {"monthly_budget": 1000}
  }'
```

#### 2. **Python SDK Integration**

Use the CLI module as a library:

```python
from finopsguard.cli.main import FinOpsGuardCLI

# Initialize client
client = FinOpsGuardCLI(api_url="http://finopsguard:8080")

# Check cost impact
result = client.check_cost(
    file_path="main.tf",
    environment="prod",
    budget=1000
)

# Evaluate policy
policy_result = client.evaluate_policy(
    file_path="main.tf",
    policy_id="no_large_instances_in_dev"
)
```

#### 3. **GitHub Actions Integration**

Use the pre-built workflow:

```yaml
# .github/workflows/cost-check.yml
name: Cost Check
on: [pull_request]

jobs:
  finopsguard:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Run FinOpsGuard
        uses: ./.github/workflows/finopsguard-check.yml  # After copying from examples/
        with:
          environment: ${{ github.ref == 'refs/heads/main' && 'prod' || 'dev' }}
          budget: 1000
```

Or use the universal script:

```yaml
- name: Cost Analysis
  run: |
    curl -O https://raw.githubusercontent.com/your-org/FinOpsGuard/main/scripts/finopsguard-cicd.sh
    chmod +x finopsguard-cicd.sh
    ./finopsguard-cicd.sh --format json --output cost-report.json
  env:
    FINOPSGUARD_URL: https://finopsguard.your-company.com
    GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
```

#### 4. **GitLab CI Integration**

Copy the template from examples and include it in your `.gitlab-ci.yml`:

```yaml
include:
  - local: '.gitlab/ci-templates/finopsguard.yml'

stages:
  - validate
  - deploy

cost-check:
  extends: .finopsguard-check
  stage: validate
  variables:
    ENVIRONMENT: "prod"
    BUDGET: "1000"
```

#### 5. **Jenkins Integration**

```groovy
pipeline {
    agent any
    
    stages {
        stage('Cost Analysis') {
            steps {
                script {
                    sh '''
                        curl -X POST ${FINOPSGUARD_URL}/mcp/checkCostImpact \
                          -H 'Content-Type: application/json' \
                          -d @- <<EOF
                        {
                          "iac_type": "terraform",
                          "iac_payload": "$(base64 -w0 main.tf)",
                          "environment": "${ENVIRONMENT}",
                          "budget_rules": {"monthly_budget": ${BUDGET}}
                        }
EOF
                    '''
                }
            }
        }
    }
}
```

#### 6. **ArgoCD Integration**

PreSync hook for cost validation:

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: finopsguard-presync
data:
  presync.sh: |
    #!/bin/bash
    # Extract manifests and check cost
    kubectl get application $ARGOCD_APP_NAME -o yaml > app.yaml
    
    # Call FinOpsGuard
    PAYLOAD=$(base64 -w0 app.yaml)
    RESULT=$(curl -X POST $FINOPSGUARD_URL/mcp/checkCostImpact \
      -H 'Content-Type: application/json' \
      -d "{\"iac_type\":\"k8s\",\"iac_payload\":\"$PAYLOAD\"}")
    
    # Check for policy violations
    if echo "$RESULT" | jq -e '.risk_flags[] | select(. == "policy_blocked")'; then
      echo "Cost policy violation - blocking deployment"
      exit 1
    fi
---
apiVersion: batch/v1
kind: Job
metadata:
  generateName: finopsguard-presync-
  annotations:
    argocd.argoproj.io/hook: PreSync
spec:
  template:
    spec:
      containers:
      - name: finopsguard-check
        image: curlimages/curl
        command: ["/bin/sh", "/scripts/presync.sh"]
        volumeMounts:
        - name: scripts
          mountPath: /scripts
      volumes:
      - name: scripts
        configMap:
          name: finopsguard-presync
      restartPolicy: Never
```

#### 7. **Terraform Cloud/Enterprise Integration**

Sentinel policy using external data source:

```hcl
import "http"
import "json"

# Call FinOpsGuard for cost analysis
finopsguard_check = func() {
    # Prepare payload
    payload = {
        "iac_type": "terraform",
        "iac_payload": base64encode(tfplan_json),
        "environment": workspace.name,
        "budget_rules": {"monthly_budget": 1000}
    }
    
    # Make request
    req = http.request("https://finopsguard.company.com/mcp/checkCostImpact").
        with_body(json.marshal(payload)).
        with_header("Content-Type", "application/json")
    
    resp = json.unmarshal(req.body)
    
    # Check for violations
    if "policy_blocked" in resp.risk_flags {
        return false
    }
    
    return true
}

main = rule {
    finopsguard_check()
}
```

#### 8. **Slack Integration**

Post cost analysis to Slack channels:

```python
import requests
import json

def post_cost_analysis_to_slack(webhook_url, analysis_result):
    """Post cost analysis to Slack."""
    
    message = {
        "blocks": [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": "💰 FinOpsGuard Cost Analysis"
                }
            },
            {
                "type": "section",
                "fields": [
                    {
                        "type": "mrkdwn",
                        "text": f"*Estimated Monthly Cost:*\n${analysis_result['estimated_monthly_cost']:.2f}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*First Week Cost:*\n${analysis_result['estimated_first_week_cost']:.2f}"
                    }
                ]
            }
        ]
    }
    
    if "over_budget" in analysis_result.get("risk_flags", []):
        message["blocks"].append({
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": "⚠️ *Warning:* Budget exceeded!"
            }
        })
    
    requests.post(webhook_url, json=message)

# Usage
analysis = requests.post(
    "http://finopsguard:8080/mcp/checkCostImpact",
    json={"iac_type": "terraform", "iac_payload": payload}
).json()

post_cost_analysis_to_slack(
    webhook_url="https://hooks.slack.com/services/YOUR/WEBHOOK/URL",
    analysis_result=analysis
)
```

#### 9. **Prometheus/Grafana Integration**

Monitor FinOpsGuard metrics:

```yaml
# prometheus.yml
scrape_configs:
  - job_name: 'finopsguard'
    static_configs:
      - targets: ['finopsguard:8080']
    metrics_path: '/metrics'
    scrape_interval: 15s
```

Create Grafana dashboard queries:
```promql
# Total cost checks
sum(finops_checks_total)

# Average check duration
rate(finops_checks_duration_seconds_sum[5m]) / 
rate(finops_checks_duration_seconds_count[5m])

# Policy blocks
sum(finops_blocks_total)

# Cache hit rate
sum(finops_cache_hits_total) / 
(sum(finops_cache_hits_total) + sum(finops_cache_misses_total))
```

#### 10. **Kubernetes Admission Controller**

Validate resources before creation:

```yaml
apiVersion: admissionregistration.k8s.io/v1
kind: ValidatingWebhookConfiguration
metadata:
  name: finopsguard-validator
webhooks:
- name: cost.finopsguard.io
  rules:
  - apiGroups: ["*"]
    apiVersions: ["*"]
    operations: ["CREATE", "UPDATE"]
    resources: ["deployments", "statefulsets"]
  clientConfig:
    service:
      name: finopsguard
      namespace: finopsguard
      path: /validate/cost
  admissionReviewVersions: ["v1"]
  sideEffects: None
```

#### 11. **Custom Tool Integration**

Use FinOpsGuard API in your own tools:

```python
import httpx
import base64

class CostAnalyzer:
    def __init__(self, api_url: str):
        self.api_url = api_url
        self.client = httpx.Client(base_url=api_url)
    
    def analyze_terraform(self, tf_content: str, budget: float = None):
        """Analyze Terraform code for cost impact."""
        payload = base64.b64encode(tf_content.encode()).decode()
        
        request = {
            "iac_type": "terraform",
            "iac_payload": payload,
            "environment": "prod"
        }
        
        if budget:
            request["budget_rules"] = {"monthly_budget": budget}
        
        response = self.client.post("/mcp/checkCostImpact", json=request)
        return response.json()
    
    def get_pricing(self, cloud: str, region: str = None):
        """Get pricing catalog."""
        response = self.client.post(
            "/mcp/getPriceCatalog",
            json={"cloud": cloud, "region": region}
        )
        return response.json()

# Usage
analyzer = CostAnalyzer("http://finopsguard:8080")
result = analyzer.analyze_terraform(open("main.tf").read(), budget=1000)
print(f"Monthly cost: ${result['estimated_monthly_cost']:.2f}")
```

#### 12. **VS Code Extension Integration**

Create a VS Code extension that uses FinOpsGuard:

```typescript
// extension.ts
import * as vscode from 'vscode';
import axios from 'axios';

export function activate(context: vscode.ExtensionContext) {
    let disposable = vscode.commands.registerCommand(
        'finopsguard.analyzeCost',
        async () => {
            const editor = vscode.window.activeTextEditor;
            if (!editor) return;
            
            const tfContent = editor.document.getText();
            const payload = Buffer.from(tfContent).toString('base64');
            
            const response = await axios.post(
                'http://finopsguard:8080/mcp/checkCostImpact',
                {
                    iac_type: 'terraform',
                    iac_payload: payload,
                    environment: 'dev'
                }
            );
            
            vscode.window.showInformationMessage(
                `Estimated Monthly Cost: $${response.data.estimated_monthly_cost}`
            );
        }
    );
    
    context.subscriptions.push(disposable);
}
```

### MCP Protocol Compliance

FinOpsGuard implements the MCP specification with:

- ✅ **Stateless Design**: Each request is independent
- ✅ **JSON Payloads**: Standard JSON request/response
- ✅ **HTTP/REST**: Standard HTTP protocol
- ✅ **Versioned API**: Future-proof with version support
- ✅ **Error Handling**: Consistent error response format
- ✅ **Async Support**: Non-blocking operations
- ✅ **OpenAPI Schema**: Auto-generated documentation

### Integration Best Practices

1. **Use Base64 Encoding**: Always base64-encode IaC payloads
2. **Set Environment**: Specify dev/staging/prod for accurate policy evaluation
3. **Handle Errors**: Check for `risk_flags` and `policy_eval.status`
4. **Cache Results**: Use analysis IDs to track historical results
5. **Monitor Metrics**: Track via Prometheus for observability
6. **Enable Caching**: Use Redis for better performance in high-traffic scenarios

### Available Integrations

FinOpsGuard provides ready-to-use integrations for:

- ✅ **GitHub Actions** - Pre-built workflows
- ✅ **GitLab CI** - Reusable templates
- ✅ **Jenkins** - Pipeline examples
- ✅ **CircleCI** - Job configurations
- ✅ **Azure DevOps** - Pipeline tasks
- ✅ **ArgoCD** - PreSync hooks
- ✅ **Flux CD** - Notification providers
- ✅ **Terraform Cloud** - Sentinel policies
- ✅ **Kubernetes** - Admission controllers
- ✅ **Slack** - Bot integration
- ✅ **VS Code** - Extension support
- ✅ **Prometheus/Grafana** - Monitoring

**See [docs/integrations.md](docs/integrations.md) for detailed integration examples and code samples.**

## Persistent Storage

FinOpsGuard supports PostgreSQL for persistent storage of policies and analysis history:

### Database Features
- **Policy Persistence**: Policies stored in PostgreSQL and synced to memory
- **Analysis History**: Full analysis results with queryable metadata
- **Audit Trail**: Complete history with timestamps and context
- **Automatic Failover**: Falls back to in-memory storage if database unavailable
- **Connection Pooling**: Efficient connection management (10-30 connections)
- **Migrations**: Alembic for schema management

### Enable PostgreSQL

**Docker Compose:**
```bash
# Start with database
docker-compose --profile database up -d

# Or full stack (database + caching + monitoring)
docker-compose --profile database --profile caching --profile monitoring up -d

# Set environment variable
echo "DB_ENABLED=true" >> .env
docker-compose restart finopsguard
```

**Check Database Status:**
```bash
# Get database statistics
curl http://localhost:8080/mcp/database/info

# Example response:
# {
#   "enabled": true,
#   "total_analyses": 1234,
#   "average_monthly_cost": 845.50,
#   "blocked_count": 12
# }
```

### Database Management

```bash
# Initialize database (create tables)
make db-init

# Run migrations
make db-upgrade

# Check migration status
make db-status

# Backup database
make db-backup

# Open database shell
make db-shell
```

**See [docs/database.md](docs/database.md) for comprehensive database documentation.**

## Real-time Pricing

FinOpsGuard supports live pricing APIs for accurate cost estimates:

### Pricing Sources

| Provider | API | Authentication | Status |
|----------|-----|----------------|--------|
| **AWS** | AWS Pricing API | IAM credentials | ✅ Supported |
| **GCP** | Cloud Billing API | API key/Service account | ✅ Supported |
| **Azure** | Retail Prices API | None (public) | ✅ Supported |

### Enable Live Pricing

```bash
# Enable real-time pricing
LIVE_PRICING_ENABLED=true
PRICING_FALLBACK_TO_STATIC=true

# AWS Pricing API
AWS_PRICING_ENABLED=true
AWS_ACCESS_KEY_ID=<your-access-key>
AWS_SECRET_ACCESS_KEY=<your-secret-key>

# GCP Cloud Billing API
GCP_PRICING_ENABLED=true
GCP_PRICING_API_KEY=<your-api-key>

# Azure Retail Prices API (no auth needed!)
AZURE_PRICING_ENABLED=true
```

### Pricing Modes

- **Live Only**: Most accurate, requires API credentials
- **Static Only**: Fast, no credentials, may be outdated
- **Hybrid (Recommended)**: Live with static fallback

**Benefits of Hybrid Mode:**
- ✅ Accurate pricing when APIs available
- ✅ Graceful fallback if APIs fail
- ✅ No downtime due to pricing issues
- ✅ Automatic caching reduces API calls by 90%+

**See [docs/pricing.md](docs/pricing.md) for comprehensive pricing documentation.**

## Authentication & Security

FinOpsGuard supports multiple authentication methods for enterprise security:

### Authentication Methods

1. **API Keys** - For CI/CD and automation
2. **JWT Tokens** - For web UI and CLI
3. **OAuth2** - SSO with GitHub, Google, Azure AD
4. **mTLS** - Certificate-based service authentication

### Enable Authentication

```bash
# Basic setup
AUTH_ENABLED=true
AUTH_MODE=api_key
JWT_SECRET=$(openssl rand -base64 32)
ADMIN_PASSWORD=<secure-password>
```

### Create API Key

```bash
# Login as admin
TOKEN=$(curl -X POST http://localhost:8080/auth/login \
  -d '{"username":"admin","password":"admin"}' | jq -r '.access_token')

# Create API key
API_KEY=$(curl -X POST http://localhost:8080/auth/api-keys \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"name":"CI/CD","roles":["api"],"expires_days":365}' | jq -r '.api_key')

# Use in CI/CD
export FINOPSGUARD_API_KEY=$API_KEY
```

### Use Authentication

```bash
# API Key
curl -H 'X-API-Key: fops_xxxxx' http://finopsguard:8080/mcp/checkCostImpact ...

# JWT Token
curl -H 'Authorization: Bearer eyJhbGc...' http://finopsguard:8080/mcp/checkCostImpact ...

# mTLS
curl --cert client.crt --key client.key https://finopsguard:8080/mcp/checkCostImpact ...
```

### Role-Based Access Control

| Role | Permissions |
|------|-------------|
| **admin** | Full access to all operations |
| **user** | Read/write policies, run analyses |
| **viewer** | Read-only access |
| **api** | API access for service accounts |

**See [docs/authentication.md](docs/authentication.md) for comprehensive authentication documentation.**

## Webhooks

FinOpsGuard provides a comprehensive webhook system for event-driven notifications about cost anomalies and policy changes.

### Webhook Features

- **Event-Driven Notifications**: Automatic alerts for cost anomalies, budget violations, and policy changes
- **Robust Delivery**: Retry logic, timeout handling, and delivery status tracking
- **Security**: HMAC signature verification for webhook authenticity
- **Flexible Configuration**: Custom headers, SSL settings, and event filtering
- **Background Processing**: Asynchronous delivery with proper error handling
- **Full API**: Complete CRUD operations for webhook management

### Supported Events

| Event Type | Description | Trigger |
|------------|-------------|---------|
| `cost.anomaly.detected` | Cost anomaly detected | When analysis shows unusual cost patterns |
| `budget.exceeded` | Budget limit exceeded | When estimated cost exceeds budget threshold |
| `cost.spike` | Significant cost increase | When cost increases dramatically |
| `high.cost.resource` | High-cost resource detected | When individual resources have high costs |
| `policy.created` | New policy created | When a policy is created via API |
| `policy.updated` | Policy updated | When an existing policy is modified |
| `policy.deleted` | Policy deleted | When a policy is removed |

### Webhook Configuration

```bash
# Create a webhook for cost anomaly notifications
curl -X POST "http://localhost:8080/webhooks" \
  -H 'Content-Type: application/json' \
  -d '{
    "name": "Cost Anomaly Alerts",
    "description": "Notify when cost anomalies are detected",
    "url": "https://your-app.com/webhooks/finopsguard",
    "events": ["cost.anomaly.detected", "budget.exceeded"],
    "secret": "your-webhook-secret",
    "enabled": true,
    "verify_ssl": true,
    "timeout_seconds": 30,
    "retry_attempts": 3,
    "retry_delay_seconds": 5,
    "headers": {
      "X-Custom-Header": "custom-value"
    }
  }'
```

### Webhook Payload Format

```json
{
  "event_id": "evt_1234567890",
  "event_type": "cost.anomaly.detected",
  "timestamp": "2024-01-15T10:30:00Z",
  "webhook_id": "webhook_123",
  "data": {
    "analysis_id": "analysis_456",
    "estimated_monthly_cost": 1500.00,
    "budget_limit": 1000.00,
    "anomaly_type": "budget_exceeded",
    "environment": "prod",
    "resources": [
      {
        "type": "aws_instance",
        "size": "t3.large",
        "estimated_cost": 750.00
      }
    ],
    "recommendations": [
      "Consider using t3.medium instances",
      "Review resource allocation"
    ]
  }
}
```

### HMAC Signature Verification

FinOpsGuard signs webhook payloads with HMAC-SHA256 for security:

```python
import hmac
import hashlib
import json

def verify_webhook_signature(payload, signature, secret):
    """Verify webhook signature."""
    expected_signature = hmac.new(
        secret.encode(),
        payload.encode(),
        hashlib.sha256
    ).hexdigest()
    
    return hmac.compare_digest(signature, expected_signature)

# Example verification
payload = request.body
signature = request.headers.get('X-FinOpsGuard-Signature')
secret = 'your-webhook-secret'

if verify_webhook_signature(payload, signature, secret):
    # Process webhook
    pass
else:
    # Reject webhook
    return 401
```

### Webhook Management

```bash
# List all webhooks
curl http://localhost:8080/webhooks

# Get specific webhook
curl http://localhost:8080/webhooks/{webhook_id}

# Update webhook
curl -X PUT http://localhost:8080/webhooks/{webhook_id} \
  -H 'Content-Type: application/json' \
  -d '{"enabled": false}'

# Delete webhook
curl -X DELETE http://localhost:8080/webhooks/{webhook_id}

# Get delivery history
curl http://localhost:8080/webhooks/{webhook_id}/deliveries

# Get webhook statistics
curl http://localhost:8080/webhooks/stats
```

### Delivery Status

Webhook deliveries are tracked with the following statuses:

- `pending` - Delivery not yet attempted
- `delivered` - Successfully delivered
- `failed` - Delivery failed after all retries
- `retrying` - Currently retrying delivery

### Error Handling

Webhooks include comprehensive error handling:

- **Timeout**: Configurable timeout per webhook
- **Retries**: Automatic retry with exponential backoff
- **Dead Letter**: Failed deliveries are logged for debugging
- **Circuit Breaker**: Temporary suspension of failing webhooks

### Integration Examples

#### Slack Integration
```python
import requests
import json

def handle_finopsguard_webhook(request):
    """Handle FinOpsGuard webhook for Slack notifications."""
    payload = request.json
    
    if payload['event_type'] == 'budget.exceeded':
        message = {
            "text": f"🚨 Budget Exceeded!",
            "blocks": [
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"*Environment:* {payload['data']['environment']}\n*Estimated Cost:* ${payload['data']['estimated_monthly_cost']:.2f}\n*Budget Limit:* ${payload['data']['budget_limit']:.2f}"
                    }
                }
            ]
        }
        
        requests.post(
            "https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK",
            json=message
        )
```

#### Discord Integration
```python
def handle_finopsguard_webhook(request):
    """Handle FinOpsGuard webhook for Discord notifications."""
    payload = request.json
    
    embed = {
        "title": "💰 Cost Anomaly Detected",
        "color": 0xff0000,
        "fields": [
            {
                "name": "Environment",
                "value": payload['data']['environment'],
                "inline": True
            },
            {
                "name": "Estimated Cost",
                "value": f"${payload['data']['estimated_monthly_cost']:.2f}",
                "inline": True
            },
            {
                "name": "Budget Limit",
                "value": f"${payload['data']['budget_limit']:.2f}",
                "inline": True
            }
        ],
        "timestamp": payload['timestamp']
    }
    
    requests.post(
        "https://discord.com/api/webhooks/YOUR/DISCORD/WEBHOOK",
        json={"embeds": [embed]}
    )
```

### Best Practices

1. **Always verify signatures** to ensure webhook authenticity
2. **Handle duplicates** - webhooks may be delivered multiple times
3. **Respond quickly** - webhook endpoints should respond within 30 seconds
4. **Use HTTPS** - never use HTTP for webhook endpoints in production
5. **Monitor delivery status** - track failed deliveries and retry patterns
6. **Test webhooks** - use webhook testing tools during development

**See [docs/webhooks.md](docs/webhooks.md) for comprehensive webhook documentation.**

## Caching

FinOpsGuard uses Redis for intelligent caching to dramatically improve performance:

### Cache Features
- **Pricing Data**: AWS/GCP pricing cached for 24 hours
- **Analysis Results**: Full cost analyses cached for 1 hour
- **Parsed Terraform**: Parsed IaC cached for 30 minutes
- **Policy Evaluations**: Policy results cached for 30 minutes
- **Distributed Mode**: Native Redis Cluster support for horizontal scaling
- **Automatic TTL**: Smart expiration based on data volatility
- **Cache Invalidation**: Automatic invalidation on policy updates

### Enable Caching

**Docker Compose:**
```bash
# Enable Redis caching
docker-compose --profile caching up -d

# Set environment variable
echo "REDIS_ENABLED=true" >> .env
docker-compose restart
```

#### Redis Cluster Mode

For high availability deployments, enable Redis Cluster:

```bash
echo "REDIS_ENABLED=true" >> .env
echo "REDIS_CLUSTER_ENABLED=true" >> .env
echo "REDIS_CLUSTER_NODES=redis-cluster-0:6379,redis-cluster-1:6379,redis-cluster-2:6379" >> .env
docker-compose restart finopsguard
```

Cluster mode automatically fans out cache operations across all masters and surfaces cluster health via `/mcp/cache/info`.

**Check Cache Status:**
```bash
# Get cache statistics
curl http://localhost:8080/mcp/cache/info

# Example response:
# {
#   "enabled": true,
#   "mode": "cluster",
#   "cluster_state": "ok",
#   "cluster_nodes": [
#     "redis-cluster-0:6379",
#     "redis-cluster-1:6379",
#     "redis-cluster-2:6379"
#   ],
#   "connected_clients": 18,
#   "used_memory": "1.2M",
#   "keyspace_hits": 1523,
#   "keyspace_misses": 45
# }
```

### Cache Management

```bash
# Flush all cache (admin operation)
curl -X POST http://localhost:8080/mcp/cache/flush

# Monitor cache metrics
curl http://localhost:8080/metrics | grep cache
```

### Performance Impact

With Redis caching enabled:
- **Pricing Lookups**: ~100x faster (1-2ms vs 100-200ms)
- **Repeated Analyses**: ~50x faster (10-20ms vs 500-1000ms)
- **Policy Evaluations**: ~10x faster (5-10ms vs 50-100ms)

## Deployment Options

FinOpsGuard supports multiple deployment methods:

### 🐳 Docker Compose
- **Use case**: Development, testing, small-scale production
- **Setup time**: < 5 minutes
- **Features**: Optional monitoring (Prometheus/Grafana), Redis caching
- **Quick start**: `docker-compose up -d`
- **Guide**: [deploy/QUICK_START.md](deploy/QUICK_START.md)

### ☸️ Kubernetes
- **Use case**: Production, high availability, auto-scaling
- **Setup time**: 10-15 minutes
- **Features**: HPA, PDB, Ingress, ServiceMonitor, multi-replica
- **Quick start**: `make k8s-deploy` or `kubectl apply -k deploy/kubernetes/`
- **Guide**: [docs/deployment.md](docs/deployment.md)

### 🛠️ Makefile Commands
Convenient commands for common operations:
```bash
make help              # Show all available commands
make test              # Run tests
make docker-compose-up # Start with Docker Compose
make k8s-deploy        # Deploy to Kubernetes
make k8s-logs          # View Kubernetes logs
```

For comprehensive deployment documentation, see:
- **Quick Start**: [deploy/QUICK_START.md](deploy/QUICK_START.md)
- **Full Guide**: [docs/deployment.md](docs/deployment.md)
- **Troubleshooting**: [deploy/TROUBLESHOOTING.md](deploy/TROUBLESHOOTING.md)

## Roadmap

### ✅ MVP+ (0.2) - COMPLETED
- ✅ Policy engine with DSL and blocking mode
- ✅ Comprehensive Terraform parser
- ✅ Multi-cloud cost simulation (AWS + GCP + Azure)
- ✅ Real-time pricing APIs (AWS Pricing API, GCP Cloud Billing API, Azure Retail Prices API)
- ✅ Intelligent pricing fallback (live → static → default)
- ✅ Policy management API
- ✅ Admin UI with modern web interface
- ✅ CI/CD integration (GitHub Actions, GitLab CI, CLI, Universal Script)
- ✅ Authentication & Authorization (API keys, JWT, OAuth2, mTLS, RBAC)
- ✅ PostgreSQL persistent storage for policies and analysis history
- ✅ Redis caching for pricing data and analysis results (10-100x performance boost)
- ✅ Docker Compose deployment with full stack (database + caching + monitoring)
- ✅ Kubernetes deployment with HA and auto-scaling
- ✅ MCP agent integration with 12+ platforms
  - ✅ AWS CloudWatch metrics and Cost Explorer integration
  - ✅ GCP Cloud Monitoring and BigQuery billing export
  - ✅ Azure Monitor and Cost Management integration
  - ✅ REST API endpoints for usage data
  - ✅ Intelligent caching with configurable TTL
- ✅ **Webhooks**: Event-driven notifications for cost anomalies and policy changes
  - ✅ Cost anomaly detection (budget violations, cost spikes, high-cost resources)
  - ✅ Policy event notifications (create, update, delete)
  - ✅ Robust delivery with retry logic and timeout handling
  - ✅ HMAC signature verification for webhook security
  - ✅ Background task processing for asynchronous delivery
  - ✅ Complete webhook management API (CRUD operations)
  - ✅ Delivery tracking and statistics
- ✅ Audit Logging: Detailed access logs and compliance reporting
- ✅ Complete test suite (245+ tests including webhook functionality)

### Next Phase (0.3)
- **Enhanced Caching**: Distributed caching with Redis Cluster
- **Enhanced Admin UI**: Advanced analytics and reporting dashboards with usage visualization
- **Multi-tenant Support**: Organization and team management
- **Usage Analytics Dashboard**: Visualize historical usage trends and cost patterns
- **Webhook UI**: Web-based webhook configuration and monitoring interface

### Future (0.4+)
- **ML Cost Forecasting**: Seasonal patterns and usage prediction
- **Auto-optimization**: Automated PR generation for cost savings
- **Multi-account Support**: Organization-wide cost governance
- **Advanced Policies**: Time-based rules, dependency-aware policies

### Technical Debt & Improvements
- **User Database**: PostgreSQL storage for users and sessions
- **Multi-tenancy**: Organization and team isolation  
- **Advanced RBAC**: Fine-grained permissions and resource-level access control
- **Monitoring**: Enhanced observability and alerting
