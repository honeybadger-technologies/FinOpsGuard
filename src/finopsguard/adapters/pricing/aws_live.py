"""AWS real-time pricing adapter using AWS Pricing API."""

import os
import logging
from typing import Dict, List, Optional, Any
import json

import requests

logger = logging.getLogger(__name__)

# Configuration
AWS_PRICING_ENABLED = os.getenv("AWS_PRICING_ENABLED", "false").lower() == "true"
AWS_PRICING_API_ENDPOINT = "https://pricing.us-east-1.amazonaws.com"
AWS_REGION = os.getenv("AWS_REGION", "us-east-1")


class AWSLivePricingAdapter:
    """AWS live pricing adapter using AWS Pricing API."""
    
    def __init__(self):
        """Initialize AWS pricing adapter."""
        self.enabled = AWS_PRICING_ENABLED
        self.endpoint = AWS_PRICING_API_ENDPOINT
        self.session = requests.Session()
        self.session.headers.update({
            "Content-Type": "application/x-amz-json-1.1"
        })
    
    def get_ec2_pricing(
        self,
        instance_type: str,
        region: str = None,
        operating_system: str = "Linux"
    ) -> Optional[Dict[str, Any]]:
        """
        Get real-time EC2 pricing.
        
        Args:
            instance_type: EC2 instance type (e.g., t3.medium)
            region: AWS region
            operating_system: OS (Linux, Windows)
            
        Returns:
            Pricing information or None
        """
        if not self.enabled:
            return None
        
        region = region or AWS_REGION
        
        try:
            # Convert region name to pricing API format
            region_name = self._get_region_name(region)
            
            # Build filter
            filters = [
                {"Type": "TERM_MATCH", "Field": "instanceType", "Value": instance_type},
                {"Type": "TERM_MATCH", "Field": "location", "Value": region_name},
                {"Type": "TERM_MATCH", "Field": "operatingSystem", "Value": operating_system},
                {"Type": "TERM_MATCH", "Field": "tenancy", "Value": "Shared"},
                {"Type": "TERM_MATCH", "Field": "preInstalledSw", "Value": "NA"},
                {"Type": "TERM_MATCH", "Field": "capacitystatus", "Value": "Used"}
            ]
            
            payload = {
                "ServiceCode": "AmazonEC2",
                "Filters": filters,
                "FormatVersion": "aws_v1",
                "MaxResults": 1
            }
            
            response = self.session.post(
                f"{self.endpoint}/",
                headers={"X-Amz-Target": "AWSPriceListService.GetProducts"},
                json=payload,
                timeout=10
            )
            
            if response.status_code != 200:
                logger.warning(f"AWS Pricing API returned {response.status_code}")
                return None
            
            data = response.json()
            price_list = data.get("PriceList", [])
            
            if not price_list:
                logger.warning(f"No pricing found for {instance_type} in {region}")
                return None
            
            # Parse pricing from response
            price_item = json.loads(price_list[0])
            on_demand = price_item.get("terms", {}).get("OnDemand", {})
            
            if not on_demand:
                return None
            
            # Extract price from nested structure
            for term in on_demand.values():
                for price_dimension in term.get("priceDimensions", {}).values():
                    price_per_unit = price_dimension.get("pricePerUnit", {}).get("USD")
                    if price_per_unit:
                        hourly_price = float(price_per_unit)
                        
                        # Extract vCPU and memory from attributes
                        attributes = price_item.get("product", {}).get("attributes", {})
                        vcpu = int(attributes.get("vcpu", 2))
                        memory = float(attributes.get("memory", "4 GiB").split()[0])
                        
                        return {
                            "hourly_price": hourly_price,
                            "monthly_price": hourly_price * 730,
                            "vcpu": vcpu,
                            "memory": memory,
                            "region": region,
                            "confidence": "high"
                        }
            
            return None
            
        except Exception as e:
            logger.error(f"Error fetching AWS pricing for {instance_type}: {e}")
            return None
    
    def get_rds_pricing(
        self,
        instance_class: str,
        engine: str = "postgres",
        region: str = None
    ) -> Optional[Dict[str, Any]]:
        """
        Get real-time RDS pricing.
        
        Args:
            instance_class: RDS instance class (e.g., db.t3.medium)
            engine: Database engine
            region: AWS region
            
        Returns:
            Pricing information or None
        """
        if not self.enabled:
            return None
        
        region = region or AWS_REGION
        
        try:
            region_name = self._get_region_name(region)
            
            filters = [
                {"Type": "TERM_MATCH", "Field": "instanceType", "Value": instance_class},
                {"Type": "TERM_MATCH", "Field": "location", "Value": region_name},
                {"Type": "TERM_MATCH", "Field": "databaseEngine", "Value": engine.capitalize()},
                {"Type": "TERM_MATCH", "Field": "deploymentOption", "Value": "Single-AZ"}
            ]
            
            payload = {
                "ServiceCode": "AmazonRDS",
                "Filters": filters,
                "FormatVersion": "aws_v1",
                "MaxResults": 1
            }
            
            response = self.session.post(
                f"{self.endpoint}/",
                headers={"X-Amz-Target": "AWSPriceListService.GetProducts"},
                json=payload,
                timeout=10
            )
            
            if response.status_code != 200:
                return None
            
            data = response.json()
            price_list = data.get("PriceList", [])
            
            if not price_list:
                return None
            
            # Parse pricing
            price_item = json.loads(price_list[0])
            on_demand = price_item.get("terms", {}).get("OnDemand", {})
            
            for term in on_demand.values():
                for price_dimension in term.get("priceDimensions", {}).values():
                    price_per_unit = price_dimension.get("pricePerUnit", {}).get("USD")
                    if price_per_unit:
                        hourly_price = float(price_per_unit)
                        
                        return {
                            "hourly_price": hourly_price,
                            "monthly_price": hourly_price * 730,
                            "engine": engine,
                            "region": region,
                            "confidence": "high"
                        }
            
            return None
            
        except Exception as e:
            logger.error(f"Error fetching RDS pricing for {instance_class}: {e}")
            return None
    
    def _get_region_name(self, region_code: str) -> str:
        """
        Convert AWS region code to pricing API region name.
        
        Args:
            region_code: AWS region code (e.g., us-east-1)
            
        Returns:
            Region name for pricing API
        """
        region_mapping = {
            "us-east-1": "US East (N. Virginia)",
            "us-east-2": "US East (Ohio)",
            "us-west-1": "US West (N. California)",
            "us-west-2": "US West (Oregon)",
            "eu-west-1": "EU (Ireland)",
            "eu-west-2": "EU (London)",
            "eu-west-3": "EU (Paris)",
            "eu-central-1": "EU (Frankfurt)",
            "ap-southeast-1": "Asia Pacific (Singapore)",
            "ap-southeast-2": "Asia Pacific (Sydney)",
            "ap-northeast-1": "Asia Pacific (Tokyo)",
            "ap-south-1": "Asia Pacific (Mumbai)",
        }
        
        return region_mapping.get(region_code, "US East (N. Virginia)")


# Global instance
_aws_live_adapter = None


def get_aws_live_adapter() -> AWSLivePricingAdapter:
    """
    Get global AWS live pricing adapter instance.
    
    Returns:
        AWSLivePricingAdapter instance
    """
    global _aws_live_adapter
    if _aws_live_adapter is None:
        _aws_live_adapter = AWSLivePricingAdapter()
    return _aws_live_adapter


