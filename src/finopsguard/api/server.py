"""
FastAPI server for FinOpsGuard MCP endpoints
"""

import os
from datetime import datetime
from fastapi import FastAPI, HTTPException
from fastapi.responses import PlainTextResponse

from .handlers import (
    check_cost_impact, suggest_optimizations, evaluate_policy,
    get_price_catalog, list_recent_analyses, list_policies,
    get_policy, create_policy, delete_policy
)
from ..types.api import (
    CheckRequest, SuggestRequest, PolicyRequest,
    PriceQuery, ListQuery
)
from ..metrics.prometheus import get_metrics_text


app = FastAPI(
    title="FinOpsGuard",
    description="MCP agent providing cost-aware guardrails for IaC in CI/CD",
    version="0.1.0"
)


@app.post("/mcp/checkCostImpact")
async def check_cost_impact_endpoint(request: CheckRequest):
    """Check cost impact of IaC changes"""
    try:
        response = await check_cost_impact(request)
        return response
    except ValueError as e:
        error_msg = str(e)
        if error_msg in ['invalid_request', 'invalid_payload_encoding']:
            raise HTTPException(status_code=400, detail={"error": error_msg})
        raise HTTPException(status_code=500, detail={"error": "internal_error"})
    except Exception:
        raise HTTPException(status_code=500, detail={"error": "internal_error"})


@app.post("/mcp/suggestOptimizations")
async def suggest_optimizations_endpoint(request: SuggestRequest):
    """Suggest cost optimizations"""
    response = await suggest_optimizations(request)
    return response


@app.post("/mcp/evaluatePolicy")
async def evaluate_policy_endpoint(request: PolicyRequest):
    """Evaluate policy against IaC"""
    response = await evaluate_policy(request)
    return response


@app.post("/mcp/getPriceCatalog")
async def get_price_catalog_endpoint(request: PriceQuery):
    """Get price catalog for cloud resources"""
    response = await get_price_catalog(request)
    return response


@app.post("/mcp/listRecentAnalyses")
async def list_recent_analyses_endpoint(request: ListQuery):
    """List recent cost analyses"""
    response = await list_recent_analyses(request)
    return response


@app.get("/mcp/policies")
async def list_policies_endpoint():
    """List all policies"""
    response = await list_policies()
    return response


@app.get("/mcp/policies/{policy_id}")
async def get_policy_endpoint(policy_id: str):
    """Get a specific policy by ID"""
    try:
        response = await get_policy(policy_id)
        return response
    except ValueError as e:
        raise HTTPException(status_code=404, detail={"error": str(e)})


@app.post("/mcp/policies")
async def create_policy_endpoint(policy_data: dict):
    """Create a new policy"""
    try:
        response = await create_policy(policy_data)
        return response
    except ValueError as e:
        raise HTTPException(status_code=400, detail={"error": str(e)})


@app.delete("/mcp/policies/{policy_id}")
async def delete_policy_endpoint(policy_id: str):
    """Delete a policy by ID"""
    try:
        response = await delete_policy(policy_id)
        return response
    except ValueError as e:
        raise HTTPException(status_code=404, detail={"error": str(e)})


@app.get("/healthz")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "ok",
        "now": datetime.now().isoformat()
    }


@app.get("/metrics", response_class=PlainTextResponse)
async def metrics():
    """Prometheus metrics endpoint"""
    try:
        return get_metrics_text()
    except Exception:
        raise HTTPException(status_code=500, detail={"error": "metrics_unavailable"})


def create_app() -> FastAPI:
    """Create and configure the FastAPI application"""
    return app


if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)
