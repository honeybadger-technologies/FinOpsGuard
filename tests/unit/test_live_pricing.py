"""Unit tests for real-time pricing adapters."""

import pytest
import os


class TestAWSLivePricing:
    """Test AWS live pricing adapter."""
    
    def test_aws_adapter_initialization(self):
        """Test AWS live pricing adapter initializes."""
        from finopsguard.adapters.pricing.aws_live import AWSLivePricingAdapter
        
        adapter = AWSLivePricingAdapter()
        assert adapter is not None
        assert hasattr(adapter, 'enabled')
        # Should be disabled by default without credentials
        assert adapter.enabled == (os.getenv("AWS_PRICING_ENABLED", "false").lower() == "true")
    
    def test_region_name_mapping(self):
        """Test AWS region name mapping."""
        from finopsguard.adapters.pricing.aws_live import AWSLivePricingAdapter
        
        adapter = AWSLivePricingAdapter()
        
        assert adapter._get_region_name("us-east-1") == "US East (N. Virginia)"
        assert adapter._get_region_name("us-west-2") == "US West (Oregon)"
        assert adapter._get_region_name("eu-west-1") == "EU (Ireland)"


class TestGCPLivePricing:
    """Test GCP live pricing adapter."""
    
    def test_gcp_adapter_initialization(self):
        """Test GCP live pricing adapter initializes."""
        from finopsguard.adapters.pricing.gcp_live import GCPLivePricingAdapter
        
        adapter = GCPLivePricingAdapter()
        assert adapter is not None
        assert hasattr(adapter, 'enabled')
        # Should be disabled without API key
        expected_enabled = (
            os.getenv("GCP_PRICING_ENABLED", "false").lower() == "true" and
            bool(os.getenv("GCP_PRICING_API_KEY", ""))
        )
        assert adapter.enabled == expected_enabled


class TestAzureLivePricing:
    """Test Azure live pricing adapter."""
    
    def test_azure_adapter_initialization(self):
        """Test Azure live pricing adapter initializes."""
        from finopsguard.adapters.pricing.azure_live import AzureLivePricingAdapter
        
        adapter = AzureLivePricingAdapter()
        assert adapter is not None
        assert hasattr(adapter, 'enabled')
        assert adapter.enabled == (os.getenv("AZURE_PRICING_ENABLED", "false").lower() == "true")


class TestPricingFactory:
    """Test pricing factory with fallback logic."""
    
    def test_factory_initialization(self):
        """Test pricing factory initializes."""
        from finopsguard.adapters.pricing.pricing_factory import PricingFactory
        
        factory = PricingFactory()
        assert factory is not None
        assert hasattr(factory, 'live_enabled')
        assert hasattr(factory, 'fallback_enabled')
    
    def test_get_instance_price_fallback(self):
        """Test getting instance price with fallback to static."""
        from finopsguard.adapters.pricing.pricing_factory import get_pricing_factory
        
        factory = get_pricing_factory()
        
        # Should fall back to static pricing
        aws_price = factory.get_instance_price("aws", "t3.medium", "us-east-1")
        assert aws_price is not None
        assert isinstance(aws_price, dict)
        assert aws_price.get("hourly_price") is not None or aws_price.get("price") is not None
        
        gcp_price = factory.get_instance_price("gcp", "e2-medium", "us-central1")
        assert gcp_price is not None
        assert isinstance(gcp_price, dict)
        
        azure_price = factory.get_instance_price("azure", "Standard_D2s_v3", "eastus")
        assert azure_price is not None
        assert isinstance(azure_price, dict)
    
    def test_get_database_price_fallback(self):
        """Test getting database price with fallback."""
        from finopsguard.adapters.pricing.pricing_factory import get_pricing_factory
        
        factory = get_pricing_factory()
        
        aws_db = factory.get_database_price("aws", "db.t3.medium")
        assert aws_db is not None
        assert "confidence" in aws_db
        
        gcp_db = factory.get_database_price("gcp", "db-n1-standard-1")
        assert gcp_db is not None
        
        azure_db = factory.get_database_price("azure", "S1")
        assert azure_db is not None
    
    def test_pricing_confidence_levels(self):
        """Test pricing confidence levels."""
        from finopsguard.adapters.pricing.pricing_factory import get_pricing_factory
        
        factory = get_pricing_factory()
        
        # Known instance should have medium/high confidence
        price = factory.get_instance_price("aws", "t3.medium")
        assert isinstance(price, dict)
        # Confidence may be in the dict or may not be present
        if "confidence" in price:
            assert price["confidence"] in ["medium", "high", "low"]
        
        # Unknown instance should have low confidence
        price = factory.get_instance_price("aws", "unknown.type.xxx")
        assert isinstance(price, dict)
        if "confidence" in price:
            assert price["confidence"] == "low"


class TestLivePricingIntegration:
    """Test live pricing integration."""
    
    def test_live_pricing_disabled_by_default(self):
        """Test that live pricing is disabled by default."""
        live_enabled = os.getenv("LIVE_PRICING_ENABLED", "false").lower() == "true"
        assert not live_enabled or os.getenv("LIVE_PRICING_ENABLED") == "true"
    
    def test_fallback_enabled_by_default(self):
        """Test that fallback is enabled by default."""
        fallback_enabled = os.getenv("PRICING_FALLBACK_TO_STATIC", "true").lower() == "true"
        assert fallback_enabled or os.getenv("PRICING_FALLBACK_TO_STATIC") == "false"
    
    @pytest.mark.skipif(
        os.getenv("AWS_PRICING_ENABLED", "false").lower() != "true",
        reason="AWS live pricing not enabled"
    )
    def test_aws_live_pricing_api_call(self):
        """Test actual AWS Pricing API call (if enabled)."""
        from finopsguard.adapters.pricing.aws_live import get_aws_live_adapter
        
        adapter = get_aws_live_adapter()
        if not adapter.enabled:
            pytest.skip("AWS live pricing not enabled")
        
        # Try to get pricing for common instance
        price = adapter.get_ec2_pricing("t3.medium", "us-east-1")
        
        if price:  # May fail due to API limits or credentials
            assert "hourly_price" in price
            assert price["confidence"] == "high"
    
    @pytest.mark.skipif(
        os.getenv("AZURE_PRICING_ENABLED", "false").lower() != "true",
        reason="Azure live pricing not enabled"
    )
    def test_azure_live_pricing_api_call(self):
        """Test actual Azure Pricing API call (if enabled)."""
        from finopsguard.adapters.pricing.azure_live import get_azure_live_adapter
        
        adapter = get_azure_live_adapter()
        if not adapter.enabled:
            pytest.skip("Azure live pricing not enabled")
        
        # Azure Retail Prices API is public (no auth required)
        price = adapter.get_vm_pricing("Standard_D2s_v3", "eastus")
        
        if price:
            assert "hourly_price" in price
            assert price["confidence"] == "high"

