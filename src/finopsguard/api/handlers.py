"""
API handlers for MCP endpoints
"""

import base64
import hashlib
import json
import time
from datetime import datetime
from typing import Dict, Any

from ..types.api import (
    CheckRequest, CheckResponse, SuggestRequest, SuggestResponse,
    PolicyRequest, PolicyResponse, PriceQuery, PriceCatalogResponse,
    ListQuery, ListResponse, PriceCatalogItem
)
from ..types.models import PolicyEvaluation
from ..engine.policy_engine import PolicyEngine
from ..parsers.terraform import parse_terraform_to_crmodel
from ..engine.simulation import simulate_cost
from ..adapters.pricing.aws_static import list_aws_ec2_ondemand
from ..storage.analyses import add_analysis, AnalysisRecord, list_analyses
from ..cache import get_analysis_cache, get_pricing_cache

# Initialize policy engine and caches
policy_engine = PolicyEngine()
analysis_cache = get_analysis_cache()
pricing_cache = get_pricing_cache()


async def check_cost_impact(req: CheckRequest) -> CheckResponse:
    """Check cost impact of IaC changes"""
    start_time = int(time.time() * 1000)
    
    if not req or not req.iac_type or not req.iac_payload:
        raise ValueError('invalid_request')
    
    # Create request hash for caching
    request_hash = hashlib.sha256(
        json.dumps({
            "iac_type": req.iac_type,
            "iac_payload": req.iac_payload,
            "environment": req.environment,
            "budget_rules": req.budget_rules if isinstance(req.budget_rules, dict) else (req.budget_rules.model_dump() if req.budget_rules else None)
        }, sort_keys=True).encode()
    ).hexdigest()[:32]
    
    # Check cache first
    cached_result = analysis_cache.get_full_analysis(request_hash)
    if cached_result:
        # Return cached result with updated timestamp
        cached_result['duration_ms'] = max(1, int(time.time() * 1000) - start_time)
        return CheckResponse(**cached_result)
    
    # Parse IaC
    cr_model = None
    if req.iac_type == 'terraform':
        try:
            decoded = base64.b64decode(req.iac_payload).decode('utf-8')
        except Exception:
            raise ValueError('invalid_payload_encoding')
        
        # Try to get cached parsed Terraform
        cached_parsed = analysis_cache.get_parsed_terraform(decoded)
        if cached_parsed:
            from ..types.models import CanonicalResourceModel
            cr_model = CanonicalResourceModel(**cached_parsed)
        else:
            cr_model = parse_terraform_to_crmodel(decoded)
            # Cache the parsed result
            analysis_cache.set_parsed_terraform(decoded, cr_model.model_dump())
    else:
        from ..types.models import CanonicalResourceModel
        cr_model = CanonicalResourceModel(resources=[])
    
    # Simulate cost
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
    response.policy_eval = policy_result
    
    # Send webhook notifications for cost anomalies
    try:
        from ..webhooks.events import WebhookEventService
        webhook_service = WebhookEventService()
        
        # Prepare analysis data for webhook events
        analysis_data = {
            'estimated_monthly_cost': response.estimated_monthly_cost,
            'estimated_first_week_cost': response.estimated_first_week_cost,
            'breakdown_by_resource': [item.model_dump() for item in response.breakdown_by_resource],
            'risk_flags': response.risk_flags,
            'recommendations': [rec.model_dump() for rec in response.recommendations],
            'policy_eval': policy_result.model_dump(),
            'duration_ms': duration_ms,
            'environment': req.environment
        }
        
        # Add budget limit if provided
        if req.budget_rules and 'monthly_budget' in req.budget_rules:
            analysis_data['budget_limit'] = req.budget_rules['monthly_budget']
        
        # Detect and send webhook events for anomalies
        await webhook_service.detect_cost_anomalies(
            current_analysis=analysis_data,
            previous_analyses=[],  # TODO: Get from database
            environment=req.environment
        )
    except Exception as e:
        # Don't fail the request if webhook delivery fails
        logger.warning(f"Failed to send webhook notifications: {e}")
    
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
    
    # Prepare result data
    result_data = response.model_dump()
    
    # Store analysis record (both in-memory and database if available)
    add_analysis(
        record=AnalysisRecord(
            request_id=str(start_time),
            started_at=datetime.fromtimestamp(start_time / 1000).isoformat(),
            duration_ms=duration_ms,
            summary=f"monthly={response.estimated_monthly_cost:.2f} resources={len(response.breakdown_by_resource)}"
        ),
        result_data=result_data
    )
    
    # Cache the full analysis result
    analysis_cache.set_full_analysis(request_hash, result_data)
    
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
    
    # Try to get from cache first
    cached_catalog = pricing_cache.get_price_catalog(
        cloud=req.cloud,
        instance_types=req.instance_types
    )
    if cached_catalog:
        return PriceCatalogResponse(**cached_catalog)
    
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
    elif req.cloud == 'gcp':
        from ..adapters.pricing.gcp_static import get_gcp_price_catalog
        gcp_catalog = get_gcp_price_catalog()
        
        # Convert GCP pricing to catalog format
        for service_name, service_data in gcp_catalog['services'].items():
            if 'instances' in service_data:
                for instance_type, pricing in service_data['instances'].items():
                    items.append(PriceCatalogItem(
                        sku=f"gcp-{service_name}-{instance_type}",
                        description=f"GCP {service_name} {instance_type}",
                        region=req.region or 'us-central1',
                        unit='hour',
                        price=pricing['price'],
                        attributes={
                            'cpu': str(pricing.get('cpu', 1)),
                            'memory': str(pricing.get('memory', 1)),
                            'gpu': str(pricing.get('gpu', 0))
                        }
                    ))
    
    response = PriceCatalogResponse(
        updated_at=datetime.now().isoformat(),
        pricing_confidence='high' if items else 'low',
        items=items
    )
    
    # Cache the catalog
    pricing_cache.set_price_catalog(
        cloud=req.cloud,
        catalog_data=response.model_dump(),
        instance_types=req.instance_types
    )
    
    return response


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
    
    # Map string operators to enum values
    operator_map = {
        "equals": PolicyOperator.EQ,
        "not_equals": PolicyOperator.NE,
        "in": PolicyOperator.IN,
        "not_in": PolicyOperator.NE,  # Will need special handling
        "greater_than": PolicyOperator.GT,
        "less_than": PolicyOperator.LT
    }
    
    # Build policy expression if provided
    expression = None
    if "rules" in policy_data:
        rules = []
        for rule_data in policy_data["rules"]:
            # Handle nested expression structure from admin UI
            if "expression" in rule_data:
                expr_data = rule_data["expression"]
                operator_str = expr_data["operator"]
                operator = operator_map.get(operator_str, PolicyOperator.EQ)
                
                rule = PolicyRule(
                    field=expr_data["field"],
                    operator=operator,
                    value=expr_data["value"]
                )
            else:
                # Handle direct rule structure
                operator_str = rule_data["operator"]
                operator = operator_map.get(operator_str, PolicyOperator.EQ)
                
                rule = PolicyRule(
                    field=rule_data["field"],
                    operator=operator,
                    value=rule_data["value"]
                )
            rules.append(rule)
        
        if rules:
            expression = PolicyExpression(
                rules=rules,
                operator=policy_data.get("rule_operator", "and")
            )
    
    # Generate a unique ID if not provided
    import uuid
    policy_id = policy_data.get("id", str(uuid.uuid4()))
    
    policy = Policy(
        id=policy_id,
        name=policy_data["name"],
        description=policy_data.get("description"),
        budget=policy_data.get("budget"),
        expression=expression,
        on_violation=PolicyViolationAction(policy_data.get("action", policy_data.get("on_violation", "advisory"))),
        enabled=policy_data.get("enabled", True)
    )
    
    policy_engine.add_policy(policy)
    
    # Send webhook notification
    try:
        from ..webhooks.events import WebhookEventService
        webhook_service = WebhookEventService()
        await webhook_service.send_policy_created_event(
            policy_data=policy.model_dump(),
            created_by="api_user"  # TODO: Get from auth context
        )
    except Exception as e:
        logger.warning(f"Failed to send policy created webhook: {e}")
    
    return {"message": f"Policy {policy.id} created successfully"}


