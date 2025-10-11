"""Integration tests for usage API endpoints."""

import pytest
from datetime import datetime, timedelta
from fastapi.testclient import TestClient
from unittest.mock import patch, Mock

from finopsguard.api.server import app
from finopsguard.types.usage import ResourceUsage, CostUsageRecord, UsageSummary


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


@pytest.fixture
def mock_resource_usage():
    """Mock resource usage data."""
    return ResourceUsage(
        resource_id="i-1234567890abcdef0",
        resource_type="ec2",
        region="us-east-1",
        cloud_provider="aws",
        start_time=datetime(2024, 1, 1),
        end_time=datetime(2024, 1, 7),
        metrics=[],
        avg_cpu_utilization=45.5
    )


@pytest.fixture
def mock_cost_records():
    """Mock cost usage records."""
    return [
        CostUsageRecord(
            date=datetime(2024, 1, 1),
            start_time=datetime(2024, 1, 1),
            end_time=datetime(2024, 1, 2),
            cost=100.0,
            currency="USD",
            usage_amount=24.0,
            usage_unit="hours",
            service="AmazonEC2",
            region="us-east-1"
        )
    ]


@pytest.fixture
def mock_usage_summary():
    """Mock usage summary."""
    return UsageSummary(
        cloud_provider="aws",
        resource_type="ec2",
        region="us-east-1",
        start_time=datetime(2024, 1, 1),
        end_time=datetime(2024, 1, 31),
        total_resources=5,
        total_cost=1000.0,
        average_cost_per_resource=200.0,
        total_usage=3600.0,
        average_usage=720.0,
        usage_unit="hours",
        avg_cpu_utilization=45.5,
        confidence="high"
    )


class TestUsageAvailability:
    """Test usage availability endpoint."""
    
    def test_check_availability(self, client):
        """Test availability check endpoint."""
        response = client.get("/usage/availability")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "enabled" in data
        assert "aws_available" in data
        assert "gcp_available" in data
        assert "azure_available" in data


class TestResourceUsage:
    """Test resource usage endpoint."""
    
    @patch('finopsguard.api.usage_endpoints.get_usage_factory')
    def test_get_resource_usage_disabled(self, mock_factory, client):
        """Test resource usage when integration is disabled."""
        mock_factory_instance = Mock()
        mock_factory_instance.enabled = False
        mock_factory.return_value = mock_factory_instance
        
        response = client.post("/usage/resource", json={
            "cloud_provider": "aws",
            "resource_id": "i-123",
            "resource_type": "ec2",
            "start_time": "2024-01-01T00:00:00Z",
            "end_time": "2024-01-07T00:00:00Z",
            "region": "us-east-1"
        })
        
        assert response.status_code == 503
        assert "not enabled" in response.json()["detail"]
    
    @patch('finopsguard.api.usage_endpoints.get_usage_factory')
    def test_get_resource_usage_unavailable(self, mock_factory, client):
        """Test resource usage when provider is unavailable."""
        mock_factory_instance = Mock()
        mock_factory_instance.enabled = True
        mock_factory_instance.is_available.return_value = False
        mock_factory.return_value = mock_factory_instance
        
        response = client.post("/usage/resource", json={
            "cloud_provider": "aws",
            "resource_id": "i-123",
            "resource_type": "ec2",
            "start_time": "2024-01-01T00:00:00Z",
            "end_time": "2024-01-07T00:00:00Z",
            "region": "us-east-1"
        })
        
        assert response.status_code == 503
        assert "not available" in response.json()["detail"]
    
    @patch('finopsguard.api.usage_endpoints.get_usage_factory')
    def test_get_resource_usage_success(self, mock_factory, client, mock_resource_usage):
        """Test successful resource usage retrieval."""
        mock_factory_instance = Mock()
        mock_factory_instance.enabled = True
        mock_factory_instance.is_available.return_value = True
        mock_factory_instance.get_resource_usage.return_value = mock_resource_usage
        mock_factory.return_value = mock_factory_instance
        
        response = client.post("/usage/resource", json={
            "cloud_provider": "aws",
            "resource_id": "i-1234567890abcdef0",
            "resource_type": "ec2",
            "start_time": "2024-01-01T00:00:00Z",
            "end_time": "2024-01-07T00:00:00Z",
            "region": "us-east-1"
        })
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["resource_id"] == "i-1234567890abcdef0"
        assert data["resource_type"] == "ec2"
        assert data["avg_cpu_utilization"] == 45.5
    
    @patch('finopsguard.api.usage_endpoints.get_usage_factory')
    def test_get_resource_usage_not_found(self, mock_factory, client):
        """Test resource usage when no data found."""
        mock_factory_instance = Mock()
        mock_factory_instance.enabled = True
        mock_factory_instance.is_available.return_value = True
        mock_factory_instance.get_resource_usage.return_value = None
        mock_factory.return_value = mock_factory_instance
        
        response = client.post("/usage/resource", json={
            "cloud_provider": "aws",
            "resource_id": "i-nonexistent",
            "resource_type": "ec2",
            "start_time": "2024-01-01T00:00:00Z",
            "end_time": "2024-01-07T00:00:00Z",
            "region": "us-east-1"
        })
        
        assert response.status_code == 404


