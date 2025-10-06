"""
Policy types and DSL definitions
"""

from typing import Dict, List, Optional, Union, Any
from enum import Enum
from pydantic import BaseModel, Field
from .models import CanonicalResourceModel


class PolicyViolationAction(str, Enum):
    """Actions to take when a policy is violated"""
    ADVISORY = "advisory"
    BLOCK = "block"


class PolicyOperator(str, Enum):
    """Supported operators for policy rules"""
    EQ = "=="
    NE = "!="
    GT = ">"
    GTE = ">="
    LT = "<"
    LTE = "<="
    IN = "in"
    CONTAINS = "contains"
    STARTS_WITH = "starts_with"
    ENDS_WITH = "ends_with"


class PolicyRule(BaseModel):
    """A single policy rule expression"""
    field: str = Field(..., description="Field to evaluate (e.g., 'resource.type', 'environment')")
    operator: PolicyOperator = Field(..., description="Comparison operator")
    value: Union[str, int, float, List[str]] = Field(..., description="Value to compare against")
    
    def evaluate(self, context: Dict[str, Any]) -> bool:
        """Evaluate the rule against a context"""
        field_value = self._get_field_value(context, self.field)
        
        if self.operator == PolicyOperator.EQ:
            return field_value == self.value
        elif self.operator == PolicyOperator.NE:
            return field_value != self.value
        elif self.operator == PolicyOperator.GT:
            return self._compare_numeric(field_value, self.value, lambda a, b: a > b)
        elif self.operator == PolicyOperator.GTE:
            return self._compare_numeric(field_value, self.value, lambda a, b: a >= b)
        elif self.operator == PolicyOperator.LT:
            return self._compare_numeric(field_value, self.value, lambda a, b: a < b)
        elif self.operator == PolicyOperator.LTE:
            return self._compare_numeric(field_value, self.value, lambda a, b: a <= b)
        elif self.operator == PolicyOperator.IN:
            return field_value in self.value if isinstance(self.value, list) else False
        elif self.operator == PolicyOperator.CONTAINS:
            return str(self.value).lower() in str(field_value).lower()
        elif self.operator == PolicyOperator.STARTS_WITH:
            return str(field_value).startswith(str(self.value))
        elif self.operator == PolicyOperator.ENDS_WITH:
            return str(field_value).endswith(str(self.value))
        
        return False
    
    def _get_field_value(self, context: Dict[str, Any], field: str) -> Any:
        """Get nested field value from context"""
        parts = field.split('.')
        value = context
        
        for part in parts:
            if isinstance(value, dict) and part in value:
                value = value[part]
            elif isinstance(value, list) and part.isdigit():
                index = int(part)
                if 0 <= index < len(value):
                    value = value[index]
                else:
                    return None
            else:
                return None
        
        return value
    
    def _compare_numeric(self, a: Any, b: Any, compare_func) -> bool:
        """Compare numeric values safely"""
        try:
            num_a = float(a) if a is not None else 0
            num_b = float(b) if b is not None else 0
            return compare_func(num_a, num_b)
        except (ValueError, TypeError):
            return False


class PolicyExpression(BaseModel):
    """A policy expression that can contain multiple rules with logical operators"""
    rules: List[PolicyRule] = Field(..., description="List of rules")
    operator: str = Field(default="and", description="Logical operator ('and' or 'or')")
    
    def evaluate(self, context: Dict[str, Any]) -> bool:
        """Evaluate the expression against a context"""
        if not self.rules:
            return True
        
        results = [rule.evaluate(context) for rule in self.rules]
        
        if self.operator.lower() == "or":
            return any(results)
        else:  # default to "and"
            return all(results)