async def update_policy(policy_id: str, policy_data: Dict[str, Any]) -> Dict[str, Any]:
    """Update an existing policy"""
    from ..types.policy import Policy, PolicyViolationAction, PolicyExpression, PolicyRule, PolicyOperator
    
    # Map string operators to enum values
    operator_map = {
        "equals": PolicyOperator.EQ,
        "not_equals": PolicyOperator.NE,
        "in": PolicyOperator.IN,
        "not_in": PolicyOperator.NE,  # Will need special handling
        "greater_than": PolicyOperator.GT,
        "less_than": PolicyOperator.LT
    }
    
    # Check if policy exists
    existing_policy = policy_engine.get_policy(policy_id)
    if not existing_policy:
        raise ValueError(f"Policy {policy_id} not found")
    
    # Build policy expression if provided
    expression = None
    if "rules" in policy_data:
        rules = []
        for rule_data in policy_data["rules"]:
            # Handle nested expression structure from admin UI
            if "expression" in rule_data:
                expr_data = rule_data["expression"]
                operator_str = expr_data["operator"]
                operator = operator_map.get(operator_str, PolicyOperator.EQ)
                
                rule = PolicyRule(
                    field=expr_data["field"],
                    operator=operator,
                    value=expr_data["value"]
                )
            else:
                # Handle direct rule structure
                operator_str = rule_data["operator"]
                operator = operator_map.get(operator_str, PolicyOperator.EQ)
                
                rule = PolicyRule(
                    field=rule_data["field"],
                    operator=operator,
                    value=rule_data["value"]
                )
            rules.append(rule)
        
        if rules:
            expression = PolicyExpression(
                rules=rules,
                operator=policy_data.get("rule_operator", "and")
            )
    
    # Create updated policy
    policy = Policy(
        id=policy_id,  # Keep the original ID
        name=policy_data["name"],
        description=policy_data.get("description", ""),
        budget=policy_data.get("budget"),
        expression=expression,
        on_violation=PolicyViolationAction(policy_data.get("action", policy_data.get("on_violation", "advisory"))),
        enabled=policy_data.get("enabled", True)
    )
    
    # Update the policy
    success = policy_engine.update_policy(policy_id, policy)
    if not success:
        raise ValueError(f"Failed to update policy {policy_id}")
    
    # Invalidate cache for this policy
    analysis_cache.invalidate_policy(policy_id)
    
    # Send webhook notification
    try:
        from ..webhooks.events import WebhookEventService
        webhook_service = WebhookEventService()
        changes = {
            "old_policy": existing_policy.model_dump(),
            "new_policy": policy.model_dump()
        }
        await webhook_service.send_policy_updated_event(
            policy_data=policy.model_dump(),
            updated_by="api_user",  # TODO: Get from auth context
            changes=changes
        )
    except Exception as e:
        logger.warning(f"Failed to send policy updated webhook: {e}")
    
    return {
        "id": policy.id,
        "name": policy.name,
        "description": policy.description,
        "enabled": policy.enabled,
        "message": f"Policy {policy.name} updated successfully"
    }


async def delete_policy(policy_id: str) -> Dict[str, Any]:
    """Delete a policy by ID"""
    # Get policy before deletion for webhook
    policy = policy_engine.get_policy(policy_id)
    if not policy:
        raise ValueError(f"Policy {policy_id} not found")
    
    success = policy_engine.remove_policy(policy_id)
    if not success:
        raise ValueError(f"Policy {policy_id} not found")
    
    # Invalidate cache for this policy
    analysis_cache.invalidate_policy(policy_id)
    
    # Send webhook notification
    try:
        from ..webhooks.events import WebhookEventService
        webhook_service = WebhookEventService()
        await webhook_service.send_policy_deleted_event(
            policy_id=policy.id,
            policy_name=policy.name,
            deleted_by="api_user"  # TODO: Get from auth context
        )
    except Exception as e:
        logger.warning(f"Failed to send policy deleted webhook: {e}")
    
    return {"message": f"Policy {policy_id} deleted successfully"}
