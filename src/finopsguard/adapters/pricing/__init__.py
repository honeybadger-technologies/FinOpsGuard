"""
Pricing adapters for different cloud providers.

This module provides pricing adapters for AWS, GCP, and other cloud providers.
"""

from .aws_static import (
    get_aws_ec2_ondemand_price,
    list_aws_ec2_ondemand,
    MONTHLY_FLAT_USD,
    HOURLY_SERVICE_USD
)

from .gcp_static import (
    get_gcp_instance_price,
    get_gcp_database_price,
    get_gcp_storage_price,
    get_gcp_load_balancer_price,
    get_gcp_kubernetes_price,
    get_gcp_cloud_run_price,
    get_gcp_cloud_functions_price,
    get_gcp_price_catalog,
    is_gcp_resource
)

from .azure_static import (
    get_azure_vm_price,
    get_azure_sql_price,
    get_azure_storage_price,
    get_azure_aks_price,
    get_azure_app_service_price,
    get_azure_functions_price,
    get_azure_load_balancer_price,
    get_azure_redis_price,
    get_azure_cosmos_price,
    get_azure_price_catalog,
    is_azure_resource
)

__all__ = [
    # AWS pricing functions
    "get_aws_ec2_ondemand_price",
    "list_aws_ec2_ondemand",
    "MONTHLY_FLAT_USD",
    "HOURLY_SERVICE_USD",
    
    # GCP pricing functions
    "get_gcp_instance_price",
    "get_gcp_database_price",
    "get_gcp_storage_price",
    "get_gcp_load_balancer_price",
    "get_gcp_kubernetes_price",
    "get_gcp_cloud_run_price",
    "get_gcp_cloud_functions_price",
    "get_gcp_price_catalog",
    "is_gcp_resource",
    
    # Azure pricing functions
    "get_azure_vm_price",
    "get_azure_sql_price",
    "get_azure_storage_price",
    "get_azure_aks_price",
    "get_azure_app_service_price",
    "get_azure_functions_price",
    "get_azure_load_balancer_price",
    "get_azure_redis_price",
    "get_azure_cosmos_price",
    "get_azure_price_catalog",
    "is_azure_resource",
]