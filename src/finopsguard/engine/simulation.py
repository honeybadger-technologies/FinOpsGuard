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
from ..adapters.pricing.gcp_static import (
    get_gcp_instance_price,
    get_gcp_database_price,
    get_gcp_storage_price,
    get_gcp_load_balancer_price,
    get_gcp_kubernetes_price,
    get_gcp_cloud_run_price,
    get_gcp_cloud_functions_price
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
            if resource.count > 0:
                breakdown.append(ResourceBreakdownItem(
                    resource_id=resource.id,
                    monthly_cost=monthly,
                    notes=[]
                ))
            continue
            
        if resource.type == 'aws_lb':
            monthly = MONTHLY_FLAT_USD['aws_lb_application'] * resource.count
            total_monthly += monthly
            if resource.count > 0:
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
            if resource.count > 0:
                breakdown.append(ResourceBreakdownItem(
                    resource_id=resource.id,
                    monthly_cost=monthly,
                    notes=[]
                ))
            continue
            
        if resource.type == 'aws_eks_cluster':
            monthly = MONTHLY_FLAT_USD['aws_eks_cluster_control_plane'] * resource.count
            total_monthly += monthly
            if resource.count > 0:
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
            if resource.count > 0:
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
            if resource.count > 0:
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
            if resource.count > 0:
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
            if resource.count > 0:
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
            if resource.count > 0:
                breakdown.append(ResourceBreakdownItem(
                    resource_id=resource.id,
                    monthly_cost=monthly,
                    notes=[]
                ))
            continue

        # GCP Compute Engine instances
        if resource.type == 'gcp_compute_instance':
            price_info = get_gcp_instance_price(resource.size, resource.region)
            hourly_cost = price_info['price_per_hour']
            monthly = hourly_cost * 730 * resource.count
            total_monthly += monthly
            if resource.count > 0:
                breakdown.append(ResourceBreakdownItem(
                    resource_id=resource.id,
                    monthly_cost=monthly,
                    notes=[]
                ))
            continue

        # GCP Cloud SQL instances
        if resource.type == 'gcp_sql_database_instance':
            price_info = get_gcp_database_price(resource.size, resource.region)
            hourly_cost = price_info['price_per_hour']
            monthly = hourly_cost * 730 * resource.count
            total_monthly += monthly
            if resource.count > 0:
                breakdown.append(ResourceBreakdownItem(
                    resource_id=resource.id,
                    monthly_cost=monthly,
                    notes=[]
                ))
            continue

        # GCP Cloud Storage buckets
        if resource.type == 'gcp_storage_bucket':
            price_info = get_gcp_storage_price(resource.size)
            # Estimate 100GB per bucket as default
            estimated_storage_gb = 100
            monthly = price_info['price_per_gb_month'] * estimated_storage_gb * resource.count
            total_monthly += monthly
            if resource.count > 0:
                breakdown.append(ResourceBreakdownItem(
                    resource_id=resource.id,
                    monthly_cost=monthly,
                    notes=[f'Estimated {estimated_storage_gb}GB per bucket']
                ))
            continue

        # GCP Kubernetes Engine clusters
        if resource.type == 'gcp_container_cluster':
            price_info = get_gcp_kubernetes_price(resource.size)
            hourly_cost = price_info['price_per_cluster_hour']
            monthly = hourly_cost * 730 * resource.count
            total_monthly += monthly
            breakdown.append(ResourceBreakdownItem(
                resource_id=resource.id,
                monthly_cost=monthly,
                notes=['Cluster management cost only - node costs separate']
            ))
            continue

        # GCP Cloud Run services
        if resource.type == 'gcp_cloud_run_service':
            price_info = get_gcp_cloud_run_price()
            # Estimate 2 vCPU and 4GB memory per service, 720 hours per month
            estimated_cpu_hours = 2 * 720 * resource.count
            estimated_memory_gb_hours = 4 * 720 * resource.count
            monthly = (estimated_cpu_hours * price_info['cpu_per_hour'] + 
                      estimated_memory_gb_hours * price_info['memory_per_gb_hour'])
            total_monthly += monthly
            breakdown.append(ResourceBreakdownItem(
                resource_id=resource.id,
                monthly_cost=monthly,
                notes=['Estimated 2 vCPU, 4GB memory, 720 hours/month']
            ))
            continue

        # GCP Cloud Functions
        if resource.type == 'gcp_cloudfunctions_function':
            price_info = get_gcp_cloud_functions_price()
            # Estimate 1M invocations and 100GB-seconds per function per month
            estimated_invocations = 1000000 * resource.count
            estimated_gb_seconds = 100 * resource.count
            monthly = (estimated_invocations * price_info['invocations_per_million'] / 1000000 +
                      estimated_gb_seconds * price_info['gb_seconds'])
            total_monthly += monthly
            breakdown.append(ResourceBreakdownItem(
                resource_id=resource.id,
                monthly_cost=monthly,
                notes=['Estimated 1M invocations, 100GB-seconds per month']
            ))
            continue

        # GCP Load Balancers
        if resource.type == 'gcp_load_balancer':
            price_info = get_gcp_load_balancer_price(resource.size)
            hourly_cost = price_info['price_per_hour']
            monthly = hourly_cost * 730 * resource.count
            total_monthly += monthly
            if resource.count > 0:
                breakdown.append(ResourceBreakdownItem(
                    resource_id=resource.id,
                    monthly_cost=monthly,
                    notes=[]
                ))
            continue

        # GCP Redis instances
        if resource.type == 'gcp_redis_instance':
            # Estimate pricing based on memory size
            memory_gb = int(resource.size.split('-')[-1].replace('GB', '')) if 'GB' in resource.size else 1
            # Rough estimate: $0.10 per GB per hour
            hourly_cost = 0.10 * memory_gb
            monthly = hourly_cost * 730 * resource.count
            total_monthly += monthly
            breakdown.append(ResourceBreakdownItem(
                resource_id=resource.id,
                monthly_cost=monthly,
                notes=[f'Estimated {memory_gb}GB memory']
            ))
            continue

        # GCP BigQuery datasets
        if resource.type == 'gcp_bigquery_dataset':
            # BigQuery is pay-per-use, estimate $10/month per dataset
            monthly = 10.0 * resource.count
            total_monthly += monthly
            breakdown.append(ResourceBreakdownItem(
                resource_id=resource.id,
                monthly_cost=monthly,
                notes=['Estimated $10/month per dataset (pay-per-use)']
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
