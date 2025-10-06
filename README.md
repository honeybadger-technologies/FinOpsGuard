# FinOpsGuard

MCP agent providing cost-aware guardrails for IaC in CI/CD.

## Overview
- Implements MCP endpoints to analyze IaC changes and enforce cost policies.
- Integrates with GitHub/GitLab CI to post advisory or blocking feedback.
- Uses pricing and (optional) usage adapters for projections.
- FastAPI server with MCP routes and Prometheus metrics.

## Current Status (MVP scaffold)
- FastAPI server with routes:
  - POST `/mcp/checkCostImpact`
  - POST `/mcp/suggestOptimizations`
  - POST `/mcp/evaluatePolicy`
  - POST `/mcp/getPriceCatalog`
  - POST `/mcp/listRecentAnalyses`
  - GET `/healthz` (liveness)
  - GET `/metrics` (Prometheus)
- Pydantic models in `src/finopsguard/types/*`
- Auto-generated OpenAPI schema at `/docs`
- CI examples:
  - GitHub Actions: `.github/workflows/finopsguard-check.yml`
  - GitLab CI: `.gitlab/ci-example.yml`

## Repo Structure
```
src/finopsguard/
  api/                 # MCP methods surface
  adapters/
    pricing/           # Cloud pricing adapters (AWS/GCP/Azure)
    usage/             # Historical usage adapters (optional)
  parsers/             # Terraform/K8s/etc -> Canonical Resource Model
  engine/              # Simulation, policy evaluation
  integrations/
    github/            # Action helpers & PR commenting
    gitlab/            # CI job helpers
  metrics/             # Prometheus metrics emitters
  storage/             # Cache, audit log storage
  
tests/
  unit/
  integration/

docs/
  architecture.md
  requirements.md
```

## Prerequisites
- Python 3.11+
- pip

## Install
```bash
pip install -r requirements.txt
```

## Run (development)
```bash
python -m finopsguard.main
# FinOpsGuard MCP listening on :8080
```

Verify:
```bash
curl -sS http://localhost:8080/healthz
curl -sS http://localhost:8080/metrics | head
```

## Build and Run (production)
```bash
python -m finopsguard.main
```

## Docker
```bash
# Build image
docker build -t finopsguard:latest .
# Run container
docker run --rm -p 8080:8080 finopsguard:latest
```

## OpenAPI
FastAPI automatically generates OpenAPI schema at `/docs` endpoint.

## CI Examples
- GitHub Actions example workflow: `.github/workflows/finopsguard-check.yml`
- GitLab CI job example: `.gitlab/ci-example.yml`

## FR-1: MCP Endpoint — Cost Check

Request example:
```bash
PAYLOAD=$(printf 'resource "aws_instance" "example" { instance_type = "t3.medium" }\nprovider "aws" { region="us-east-1" }' | base64)
curl -sS -X POST "$FINOPSGUARD_URL/mcp/checkCostImpact" \
  -H 'Content-Type: application/json' \
  -d '{
    "iac_type":"terraform",
    "iac_payload":"'"$PAYLOAD"'",
    "environment":"dev",
    "budget_rules": {"monthly_budget": 25}
  }'
```

Response fields:
- `estimated_monthly_cost`, `estimated_first_week_cost`
- `breakdown_by_resource[]`
- `risk_flags[]` (e.g., `over_budget`)
- `recommendations[]`
- `policy_eval` (if budget provided)
- `pricing_confidence`, `duration_ms`

Errors:
- `400` `{ "error": "invalid_request|invalid_payload_encoding" }`
- `500` `{ "error": "internal_error" }`

For detailed requirements and scope, see `docs/requirements.md`.

## Testing

Run unit tests:
```bash
pytest tests/unit/
```

Run integration tests:
```bash
pytest tests/integration/
```

Run all tests:
```bash
pytest tests/
```

## Roadmap

- MVP (0.1) ✅ **COMPLETED**
  - ✅ checkCostImpact for Terraform + Kubernetes YAML
  - ✅ AWS pricing adapter (on-demand + spot)
  - ✅ GitHub Action (advisory mode)
  - ✅ Prometheus metrics + basic structured logging
  - ✅ Unit tests and a basic integration test

- MVP+ (0.2)
  - Policy engine with minimal DSL + blocking mode
  - GCP/Azure pricing adapters
  - Usage adapter (CloudWatch/Billing) for run-rate hints
  - Minimal admin UI for analyses, policies, overrides

- Future (0.3+)
  - Cost forecasts with seasonality/ML
  - Auto-apply recommended changes via PRs
  - Multi-account/org chargeback reports

- Near-term dev milestones
  - Define parser interfaces; add Terraform/K8s parsers returning CRModel
  - Implement AWS pricing adapter with local cache and confidence flag
  - Wire simulation engine to compute estimates and resource breakdowns
  - Implement policy evaluation path and CI blocking exit codes
  - Expand OpenAPI and add request/response validation
  - Harden auth (mTLS/OAuth2), add RBAC scaffolding
  - CI: lint/test; Docker build; optional K8s manifests

- Quality gates
  - Meet AC-1..AC-5
  - NFR targets (latency, concurrency, privacy) with metrics dashboards
