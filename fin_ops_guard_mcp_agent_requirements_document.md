# FinOpsGuard — MCP Agent

**Purpose:** This document defines the functional and non-functional requirements, APIs, data models, integration flows, tests, and acceptance criteria for *FinOpsGuard*, an MCP (Model Context Protocol) agent that provides proactive cost-aware deployment guardrails for DevOps pipelines. This document is targeted for automated code generation tools (e.g., cursor.ai) and developer teams who will implement, test, and deploy the agent.

---

## 1. Executive Summary

FinOpsGuard is an MCP agent that analyzes Infrastructure-as-Code (IaC) changes and CI/CD pipeline events to simulate, estimate, and enforce cost and efficiency policies *before* resources are provisioned. It returns actionable recommendations, blocks deployments that violate policy (optional), and integrates with PRs, pipeline logs, and observability dashboards.

**Key capabilities**
- Parse IaC manifests (Terraform, Helm charts, Kubernetes manifests, Pulumi) and CI configs
- Run a cost projection simulation using live pricing + historical usage
- Detect cost anti-patterns and provide optimization suggestions
- Respond to MCP requests with structured results (advisory or blocking)
- Provide audit logs and metrics for FinOps teams

---

## 2. Stakeholders & Personas

- **DevOps Engineer** — wants quick feedback in PRs/pipelines about cost impact and optimization suggestions.
- **Platform/Infrastructure Engineer** — enforces organization budgeting and policies, needs blocking and drift detection.
- **FinOps Analyst** — wants aggregated reports and cost projection data to set budgets.
- **SRE** — wants to understand operational impact and availability/cost tradeoffs.
- **Security/Compliance** — audits access and ensures the agent follows security rules.

---

## 3. High-level Architecture

Components:
1. **MCP Agent (FinOpsGuard)** — stateless service exposing MCP endpoints for analysis and actions.
2. **Pricing Adapter** — connectors for cloud provider pricing APIs (AWS, GCP, Azure) and cached price catalog.
3. **Usage Adapter (optional)** — connectors to pull historical usage metrics (CloudWatch, Billing export, BigQuery).
4. **IaC Parsers** — modules to parse Terraform HCL, Helm charts, Kubernetes manifests, Pulumi JSON.
5. **Simulation Engine** — computes cost projection, run-rate, and sensitivity analysis.
6. **Policy Engine** — evaluates budget rules, custom rules, FinOps guardrails.
7. **Storage (optional)** — for caching price catalogs, storing audit logs, and historical projections (Postgres/SQLite).
8. **Integrations** — GitHub/GitLab PR comments, CI (GitHub Actions/GitLab CI/Argo), Slack, Grafana metrics.

Deployment model: Docker container(s) + Kubernetes deployment; horizontal scaling supported.

---

## 4. Goals & Non-Goals

### Goals
- Provide reliable cost projection for IaC changes within CI/CD pipelines
- Provide clear, actionable optimization suggestions
- Support both advisory and blocking modes
- Integrate with major IaC tools and CI systems
- Maintain secure and auditable operations

### Non-Goals
- Act as a complete FinOps platform (no full billing/chargeback features)
- Replace specialized cloud provider price quoting tools for enterprise discounts

---

## 5. Functional Requirements

Each requirement is labeled FR-#.

### FR-1: MCP Endpoint — Cost Check
**Description:** Expose MCP method `checkCostImpact`.
**Input:** IaC payload (file(s) or parsed JSON), `environment` (dev/staging/prod), `budget_rules` (optional), `simulation_options`.
**Output:** JSON with `estimated_monthly_cost`, `estimated_first_week_cost`, `breakdown_by_resource`, `risk_flags`, `recommendations`.
**Behavior:** Must run within pipeline-friendly time (default < 30s for small manifests, configurable). Should support both synchronous and asynchronous invocation.

### FR-2: MCP Endpoint — Suggest Optimizations
**Description:** Expose MCP method `suggestOptimizations`.
**Input:** Service topology or resource list.
**Output:** Ranked `suggestions` (e.g., instance family changes, use spot instances, right-sizing), estimated savings per suggestion, estimated impact on reliability.

### FR-3: MCP Endpoint — Policy Evaluation
**Description:** `evaluatePolicy(iac_payload, policy_id)` returns pass/fail and details.
**Policies:** budget cap, resource tag requirements, region-specific rules, max instance types.
**Modes:** `advisory`, `blocking`.

### FR-4: IaC Parsers
**Description:** Accept raw IaC inputs (Terraform HCL files, Helm Chart tarball, Kubernetes YAML, Pulumi JSON) and parse into a canonical resource model.
**Error handling:** Return parse errors with file and line references.

