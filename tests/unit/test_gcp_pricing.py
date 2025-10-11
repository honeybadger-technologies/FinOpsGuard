"""
Unit tests for GCP pricing adapter
"""

from finopsguard.adapters.pricing.gcp_static import (
    get_gcp_instance_price,
    get_gcp_database_price,
    get_gcp_storage_price,
    get_gcp_load_balancer_price,
    get_gcp_kubernetes_price,
    get_gcp_cloud_run_price,
    get_gcp_cloud_functions_price,
    get_gcp_price_catalog,
    is_gcp_resource,
    GCPPricingData
)


class TestGCPInstancePricing:
    """Test GCP Compute Engine instance pricing"""
    
    def test_get_gcp_instance_price_known_type(self):
        """Test pricing for known instance types"""
        result = get_gcp_instance_price("e2-standard-4")
        
        assert result["price_per_hour"] == 0.134
        assert result["cpu"] == 4
        assert result["memory"] == 16
        assert result["region"] == "us-central1"
        assert result["confidence"] == "high"
    
    def test_get_gcp_instance_price_unknown_type(self):
        """Test pricing for unknown instance types"""
        result = get_gcp_instance_price("unknown-instance-type")
        
        assert result["price_per_hour"] == 0.10  # Default fallback
        assert result["cpu"] == 2
        assert result["memory"] == 8
        assert result["confidence"] == "low"
        assert "Unknown instance type" in result["note"]
    
    def test_get_gcp_instance_price_with_region(self):
        """Test pricing with custom region"""
        result = get_gcp_instance_price("e2-micro", "europe-west1")
        
        assert result["price_per_hour"] == 0.006
        assert result["region"] == "europe-west1"
        assert result["confidence"] == "high"
    
    def test_gpu_instance_pricing(self):
        """Test GPU instance pricing"""
        result = get_gcp_instance_price("n1-standard-4-gpu")
        
        assert result["price_per_hour"] == 1.18
        assert result["cpu"] == 4
        assert result["memory"] == 15
        assert result["gpu"] == 1


class TestGCPDatabasePricing:
    """Test GCP Cloud SQL pricing"""
    
    def test_get_gcp_database_price_known_type(self):
        """Test pricing for known database instance types"""
        result = get_gcp_database_price("db-n1-standard-2")
        
        assert result["price_per_hour"] == 0.082
        assert result["cpu"] == 2
        assert result["memory"] == 7.5
        assert result["storage"] == 10
        assert result["confidence"] == "high"
    
    def test_get_gcp_database_price_unknown_type(self):
        """Test pricing for unknown database instance types"""
        result = get_gcp_database_price("unknown-db-type")
        
        assert result["price_per_hour"] == 0.05  # Default fallback
        assert result["cpu"] == 1
        assert result["memory"] == 4
        assert result["confidence"] == "low"
        assert "Unknown database instance type" in result["note"]


class TestGCPStoragePricing:
    """Test GCP Cloud Storage pricing"""
    
    def test_get_gcp_storage_price_standard(self):
        """Test standard storage pricing"""
        result = get_gcp_storage_price("standard")
        
        assert result["price_per_gb_month"] == 0.020
        assert result["storage_class"] == "standard"
        assert result["confidence"] == "high"
    
    def test_get_gcp_storage_price_archive(self):
        """Test archive storage pricing"""
        result = get_gcp_storage_price("archive")
        
        assert result["price_per_gb_month"] == 0.0012
        assert result["storage_class"] == "archive"
        assert result["confidence"] == "high"
    
    def test_get_gcp_storage_price_unknown_class(self):
        """Test unknown storage class pricing"""
        result = get_gcp_storage_price("unknown-class")
        
        assert result["price_per_gb_month"] == 0.020  # Default to standard
        assert result["storage_class"] == "standard"
        assert result["confidence"] == "low"
        assert "Unknown storage class" in result["note"]


