"""
Integration tests for policy management endpoints
"""

import pytest
import base64
from fastapi.testclient import TestClient
from finopsguard.main import app


client = TestClient(app)


def test_list_policies_endpoint():
    """Test listing all policies"""
    response = client.get("/mcp/policies")
    assert response.status_code == 200
    
    data = response.json()
    assert "policies" in data
    assert isinstance(data["policies"], list)
    assert len(data["policies"]) > 0
    
    # Check that default policies are present
    policy_ids = [policy["id"] for policy in data["policies"]]
    assert "default_monthly_budget" in policy_ids
    assert "no_gpu_in_dev" in policy_ids


def test_get_policy_endpoint():
    """Test getting a specific policy"""
    response = client.get("/mcp/policies/default_monthly_budget")
    assert response.status_code == 200
    
    data = response.json()
    assert data["id"] == "default_monthly_budget"
    assert data["name"] == "Default Monthly Budget"
    assert data["budget"] == 1000.0
    assert data["on_violation"] == "advisory"
    assert data["enabled"] is True


def test_get_policy_not_found():
    """Test getting a non-existent policy"""
    response = client.get("/mcp/policies/non_existent_policy")
    assert response.status_code == 404
    
    data = response.json()
    assert "error" in data["detail"]


def test_create_policy_endpoint():
    """Test creating a new policy"""
    policy_data = {
        "id": "test_policy",
        "name": "Test Policy",
        "description": "A test policy",
        "budget": 500.0,
        "on_violation": "block",
        "enabled": True
    }
    
    response = client.post("/mcp/policies", json=policy_data)
    assert response.status_code == 200
    
    data = response.json()
    assert "message" in data
    assert "test_policy" in data["message"]
    
    # Verify the policy was created
    get_response = client.get("/mcp/policies/test_policy")
    assert get_response.status_code == 200
    
    policy = get_response.json()
    assert policy["id"] == "test_policy"
    assert policy["budget"] == 500.0
    assert policy["on_violation"] == "block"


def test_create_policy_with_rules():
    """Test creating a policy with rules"""
    policy_data = {
        "id": "test_rule_policy",
        "name": "Test Rule Policy",
        "description": "A test policy with rules",
        "rules": [
            {
                "field": "environment",
                "operator": "==",
                "value": "dev"
            },
            {
                "field": "estimated_monthly_cost",
                "operator": ">",
                "value": 100
            }
        ],
        "rule_operator": "and",
        "on_violation": "advisory",
        "enabled": True
    }
    
    response = client.post("/mcp/policies", json=policy_data)
    assert response.status_code == 200
    
    # Verify the policy was created
    get_response = client.get("/mcp/policies/test_rule_policy")
    assert get_response.status_code == 200
    
    policy = get_response.json()
    assert policy["id"] == "test_rule_policy"
    assert policy["expression"] is not None
    assert len(policy["expression"]["rules"]) == 2


def test_delete_policy_endpoint():
    """Test deleting a policy"""
    # First create a policy to delete
    policy_data = {
        "id": "policy_to_delete",
        "name": "Policy to Delete",
        "budget": 100.0,
        "on_violation": "advisory"
    }
    
    create_response = client.post("/mcp/policies", json=policy_data)
    assert create_response.status_code == 200
    
    # Verify it exists
    get_response = client.get("/mcp/policies/policy_to_delete")
    assert get_response.status_code == 200
    
    # Delete it
    delete_response = client.delete("/mcp/policies/policy_to_delete")
    assert delete_response.status_code == 200
    
    data = delete_response.json()
    assert "message" in data
    assert "deleted" in data["message"]
    
    # Verify it's gone
    get_response = client.get("/mcp/policies/policy_to_delete")
    assert get_response.status_code == 404


def test_delete_policy_not_found():
    """Test deleting a non-existent policy"""
    response = client.delete("/mcp/policies/non_existent_policy")
    assert response.status_code == 404


def test_policy_evaluation_with_blocking():
    """Test policy evaluation with blocking mode"""
    terraform_content = '''
    resource "aws_instance" "example" {
        instance_type = "m5.large"
    }
    provider "aws" {
        region = "us-east-1"
    }
    '''
    
    payload = base64.b64encode(terraform_content.encode()).decode()
    
    request_data = {
        "iac_type": "terraform",
        "iac_payload": payload,
        "environment": "dev",
        "policy_id": "no_large_instances_in_dev",
        "mode": "blocking"
    }
    
    response = client.post("/mcp/evaluatePolicy", json=request_data)
    assert response.status_code == 200
    
    data = response.json()
    assert data["status"] == "fail"  # Should be blocked
    assert "no_large_instances_in_dev" in data["policy_id"]


def test_policy_evaluation_advisory_mode():
    """Test policy evaluation in advisory mode"""
    terraform_content = '''
    resource "aws_instance" "example" {
        instance_type = "m5.large"
    }
    provider "aws" {
        region = "us-east-1"
    }
    '''
    
    payload = base64.b64encode(terraform_content.encode()).decode()
    
    request_data = {
        "iac_type": "terraform",
        "iac_payload": payload,
        "environment": "dev",
        "policy_id": "no_large_instances_in_dev",
        "mode": "advisory"
    }
    
    response = client.post("/mcp/evaluatePolicy", json=request_data)
    assert response.status_code == 200
    
    data = response.json()
    assert data["status"] == "fail"  # Policy still fails, but not blocking
    assert "no_large_instances_in_dev" in data["policy_id"]


def test_cost_impact_with_policy_evaluation():
    """Test cost impact check with policy evaluation"""
    terraform_content = '''
    resource "aws_instance" "example" {
        instance_type = "t3.medium"
    }
    provider "aws" {
        region = "us-east-1"
    }
    '''
    
    payload = base64.b64encode(terraform_content.encode()).decode()
    
    request_data = {
        "iac_type": "terraform",
        "iac_payload": payload,
        "environment": "dev",
        "budget_rules": {"monthly_budget": 25}
    }
    
    response = client.post("/mcp/checkCostImpact", json=request_data)
    assert response.status_code == 200
    
    data = response.json()
    assert "policy_eval" in data
    assert data["policy_eval"]["policy_id"] is not None
    assert data["policy_eval"]["status"] in ["pass", "fail"]
    assert data["policy_eval"]["reason"] is not None