### FR-5: Pricing Adapter
**Description:** Fetch current on-demand/spot/reserved prices for AWS/GCP/Azure for given regions and instance types.
**Fallback:** Use cached price catalog if live API fails; return `pricing_confidence` field.

### FR-6: Usage Adapter (Optional but recommended)
**Description:** Pull historical usage to inform run-rate (e.g., utilization patterns) and predict idle resources.

### FR-7: CI/CD Integration Helpers
**Description:** Provide example integrations for GitHub Actions, GitLab CI, and Argo Workflows that call MCP endpoints.
**Output:** PR comments (Markdown) with human-friendly summary and machine-readable JSON artifact.

### FR-8: Reporting & Metrics
**Description:** Emit Prometheus metrics for number of checks, average estimated cost, block counts, recommendation acceptance rate.

### FR-9: Audit Logging
**Description:** All requests and responses, policy decisions, and overrides must be logged (immutable with timestamps) to a storage backend.

### FR-10: Admin UI (Minimal)
**Description:** A lightweight web UI to review recent analyses, policy configuration, and manual overrides. (Optional for MVP)

---

## 6. Non-Functional Requirements (NFR)

- **NFR-1 (Performance):** Typical small manifest analysis < 30s. Large manifests (<500 resources) < 2 minutes.
- **NFR-2 (Scalability):** Support concurrent processing of 50 requests/sec in clustered deployment.
- **NFR-3 (Security):** Use OAuth2 or mTLS for MCP calls. Secrets (cloud billing API keys) stored in K8s secrets / Vault.
- **NFR-4 (Reliability):** 99.9% uptime SLA for the agent component (when deployed in production).
- **NFR-5 (Extensibility):** Adapter pattern for adding more cloud providers or IaC formats.
- **NFR-6 (Privacy):** Do not persist raw IaC files unless admin opt-in. Mask secrets detected in IaC.

---

## 7. Data Model / JSON Schemas

Provide concise canonical schemas that cursor.ai can use to scaffold models.

### 7.1 Canonical Resource Model (CRModel)
```json
{
  "resources": [
    {
      "id": "string",
      "type": "aws_instance | aws_ebs | k8s_deployment | gcp_compute_instance | ...",
      "name": "string",
      "region": "string",
      "size": "string",
      "count": 1,
      "tags": {"key":"value"},
      "metadata": { }
    }
  ]
}
```

### 7.2 checkCostImpact Request
```json
{
  "iac_type": "terraform|helm|k8s|pulumi",
  "iac_payload": "(string or tarball reference)",
  "environment": "dev|staging|prod",
  "budget_rules": {"monthly_budget": 1000, "max_per_resource": 500},
  "options": {"prefer_spot": true, "max_execution_secs": 60}
}
```

### 7.3 checkCostImpact Response
```json
{
  "estimated_monthly_cost": 123.45,
  "estimated_first_week_cost": 32.12,
  "breakdown_by_resource": [
    {"resource_id":"...","monthly_cost": 12.34, "notes": []}
  ],
  "risk_flags": ["over_budget", "idle_resource"],
  "recommendations": [
    {"id":"r1","type":"right_size","description":"Use c7g.large instead of m5.large","estimated_savings_monthly": 10.5}
  ],
  "policy_eval": {"status":"pass|fail","policy_id":"...","reason":"..."},
  "pricing_confidence": "high|medium|low",
  "duration_ms": 5123
}
```

---

## 8. MCP Methods / API Surface

Design MCP methods with clear request/response types. Example methods:

- `checkCostImpact(CheckRequest) -> CheckResponse`
- `suggestOptimizations(SuggestRequest) -> SuggestResponse`
- `evaluatePolicy(PolicyRequest) -> PolicyResponse`
- `getPriceCatalog(PriceQuery) -> PriceCatalogResponse`
- `listRecentAnalyses(ListQuery) -> ListResponse`

Include machine-readable OpenAPI-like descriptions for cursor.ai to scaffold endpoints and types.

---

## 9. Example Workflows

### 9.1 GitHub PR (Advisory)
1. Developer opens PR with Terraform changes.
2. GitHub Action calls `checkCostImpact` with `iac_payload` and `environment=dev`.
3. If `estimated_monthly_cost` increases > 20% vs baseline, post PR comment with summary and attach JSON artifact.
4. Developer reviews suggestions and amends PR.

### 9.2 CI/CD Blocking
1. Pipeline job calls `evaluatePolicy` with `mode=blocking`.
2. If `policy_eval.status == fail` the step fails and returns human-readable reason.