class TestGCPLoadBalancerPricing:
    """Test GCP Load Balancer pricing"""
    
    def test_get_gcp_load_balancer_price_http(self):
        """Test HTTP load balancer pricing"""
        result = get_gcp_load_balancer_price("http_lb")
        
        assert result["price_per_hour"] == 0.025
        assert result["lb_type"] == "http_lb"
        assert result["confidence"] == "high"
    
    def test_get_gcp_load_balancer_price_ssl(self):
        """Test SSL load balancer pricing"""
        result = get_gcp_load_balancer_price("ssl_lb")
        
        assert result["price_per_hour"] == 0.025
        assert result["lb_type"] == "ssl_lb"
        assert result["confidence"] == "high"
    
    def test_get_gcp_load_balancer_price_unknown_type(self):
        """Test unknown load balancer type pricing"""
        result = get_gcp_load_balancer_price("unknown-lb")
        
        assert result["price_per_hour"] == 0.025  # Default fallback
        assert result["lb_type"] == "http_lb"
        assert result["confidence"] == "low"


class TestGCPKubernetesPricing:
    """Test GCP Kubernetes Engine pricing"""
    
    def test_get_gcp_kubernetes_price_standard(self):
        """Test standard cluster pricing"""
        result = get_gcp_kubernetes_price("standard_cluster")
        
        assert result["price_per_cluster_hour"] == 0.10
        assert result["cluster_type"] == "standard_cluster"
        assert result["confidence"] == "high"
    
    def test_get_gcp_kubernetes_price_autopilot(self):
        """Test autopilot cluster pricing"""
        result = get_gcp_kubernetes_price("autopilot_cluster")
        
        assert result["price_per_cluster_hour"] == 0.10
        assert result["cluster_type"] == "autopilot_cluster"
        assert result["confidence"] == "high"


class TestGCPCloudRunPricing:
    """Test GCP Cloud Run pricing"""
    
    def test_get_gcp_cloud_run_price(self):
        """Test Cloud Run pricing"""
        result = get_gcp_cloud_run_price()
        
        assert result["cpu_per_hour"] == 0.024
        assert result["memory_per_gb_hour"] == 0.0025
        assert result["requests_per_million"] == 0.40
        assert result["confidence"] == "high"


class TestGCPCloudFunctionsPricing:
    """Test GCP Cloud Functions pricing"""
    
    def test_get_gcp_cloud_functions_price(self):
        """Test Cloud Functions pricing"""
        result = get_gcp_cloud_functions_price()
        
        assert result["invocations_per_million"] == 0.40
        assert result["gb_seconds"] == 0.0000025
        assert result["confidence"] == "high"


class TestGCPPriceCatalog:
    """Test GCP price catalog"""
    
    def test_get_gcp_price_catalog_structure(self):
        """Test price catalog structure"""
        catalog = get_gcp_price_catalog()
        
        assert catalog["provider"] == "gcp"
        assert catalog["region"] == "us-central1"
        assert "services" in catalog
        assert "compute_engine" in catalog["services"]
        assert "cloud_sql" in catalog["services"]
        assert "cloud_storage" in catalog["services"]
        assert "cloud_run" in catalog["services"]
        assert "kubernetes_engine" in catalog["services"]
        assert "cloud_functions" in catalog["services"]
        assert "load_balancer" in catalog["services"]
        assert catalog["confidence"] == "high"
    
    def test_get_gcp_price_catalog_compute_engine(self):
        """Test Compute Engine pricing in catalog"""
        catalog = get_gcp_price_catalog()
        compute_engine = catalog["services"]["compute_engine"]
        
        assert "instances" in compute_engine
        assert "e2-micro" in compute_engine["instances"]
        assert compute_engine["instances"]["e2-micro"]["price"] == 0.006
        assert compute_engine["description"] == "Compute Engine instance pricing (per hour)"


class TestGCPResourceDetection:
    """Test GCP resource type detection"""
    
    def test_is_gcp_resource_known_types(self):
        """Test detection of known GCP resource types"""
        assert is_gcp_resource("google_compute_instance") is True
        assert is_gcp_resource("google_sql_database_instance") is True
        assert is_gcp_resource("google_storage_bucket") is True
        assert is_gcp_resource("google_container_cluster") is True
        assert is_gcp_resource("google_cloud_run_service") is True
        assert is_gcp_resource("google_cloudfunctions_function") is True
        assert is_gcp_resource("google_compute_global_forwarding_rule") is True
        assert is_gcp_resource("google_redis_instance") is True
        assert is_gcp_resource("google_bigquery_dataset") is True
    
    def test_is_gcp_resource_aws_types(self):
        """Test that AWS resource types are not detected as GCP"""
        assert is_gcp_resource("aws_instance") is False
        assert is_gcp_resource("aws_db_instance") is False
        assert is_gcp_resource("aws_s3_bucket") is False
        assert is_gcp_resource("aws_eks_cluster") is False
    
    def test_is_gcp_resource_unknown_types(self):
        """Test unknown resource types"""
        assert is_gcp_resource("unknown_resource_type") is False
        assert is_gcp_resource("azure_virtual_machine") is False


