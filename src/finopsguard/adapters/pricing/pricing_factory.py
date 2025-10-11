"""Pricing adapter factory with fallback logic."""

import os
import logging
from typing import Dict, Optional, Any

logger = logging.getLogger(__name__)

# Configuration
LIVE_PRICING_ENABLED = os.getenv("LIVE_PRICING_ENABLED", "false").lower() == "true"
PRICING_FALLBACK_TO_STATIC = os.getenv("PRICING_FALLBACK_TO_STATIC", "true").lower() == "true"


class PricingFactory:
    """
    Unified pricing factory that tries live pricing first,
    then falls back to static pricing.
    """
    
    def __init__(self):
        """Initialize pricing factory."""
        self.live_enabled = LIVE_PRICING_ENABLED
        self.fallback_enabled = PRICING_FALLBACK_TO_STATIC
        
        # Lazy load adapters
        self._aws_live = None
        self._gcp_live = None
        self._azure_live = None
    
    def get_instance_price(
        self,
        cloud: str,
        instance_type: str,
        region: str = None
    ) -> Dict[str, Any]:
        """
        Get instance pricing with automatic fallback.
        
        Args:
            cloud: Cloud provider (aws, gcp, azure)
            instance_type: Instance/VM type
            region: Region
            
        Returns:
            Pricing information with confidence level
        """
        price_data = None
        
        # Try live pricing first
        if self.live_enabled:
            price_data = self._get_live_instance_price(cloud, instance_type, region)
            if price_data:
                logger.info(f"Using live pricing for {cloud} {instance_type}")
                return price_data
        
        # Fall back to static pricing
        if self.fallback_enabled or not self.live_enabled:
            price_data = self._get_static_instance_price(cloud, instance_type, region)
            if price_data:
                logger.debug(f"Using static pricing for {cloud} {instance_type}")
                return price_data
        
        # Return default fallback
        logger.warning(f"No pricing found for {cloud} {instance_type}, using default")
        return {
            "hourly_price": 0.10,
            "monthly_price": 73.0,
            "confidence": "low"
        }
    
    def _get_live_instance_price(
        self,
        cloud: str,
        instance_type: str,
        region: str
    ) -> Optional[Dict[str, Any]]:
        """Get live instance pricing."""
        try:
            if cloud == "aws":
                from .aws_live import get_aws_live_adapter
                adapter = get_aws_live_adapter()
                return adapter.get_ec2_pricing(instance_type, region)
            
            elif cloud == "gcp":
                from .gcp_live import get_gcp_live_adapter
                adapter = get_gcp_live_adapter()
                return adapter.get_compute_pricing(instance_type, region)
            
            elif cloud == "azure":
                from .azure_live import get_azure_live_adapter
                adapter = get_azure_live_adapter()
                return adapter.get_vm_pricing(instance_type, region)
            
        except Exception as e:
            logger.error(f"Error getting live pricing for {cloud}: {e}")
        
        return None
    
    def _get_static_instance_price(
        self,
        cloud: str,
        instance_type: str,
        region: str
    ) -> Optional[Dict[str, Any]]:
        """Get static instance pricing."""
        try:
            if cloud == "aws":
                from .aws_static import get_aws_ec2_ondemand_price
                price_obj = get_aws_ec2_ondemand_price(region, instance_type)
                # Convert InstancePrice object to dict
                return {
                    "hourly_price": price_obj.hourly_usd,
                    "monthly_price": price_obj.monthly_usd,
                    "confidence": price_obj.pricing_confidence
                }
            
            elif cloud == "gcp":
                from .gcp_static import get_gcp_instance_price
                return get_gcp_instance_price(instance_type, region)
            
            elif cloud == "azure":
                from .azure_static import get_azure_vm_price
                return get_azure_vm_price(instance_type, region)
            
        except Exception as e:
            logger.error(f"Error getting static pricing for {cloud}: {e}")
        
        return None
    
    def get_database_price(
        self,
        cloud: str,
        db_type: str,
        region: str = None
    ) -> Dict[str, Any]:
        """
        Get database pricing with automatic fallback.
        
        Args:
            cloud: Cloud provider
            db_type: Database type/tier
            region: Region
            
        Returns:
            Pricing information
        """
        price_data = None
        
        # Try live pricing first
        if self.live_enabled:
            try:
                if cloud == "aws":
                    from .aws_live import get_aws_live_adapter
                    adapter = get_aws_live_adapter()
                    price_data = adapter.get_rds_pricing(db_type, region=region)
                
                elif cloud == "gcp":
                    # GCP SQL pricing via API (not implemented yet)
                    pass
                
                elif cloud == "azure":
                    from .azure_live import get_azure_live_adapter
                    adapter = get_azure_live_adapter()
                    price_data = adapter.get_sql_pricing(db_type, region)
                
                if price_data:
                    return price_data
            except Exception as e:
                logger.error(f"Error getting live database pricing: {e}")
        
        # Fall back to static pricing
        if cloud == "aws":
            # Use static AWS RDS pricing
            return {"hourly_price": 0.15, "monthly_price": 109.5, "confidence": "medium"}
        elif cloud == "gcp":
            from .gcp_static import get_gcp_database_price
            return get_gcp_database_price(db_type, region)
        elif cloud == "azure":
            from .azure_static import get_azure_sql_price
            return get_azure_sql_price(db_type, region)
        
        return {"hourly_price": 0.10, "monthly_price": 73.0, "confidence": "low"}


# Global instance
_pricing_factory = None


def get_pricing_factory() -> PricingFactory:
    """
    Get global pricing factory instance.
    
    Returns:
        PricingFactory instance
    """
    global _pricing_factory
    if _pricing_factory is None:
        _pricing_factory = PricingFactory()
    return _pricing_factory

