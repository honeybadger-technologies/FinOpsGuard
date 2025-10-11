"""GCP real-time pricing adapter using Cloud Billing API."""

import os
import logging
from typing import Dict, List, Optional, Any

import requests

logger = logging.getLogger(__name__)

# Configuration
GCP_PRICING_ENABLED = os.getenv("GCP_PRICING_ENABLED", "false").lower() == "true"
GCP_PRICING_API_KEY = os.getenv("GCP_PRICING_API_KEY", "")
GCP_BILLING_API_ENDPOINT = "https://cloudbilling.googleapis.com/v1"


class GCPLivePricingAdapter:
    """GCP live pricing adapter using Cloud Billing API."""
    
    def __init__(self):
        """Initialize GCP pricing adapter."""
        self.enabled = GCP_PRICING_ENABLED and bool(GCP_PRICING_API_KEY)
        self.api_key = GCP_PRICING_API_KEY
        self.endpoint = GCP_BILLING_API_ENDPOINT
        
        if GCP_PRICING_ENABLED and not GCP_PRICING_API_KEY:
            logger.warning("GCP pricing enabled but API key not provided")
            self.enabled = False
    
    def get_compute_pricing(
        self,
        machine_type: str,
        region: str = "us-central1"
    ) -> Optional[Dict[str, Any]]:
        """
        Get real-time Compute Engine pricing.
        
        Args:
            machine_type: Machine type (e.g., n1-standard-1)
            region: GCP region
            
        Returns:
            Pricing information or None
        """
        if not self.enabled:
            return None
        
        try:
            # Query Cloud Billing API
            url = f"{self.endpoint}/services/6F81-5844-456A/skus"  # Compute Engine service
            params = {
                "key": self.api_key,
                "currencyCode": "USD"
            }
            
            response = requests.get(url, params=params, timeout=10)
            
            if response.status_code != 200:
                logger.warning(f"GCP Billing API returned {response.status_code}")
                return None
            
            data = response.json()
            skus = data.get("skus", [])
            
            # Find matching SKU
            for sku in skus:
                description = sku.get("description", "")
                if machine_type in description and region in description.lower():
                    # Extract pricing
                    pricing_info = sku.get("pricingInfo", [])
                    if pricing_info:
                        pricing_expression = pricing_info[0].get("pricingExpression", {})
                        tiered_rates = pricing_expression.get("tieredRates", [])
                        
                        if tiered_rates:
                            unit_price = tiered_rates[0].get("unitPrice", {})
                            nanos = unit_price.get("nanos", 0)
                            units = unit_price.get("units", "0")
                            
                            # Convert to USD
                            hourly_price = float(units) + (nanos / 1_000_000_000)
                            
                            return {
                                "hourly_price": hourly_price,
                                "monthly_price": hourly_price * 730,
                                "machine_type": machine_type,
                                "region": region,
                                "confidence": "high"
                            }
            
            return None
            
        except Exception as e:
            logger.error(f"Error fetching GCP pricing for {machine_type}: {e}")
            return None


# Global instance
_gcp_live_adapter = None


def get_gcp_live_adapter() -> GCPLivePricingAdapter:
    """
    Get global GCP live pricing adapter instance.
    
    Returns:
        GCPLivePricingAdapter instance
    """
    global _gcp_live_adapter
    if _gcp_live_adapter is None:
        _gcp_live_adapter = GCPLivePricingAdapter()
    return _gcp_live_adapter