class Policy(BaseModel):
    """A complete policy definition"""
    id: str = Field(..., description="Unique policy identifier")
    name: str = Field(..., description="Human-readable policy name")
    description: Optional[str] = Field(None, description="Policy description")
    expression: Optional[PolicyExpression] = Field(None, description="Rule expression")
    budget: Optional[float] = Field(None, description="Budget limit for budget policies")
    on_violation: PolicyViolationAction = Field(default=PolicyViolationAction.ADVISORY, 
                                               description="Action to take on violation")
    enabled: bool = Field(default=True, description="Whether the policy is enabled")
    
    def evaluate(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Evaluate the policy against a context"""
        result = {
            "policy_id": self.id,
            "policy_name": self.name,
            "status": "pass",
            "reason": None,
            "violation_details": None
        }
        
        if not self.enabled:
            result["reason"] = "Policy is disabled"
            return result
        
        # Budget-based policy
        if self.budget is not None:
            monthly_cost = context.get("estimated_monthly_cost", 0)
            if monthly_cost > self.budget:
                result["status"] = "fail"
                result["reason"] = f"Monthly cost ${monthly_cost:.2f} exceeds budget ${self.budget:.2f}"
                result["violation_details"] = {
                    "actual_cost": monthly_cost,
                    "budget_limit": self.budget,
                    "overage": monthly_cost - self.budget
                }
            else:
                result["reason"] = f"Monthly cost ${monthly_cost:.2f} within budget ${self.budget:.2f}"
        
        # Rule-based policy
        elif self.expression:
            # For policies that define what should NOT happen (like "no GPU in dev"),
            # the policy fails when the expression is TRUE (conditions are met)
            if self.expression.evaluate(context):
                result["status"] = "fail"
                result["reason"] = f"Policy '{self.name}' rule violation"
                result["violation_details"] = {
                    "failed_rules": [rule.model_dump() for rule in self.expression.rules 
                                   if rule.evaluate(context)]
                }
            else:
                result["reason"] = f"Policy '{self.name}' rules satisfied"
        
        return result


class PolicyEvaluationResult(BaseModel):
    """Result of evaluating multiple policies"""
    overall_status: str = Field(..., description="Overall evaluation status")
    blocking_violations: List[Dict[str, Any]] = Field(default_factory=list, 
                                                     description="Blocking policy violations")
    advisory_violations: List[Dict[str, Any]] = Field(default_factory=list, 
                                                     description="Advisory policy violations")
    passed_policies: List[str] = Field(default_factory=list, 
                                      description="IDs of policies that passed")
    evaluation_context: Dict[str, Any] = Field(default_factory=dict, 
                                              description="Context used for evaluation")


class PolicyStore:
    """In-memory policy storage and management"""
    
    def __init__(self):
        self._policies: Dict[str, Policy] = {}
        self._default_policies()
    
    def _default_policies(self):
        """Initialize with some default policies"""
        # Default budget policy
        budget_policy = Policy(
            id="default_monthly_budget",
            name="Default Monthly Budget",
            description="Default monthly budget limit",
            budget=1000.0,
            on_violation=PolicyViolationAction.ADVISORY
        )
        self.add_policy(budget_policy)
        
        # No GPU instances in dev
        gpu_policy = Policy(
            id="no_gpu_in_dev",
            name="No GPU Instances in Development",
            description="Prevent GPU instances in development environment",
            expression=PolicyExpression(
                rules=[
                    PolicyRule(field="resource.type", operator=PolicyOperator.EQ, value="aws_gpu_instance"),
                    PolicyRule(field="environment", operator=PolicyOperator.EQ, value="dev")
                ],
                operator="and"
            ),
            on_violation=PolicyViolationAction.ADVISORY
        )
        self.add_policy(gpu_policy)
        
        # No large instances in dev
        large_instance_policy = Policy(
            id="no_large_instances_in_dev",
            name="No Large Instances in Development",
            description="Prevent large instance types in development environment",
            expression=PolicyExpression(
                rules=[
                    PolicyRule(field="resource.size", operator=PolicyOperator.IN, 
                              value=["m5.large", "m5.xlarge", "m5.2xlarge", "c5.large", "c5.xlarge"]),
                    PolicyRule(field="environment", operator=PolicyOperator.EQ, value="dev")
                ],
                operator="and"
            ),
            on_violation=PolicyViolationAction.BLOCK
        )
        self.add_policy(large_instance_policy)
    
    def add_policy(self, policy: Policy) -> None:
        """Add or update a policy"""
        self._policies[policy.id] = policy
    
    def update_policy(self, policy_id: str, updated_policy: Policy) -> bool:
        """Update an existing policy by ID"""
        if policy_id in self._policies:
            # Preserve the original ID
            updated_policy.id = policy_id
            self._policies[policy_id] = updated_policy
            return True
        return False
    
    def remove_policy(self, policy_id: str) -> bool:
        """Remove a policy by ID"""
        if policy_id in self._policies:
            del self._policies[policy_id]
            return True
        return False
    
    def get_policy(self, policy_id: str) -> Optional[Policy]:
        """Get a policy by ID"""
        return self._policies.get(policy_id)
    
    def list_policies(self) -> List[Policy]:
        """List all policies"""
        return list(self._policies.values())
    
    def get_enabled_policies(self) -> List[Policy]:
        """Get all enabled policies"""
        return [p for p in self._policies.values() if p.enabled]
