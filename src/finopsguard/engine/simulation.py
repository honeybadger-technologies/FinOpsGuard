"""
Cost simulation engine
"""

from typing import List
from ..types.models import CanonicalResourceModel
from ..types.api import CheckResponse, ResourceBreakdownItem
from ..adapters.pricing.aws_static import (
    get_aws_ec2_ondemand_price,
    MONTHLY_FLAT_USD,
    HOURLY_SERVICE_USD
)


def simulate_cost(cr_model: CanonicalResourceModel) -> CheckResponse:
    """Simulate cost for a canonical resource model"""
    breakdown: List[ResourceBreakdownItem] = []
    total_monthly = 0.0
    
    for resource in cr_model.resources:
        if resource.type == 'aws_instance':
            price = get_aws_ec2_ondemand_price(resource.region, resource.size)
            monthly = price.monthly_usd * resource.count
            total_monthly += monthly
            breakdown.append(ResourceBreakdownItem(
                resource_id=resource.id,
                monthly_cost=monthly,
                notes=[]
            ))
            continue
            
        if resource.type == 'aws_lb':
            monthly = MONTHLY_FLAT_USD['aws_lb_application'] * resource.count
            total_monthly += monthly
            breakdown.append(ResourceBreakdownItem(
                resource_id=resource.id,
                monthly_cost=monthly,
                notes=[]
            ))
            continue
            
        if resource.type == 'aws_asg':
            price = get_aws_ec2_ondemand_price(resource.region, resource.size)
            monthly = price.monthly_usd * resource.count
            total_monthly += monthly
            breakdown.append(ResourceBreakdownItem(
                resource_id=resource.id,
                monthly_cost=monthly,
                notes=[]
            ))
            continue
            
        if resource.type == 'aws_eks_cluster':
            monthly = MONTHLY_FLAT_USD['aws_eks_cluster_control_plane'] * resource.count
            total_monthly += monthly
            breakdown.append(ResourceBreakdownItem(
                resource_id=resource.id,
                monthly_cost=monthly,
                notes=[]
            ))
            continue
            
        if resource.type == 'aws_rds_instance':
            key = f"{resource.region}:{resource.size}"
            hourly = HOURLY_SERVICE_USD['rds'].get(key, 0.05)
            monthly = hourly * 730 * resource.count
            total_monthly += monthly
            breakdown.append(ResourceBreakdownItem(
                resource_id=resource.id,
                monthly_cost=monthly,
                notes=[]
            ))
            continue
            
        if resource.type == 'aws_redshift_cluster':
            key = f"{resource.region}:{resource.size}"
            hourly = HOURLY_SERVICE_USD['redshift'].get(key, 0.25)
            monthly = hourly * 730 * resource.count
            total_monthly += monthly
            breakdown.append(ResourceBreakdownItem(
                resource_id=resource.id,
                monthly_cost=monthly,
                notes=[]
            ))
            continue
            
        if resource.type == 'aws_opensearch':
            key = f"{resource.region}:{resource.size}"
            hourly = HOURLY_SERVICE_USD['opensearch'].get(key, 0.04)
            monthly = hourly * 730 * resource.count
            total_monthly += monthly
            breakdown.append(ResourceBreakdownItem(
                resource_id=resource.id,
                monthly_cost=monthly,
                notes=[]
            ))
            continue
            
        if resource.type == 'aws_elasticache':
            key = f"{resource.region}:{resource.size}"
            hourly = HOURLY_SERVICE_USD['elasticache'].get(key, 0.03)
            monthly = hourly * 730 * resource.count
            total_monthly += monthly
            breakdown.append(ResourceBreakdownItem(
                resource_id=resource.id,
                monthly_cost=monthly,
                notes=[]
            ))
            continue
            
        if resource.type == 'aws_dynamodb_table':
            if resource.size == 'PAY_PER_REQUEST':
                breakdown.append(ResourceBreakdownItem(
                    resource_id=resource.id,
                    monthly_cost=0,
                    notes=['ppr model not estimated']
                ))
                continue
                
            read = resource.metadata.get('read_capacity', 0) if resource.metadata else 0
            write = resource.metadata.get('write_capacity', 0) if resource.metadata else 0
            hourly = (read * HOURLY_SERVICE_USD['dynamodb_provisioned']['read_capacity_hour'] +
                     write * HOURLY_SERVICE_USD['dynamodb_provisioned']['write_capacity_hour'])
            monthly = hourly * 730
            total_monthly += monthly
            breakdown.append(ResourceBreakdownItem(
                resource_id=resource.id,
                monthly_cost=monthly,
                notes=[]
            ))
            continue

    estimated_first_week_cost = total_monthly / 4.345  # approx 1 week of month

    return CheckResponse(
        estimated_monthly_cost=round(total_monthly, 2),
        estimated_first_week_cost=round(estimated_first_week_cost, 2),
        breakdown_by_resource=breakdown,
        risk_flags=[],
        recommendations=[],
        pricing_confidence='high',
        duration_ms=1,
    )