class TestGCPPricingData:
    """Test GCP pricing data constants"""
    
    def test_compute_engine_pricing_data(self):
        """Test Compute Engine pricing data structure"""
        assert "e2-micro" in GCPPricingData.COMPUTE_ENGINE_PRICING
        assert "e2-standard-4" in GCPPricingData.COMPUTE_ENGINE_PRICING
        assert "n1-standard-4-gpu" in GCPPricingData.COMPUTE_ENGINE_PRICING
        
        # Test structure
        e2_micro = GCPPricingData.COMPUTE_ENGINE_PRICING["e2-micro"]
        assert "cpu" in e2_micro
        assert "memory" in e2_micro
        assert "price" in e2_micro
        assert e2_micro["cpu"] == 2
        assert e2_micro["memory"] == 1
        assert e2_micro["price"] == 0.006
    
    def test_cloud_sql_pricing_data(self):
        """Test Cloud SQL pricing data structure"""
        assert "db-f1-micro" in GCPPricingData.CLOUD_SQL_PRICING
        assert "db-n1-standard-4" in GCPPricingData.CLOUD_SQL_PRICING
        
        # Test structure
        db_micro = GCPPricingData.CLOUD_SQL_PRICING["db-f1-micro"]
        assert "cpu" in db_micro
        assert "memory" in db_micro
        assert "storage" in db_micro
        assert "price" in db_micro
    
    def test_storage_pricing_data(self):
        """Test Cloud Storage pricing data structure"""
        assert "standard" in GCPPricingData.CLOUD_STORAGE_PRICING
        assert "nearline" in GCPPricingData.CLOUD_STORAGE_PRICING
        assert "coldline" in GCPPricingData.CLOUD_STORAGE_PRICING
        assert "archive" in GCPPricingData.CLOUD_STORAGE_PRICING
        
        # Test pricing order (archive should be cheapest)
        storage = GCPPricingData.CLOUD_STORAGE_PRICING
        assert storage["archive"]["price"] < storage["coldline"]["price"]
        assert storage["coldline"]["price"] < storage["nearline"]["price"]
        assert storage["nearline"]["price"] < storage["standard"]["price"]


class TestGCPPricingIntegration:
    """Integration tests for GCP pricing"""
    
    def test_all_instance_types_have_valid_pricing(self):
        """Test that all instance types in pricing data have valid pricing"""
        for instance_type, pricing in GCPPricingData.COMPUTE_ENGINE_PRICING.items():
            assert isinstance(pricing["price"], (int, float))
            assert pricing["price"] > 0
            assert isinstance(pricing["cpu"], int)
            assert pricing["cpu"] > 0
            assert isinstance(pricing["memory"], int)
            assert pricing["memory"] > 0
    
    def test_all_database_types_have_valid_pricing(self):
        """Test that all database types in pricing data have valid pricing"""
        for db_type, pricing in GCPPricingData.CLOUD_SQL_PRICING.items():
            assert isinstance(pricing["price"], (int, float))
            assert pricing["price"] > 0
            assert isinstance(pricing["cpu"], int)
            assert pricing["cpu"] > 0
            assert isinstance(pricing["memory"], (int, float))
            assert pricing["memory"] > 0
            assert isinstance(pricing["storage"], int)
            assert pricing["storage"] > 0
    
    def test_storage_classes_have_valid_pricing(self):
        """Test that all storage classes have valid pricing"""
        for storage_class, pricing in GCPPricingData.CLOUD_STORAGE_PRICING.items():
            assert isinstance(pricing["price"], (int, float))
            assert pricing["price"] > 0
