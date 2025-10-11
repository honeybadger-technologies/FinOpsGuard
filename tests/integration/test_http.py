"""
Integration tests for HTTP endpoints
"""

import base64
from fastapi.testclient import TestClient
from finopsguard.main import app


client = TestClient(app)


def test_health_check():
    """Test health check endpoint"""
    response = client.get("/healthz")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "now" in data


def test_metrics_endpoint():
    """Test metrics endpoint"""
    response = client.get("/metrics")
    assert response.status_code == 200
    assert response.headers["content-type"] == "text/plain; charset=utf-8"


def test_check_cost_impact_endpoint():
    """Test checkCostImpact endpoint"""
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
        "environment": "dev"
    }
    
    response = client.post("/mcp/checkCostImpact", json=request_data)
    assert response.status_code == 200
    
    data = response.json()
    assert "estimated_monthly_cost" in data
    assert "estimated_first_week_cost" in data
    assert "breakdown_by_resource" in data
    assert "pricing_confidence" in data
    assert data["estimated_monthly_cost"] > 0


def test_check_cost_impact_invalid_request():
    """Test checkCostImpact with invalid request"""
    request_data = {
        "iac_type": "terraform",
        "iac_payload": "",
        "environment": "dev"
    }
    
    response = client.post("/mcp/checkCostImpact", json=request_data)
    assert response.status_code == 400
    assert "detail" in response.json()
    assert "error" in response.json()["detail"]


def test_get_price_catalog_endpoint():
    """Test getPriceCatalog endpoint"""
    request_data = {
        "cloud": "aws",
        "region": "us-east-1"
    }
    
    response = client.post("/mcp/getPriceCatalog", json=request_data)
    assert response.status_code == 200
    
    data = response.json()
    assert "updated_at" in data
    assert "pricing_confidence" in data
    assert "items" in data


def test_list_recent_analyses_endpoint():
    """Test listRecentAnalyses endpoint"""
    request_data = {
        "limit": 10
    }
    
    response = client.post("/mcp/listRecentAnalyses", json=request_data)
    assert response.status_code == 200
    
    data = response.json()
    assert "items" in data
    assert "next_cursor" in data
