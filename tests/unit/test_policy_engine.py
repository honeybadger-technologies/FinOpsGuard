"""
Unit tests for policy engine functionality
"""

import pytest
from finopsguard.types.policy import (
    Policy, PolicyRule, PolicyExpression, PolicyOperator, 
    PolicyViolationAction
)
from finopsguard.engine.policy_engine import PolicyEngine
from finopsguard.types.models import CanonicalResource, CanonicalResourceModel
from finopsguard.types.api import CheckResponse, ResourceBreakdownItem


@pytest.fixture
def policy_engine():
    """Create a policy engine instance for testing"""
    return PolicyEngine()


@pytest.fixture
def sample_cr_model():
    """Create a sample canonical resource model"""
    resources = [
        CanonicalResource(
            id="test-instance-1",
            type="aws_instance",
            name="test-instance",
            region="us-east-1",
            size="t3.medium",
            count=1,
            tags={},
            metadata={}
        )
    ]
    return CanonicalResourceModel(resources=resources)


@pytest.fixture
def sample_check_response():
    """Create a sample check response"""
    return CheckResponse(
        estimated_monthly_cost=50.0,
        estimated_first_week_cost=12.5,
        breakdown_by_resource=[
            ResourceBreakdownItem(
                resource_id="test-instance-1",
                monthly_cost=50.0,
                notes=[]
            )
        ],
        risk_flags=[],
        recommendations=[],
        pricing_confidence="high",
        duration_ms=100
    )


class TestPolicyRule:
    """Test policy rule evaluation"""
    
    def test_equality_rule(self):
        """Test equality rule evaluation"""
        rule = PolicyRule(field="environment", operator=PolicyOperator.EQ, value="dev")
        context = {"environment": "dev"}
        assert rule.evaluate(context) is True
        
        context = {"environment": "prod"}
        assert rule.evaluate(context) is False
    
    def test_numeric_comparison_rule(self):
        """Test numeric comparison rules"""
        rule = PolicyRule(field="estimated_monthly_cost", operator=PolicyOperator.GT, value=100.0)
        context = {"estimated_monthly_cost": 150.0}
        assert rule.evaluate(context) is True
        
        context = {"estimated_monthly_cost": 50.0}
        assert rule.evaluate(context) is False
    
    def test_in_operator_rule(self):
        """Test 'in' operator rule"""
        rule = PolicyRule(field="resource.type", operator=PolicyOperator.IN, 
                         value=["aws_instance", "aws_db_instance"])
        context = {"resource": {"type": "aws_instance"}}
        assert rule.evaluate(context) is True
        
        context = {"resource": {"type": "aws_s3_bucket"}}
        assert rule.evaluate(context) is False
    
    def test_contains_rule(self):
        """Test contains operator rule"""
        rule = PolicyRule(field="resource.size", operator=PolicyOperator.CONTAINS, value="large")
        context = {"resource": {"size": "t3.large"}}
        assert rule.evaluate(context) is True
        
        context = {"resource": {"size": "t3.small"}}
        assert rule.evaluate(context) is False


class TestPolicyExpression:
    """Test policy expression evaluation"""
    
    def test_and_expression(self):
        """Test AND expression evaluation"""
        rules = [
            PolicyRule(field="environment", operator=PolicyOperator.EQ, value="dev"),
            PolicyRule(field="estimated_monthly_cost", operator=PolicyOperator.LT, value=100.0)
        ]
        expression = PolicyExpression(rules=rules, operator="and")
        
        context = {"environment": "dev", "estimated_monthly_cost": 50.0}
        assert expression.evaluate(context) is True
        
        context = {"environment": "prod", "estimated_monthly_cost": 50.0}
        assert expression.evaluate(context) is False
        
        context = {"environment": "dev", "estimated_monthly_cost": 150.0}
        assert expression.evaluate(context) is False
    
    def test_or_expression(self):
        """Test OR expression evaluation"""
        rules = [
            PolicyRule(field="environment", operator=PolicyOperator.EQ, value="dev"),
            PolicyRule(field="environment", operator=PolicyOperator.EQ, value="staging")
        ]
        expression = PolicyExpression(rules=rules, operator="or")
        
        context = {"environment": "dev"}
        assert expression.evaluate(context) is True
        
        context = {"environment": "staging"}
        assert expression.evaluate(context) is True
        
        context = {"environment": "prod"}
        assert expression.evaluate(context) is False


