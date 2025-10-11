"""Unit tests for usage integration adapters."""

import os
import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, MagicMock, patch

from finopsguard.types.usage import (
    ResourceUsage,
    CostUsageRecord,
    UsageSummary,
    UsageQuery,
    UsageMetric
)
from finopsguard.adapters.usage import (
    get_usage_factory,
    get_aws_usage_adapter,
    get_gcp_usage_adapter,
    get_azure_usage_adapter
)


# Test fixtures
@pytest.fixture
def sample_usage_query():
    """Sample usage query for testing."""
    return UsageQuery(
        cloud_provider="aws",
        start_time=datetime(2024, 1, 1),
        end_time=datetime(2024, 1, 31),
        resource_types=["ec2"],
        regions=["us-east-1"],
        granularity="DAILY"
    )


@pytest.fixture
def sample_resource_usage():
    """Sample resource usage data."""
    return ResourceUsage(
        resource_id="i-1234567890abcdef0",
        resource_type="ec2",
        region="us-east-1",
        cloud_provider="aws",
        start_time=datetime(2024, 1, 1),
        end_time=datetime(2024, 1, 31),
        metrics=[
            UsageMetric(
                timestamp=datetime(2024, 1, 1, 12, 0),
                value=45.5,
                unit="Percent",
                metric_name="CPUUtilization",
                dimensions={"InstanceId": "i-1234567890abcdef0"}
            )
        ],
        avg_cpu_utilization=45.5
    )


@pytest.fixture
def sample_cost_records():
    """Sample cost usage records."""
    return [
        CostUsageRecord(
            date=datetime(2024, 1, 1),
            start_time=datetime(2024, 1, 1),
            end_time=datetime(2024, 1, 2),
            cost=123.45,
            currency="USD",
            usage_amount=24.0,
            usage_unit="hours",
            service="AmazonEC2",
            region="us-east-1",
            dimensions={"service": "AmazonEC2"}
        )
    ]


class TestUsageFactory:
    """Test suite for UsageFactory."""
    
    def test_factory_initialization(self):
        """Test that factory initializes correctly."""
        factory = get_usage_factory()
        assert factory is not None
        assert factory._aws_adapter is None  # Lazy loading
        assert factory._gcp_adapter is None
        assert factory._azure_adapter is None
    
    @patch.dict(os.environ, {"USAGE_INTEGRATION_ENABLED": "false"})
    def test_factory_disabled(self):
        """Test that factory returns None when disabled."""
        from finopsguard.adapters.usage.usage_factory import UsageFactory
        factory = UsageFactory()
        
        result = factory.get_resource_usage(
            cloud_provider="aws",
            resource_id="i-123",
            resource_type="ec2",
            start_time=datetime(2024, 1, 1),
            end_time=datetime(2024, 1, 2)
        )
        
        assert result is None
    
    @patch.dict(os.environ, {"USAGE_INTEGRATION_ENABLED": "true", "AWS_USAGE_ENABLED": "false"})
    def test_factory_adapter_unavailable(self):
        """Test factory when adapter is not available."""
        from finopsguard.adapters.usage.usage_factory import UsageFactory
        factory = UsageFactory()
        
        assert not factory.is_available("aws")
    
    def test_factory_invalid_cloud_provider(self):
        """Test factory with invalid cloud provider."""
        factory = get_usage_factory()
        
        with pytest.raises(ValueError, match="Unsupported cloud provider"):
            factory._get_adapter("invalid_cloud")
    
    @patch.dict(os.environ, {"USAGE_INTEGRATION_ENABLED": "true", "AWS_USAGE_ENABLED": "true"})
    @patch('finopsguard.adapters.usage.aws_usage.boto3')
    def test_factory_get_resource_usage(self, mock_boto3, sample_resource_usage):
        """Test getting resource usage through factory."""
        from finopsguard.adapters.usage.usage_factory import UsageFactory
        factory = UsageFactory()
        
        # Mock AWS adapter
        mock_adapter = Mock()
        mock_adapter.is_available.return_value = True
        mock_adapter.get_resource_usage.return_value = sample_resource_usage
        
        with patch.object(factory, '_get_aws_adapter', return_value=mock_adapter):
            result = factory.get_resource_usage(
                cloud_provider="aws",
                resource_id="i-123",
                resource_type="ec2",
                start_time=datetime(2024, 1, 1),
                end_time=datetime(2024, 1, 2)
            )
            
            assert result is not None
            assert result.resource_id == "i-1234567890abcdef0"
            assert result.avg_cpu_utilization == 45.5
    
    def test_factory_caching(self):
        """Test that factory caches results."""
        from finopsguard.adapters.usage.usage_factory import UsageFactory
        factory = UsageFactory()
        
        # Set something in cache
        key = "test_key"
        data = {"test": "data"}
        factory._set_cache(key, data)
        
        # Retrieve from cache
        cached = factory._get_from_cache(key)
        assert cached == data
        
        # Clear cache
        factory.clear_cache()
        cached = factory._get_from_cache(key)
        assert cached is None


