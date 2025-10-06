"""
AWS pricing adapter with static pricing data
"""

from typing import Dict, List, Tuple
from ...types.models import PricingConfidence


# Static pricing data - simplified for MVP
ON_DEMAND_HOURLY_USD: Dict[str, float] = {
    'us-east-1:t3.micro': 0.0104,
    'us-east-1:t3.medium': 0.0416,
    'us-east-1:m5.large': 0.096,
    'us-east-1:c7g.large': 0.072,
}

# Simplified monthly costs for LB/EKS control plane, etc.
MONTHLY_FLAT_USD = {
    'aws_lb_application': 18,  # very rough placeholder
    'aws_eks_cluster_control_plane': 73,  # EKS control plane approx per month
}

# Naive static hourly prices (very rough placeholders) for select services
HOURLY_SERVICE_USD = {
    'rds': {
        'us-east-1:db.t3.micro': 0.017,
        'us-east-1:db.t3.small': 0.034,
    },
    'redshift': {
        'us-east-1:dc2.large': 0.25,
    },
    'opensearch': {
        'us-east-1:t3.small.search': 0.036,
    },
    'elasticache': {
        'us-east-1:cache.t3.micro': 0.017,
    },
    'dynamodb_provisioned': {
        'read_capacity_hour': 0.00013,  # per RCU-hour
        'write_capacity_hour': 0.00065,  # per WCU-hour
    },
}


class InstancePrice:
    """AWS instance pricing information"""
    
    def __init__(self, hourly_usd: float, monthly_usd: float, pricing_confidence: PricingConfidence):
        self.hourly_usd = hourly_usd
        self.monthly_usd = monthly_usd
        self.pricing_confidence = pricing_confidence


def get_aws_ec2_ondemand_price(region: str, instance_type: str) -> InstancePrice:
    """Get AWS EC2 on-demand pricing for a specific region and instance type"""
    key = f"{region}:{instance_type}"
    hourly = ON_DEMAND_HOURLY_USD.get(key)
    
    if hourly is None:
        # default fallback
        return InstancePrice(
            hourly_usd=0.1,
            monthly_usd=0.1 * 730,
            pricing_confidence='low'
        )
    
    return InstancePrice(
        hourly_usd=hourly,
        monthly_usd=hourly * 730,
        pricing_confidence='high'
    )


def list_aws_ec2_ondemand(region: str = None, instance_types: List[str] = None) -> List[Dict]:
    """List AWS EC2 on-demand pricing for given region and instance types"""
    items = []
    
    for key, price in ON_DEMAND_HOURLY_USD.items():
        r, it = key.split(':')
        
        if region and r != region:
            continue
        if instance_types and instance_types and it not in instance_types:
            continue
            
        items.append({
            'sku': f'aws_ec2_{it}_ondemand_{r}',
            'region': r,
            'unit': 'hour',
            'price': price,
            'description': f'EC2 {it} on-demand in {r}',
        })
    
    return items