class TestCostUsage:
    """Test cost usage endpoint."""
    
    @patch('finopsguard.api.usage_endpoints.get_usage_factory')
    def test_get_cost_usage_success(self, mock_factory, client, mock_cost_records):
        """Test successful cost usage retrieval."""
        mock_factory_instance = Mock()
        mock_factory_instance.enabled = True
        mock_factory_instance.is_available.return_value = True
        mock_factory_instance.get_cost_usage.return_value = mock_cost_records
        mock_factory.return_value = mock_factory_instance
        
        response = client.post("/usage/cost", json={
            "cloud_provider": "aws",
            "start_time": "2024-01-01T00:00:00Z",
            "end_time": "2024-01-31T00:00:00Z",
            "granularity": "DAILY",
            "group_by": ["service"]
        })
        
        assert response.status_code == 200
        data = response.json()
        
        assert len(data) == 1
        assert data[0]["service"] == "AmazonEC2"
        assert data[0]["cost"] == 100.0


class TestUsageSummary:
    """Test usage summary endpoint."""
    
    @patch('finopsguard.api.usage_endpoints.get_usage_factory')
    def test_get_usage_summary_success(self, mock_factory, client, mock_usage_summary):
        """Test successful usage summary generation."""
        mock_factory_instance = Mock()
        mock_factory_instance.enabled = True
        mock_factory_instance.is_available.return_value = True
        mock_factory_instance.get_usage_summary.return_value = mock_usage_summary
        mock_factory.return_value = mock_factory_instance
        
        response = client.post("/usage/summary", json={
            "cloud_provider": "aws",
            "start_time": "2024-01-01T00:00:00Z",
            "end_time": "2024-01-31T00:00:00Z",
            "resource_types": ["ec2"],
            "regions": ["us-east-1"],
            "granularity": "DAILY"
        })
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["cloud_provider"] == "aws"
        assert data["total_resources"] == 5
        assert data["total_cost"] == 1000.0
        assert data["confidence"] == "high"


class TestUsageExample:
    """Test usage example endpoint."""
    
    @patch('finopsguard.api.usage_endpoints.get_usage_factory')
    def test_get_usage_example_success(self, mock_factory, client, mock_cost_records):
        """Test successful usage example retrieval."""
        mock_factory_instance = Mock()
        mock_factory_instance.enabled = True
        mock_factory_instance.is_available.return_value = True
        mock_factory_instance.get_cost_usage.return_value = mock_cost_records
        mock_factory.return_value = mock_factory_instance
        
        response = client.get("/usage/example/aws?days=7")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["cloud_provider"] == "aws"
        assert "time_range" in data
        assert "summary" in data
        assert data["summary"]["total_cost"] == 100.0


class TestClearCache:
    """Test cache clearing endpoint."""
    
    @patch('finopsguard.api.usage_endpoints.get_usage_factory')
    def test_clear_cache(self, mock_factory, client):
        """Test cache clearing."""
        mock_factory_instance = Mock()
        mock_factory.return_value = mock_factory_instance
        
        response = client.delete("/usage/cache")
        
        assert response.status_code == 200
        assert "cleared" in response.json()["message"]
        mock_factory_instance.clear_cache.assert_called_once()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