class TestAWSUsageAdapter:
    """Test suite for AWS usage adapter."""
    
    @patch.dict(os.environ, {"AWS_USAGE_ENABLED": "false"})
    def test_aws_adapter_disabled(self):
        """Test AWS adapter when disabled."""
        adapter = get_aws_usage_adapter()
        assert not adapter.is_available()
    
    @patch.dict(os.environ, {"AWS_USAGE_ENABLED": "true"})
    @patch('finopsguard.adapters.usage.aws_usage.boto3')
    def test_aws_adapter_initialization(self, mock_boto3):
        """Test AWS adapter initialization."""
        # Mock boto3 clients
        mock_cloudwatch = Mock()
        mock_ce = Mock()
        mock_boto3.client.side_effect = lambda service, **kwargs: {
            'cloudwatch': mock_cloudwatch,
            'ce': mock_ce,
            'sts': Mock(get_caller_identity=lambda: {"Account": "123456789012"})
        }[service]
        
        adapter = get_aws_usage_adapter()
        assert adapter.cloud_provider == "aws"
    
    @patch.dict(os.environ, {"AWS_USAGE_ENABLED": "true"})
    @patch('finopsguard.adapters.usage.aws_usage.boto3')
    def test_aws_get_resource_usage(self, mock_boto3):
        """Test getting CloudWatch metrics for AWS resource."""
        # Mock CloudWatch client
        mock_cloudwatch = Mock()
        mock_cloudwatch.get_metric_statistics.return_value = {
            'Datapoints': [
                {
                    'Timestamp': datetime(2024, 1, 1, 12, 0),
                    'Average': 45.5,
                    'Unit': 'Percent'
                }
            ]
        }
        
        mock_boto3.client.return_value = mock_cloudwatch
        
        adapter = get_aws_usage_adapter()
        adapter._cloudwatch = mock_cloudwatch
        adapter._enabled = True
        
        result = adapter.get_resource_usage(
            resource_id="i-123",
            resource_type="ec2",
            start_time=datetime(2024, 1, 1),
            end_time=datetime(2024, 1, 2),
            region="us-east-1"
        )
        
        assert result is not None
        assert result.resource_id == "i-123"
        assert result.resource_type == "ec2"
        assert len(result.metrics) > 0
    
    @patch.dict(os.environ, {"AWS_USAGE_ENABLED": "true"})
    @patch('finopsguard.adapters.usage.aws_usage.boto3')
    def test_aws_get_cost_usage(self, mock_boto3):
        """Test getting Cost Explorer data."""
        # Mock Cost Explorer client
        mock_ce = Mock()
        mock_ce.get_cost_and_usage.return_value = {
            'ResultsByTime': [
                {
                    'TimePeriod': {
                        'Start': '2024-01-01',
                        'End': '2024-01-02'
                    },
                    'Total': {
                        'UnblendedCost': {
                            'Amount': '123.45',
                            'Unit': 'USD'
                        },
                        'UsageQuantity': {
                            'Amount': '24.0',
                            'Unit': 'hours'
                        }
                    }
                }
            ]
        }
        
        mock_boto3.client.return_value = mock_ce
        
        adapter = get_aws_usage_adapter()
        adapter._ce = mock_ce
        adapter._enabled = True
        
        result = adapter.get_cost_usage(
            start_time=datetime(2024, 1, 1),
            end_time=datetime(2024, 1, 2),
            granularity="DAILY"
        )
        
        assert result is not None
        assert len(result) > 0
        assert result[0].cost == 123.45


