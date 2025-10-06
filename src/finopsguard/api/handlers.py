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
from ..types.policy import Policy
from ..engine.policy_engine import PolicyEngine
from ..parsers.terraform import parse_terraform_to_crmodel
from ..engine.simulation import simulate_cost
from ..adapters.pricing.aws_static import list_aws_ec2_ondemand
from ..storage.analyses import add_analysis, AnalysisRecord, list_analyses

# Initialize policy engine
policy_engine = PolicyEngine()


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

    # Create custom budget policy if budget rules are provided
    custom_policies = []
    if req.budget_rules and 'monthly_budget' in req.budget_rules:
        from ..types.policy import Policy, PolicyViolationAction
        monthly_budget = req.budget_rules['monthly_budget']
        budget_policy = Policy(
            id='request_budget',
            name='Request Budget Rule',
            description='Budget rule from request',
            budget=monthly_budget,
            on_violation=PolicyViolationAction.ADVISORY
        )
        custom_policies.append(budget_policy)

    # Evaluate policies using the policy engine
    policy_result = policy_engine.evaluate_policies(
        cr_model=cr_model,
        check_response=response,
        environment=req.environment,
        custom_policies=custom_policies
    )

    # Update response based on policy evaluation
    if policy_result.overall_status == "block":
        response.risk_flags.append('policy_blocked')
        response.policy_eval = PolicyEvaluation(
            status='fail',
            policy_id='multiple_policies',
            reason=f"Blocking policy violations: {len(policy_result.blocking_violations)}"
        )
    elif policy_result.overall_status == "advisory":
        response.risk_flags.append('policy_advisory')
        response.policy_eval = PolicyEvaluation(
            status='pass',
            policy_id='multiple_policies',
            reason=f"Advisory violations: {len(policy_result.advisory_violations)}"
        )
    else:
        response.policy_eval = PolicyEvaluation(
            status='pass',
            policy_id='all_policies',
            reason='All policies satisfied'
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
    try:
        # Parse the IaC payload
        if req.iac_type == 'terraform':
            try:
                decoded = base64.b64decode(req.iac_payload).decode('utf-8')
            except Exception:
                raise ValueError('invalid_payload_encoding')
            
            from ..parsers.terraform import parse_terraform_to_crmodel
            cr_model = parse_terraform_to_crmodel(decoded)
        else:
            from ..types.models import CanonicalResourceModel
            cr_model = CanonicalResourceModel(resources=[])
        
        # Get the specific policy
        policy = policy_engine.get_policy(req.policy_id)
        if not policy:
            return PolicyResponse(
                status='fail',
                policy_id=req.policy_id,
                reason=f'Policy {req.policy_id} not found'
            )
        
        # Create a mock cost response for policy evaluation
        from ..engine.simulation import simulate_cost
        cost_response = simulate_cost(cr_model)
        
        # Build evaluation context
        context = policy_engine._build_evaluation_context(cr_model, cost_response, req.environment)
        
        # Evaluate the specific policy
        result = policy.evaluate(context)
        
        # Determine if this should be blocking based on mode
        should_block = req.mode == 'blocking' and result['status'] == 'fail'
        
        return PolicyResponse(
            status='fail' if should_block else result['status'],
            policy_id=result['policy_id'],
            reason=result['reason']
        )
        
    except Exception as e:
        return PolicyResponse(
            status='fail',
            policy_id=req.policy_id,
            reason=f'Policy evaluation error: {str(e)}'
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


async def list_policies() -> Dict[str, Any]:
    """List all policies"""
    policies = policy_engine.list_policies()
    return {
        "policies": [
            {
                "id": policy.id,
                "name": policy.name,
                "description": policy.description,
                "enabled": policy.enabled,
                "on_violation": policy.on_violation,
                "has_budget": policy.budget is not None,
                "has_rules": policy.expression is not None
            }
            for policy in policies
        ]
    }


async def get_policy(policy_id: str) -> Dict[str, Any]:
    """Get a specific policy by ID"""
    policy = policy_engine.get_policy(policy_id)
    if not policy:
        raise ValueError(f"Policy {policy_id} not found")
    
    return {
        "id": policy.id,
        "name": policy.name,
        "description": policy.description,
        "budget": policy.budget,
        "expression": policy.expression.model_dump() if policy.expression else None,
        "on_violation": policy.on_violation,
        "enabled": policy.enabled
    }


async def create_policy(policy_data: Dict[str, Any]) -> Dict[str, Any]:
    """Create a new policy"""
    from ..types.policy import Policy, PolicyViolationAction, PolicyExpression, PolicyRule, PolicyOperator
    
    # Build policy expression if provided
    expression = None
    if "rules" in policy_data:
        rules = []
        for rule_data in policy_data["rules"]:
            rule = PolicyRule(
                field=rule_data["field"],
                operator=PolicyOperator(rule_data["operator"]),
                value=rule_data["value"]
            )
            rules.append(rule)
        
        expression = PolicyExpression(
            rules=rules,
            operator=policy_data.get("rule_operator", "and")
        )
    
    policy = Policy(
        id=policy_data["id"],
        name=policy_data["name"],
        description=policy_data.get("description"),
        budget=policy_data.get("budget"),
        expression=expression,
        on_violation=PolicyViolationAction(policy_data.get("on_violation", "advisory")),
        enabled=policy_data.get("enabled", True)
    )
    
    policy_engine.add_policy(policy)
    return {"message": f"Policy {policy.id} created successfully"}


async def delete_policy(policy_id: str) -> Dict[str, Any]:
    """Delete a policy by ID"""
    success = policy_engine.remove_policy(policy_id)
    if not success:
        raise ValueError(f"Policy {policy_id} not found")
    
    return {"message": f"Policy {policy_id} deleted successfully"}
