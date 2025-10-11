"""
Unit tests for GCP cost simulation integration
"""

from finopsguard.engine.simulation import simulate_cost
from finopsguard.types.models import CanonicalResourceModel, CanonicalResource


class TestGCPCostSimulation:
    """Test GCP resource cost simulation"""
    
    def test_simulate_gcp_compute_instance_cost(self):
        """Test cost simulation for GCP Compute Engine instances"""
        resources = [
            CanonicalResource(
                id="web-server-gce-us-central1",
                type="gcp_compute_instance",
                name="web_server",
                region="us-central1",
                size="e2-standard-4",
                count=2,
                tags={},
                metadata={}
            )
        ]
        
        model = CanonicalResourceModel(resources=resources)
        result = simulate_cost(model)
        
        assert result.estimated_monthly_cost > 0
        assert result.estimated_first_week_cost > 0
        assert len(result.breakdown_by_resource) == 1
        
        breakdown = result.breakdown_by_resource[0]
        assert breakdown.resource_id == "web-server-gce-us-central1"
        assert breakdown.monthly_cost > 0
        assert breakdown.notes == []
        
        # e2-standard-4 costs $0.134/hour, 2 instances, 730 hours/month
        expected_monthly = 0.134 * 2 * 730
        assert abs(breakdown.monthly_cost - expected_monthly) < 0.01
    
    def test_simulate_gcp_sql_database_cost(self):
        """Test cost simulation for GCP Cloud SQL instances"""
        resources = [
            CanonicalResource(
                id="main-db-sql-us-west1",
                type="gcp_sql_database_instance",
                name="main_db",
                region="us-west1",
                size="db-n1-standard-2",
                count=1,
                tags={},
                metadata={}
            )
        ]
        
        model = CanonicalResourceModel(resources=resources)
        result = simulate_cost(model)
        
        assert result.estimated_monthly_cost > 0
        assert len(result.breakdown_by_resource) == 1
        
        breakdown = result.breakdown_by_resource[0]
        assert breakdown.resource_id == "main-db-sql-us-west1"
        assert breakdown.monthly_cost > 0
        
        # db-n1-standard-2 costs $0.082/hour, 730 hours/month
        expected_monthly = 0.082 * 730
        assert abs(breakdown.monthly_cost - expected_monthly) < 0.01
    
    def test_simulate_gcp_storage_bucket_cost(self):
        """Test cost simulation for GCP Cloud Storage buckets"""
        resources = [
            CanonicalResource(
                id="data-bucket-storage-US",
                type="gcp_storage_bucket",
                name="data_bucket",
                region="US",
                size="standard",
                count=3,
                tags={},
                metadata={}
            )
        ]
        
        model = CanonicalResourceModel(resources=resources)
        result = simulate_cost(model)
        
        assert result.estimated_monthly_cost > 0
        assert len(result.breakdown_by_resource) == 1
        
        breakdown = result.breakdown_by_resource[0]
        assert breakdown.resource_id == "data-bucket-storage-US"
        assert breakdown.monthly_cost > 0
        assert "Estimated 100GB per bucket" in breakdown.notes[0]
        
        # Standard storage costs $0.020/GB/month, 3 buckets, 100GB each
        expected_monthly = 0.020 * 100 * 3
        assert abs(breakdown.monthly_cost - expected_monthly) < 0.01
    
    def test_simulate_gcp_container_cluster_cost(self):
        """Test cost simulation for GCP Kubernetes Engine clusters"""
        resources = [
            CanonicalResource(
                id="main-cluster-gke-us-central1",
                type="gcp_container_cluster",
                name="main_cluster",
                region="us-central1",
                size="standard_cluster",
                count=1,
                tags={},
                metadata={}
            )
        ]
        
        model = CanonicalResourceModel(resources=resources)
        result = simulate_cost(model)
        
        assert result.estimated_monthly_cost > 0
        assert len(result.breakdown_by_resource) == 1
        
        breakdown = result.breakdown_by_resource[0]
        assert breakdown.resource_id == "main-cluster-gke-us-central1"
        assert breakdown.monthly_cost > 0
        assert "Cluster management cost only - node costs separate" in breakdown.notes[0]
        
        # Standard cluster costs $0.10/hour, 730 hours/month
        expected_monthly = 0.10 * 730
        assert abs(breakdown.monthly_cost - expected_monthly) < 0.01
    
    def test_simulate_gcp_cloud_run_cost(self):
        """Test cost simulation for GCP Cloud Run services"""
        resources = [
            CanonicalResource(
                id="api-service-run-us-central1",
                type="gcp_cloud_run_service",
                name="api_service",
                region="us-central1",
                size="serverless",
                count=2,
                tags={},
                metadata={}
            )
        ]
        
        model = CanonicalResourceModel(resources=resources)
        result = simulate_cost(model)
        
        assert result.estimated_monthly_cost > 0
        assert len(result.breakdown_by_resource) == 1
        
        breakdown = result.breakdown_by_resource[0]
        assert breakdown.resource_id == "api-service-run-us-central1"
        assert breakdown.monthly_cost > 0
        assert "Estimated 2 vCPU, 4GB memory, 720 hours/month" in breakdown.notes[0]
        
        # 2 services, 2 vCPU each, 4GB memory each, 720 hours/month
        # CPU: 2 * 2 * 720 * $0.024 = $69.12
        # Memory: 2 * 4 * 720 * $0.0025 = $14.40
        expected_monthly = (2 * 2 * 720 * 0.024) + (2 * 4 * 720 * 0.0025)
        assert abs(breakdown.monthly_cost - expected_monthly) < 0.01
    
    def test_simulate_gcp_cloud_functions_cost(self):
        """Test cost simulation for GCP Cloud Functions"""
        resources = [
            CanonicalResource(
                id="data-processor-functions-us-central1",
                type="gcp_cloudfunctions_function",
                name="data_processor",
                region="us-central1",
                size="python39",
                count=1,
                tags={},
                metadata={}
            )
        ]
        
        model = CanonicalResourceModel(resources=resources)
        result = simulate_cost(model)
        
        assert result.estimated_monthly_cost > 0
        assert len(result.breakdown_by_resource) == 1
        
        breakdown = result.breakdown_by_resource[0]
        assert breakdown.resource_id == "data-processor-functions-us-central1"
        assert breakdown.monthly_cost > 0
        assert "Estimated 1M invocations, 100GB-seconds per month" in breakdown.notes[0]
        
        # 1M invocations at $0.40/1M + 100GB-seconds at $0.0000025/GB-second
        expected_monthly = (1000000 * 0.40 / 1000000) + (100 * 0.0000025)
        assert abs(breakdown.monthly_cost - expected_monthly) < 0.01
    
    def test_simulate_gcp_load_balancer_cost(self):
        """Test cost simulation for GCP Load Balancers"""
        resources = [
            CanonicalResource(
                id="web-lb-lb-us-central1",
                type="gcp_load_balancer",
                name="web_lb",
                region="us-central1",
                size="http_lb",
                count=1,
                tags={},
                metadata={}
            )
        ]
        
        model = CanonicalResourceModel(resources=resources)
        result = simulate_cost(model)
        
        assert result.estimated_monthly_cost > 0
        assert len(result.breakdown_by_resource) == 1
        
        breakdown = result.breakdown_by_resource[0]
        assert breakdown.resource_id == "web-lb-lb-us-central1"
        assert breakdown.monthly_cost > 0
        
        # HTTP LB costs $0.025/hour, 730 hours/month
        expected_monthly = 0.025 * 730
        assert abs(breakdown.monthly_cost - expected_monthly) < 0.01
    
    def test_simulate_gcp_redis_instance_cost(self):
        """Test cost simulation for GCP Redis instances"""
        resources = [
            CanonicalResource(
                id="cache-redis-us-west2",
                type="gcp_redis_instance",
                name="cache",
                region="us-west2",
                size="STANDARD_HA-8GB",
                count=1,
                tags={},
                metadata={}
            )
        ]
        
        model = CanonicalResourceModel(resources=resources)
        result = simulate_cost(model)
        
        assert result.estimated_monthly_cost > 0
        assert len(result.breakdown_by_resource) == 1
        
        breakdown = result.breakdown_by_resource[0]
        assert breakdown.resource_id == "cache-redis-us-west2"
        assert breakdown.monthly_cost > 0
        assert "Estimated 8GB memory" in breakdown.notes[0]
        
        # 8GB memory at $0.10/GB/hour, 730 hours/month
        expected_monthly = 0.10 * 8 * 730
        assert abs(breakdown.monthly_cost - expected_monthly) < 0.01
    
    def test_simulate_gcp_bigquery_dataset_cost(self):
        """Test cost simulation for GCP BigQuery datasets"""
        resources = [
            CanonicalResource(
                id="analytics-bigquery-US",
                type="gcp_bigquery_dataset",
                name="analytics",
                region="US",
                size="standard",
                count=2,
                tags={},
                metadata={}
            )
        ]
        
        model = CanonicalResourceModel(resources=resources)
        result = simulate_cost(model)
        
        assert result.estimated_monthly_cost > 0
        assert len(result.breakdown_by_resource) == 1
        
        breakdown = result.breakdown_by_resource[0]
        assert breakdown.resource_id == "analytics-bigquery-US"
        assert breakdown.monthly_cost > 0
        assert "Estimated $10/month per dataset (pay-per-use)" in breakdown.notes[0]
        
        # 2 datasets at $10/month each
        expected_monthly = 10.0 * 2
        assert abs(breakdown.monthly_cost - expected_monthly) < 0.01
    
    def test_simulate_mixed_aws_gcp_infrastructure_cost(self):
        """Test cost simulation for mixed AWS and GCP infrastructure"""
        resources = [
            CanonicalResource(
                id="web-server-aws-us-east-1",
                type="aws_instance",
                name="web_server",
                region="us-east-1",
                size="t3.micro",
                count=1,
                tags={},
                metadata={}
            ),
            CanonicalResource(
                id="api-server-gce-us-central1",
                type="gcp_compute_instance",
                name="api_server",
                region="us-central1",
                size="e2-small",
                count=2,
                tags={},
                metadata={}
            ),
            CanonicalResource(
                id="main-db-sql-us-west1",
                type="gcp_sql_database_instance",
                name="main_db",
                region="us-west1",
                size="db-f1-micro",
                count=1,
                tags={},
                metadata={}
            )
        ]
        
        model = CanonicalResourceModel(resources=resources)
        result = simulate_cost(model)
        
        assert result.estimated_monthly_cost > 0
        assert result.estimated_first_week_cost > 0
        assert len(result.breakdown_by_resource) == 3
        
        # Check that all resources have costs
        for breakdown in result.breakdown_by_resource:
            assert breakdown.monthly_cost > 0
        
        # Verify AWS resource
        aws_breakdown = next(b for b in result.breakdown_by_resource if "aws" in b.resource_id)
        assert aws_breakdown.resource_id == "web-server-aws-us-east-1"
        
        # Verify GCP resources
        gcp_breakdowns = [b for b in result.breakdown_by_resource if "gce" in b.resource_id or "sql" in b.resource_id]
        assert len(gcp_breakdowns) == 2
    
    def test_simulate_gcp_unknown_resource_type(self):
        """Test cost simulation for unknown GCP resource types"""
        resources = [
            CanonicalResource(
                id="unknown-resource-us-central1",
                type="gcp_unknown_service",
                name="unknown_resource",
                region="us-central1",
                size="unknown",
                count=1,
                tags={},
                metadata={}
            )
        ]
        
        model = CanonicalResourceModel(resources=resources)
        result = simulate_cost(model)
        
        # Unknown resource types should not contribute to cost
        assert result.estimated_monthly_cost == 0
        assert result.estimated_first_week_cost == 0
        assert len(result.breakdown_by_resource) == 0
    
    def test_simulate_gcp_resources_with_zero_count(self):
        """Test cost simulation for GCP resources with zero count"""
        resources = [
            CanonicalResource(
                id="zero-count-gce-us-central1",
                type="gcp_compute_instance",
                name="zero_count",
                region="us-central1",
                size="e2-micro",
                count=0,
                tags={},
                metadata={}
            )
        ]
        
        model = CanonicalResourceModel(resources=resources)
        result = simulate_cost(model)
        
        # Resources with zero count should not contribute to cost
        assert result.estimated_monthly_cost == 0
        assert result.estimated_first_week_cost == 0
        assert len(result.breakdown_by_resource) == 0
    
    def test_simulate_large_gcp_infrastructure(self):
        """Test cost simulation for large GCP infrastructure"""
        resources = [
            CanonicalResource(
                id="web-servers-gce-us-central1",
                type="gcp_compute_instance",
                name="web_servers",
                region="us-central1",
                size="e2-standard-4",
                count=10,
                tags={},
                metadata={}
            ),
            CanonicalResource(
                id="db-cluster-sql-us-central1",
                type="gcp_sql_database_instance",
                name="db_cluster",
                region="us-central1",
                size="db-n1-standard-8",
                count=3,
                tags={},
                metadata={}
            ),
            CanonicalResource(
                id="k8s-cluster-gke-us-central1",
                type="gcp_container_cluster",
                name="k8s_cluster",
                region="us-central1",
                size="standard_cluster",
                count=2,
                tags={},
                metadata={}
            )
        ]
        
        model = CanonicalResourceModel(resources=resources)
        result = simulate_cost(model)
        
        assert result.estimated_monthly_cost > 0
        assert result.estimated_first_week_cost > 0
        assert len(result.breakdown_by_resource) == 3
        
        # Check that costs scale with count
        web_breakdown = next(b for b in result.breakdown_by_resource if "web-servers" in b.resource_id)
        db_breakdown = next(b for b in result.breakdown_by_resource if "db-cluster" in b.resource_id)
        k8s_breakdown = next(b for b in result.breakdown_by_resource if "k8s-cluster" in b.resource_id)
        
        # 10 web servers should cost more than 3 databases
        assert web_breakdown.monthly_cost > db_breakdown.monthly_cost
        
        # 3 databases should cost more than 2 k8s clusters
        assert db_breakdown.monthly_cost > k8s_breakdown.monthly_cost
