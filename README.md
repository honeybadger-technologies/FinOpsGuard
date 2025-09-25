# FinOpsGuard

MCP agent providing cost-aware guardrails for IaC in CI/CD.

## Overview
- Implements MCP endpoints to analyze IaC changes and enforce cost policies.
- Integrates with GitHub/GitLab CI to post advisory or blocking feedback.
- Uses pricing and (optional) usage adapters for projections.

## Repo Structure
```
src/
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
```

## Getting Started
- Node.js 20+
- npm or pnpm

### Install
```bash
npm install
```

### Run (placeholder)
```bash
npm start
```

### Test (placeholder)
```bash
npm test
```

For detailed requirements and scope, see `fin_ops_guard_mcp_agent_requirements_document.md`.
