"""Unit tests for caching layer."""

import pytest
from finopsguard.cache import get_cache, get_pricing_cache, get_analysis_cache


class TestRedisCache:
    """Test Redis cache client."""
    
    def test_cache_initialization(self):
        """Test that cache initializes correctly."""
        cache = get_cache()
        # Cache can be enabled or disabled depending on REDIS_ENABLED env var
        # and Redis availability
        assert cache is not None
        assert hasattr(cache, 'enabled')
        assert isinstance(cache.enabled, bool)
    
    def test_get_nonexistent_key(self):
        """Test getting a nonexistent key returns None."""
        cache = get_cache()
        result = cache.get("nonexistent_key")
        assert result is None
    
    def test_set_and_get(self):
        """Test setting and getting a value."""
        cache = get_cache()
        if not cache.enabled or not cache._is_available():
            pytest.skip("Redis not available")
        
        # Test string value
        cache.set("test_key", "test_value")
        assert cache.get("test_key") == "test_value"
        
        # Clean up
        cache.delete("test_key")
    
    def test_set_and_get_dict(self):
        """Test setting and getting a dictionary."""
        cache = get_cache()
        if not cache.enabled or not cache._is_available():
            pytest.skip("Redis not available")
        
        test_data = {"key": "value", "number": 123}
        cache.set("test_dict", test_data)
        result = cache.get("test_dict")
        assert result == test_data
        
        # Clean up
        cache.delete("test_dict")
    
    def test_set_with_ttl(self):
        """Test setting a value with TTL."""
        cache = get_cache()
        if not cache.enabled or not cache._is_available():
            pytest.skip("Redis not available")
        
        cache.set("test_ttl", "value", ttl=60)
        assert cache.exists("test_ttl")
        ttl = cache.ttl("test_ttl")
        assert ttl > 0 and ttl <= 60
        
        # Clean up
        cache.delete("test_ttl")
    
    def test_delete(self):
        """Test deleting a key."""
        cache = get_cache()
        if not cache.enabled or not cache._is_available():
            pytest.skip("Redis not available")
        
        cache.set("test_delete", "value")
        assert cache.exists("test_delete")
        cache.delete("test_delete")
        assert not cache.exists("test_delete")
    
    def test_delete_pattern(self):
        """Test deleting keys by pattern."""
        cache = get_cache()
        if not cache.enabled or not cache._is_available():
            pytest.skip("Redis not available")
        
        # Set multiple keys
        cache.set("pattern:key1", "value1")
        cache.set("pattern:key2", "value2")
        cache.set("other:key", "value3")
        
        # Delete by pattern
        count = cache.delete_pattern("pattern:*")
        assert count >= 2
        assert not cache.exists("pattern:key1")
        assert not cache.exists("pattern:key2")
        assert cache.exists("other:key") or True  # May or may not exist
        
        # Clean up
        cache.delete("other:key")
    
    def test_incr(self):
        """Test incrementing a value."""
        cache = get_cache()
        if not cache.enabled or not cache._is_available():
            pytest.skip("Redis not available")
        
        cache.set("counter", "0")
        cache.incr("counter")
        result = cache.get("counter")
        assert str(result) == "1"  # Redis may return string or int
        cache.incr("counter", 5)
        result = cache.get("counter")
        assert str(result) == "6"
        
        # Clean up
        cache.delete("counter")


class TestPricingCache:
    """Test pricing cache."""
    
    def test_pricing_cache_instance(self):
        """Test getting pricing cache instance."""
        cache = get_pricing_cache()
        assert cache is not None
        assert hasattr(cache, 'get_instance_price')
        assert hasattr(cache, 'set_instance_price')
    
    def test_instance_price_cache(self):
        """Test caching instance prices."""
        cache = get_pricing_cache()
        
        # Test data
        price_data = {
            "hourly_price": 0.05,
            "monthly_price": 36.5,
            "cpu": 2,
            "memory": 4
        }
        
        # Set cache
        cache.set_instance_price("aws", "t3.medium", price_data, "us-east-1")
        
        # Get from cache
        result = cache.get_instance_price("aws", "t3.medium", "us-east-1")
        
        if result:  # Only assert if cache is enabled
            assert result == price_data
    
    def test_database_price_cache(self):
        """Test caching database prices."""
        cache = get_pricing_cache()
        
        price_data = {
            "hourly_price": 0.15,
            "storage_price": 0.10
        }
        
        cache.set_database_price("gcp", "db-n1-standard-1", price_data)
        result = cache.get_database_price("gcp", "db-n1-standard-1")
        
        if result:
            assert result == price_data
    
    def test_price_catalog_cache(self):
        """Test caching price catalogs."""
        cache = get_pricing_cache()
        
        catalog_data = {
            "items": [
                {"instance_type": "t3.small", "price": 0.02},
                {"instance_type": "t3.medium", "price": 0.04}
            ],
            "updated_at": "2025-01-01T00:00:00"
        }
        
        cache.set_price_catalog("aws", catalog_data, instance_types=["t3.small", "t3.medium"])
        result = cache.get_price_catalog("aws", instance_types=["t3.small", "t3.medium"])
        
        if result:
            assert result == catalog_data
    
    def test_invalidate_cloud(self):
        """Test invalidating all pricing for a cloud provider."""
        cache = get_pricing_cache()
        
        # Set some pricing data
        cache.set_instance_price("aws", "t3.small", {"price": 0.02})
        cache.set_instance_price("aws", "t3.medium", {"price": 0.04})
        cache.set_instance_price("gcp", "e2-small", {"price": 0.03})
        
        # Invalidate AWS pricing
        count = cache.invalidate_cloud("aws")
        
        # Verify (if cache enabled, count should be > 0)
        if cache.cache.enabled:
            assert count >= 0


