"""
Unit tests for checkCostImpact functionality
"""

import pytest
import base64
from finopsguard.api.handlers import check_cost_impact
from finopsguard.types.api import CheckRequest


@pytest.mark.asyncio
async def test_check_cost_impact_basic():
    """Test basic cost impact check with Terraform"""
    # Simple Terraform configuration
    terraform_content = '''
    resource "aws_instance" "example" {
        instance_type = "t3.medium"
    }
    provider "aws" {
        region = "us-east-1"
    }
    '''
    
    payload = base64.b64encode(terraform_content.encode()).decode()
    
    request = CheckRequest(
        iac_type="terraform",
        iac_payload=payload,
        environment="dev"
    )
    
    response = await check_cost_impact(request)
    
    assert response.estimated_monthly_cost > 0
    assert response.estimated_first_week_cost > 0
    assert len(response.breakdown_by_resource) > 0
    assert response.pricing_confidence in ['high', 'medium', 'low']
    assert response.duration_ms > 0


@pytest.mark.asyncio
async def test_check_cost_impact_with_budget():
    """Test cost impact check with budget rules"""
    terraform_content = '''
    resource "aws_instance" "example" {
        instance_type = "t3.medium"
    }
    provider "aws" {
        region = "us-east-1"
    }
    '''
    
    payload = base64.b64encode(terraform_content.encode()).decode()
    
    request = CheckRequest(
        iac_type="terraform",
        iac_payload=payload,
        environment="dev",
        budget_rules={"monthly_budget": 25}
    )
    
    response = await check_cost_impact(request)
    
    assert response.policy_eval is not None
    assert response.policy_eval.policy_id == "monthly_budget"
    assert response.policy_eval.status in ['pass', 'fail']


@pytest.mark.asyncio
async def test_check_cost_impact_invalid_request():
    """Test cost impact check with invalid request"""
    with pytest.raises(ValueError, match="invalid_request"):
        await check_cost_impact(CheckRequest(
            iac_type="terraform",
            iac_payload="",
            environment="dev"
        ))


@pytest.mark.asyncio
async def test_check_cost_impact_invalid_encoding():
    """Test cost impact check with invalid base64 encoding"""
    with pytest.raises(ValueError, match="invalid_payload_encoding"):
        await check_cost_impact(CheckRequest(
            iac_type="terraform",
            iac_payload="invalid-base64!",
            environment="dev"
        ))