class TestPolicy:
    """Test policy evaluation"""
    
    def test_budget_policy_pass(self):
        """Test budget policy that passes"""
        policy = Policy(
            id="test_budget",
            name="Test Budget",
            budget=100.0,
            on_violation=PolicyViolationAction.ADVISORY
        )
        
        context = {"estimated_monthly_cost": 50.0}
        result = policy.evaluate(context)
        
        assert result["status"] == "pass"
        assert result["policy_id"] == "test_budget"
        assert "within budget" in result["reason"]
    
    def test_budget_policy_fail(self):
        """Test budget policy that fails"""
        policy = Policy(
            id="test_budget",
            name="Test Budget",
            budget=100.0,
            on_violation=PolicyViolationAction.ADVISORY
        )
        
        context = {"estimated_monthly_cost": 150.0}
        result = policy.evaluate(context)
        
        assert result["status"] == "fail"
        assert result["policy_id"] == "test_budget"
        assert "exceeds budget" in result["reason"]
        assert result["violation_details"]["actual_cost"] == 150.0
        assert result["violation_details"]["budget_limit"] == 100.0
        assert result["violation_details"]["overage"] == 50.0
    
    def test_rule_policy_pass(self):
        """Test rule-based policy that passes"""
        rules = [
            PolicyRule(field="environment", operator=PolicyOperator.EQ, value="dev")
        ]
        expression = PolicyExpression(rules=rules, operator="and")
        
        policy = Policy(
            id="test_rule",
            name="Test Rule",
            expression=expression,
            on_violation=PolicyViolationAction.BLOCK
        )
        
        # Test with conditions that should NOT trigger the policy (prod environment)
        context = {"environment": "prod"}
        result = policy.evaluate(context)
        
        assert result["status"] == "pass"
        assert result["policy_id"] == "test_rule"
        assert "rules satisfied" in result["reason"]
    
    def test_rule_policy_fail(self):
        """Test rule-based policy that fails"""
        rules = [
            PolicyRule(field="environment", operator=PolicyOperator.EQ, value="dev"),
            PolicyRule(field="estimated_monthly_cost", operator=PolicyOperator.LT, value=100.0)
        ]
        expression = PolicyExpression(rules=rules, operator="and")
        
        policy = Policy(
            id="test_rule",
            name="Test Rule",
            expression=expression,
            on_violation=PolicyViolationAction.BLOCK
        )
        
        # Test with conditions that SHOULD trigger the policy (dev environment with low cost)
        context = {"environment": "dev", "estimated_monthly_cost": 50.0}
        result = policy.evaluate(context)
        
        assert result["status"] == "fail"
        assert result["policy_id"] == "test_rule"
        assert "rule violation" in result["reason"]
        assert "violation_details" in result


class TestPolicyEngine:
    """Test policy engine functionality"""
    
    def test_evaluate_policies_no_violations(self, policy_engine, sample_cr_model, sample_check_response):
        """Test policy evaluation with no violations"""
        result = policy_engine.evaluate_policies(
            cr_model=sample_cr_model,
            check_response=sample_check_response,
            environment="prod"
        )
        
        assert result.overall_status == "pass"
        assert len(result.blocking_violations) == 0
        assert len(result.advisory_violations) == 0
        assert len(result.passed_policies) > 0
    
    def test_evaluate_policies_with_advisory_violation(self, policy_engine, sample_cr_model, sample_check_response):
        """Test policy evaluation with advisory violations"""
        # Create a high-cost response to trigger budget violation
        high_cost_response = CheckResponse(
            estimated_monthly_cost=1500.0,
            estimated_first_week_cost=375.0,
            breakdown_by_resource=[
                ResourceBreakdownItem(
                    resource_id="test-instance-1",
                    monthly_cost=1500.0,
                    notes=[]
                )
            ],
            risk_flags=[],
            recommendations=[],
            pricing_confidence="high",
            duration_ms=100
        )
        
        result = policy_engine.evaluate_policies(
            cr_model=sample_cr_model,
            check_response=high_cost_response,
            environment="prod"
        )
        
        assert result.overall_status == "advisory"
        assert len(result.advisory_violations) > 0
        assert len(result.blocking_violations) == 0
    
    def test_evaluate_policies_with_blocking_violation(self, policy_engine, sample_check_response):
        """Test policy evaluation with blocking violations"""
        # Create a resource model with large instance in dev
        large_instance_resources = [
            CanonicalResource(
                id="test-large-instance",
                type="aws_instance",
                name="test-large-instance",
                region="us-east-1",
                size="m5.large",  # This should trigger the blocking policy
                count=1,
                tags={},
                metadata={}
            )
        ]
        large_instance_cr_model = CanonicalResourceModel(resources=large_instance_resources)
        
        # Create a dev environment response to trigger blocking policy
        result = policy_engine.evaluate_policies(
            cr_model=large_instance_cr_model,
            check_response=sample_check_response,
            environment="dev"
        )
        
        # Should have blocking violations for large instances in dev
        assert result.overall_status == "block"
        assert len(result.blocking_violations) > 0
    
    def test_policy_management(self, policy_engine):
        """Test policy management operations"""
        # Test listing policies
        policies = policy_engine.list_policies()
        assert len(policies) > 0
        
        # Test getting a specific policy
        policy = policy_engine.get_policy("default_monthly_budget")
        assert policy is not None
        assert policy.id == "default_monthly_budget"
        
        # Test adding a custom policy
        custom_policy = Policy(
            id="test_custom",
            name="Test Custom Policy",
            budget=500.0,
            on_violation=PolicyViolationAction.BLOCK
        )
        policy_engine.add_policy(custom_policy)
        
        retrieved_policy = policy_engine.get_policy("test_custom")
        assert retrieved_policy is not None
        assert retrieved_policy.budget == 500.0
        
        # Test removing a policy
        success = policy_engine.remove_policy("test_custom")
        assert success is True
        
        removed_policy = policy_engine.get_policy("test_custom")
        assert removed_policy is None
