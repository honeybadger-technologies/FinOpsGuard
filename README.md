# FinOpsGuard

MCP agent providing cost-aware guardrails for IaC in CI/CD with advanced policy enforcement.

## Overview
- **Cost Analysis**: Analyzes IaC changes and provides accurate cost projections
- **Policy Engine**: Enforces budget rules and resource constraints with blocking/advisory modes
- **Multi-Cloud Support**: AWS and GCP pricing adapters with support for multiple resource types
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
- ✅ **Terraform Parser**: Full HCL parsing with support for AWS and GCP resources
- ✅ **Cost Simulation**: Accurate monthly/weekly cost projections for both AWS and GCP
- ✅ **Policy Engine**: Budget and rule-based policies with DSL support
- ✅ **Blocking Mode**: Policy violations can block deployments
- ✅ **Multi-Cloud Support**: 
  - **AWS**: EC2, RDS, EKS, ElastiCache, DynamoDB, Redshift, OpenSearch, Load Balancers
  - **GCP**: Compute Engine, Cloud SQL, GKE, Cloud Run, Cloud Functions, Load Balancers, Redis, BigQuery
- ✅ **Auto-generated OpenAPI**: Complete API documentation at `/docs`
- ✅ **Admin UI**: Modern web interface for management and monitoring
- ✅ **CI/CD Integration**: Seamless integration with GitHub Actions and GitLab CI

## Repo Structure
```
src/finopsguard/
  api/                 # FastAPI server and MCP endpoints
  adapters/
    pricing/           # Cloud pricing adapters (AWS and GCP static data)
    usage/             # Historical usage adapters (future)
  engine/              # Cost simulation and policy evaluation
  parsers/             # Terraform HCL -> Canonical Resource Model
  storage/             # In-memory analysis storage
  types/               # Pydantic models and policy definitions
  integrations/        # CI/CD integration helpers
    github/            # GitHub Actions and PR commenting
    gitlab/            # GitLab CI and MR commenting
  cli/                 # Command-line interface tools
  metrics/             # Prometheus metrics
  
tests/
  unit/                # Unit tests (78 tests)
  integration/         # Integration tests (14 tests)

static/                # Admin UI static files
  css/                 # Stylesheets
  js/                  # JavaScript application
  assets/              # Images and other assets

scripts/               # CI/CD integration scripts
  finopsguard-cicd.sh  # Universal CI/CD integration script

.github/
  workflows/           # GitHub Actions workflows
    finopsguard-check.yml

.gitlab/
  ci-templates/        # GitLab CI job templates
    finopsguard.yml

docs/
  requirements.md      # Detailed requirements and specifications
  architecture.md      # System architecture documentation
  cicd-integration.md  # CI/CD integration guide
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

### Docker Deployment
```bash
# Build and run container
docker build -t finopsguard:latest .
docker run --rm -p 8080:8080 finopsguard:latest
```

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
- **Unit Tests** (78 tests): Core business logic, policy engine, cost simulation, AWS pricing, GCP pricing
- **Integration Tests** (14 tests): HTTP endpoints, API workflows, error handling

### Test Coverage
- ✅ Policy engine evaluation and blocking logic
- ✅ Cost simulation with AWS and GCP resources
- ✅ Terraform parser with comprehensive AWS and GCP resource support
- ✅ AWS pricing adapter with static pricing data
- ✅ GCP pricing adapter with comprehensive static pricing data
- ✅ API endpoints with request/response validation
- ✅ Error handling and edge cases
- ✅ Admin UI functionality and policy management
- ✅ CI/CD integration scripts and workflows

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
# Copy .github/workflows/finopsguard-check.yml to your repository
name: FinOpsGuard Cost Check
on: [pull_request, push]
```

### GitLab CI
```yaml
# Include in your .gitlab-ci.yml
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

## Roadmap

### ✅ MVP+ (0.2) - COMPLETED
- ✅ Policy engine with DSL and blocking mode
- ✅ Comprehensive Terraform parser
- ✅ Multi-resource cost simulation (AWS + GCP)
- ✅ Policy management API
- ✅ Admin UI with modern web interface
- ✅ CI/CD integration (GitHub Actions, GitLab CI, CLI, Universal Script)
- ✅ GCP Pricing Adapter with full resource support
- ✅ Complete test suite (92 tests)

### Next Phase (0.3)
- **Azure Pricing Adapter**: Extend beyond AWS and GCP
- **Real-time Pricing**: Live pricing API integration for accurate cost analysis
- **Usage Integration**: CloudWatch/Billing API integration
- **Enhanced Admin UI**: Advanced analytics and reporting
- **Multi-tenant Support**: Organization and team management

### Future (0.4+)
- **ML Cost Forecasting**: Seasonal patterns and usage prediction
- **Auto-optimization**: Automated PR generation for cost savings
- **Multi-account Support**: Organization-wide cost governance
- **Advanced Policies**: Time-based rules, dependency-aware policies

### Technical Debt & Improvements
- **Authentication**: mTLS/OAuth2 integration
- **RBAC**: Role-based access control
- **Caching**: Redis for pricing data and analysis results
- **Monitoring**: Enhanced observability and alerting
