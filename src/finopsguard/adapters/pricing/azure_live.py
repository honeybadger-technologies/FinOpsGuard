"""Azure real-time pricing adapter using Azure Retail Prices API."""

import os
import logging
from typing import Dict, List, Optional, Any

import requests

logger = logging.getLogger(__name__)

# Configuration
AZURE_PRICING_ENABLED = os.getenv("AZURE_PRICING_ENABLED", "false").lower() == "true"
AZURE_PRICING_API_ENDPOINT = "https://prices.azure.com/api/retail/prices"
AZURE_REGION = os.getenv("AZURE_REGION", "eastus")


class AzureLivePricingAdapter:
    """Azure live pricing adapter using Retail Prices API."""
    
    def __init__(self):
        """Initialize Azure pricing adapter."""
        self.enabled = AZURE_PRICING_ENABLED
        self.endpoint = AZURE_PRICING_API_ENDPOINT
        self.session = requests.Session()
    
    def get_vm_pricing(
        self,
        vm_size: str,
        region: str = None
    ) -> Optional[Dict[str, Any]]:
        """
        Get real-time Azure VM pricing.
        
        Args:
            vm_size: VM size (e.g., Standard_D2s_v3)
            region: Azure region
            
        Returns:
            Pricing information or None
        """
        if not self.enabled:
            return None
        
        region = region or AZURE_REGION
        
        try:
            # Build filter query
            # Example: armSkuName eq 'Standard_D2s_v3' and armRegionName eq 'eastus' and priceType eq 'Consumption'
            filter_query = (
                f"serviceName eq 'Virtual Machines' "
                f"and armSkuName eq '{vm_size}' "
                f"and armRegionName eq '{region}' "
                f"and priceType eq 'Consumption'"
            )
            
            params = {
                "$filter": filter_query,
                "currencyCode": "USD"
            }
            
            response = self.session.get(
                self.endpoint,
                params=params,
                timeout=10
            )
            
            if response.status_code != 200:
                logger.warning(f"Azure Pricing API returned {response.status_code}")
                return None
            
            data = response.json()
            items = data.get("Items", [])
            
            if not items:
                logger.warning(f"No pricing found for {vm_size} in {region}")
                return None
            
            # Get first matching item
            item = items[0]
            hourly_price = item.get("retailPrice", 0.0)
            
            return {
                "hourly_price": hourly_price,
                "monthly_price": hourly_price * 730,
                "vm_size": vm_size,
                "region": region,
                "unit_of_measure": item.get("unitOfMeasure", "1 Hour"),
                "confidence": "high"
            }
            
        except Exception as e:
            logger.error(f"Error fetching Azure pricing for {vm_size}: {e}")
            return None
    
    def get_sql_pricing(
        self,
        tier: str,
        region: str = None
    ) -> Optional[Dict[str, Any]]:
        """
        Get real-time Azure SQL Database pricing.
        
        Args:
            tier: SQL tier (e.g., S1, P1)
            region: Azure region
            
        Returns:
            Pricing information or None
        """
        if not self.enabled:
            return None
        
        region = region or AZURE_REGION
        
        try:
            filter_query = (
                f"serviceName eq 'SQL Database' "
                f"and armSkuName eq '{tier}' "
                f"and armRegionName eq '{region}' "
                f"and priceType eq 'Consumption'"
            )
            
            params = {
                "$filter": filter_query,
                "currencyCode": "USD"
            }
            
            response = self.session.get(
                self.endpoint,
                params=params,
                timeout=10
            )
            
            if response.status_code != 200:
                return None
            
            data = response.json()
            items = data.get("Items", [])
            
            if not items:
                return None
            
            item = items[0]
            hourly_price = item.get("retailPrice", 0.0)
            
            return {
                "hourly_price": hourly_price,
                "monthly_price": hourly_price * 730,
                "tier": tier,
                "region": region,
                "confidence": "high"
            }
            
        except Exception as e:
            logger.error(f"Error fetching Azure SQL pricing for {tier}: {e}")
            return None


# Global instance
_azure_live_adapter = None


def get_azure_live_adapter() -> AzureLivePricingAdapter:
    """
    Get global Azure live pricing adapter instance.
    
    Returns:
        AzureLivePricingAdapter instance
    """
    global _azure_live_adapter
    if _azure_live_adapter is None:
        _azure_live_adapter = AzureLivePricingAdapter()
    return _azure_live_adapter