class TestGCPUsageAdapter:
    """Test suite for GCP usage adapter."""
    
    @patch.dict(os.environ, {"GCP_USAGE_ENABLED": "false"})
    def test_gcp_adapter_disabled(self):
        """Test GCP adapter when disabled."""
        adapter = get_gcp_usage_adapter()
        assert not adapter.is_available()
    
    @patch.dict(os.environ, {"GCP_USAGE_ENABLED": "true", "GCP_PROJECT_ID": "test-project"})
    def test_gcp_adapter_initialization(self):
        """Test GCP adapter initialization."""
        adapter = get_gcp_usage_adapter()
        assert adapter.cloud_provider == "gcp"
        assert adapter._project_id == "test-project"
    
    @patch.dict(os.environ, {"GCP_USAGE_ENABLED": "true", "GCP_PROJECT_ID": "test-project"})
    @patch('finopsguard.adapters.usage.gcp_usage.monitoring_v3')
    def test_gcp_get_resource_usage(self, mock_monitoring):
        """Test getting Cloud Monitoring metrics for GCP resource."""
        # Mock monitoring client
        mock_client = Mock()
        mock_time_series = Mock()
        mock_time_series.points = [
            Mock(
                interval=Mock(end_time=datetime(2024, 1, 1, 12, 0)),
                value=Mock(double_value=0.455, int64_value=None)
            )
        ]
        mock_time_series.metric = Mock(type="compute.googleapis.com/instance/cpu/utilization")
        mock_time_series.resource = Mock(labels={"instance_id": "test-instance"})
        
        mock_client.list_time_series.return_value = [mock_time_series]
        mock_monitoring.MetricServiceClient.return_value = mock_client
        
        adapter = get_gcp_usage_adapter()
        adapter._monitoring = mock_client
        adapter._enabled = True
        
        result = adapter.get_resource_usage(
            resource_id="test-instance",
            resource_type="gce_instance",
            start_time=datetime(2024, 1, 1),
            end_time=datetime(2024, 1, 2),
            region="us-central1"
        )
        
        assert result is not None
        assert result.resource_id == "test-instance"
        assert result.resource_type == "gce_instance"