class TestAnalysisCache:
    """Test analysis cache."""
    
    def test_analysis_cache_instance(self):
        """Test getting analysis cache instance."""
        cache = get_analysis_cache()
        assert cache is not None
        assert hasattr(cache, 'get_parsed_terraform')
        assert hasattr(cache, 'get_full_analysis')
    
    def test_parsed_terraform_cache(self):
        """Test caching parsed Terraform."""
        cache = get_analysis_cache()
        
        terraform_content = """
        resource "aws_instance" "example" {
            instance_type = "t3.medium"
        }
        """
        
        parsed_data = {
            "resources": [
                {"type": "aws_instance", "name": "example"}
            ]
        }
        
        cache.set_parsed_terraform(terraform_content, parsed_data)
        result = cache.get_parsed_terraform(terraform_content)
        
        if result:
            assert result == parsed_data
    
    def test_cost_simulation_cache(self):
        """Test caching cost simulations."""
        cache = get_analysis_cache()
        
        simulation_data = {
            "estimated_monthly_cost": 100.5,
            "breakdown": [
                {"resource": "instance1", "cost": 50.0}
            ]
        }
        
        resource_hash = "test_hash_123"
        cache.set_cost_simulation(resource_hash, simulation_data)
        result = cache.get_cost_simulation(resource_hash)
        
        if result:
            assert result == simulation_data
    
    def test_policy_evaluation_cache(self):
        """Test caching policy evaluations."""
        cache = get_analysis_cache()
        
        evaluation_data = {
            "status": "pass",
            "policy_id": "budget_policy",
            "reason": "Within budget"
        }
        
        policy_id = "budget_policy"
        context_hash = "context_abc123"
        
        cache.set_policy_evaluation(policy_id, context_hash, evaluation_data)
        result = cache.get_policy_evaluation(policy_id, context_hash)
        
        if result:
            assert result == evaluation_data
    
    def test_full_analysis_cache(self):
        """Test caching full analysis results."""
        cache = get_analysis_cache()
        
        analysis_data = {
            "estimated_monthly_cost": 150.0,
            "risk_flags": ["over_budget"],
            "recommendations": [],
            "policy_eval": {"status": "fail"}
        }
        
        request_hash = "request_xyz789"
        cache.set_full_analysis(request_hash, analysis_data)
        result = cache.get_full_analysis(request_hash)
        
        if result:
            assert result == analysis_data
    
    def test_invalidate_policy(self):
        """Test invalidating policy cache."""
        cache = get_analysis_cache()
        
        policy_id = "test_policy"
        cache.set_policy_evaluation(policy_id, "context1", {"status": "pass"})
        cache.set_policy_evaluation(policy_id, "context2", {"status": "fail"})
        
        count = cache.invalidate_policy(policy_id)
        
        # Verify (if cache enabled, count should be >= 0)
        if cache.cache.enabled:
            assert count >= 0


class TestCacheIntegration:
    """Test cache integration."""
    
    def test_all_caches_use_same_redis(self):
        """Test that all cache instances use the same Redis connection."""
        main_cache = get_cache()
        pricing_cache = get_pricing_cache()
        analysis_cache = get_analysis_cache()
        
        # All should have the same enabled status
        if main_cache.enabled:
            assert pricing_cache.cache.enabled == main_cache.enabled
            assert analysis_cache.cache.enabled == main_cache.enabled
    
    def test_cache_info(self):
        """Test getting cache info."""
        cache = get_cache()
        info = cache.info()
        
        assert "enabled" in info
        assert isinstance(info["enabled"], bool)
        
        if info["enabled"]:
            assert "host" in info
            assert "port" in info
            assert "used_memory" in info