---

## 10. Policy Language (Minimal DSL)

Support a small declarative DSL for budget rules and constraints. Example:

```
policy "monthly_budget" {
  budget: 10000
  on_violation: block
}

policy "no_gpu_in_dev" {
  rule: resource.type == "aws_gpu_instance" and environment == "dev"
  on_violation: advisory
}
```

Cursor.ai can scaffold a simple parser and evaluator for this DSL.

---

## 11. Security & Compliance

- Authenticate MCP calls with mTLS or OAuth2 bearer tokens.
- RBAC for policy creation and overrides.
- Detect and redact secrets in IaC (e.g., `AWS_SECRET_ACCESS_KEY` literals).
- Encrypt stored logs at rest.

---

## 12. Observability & Metrics

Prometheus metrics to expose:
- `finops_checks_total` (labels: result=pass/fail, cloud=aws/gcp/azure)
- `finops_checks_duration_seconds` (histogram)
- `finops_blocks_total`
- `finops_recommendations_total`

Logs: structured JSON with `request_id`, `user`, `timestamp`, `input_digest`, `policy_decision`.

---

## 13. Acceptance Criteria & Test Cases

Provide explicit tests the generated code must pass.

### AC-1: Basic check
- Given a Terraform manifest provisioning a single `t3.medium` in `us-east-1`, `checkCostImpact` returns a positive monthly estimate and a resource breakdown.

### AC-2: Right-sizing suggestion
- Given a manifest with `m5.large` for a web service with low CPU, `suggestOptimizations` returns a right-size suggestion (e.g., `t3.large` or `c7g.large`) with estimated savings.

### AC-3: Policy blocking
- Given a policy with `monthly_budget=10` USD and a manifest that projects $50/month, `evaluatePolicy` returns `fail` and `on_violation=block` causes pipeline step to exit non-zero.

### AC-4: Parse errors
- Given malformed HCL, parser returns a well-structured error with file and line numbers.

### AC-5: Pricing confidence
- If pricing adapter fails to reach cloud API, `pricing_confidence` is `low` and response includes timestamp of last successful price refresh.

---

## 14. Implementation Notes for cursor.ai

- Target language: TypeScript (Node.js 20) + Deno/Go adapters are acceptable. Provide Dockerfile and Kubernetes manifests.
- Use a modular folder layout: `src/adapters`, `src/parsers`, `src/engine`, `src/api`, `src/integrations`, `tests`.
- Provide unit tests using Jest (or Vitest) and integration tests (calling a local price cache for deterministic outputs).
- Provide OpenAPI spec (YAML) for the MCP endpoints.
- Provide example GitHub Action and GitLab CI job YAML files.

---

## 15. MVP Scope & Roadmap

**MVP (0.1)**
- `checkCostImpact` for Terraform + Kubernetes YAML
- AWS pricing adapter for on-demand + spot
- GitHub Action integration (advisory)
- Prometheus metrics + basic logging
- Unit tests and basic integration tests

**MVP+ (0.2)**
- Policy engine with DSL and blocking mode
- GCP/Azure pricing adapters
- Usage adapter (CloudWatch/Billing)
- Minimal admin UI

**Future (0.3+)**
- Cost forecasts using ML (seasonality)
- Auto-apply recommended changes via PR
- Multi-account chargeback reports

---

## 16. Deliverables (for cursor.ai code gen)

1. TypeScript codebase scaffold with modules, interfaces, and placeholder implementations.
2. OpenAPI spec for all MCP endpoints.
3. Dockerfile and Kubernetes manifests.
4. GitHub Action example that calls `checkCostImpact` and posts results to PR.
5. Unit and integration tests that validate AC-1..AC-5.
6. README with setup, env vars, and run instructions.

---

## 17. Appendix

### 17.1 Example checkCostImpact request (JSON)
```json
{
  "iac_type": "terraform",
  "iac_payload": "<base64-tarball-or-inline-hcl>",
  "environment": "staging",
  "budget_rules": {"monthly_budget": 2000},
  "options": {"prefer_spot": true}
}
```

### 17.2 Example minimal GitHub Action step
```yaml
- name: Run FinOpsGuard check
  uses: actions/http-client@v1
  with:
    url: ${{ env.FINOPSGUARD_URL }}/mcp/checkCostImpact
    method: POST
    headers: |
      Authorization: Bearer ${{ secrets.FINOPSGUARD_TOKEN }}
      Content-Type: application/json
    body: |
      { "iac_type": "terraform", "iac_payload": "${{ steps.package.outputs.payload }}", "environment": "dev" }
```

---

*End of document.*