class TestAzureUsageAdapter:
    """Test suite for Azure usage adapter."""
    
    @patch.dict(os.environ, {"AZURE_USAGE_ENABLED": "false"})
    def test_azure_adapter_disabled(self):
        """Test Azure adapter when disabled."""
        adapter = get_azure_usage_adapter()
        assert not adapter.is_available()
    
    @patch.dict(os.environ, {
        "AZURE_USAGE_ENABLED": "true",
        "AZURE_SUBSCRIPTION_ID": "test-subscription-id"
    })
    def test_azure_adapter_initialization(self):
        """Test Azure adapter initialization."""
        adapter = get_azure_usage_adapter()
        assert adapter.cloud_provider == "azure"
        assert adapter._subscription_id == "test-subscription-id"
    
    @patch.dict(os.environ, {
        "AZURE_USAGE_ENABLED": "true",
        "AZURE_SUBSCRIPTION_ID": "test-subscription"
    })
    @patch('finopsguard.adapters.usage.azure_usage.MonitorManagementClient')
    @patch('finopsguard.adapters.usage.azure_usage.DefaultAzureCredential')
    def test_azure_get_resource_usage(self, mock_credential, mock_monitor):
        """Test getting Azure Monitor metrics."""
        # Mock monitor client
        mock_client = Mock()
        mock_metric = Mock()
        mock_metric.unit = Mock(value="Percent")
        mock_metric.timeseries = [
            Mock(data=[
                Mock(
                    time_stamp=datetime(2024, 1, 1, 12, 0),
                    average=45.5
                )
            ])
        ]
        mock_client.metrics.list.return_value = Mock(value=[mock_metric])
        mock_monitor.return_value = mock_client
        
        adapter = get_azure_usage_adapter()
        adapter._monitor = mock_client
        adapter._enabled = True
        
        result = adapter.get_resource_usage(
            resource_id="/subscriptions/test/resourceGroups/test/providers/Microsoft.Compute/virtualMachines/test-vm",
            resource_type="virtual_machine",
            start_time=datetime(2024, 1, 1),
            end_time=datetime(2024, 1, 2),
            region="eastus"
        )
        
        assert result is not None
        assert result.resource_type == "virtual_machine"


class TestUsageModels:
    """Test suite for usage data models."""
    
    def test_usage_metric_creation(self):
        """Test creating UsageMetric."""
        metric = UsageMetric(
            timestamp=datetime(2024, 1, 1),
            value=50.0,
            unit="Percent",
            metric_name="CPUUtilization",
            dimensions={"InstanceId": "i-123"}
        )
        
        assert metric.value == 50.0
        assert metric.unit == "Percent"
        assert metric.metric_name == "CPUUtilization"
    
    def test_resource_usage_creation(self):
        """Test creating ResourceUsage."""
        usage = ResourceUsage(
            resource_id="i-123",
            resource_type="ec2",
            region="us-east-1",
            cloud_provider="aws",
            start_time=datetime(2024, 1, 1),
            end_time=datetime(2024, 1, 2),
            avg_cpu_utilization=45.5
        )
        
        assert usage.resource_id == "i-123"
        assert usage.avg_cpu_utilization == 45.5
        assert len(usage.metrics) == 0  # Empty by default
    
    def test_cost_usage_record_creation(self):
        """Test creating CostUsageRecord."""
        record = CostUsageRecord(
            date=datetime(2024, 1, 1),
            start_time=datetime(2024, 1, 1),
            end_time=datetime(2024, 1, 2),
            cost=123.45,
            currency="USD",
            usage_amount=24.0,
            usage_unit="hours",
            service="AmazonEC2"
        )
        
        assert record.cost == 123.45
        assert record.service == "AmazonEC2"
        assert record.usage_amount == 24.0
    
    def test_usage_query_creation(self):
        """Test creating UsageQuery."""
        query = UsageQuery(
            cloud_provider="aws",
            start_time=datetime(2024, 1, 1),
            end_time=datetime(2024, 1, 31),
            resource_types=["ec2"],
            regions=["us-east-1"],
            granularity="DAILY"
        )
        
        assert query.cloud_provider == "aws"
        assert query.granularity == "DAILY"
        assert "ec2" in query.resource_types
    
    def test_usage_summary_creation(self):
        """Test creating UsageSummary."""
        summary = UsageSummary(
            cloud_provider="aws",
            resource_type="ec2",
            region="us-east-1",
            start_time=datetime(2024, 1, 1),
            end_time=datetime(2024, 1, 31),
            total_resources=5,
            total_cost=1234.56,
            average_cost_per_resource=246.91,
            total_usage=720.0,
            average_usage=144.0,
            usage_unit="hours"
        )
        
        assert summary.total_resources == 5
        assert summary.total_cost == 1234.56
        assert summary.average_usage == 144.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

