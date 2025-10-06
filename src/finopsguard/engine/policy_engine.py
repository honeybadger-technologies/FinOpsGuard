"""
Policy evaluation engine
"""

from typing import Dict, List, Any, Optional
from ..types.policy import Policy, PolicyStore, PolicyEvaluationResult, PolicyViolationAction
from ..types.models import CanonicalResourceModel
from ..types.api import CheckResponse


class PolicyEngine:
    """Main policy evaluation engine"""
    
    def __init__(self):
        self.policy_store = PolicyStore()
    
    def evaluate_policies(self, 
                         cr_model: CanonicalResourceModel,
                         check_response: CheckResponse,
                         environment: str,
                         custom_policies: Optional[List[Policy]] = None) -> PolicyEvaluationResult:
        """Evaluate all applicable policies against the infrastructure and cost analysis"""
        
        # Build evaluation context
        context = self._build_evaluation_context(cr_model, check_response, environment)
        
        # Get policies to evaluate
        policies_to_evaluate = self.policy_store.get_enabled_policies()
        if custom_policies:
            policies_to_evaluate.extend(custom_policies)
        
        # Evaluate each policy
        blocking_violations = []
        advisory_violations = []
        passed_policies = []
        
        for policy in policies_to_evaluate:
            # For resource-specific policies, evaluate against each resource
            if policy.expression and self._is_resource_specific_policy(policy):
                resource_violations = self._evaluate_resource_specific_policy(policy, context)
                if resource_violations:
                    if policy.on_violation == PolicyViolationAction.BLOCK:
                        blocking_violations.extend(resource_violations)
                    else:
                        advisory_violations.extend(resource_violations)
                else:
                    passed_policies.append(policy.id)
            else:
                # For budget and global policies, evaluate against the full context
                result = policy.evaluate(context)
                
                if result["status"] == "fail":
                    violation = {
                        "policy_id": result["policy_id"],
                        "policy_name": result["policy_name"],
                        "reason": result["reason"],
                        "violation_details": result["violation_details"]
                    }
                    
                    if policy.on_violation == PolicyViolationAction.BLOCK:
                        blocking_violations.append(violation)
                    else:
                        advisory_violations.append(violation)
                else:
                    passed_policies.append(policy.id)
        
        # Determine overall status
        overall_status = "pass"
        if blocking_violations:
            overall_status = "block"
        elif advisory_violations:
            overall_status = "advisory"
        
        return PolicyEvaluationResult(
            overall_status=overall_status,
            blocking_violations=blocking_violations,
            advisory_violations=advisory_violations,
            passed_policies=passed_policies,
            evaluation_context=context
        )
    
    def evaluate_single_policy(self, policy_id: str, context: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Evaluate a single policy by ID"""
        policy = self.policy_store.get_policy(policy_id)
        if not policy:
            return None
        
        return policy.evaluate(context)
    
    def add_policy(self, policy: Policy) -> None:
        """Add a new policy to the store"""
        self.policy_store.add_policy(policy)
    
    def update_policy(self, policy_id: str, updated_policy: Policy) -> bool:
        """Update an existing policy in the store"""
        return self.policy_store.update_policy(policy_id, updated_policy)
    
    def remove_policy(self, policy_id: str) -> bool:
        """Remove a policy from the store"""
        return self.policy_store.remove_policy(policy_id)
    
    def get_policy(self, policy_id: str) -> Optional[Policy]:
        """Get a policy by ID"""
        return self.policy_store.get_policy(policy_id)
    
    def list_policies(self) -> List[Policy]:
        """List all policies"""
        return self.policy_store.list_policies()
    
    def _build_evaluation_context(self, 
                                 cr_model: CanonicalResourceModel,
                                 check_response: CheckResponse,
                                 environment: str) -> Dict[str, Any]:
        """Build the evaluation context from resources and cost analysis"""
        context = {
            "environment": environment,
            "estimated_monthly_cost": check_response.estimated_monthly_cost,
            "estimated_first_week_cost": check_response.estimated_first_week_cost,
            "pricing_confidence": check_response.pricing_confidence,
            "risk_flags": check_response.risk_flags,
            "total_resources": len(cr_model.resources),
            "resources": []
        }
        
        # Add resource details
        for resource in cr_model.resources:
            resource_context = {
                "id": resource.id,
                "type": resource.type,
                "name": resource.name,
                "region": resource.region,
                "size": resource.size,
                "count": resource.count,
                "tags": resource.tags or {},
                "metadata": resource.metadata or {}
            }
            
            # Add cost information if available
            for breakdown in check_response.breakdown_by_resource:
                if breakdown.resource_id == resource.id:
                    resource_context["monthly_cost"] = breakdown.monthly_cost
                    resource_context["cost_notes"] = breakdown.notes or []
                    break
            
            context["resources"].append(resource_context)
        
        # Add aggregated resource type counts
        resource_type_counts = {}
        for resource in cr_model.resources:
            resource_type_counts[resource.type] = resource_type_counts.get(resource.type, 0) + resource.count
        
        context["resource_type_counts"] = resource_type_counts
        
        # Add region distribution
        region_counts = {}
        for resource in cr_model.resources:
            region_counts[resource.region] = region_counts.get(resource.region, 0) + resource.count
        
        context["region_counts"] = region_counts
        
        return context
    
    def _is_resource_specific_policy(self, policy: Policy) -> bool:
        """Check if a policy is resource-specific (contains resource.* fields)"""
        if not policy.expression:
            return False
        
        for rule in policy.expression.rules:
            if rule.field.startswith("resource."):
                return True
        return False
    
    def _evaluate_resource_specific_policy(self, policy: Policy, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Evaluate a resource-specific policy against each resource"""
        violations = []
        
        for resource in context.get("resources", []):
            # Create a resource-specific context
            resource_context = context.copy()
            resource_context["resource"] = resource
            
            # Evaluate the policy against this resource
            result = policy.evaluate(resource_context)
            
            if result["status"] == "fail":
                violation = {
                    "policy_id": result["policy_id"],
                    "policy_name": result["policy_name"],
                    "reason": f"{result['reason']} (resource: {resource['id']})",
                    "violation_details": result["violation_details"],
                    "resource_id": resource["id"]
                }
                violations.append(violation)
        
        return violations


class PolicyDSLParser:
    """Parser for policy DSL syntax"""
    
    @staticmethod
    def parse_policy_dsl(dsl_text: str) -> Policy:
        """Parse policy DSL text into a Policy object"""
        # This is a simplified parser - in a real implementation, you'd use a proper parser
        lines = [line.strip() for line in dsl_text.strip().split('\n') if line.strip()]
        
        if not lines or not lines[0].startswith('policy'):
            raise ValueError("Invalid policy DSL: must start with 'policy' declaration")
        
        # Extract policy name
        policy_line = lines[0]
        policy_name = policy_line.split('"')[1] if '"' in policy_line else "unnamed_policy"
        policy_id = policy_name.replace(' ', '_').lower()
        
        policy_dict = {
            "id": policy_id,
            "name": policy_name,
            "budget": None,
            "expression": None,
            "on_violation": "advisory"
        }
        
        # Parse policy body
        in_body = False
        for line in lines[1:]:
            if line == '{':
                in_body = True
                continue
            elif line == '}':
                break
            elif not in_body:
                continue
            
            if ':' in line:
                key, value = line.split(':', 1)
                key = key.strip()
                value = value.strip().rstrip(',')
                
                if key == 'budget':
                    policy_dict['budget'] = float(value)
                elif key == 'on_violation':
                    policy_dict['on_violation'] = value.strip('"')
                elif key == 'rule':
                    # Parse rule expression
                    policy_dict['expression'] = PolicyDSLParser._parse_rule_expression(value.strip('"'))
        
        return Policy(**policy_dict)
    
    @staticmethod
    def _parse_rule_expression(rule_text: str):
        """Parse a rule expression string"""
        # Simplified rule parsing - would need more sophisticated parsing in production
        from ..types.policy import PolicyExpression, PolicyRule, PolicyOperator
        
        # For now, just handle simple equality comparisons
        if '==' in rule_text:
            parts = rule_text.split('==')
            if len(parts) == 2:
                field = parts[0].strip()
                value = parts[1].strip().strip('"')
                
                # Handle simple AND conditions
                if 'and' in field:
                    rules = []
                    for condition in field.split('and'):
                        if '==' in condition:
                            cond_parts = condition.split('==')
                            if len(cond_parts) == 2:
                                rules.append(PolicyRule(
                                    field=cond_parts[0].strip(),
                                    operator=PolicyOperator.EQ,
                                    value=cond_parts[1].strip().strip('"')
                                ))
                    return PolicyExpression(rules=rules, operator="and")
                else:
                    return PolicyExpression(rules=[PolicyRule(
                        field=field,
                        operator=PolicyOperator.EQ,
                        value=value
                    )])
        
        return None
