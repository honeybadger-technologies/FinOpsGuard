"""
API handlers for MCP endpoints
"""

import base64
import time
from datetime import datetime
from typing import Dict, Any

from ..types.api import (
    CheckRequest, CheckResponse, SuggestRequest, SuggestResponse,
    PolicyRequest, PolicyResponse, PriceQuery, PriceCatalogResponse,
    ListQuery, ListResponse, PriceCatalogItem
)
from ..types.models import PolicyEvaluation
from ..parsers.terraform import parse_terraform_to_crmodel
from ..engine.simulation import simulate_cost
from ..adapters.pricing.aws_static import list_aws_ec2_ondemand
from ..storage.analyses import add_analysis, AnalysisRecord, list_analyses


async def check_cost_impact(req: CheckRequest) -> CheckResponse:
    """Check cost impact of IaC changes"""
    start_time = int(time.time() * 1000)
    
    if not req or not req.iac_type or not req.iac_payload:
        raise ValueError('invalid_request')
    
    cr_model = None
    if req.iac_type == 'terraform':
        try:
            decoded = base64.b64decode(req.iac_payload).decode('utf-8')
        except Exception:
            raise ValueError('invalid_payload_encoding')
        cr_model = parse_terraform_to_crmodel(decoded)
    else:
        from ..types.models import CanonicalResourceModel
        cr_model = CanonicalResourceModel(resources=[])
    
    sim = simulate_cost(cr_model)
    duration_ms = max(1, int(time.time() * 1000) - start_time)
    
    response = CheckResponse(
        estimated_monthly_cost=sim.estimated_monthly_cost,
        estimated_first_week_cost=sim.estimated_first_week_cost,
        breakdown_by_resource=sim.breakdown_by_resource,
        risk_flags=sim.risk_flags,
        recommendations=sim.recommendations,
        pricing_confidence=sim.pricing_confidence,
        duration_ms=duration_ms
    )

    # Apply simple budget rule if provided
    if req.budget_rules and 'monthly_budget' in req.budget_rules:
        monthly_budget = req.budget_rules['monthly_budget']
        if response.estimated_monthly_cost > monthly_budget:
            if 'over_budget' not in response.risk_flags:
                response.risk_flags.append('over_budget')
            response.policy_eval = PolicyEvaluation(
                status='fail',
                policy_id='monthly_budget',
                reason=f"Estimated {response.estimated_monthly_cost:.2f} exceeds budget {monthly_budget:.2f}"
            )
        else:
            response.policy_eval = PolicyEvaluation(
                status='pass',
                policy_id='monthly_budget',
                reason='within budget'
            )
    
    # Store analysis record
    add_analysis(AnalysisRecord(
        request_id=str(start_time),
        started_at=datetime.fromtimestamp(start_time / 1000).isoformat(),
        duration_ms=duration_ms,
        summary=f"monthly={response.estimated_monthly_cost:.2f} resources={len(response.breakdown_by_resource)}"
    ))
    
    return response


async def suggest_optimizations(req: SuggestRequest) -> SuggestResponse:
    """Suggest cost optimizations"""
    return SuggestResponse(suggestions=[])


async def evaluate_policy(req: PolicyRequest) -> PolicyResponse:
    """Evaluate policy against IaC"""
    return PolicyResponse(
        status='pass',
        policy_id=req.policy_id,
        reason='stub'
    )


async def get_price_catalog(req: PriceQuery) -> PriceCatalogResponse:
    """Get price catalog for cloud resources"""
    items = []
    
    if req.cloud == 'aws':
        aws_items = list_aws_ec2_ondemand(req.region, req.instance_types)
        items = [
            PriceCatalogItem(
                sku=item['sku'],
                description=item['description'],
                region=item['region'],
                unit='hour',
                price=item['price'],
                attributes={}
            )
            for item in aws_items
        ]
    
    return PriceCatalogResponse(
        updated_at=datetime.now().isoformat(),
        pricing_confidence='high' if items else 'low',
        items=items
    )


async def list_recent_analyses(req: ListQuery) -> ListResponse:
    """List recent cost analyses"""
    items, next_cursor = list_analyses(req.limit or 20, req.after)
    return ListResponse(items=items, next_cursor=next_cursor)
