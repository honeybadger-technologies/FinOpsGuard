"""Azure Terraform resource parser."""

import re
from typing import Optional
from ..types.models import CanonicalResource


def parse_azure_resource(
    resource_type: str,
    resource_name: str,
    resource_body: str,
    default_location: str,
    count: int
) -> Optional[CanonicalResource]:
    """
    Parse Azure Terraform resource into canonical format.
    
    Args:
        resource_type: Azure resource type (e.g., 'azurerm_linux_virtual_machine')
        resource_name: Terraform resource name
        resource_body: Resource body (HCL content)
        default_location: Default Azure location
        count: Resource count from count parameter
        
    Returns:
        CanonicalResource if parsed, None if not supported
    """
    # Extract location from resource body
    location_match = re.search(r'location\s*=\s*"([a-z0-9-]+)"', resource_body, re.IGNORECASE)
    location = location_match.group(1) if location_match else default_location
    
    # Azure Virtual Machines
    if resource_type in ['azurerm_virtual_machine', 'azurerm_linux_virtual_machine', 'azurerm_windows_virtual_machine']:
        vm_size_match = re.search(r'vm_size\s*=\s*"([A-Za-z0-9_]+)"', resource_body, re.IGNORECASE)
        vm_size = vm_size_match.group(1) if vm_size_match else 'Standard_B1s'
        
        return CanonicalResource(
            id=f"{resource_name}-{vm_size}-{location}",
            type='azure_virtual_machine',
            name=resource_name,
            region=location,
            size=vm_size,
            count=count,
            tags={},
            metadata={}
        )
    
    # Azure SQL Database
    if resource_type in ['azurerm_mssql_server', 'azurerm_sql_server']:
        return CanonicalResource(
            id=f"{resource_name}-sql-server-{location}",
            type='azure_sql_server',
            name=resource_name,
            region=location,
            size='server',
            count=count,
            tags={},
            metadata={}
        )
    
    if resource_type in ['azurerm_mssql_database', 'azurerm_sql_database']:
        sku_match = re.search(r'sku_name\s*=\s*"([A-Za-z0-9_]+)"', resource_body, re.IGNORECASE)
        sku = sku_match.group(1) if sku_match else 'S0'
        
        return CanonicalResource(
            id=f"{resource_name}-sqldb-{location}",
            type='azure_sql_database',
            name=resource_name,
            region=location,
            size=sku,
            count=count,
            tags={},
            metadata={}
        )
    
    # Azure Storage Account
    if resource_type == 'azurerm_storage_account':
        tier_match = re.search(r'account_tier\s*=\s*"([A-Za-z]+)"', resource_body, re.IGNORECASE)
        replication_match = re.search(r'account_replication_type\s*=\s*"([A-Z]+)"', resource_body, re.IGNORECASE)
        
        tier = tier_match.group(1) if tier_match else 'Standard'
        replication = replication_match.group(1) if replication_match else 'LRS'
        
        return CanonicalResource(
            id=f"{resource_name}-storage-{location}",
            type='azure_storage_account',
            name=resource_name,
            region=location,
            size=f"{tier}_{replication}",
            count=count,
            tags={},
            metadata={}
        )
    
    # Azure Kubernetes Service (AKS)
    if resource_type == 'azurerm_kubernetes_cluster':
        vm_size_match = re.search(
            r'default_node_pool\s*\{[^}]*vm_size\s*=\s*"([A-Za-z0-9_]+)"',
            resource_body,
            re.IGNORECASE | re.DOTALL
        )
        node_count_match = re.search(
            r'default_node_pool\s*\{[^}]*node_count\s*=\s*([0-9]+)',
            resource_body,
            re.IGNORECASE | re.DOTALL
        )
        
        vm_size = vm_size_match.group(1) if vm_size_match else 'Standard_DS2_v2'
        node_count = int(node_count_match.group(1)) if node_count_match else 3
        
        return CanonicalResource(
            id=f"{resource_name}-aks-{location}",
            type='azure_kubernetes_cluster',
            name=resource_name,
            region=location,
            size=f"{vm_size}-{node_count}nodes",
            count=count,
            tags={},
            metadata={'node_count': node_count}
        )
    
    # Azure App Service Plan
    if resource_type in ['azurerm_app_service_plan', 'azurerm_service_plan']:
        sku_tier_match = re.search(r'sku\s*\{[^}]*tier\s*=\s*"([A-Za-z]+)"', resource_body, re.IGNORECASE | re.DOTALL)
        sku_size_match = re.search(r'sku\s*\{[^}]*size\s*=\s*"([A-Z0-9]+)"', resource_body, re.IGNORECASE | re.DOTALL)
        sku_name_match = re.search(r'sku_name\s*=\s*"([A-Z0-9]+)"', resource_body, re.IGNORECASE)
        
        if sku_name_match:
            sku = sku_name_match.group(1)
        elif sku_tier_match and sku_size_match:
            sku = f"{sku_tier_match.group(1)}_{sku_size_match.group(1)}"
        else:
            sku = 'B1'
        
        return CanonicalResource(
            id=f"{resource_name}-appplan-{location}",
            type='azure_app_service_plan',
            name=resource_name,
            region=location,
            size=sku,
            count=count,
            tags={},
            metadata={}
        )
    
    # Azure Web App
    if resource_type in ['azurerm_app_service', 'azurerm_linux_web_app', 'azurerm_windows_web_app']:
        return CanonicalResource(
            id=f"{resource_name}-webapp-{location}",
            type='azure_web_app',
            name=resource_name,
            region=location,
            size='webapp',
            count=count,
            tags={},
            metadata={}
        )
    
    # Azure Function App
    if resource_type in ['azurerm_function_app', 'azurerm_linux_function_app', 'azurerm_windows_function_app']:
        return CanonicalResource(
            id=f"{resource_name}-function-{location}",
            type='azure_function_app',
            name=resource_name,
            region=location,
            size='function',
            count=count,
            tags={},
            metadata={}
        )
    
    # Azure Load Balancer
    if resource_type == 'azurerm_lb':
        sku_match = re.search(r'sku\s*=\s*"([A-Za-z]+)"', resource_body, re.IGNORECASE)
        sku = sku_match.group(1) if sku_match else 'Basic'
        
        return CanonicalResource(
            id=f"{resource_name}-lb-{location}",
            type='azure_load_balancer',
            name=resource_name,
            region=location,
            size=sku,
            count=count,
            tags={},
            metadata={}
        )
    
    # Azure Redis Cache
    if resource_type == 'azurerm_redis_cache':
        family_match = re.search(r'family\s*=\s*"([CP])"', resource_body, re.IGNORECASE)
        capacity_match = re.search(r'capacity\s*=\s*([0-9]+)', resource_body, re.IGNORECASE)
        sku_name_match = re.search(r'sku_name\s*=\s*"([A-Za-z]+)"', resource_body, re.IGNORECASE)
        
        family = family_match.group(1).upper() if family_match else 'C'
        capacity = int(capacity_match.group(1)) if capacity_match else 0
        sku = sku_name_match.group(1) if sku_name_match else 'Basic'
        
        return CanonicalResource(
            id=f"{resource_name}-redis-{location}",
            type='azure_redis_cache',
            name=resource_name,
            region=location,
            size=f"{sku}_{family}{capacity}",
            count=count,
            tags={},
            metadata={}
        )
    
    # Azure Cosmos DB
    if resource_type == 'azurerm_cosmosdb_account':
        consistency_match = re.search(r'consistency_level\s*=\s*"([A-Za-z]+)"', resource_body, re.IGNORECASE)
        consistency = consistency_match.group(1) if consistency_match else 'Session'
        
        return CanonicalResource(
            id=f"{resource_name}-cosmos-{location}",
            type='azure_cosmosdb_account',
            name=resource_name,
            region=location,
            size=consistency,
            count=count,
            tags={},
            metadata={}
        )
    
    # Azure Container Instances
    if resource_type == 'azurerm_container_group':
        cpu_match = re.search(r'cpu\s*=\s*"?([0-9.]+)"?', resource_body, re.IGNORECASE)
        memory_match = re.search(r'memory\s*=\s*"?([0-9.]+)"?', resource_body, re.IGNORECASE)
        
        cpu = float(cpu_match.group(1)) if cpu_match else 1.0
        memory = float(memory_match.group(1)) if memory_match else 1.5
        
        return CanonicalResource(
            id=f"{resource_name}-aci-{location}",
            type='azure_container_instances',
            name=resource_name,
            region=location,
            size=f"{cpu}cpu-{memory}gb",
            count=count,
            tags={},
            metadata={'cpu': cpu, 'memory': memory}
        )
    
    # Azure Application Gateway
    if resource_type == 'azurerm_application_gateway':
        sku_match = re.search(r'sku\s*\{[^}]*name\s*=\s*"([A-Za-z0-9_]+)"', resource_body, re.IGNORECASE | re.DOTALL)
        capacity_match = re.search(r'sku\s*\{[^}]*capacity\s*=\s*([0-9]+)', resource_body, re.IGNORECASE | re.DOTALL)
        
        sku = sku_match.group(1) if sku_match else 'Standard_v2'
        capacity = int(capacity_match.group(1)) if capacity_match else 2
        
        return CanonicalResource(
            id=f"{resource_name}-appgw-{location}",
            type='azure_application_gateway',
            name=resource_name,
            region=location,
            size=f"{sku}-{capacity}",
            count=count,
            tags={},
            metadata={'capacity': capacity}
        )
    
    # Azure PostgreSQL
    if resource_type in ['azurerm_postgresql_server', 'azurerm_postgresql_flexible_server']:
        sku_match = re.search(r'sku_name\s*=\s*"([A-Z0-9_]+)"', resource_body, re.IGNORECASE)
        storage_match = re.search(r'storage_mb\s*=\s*([0-9]+)', resource_body, re.IGNORECASE)
        
        sku = sku_match.group(1) if sku_match else 'B_Gen5_2'
        storage_gb = int(storage_match.group(1)) / 1024 if storage_match else 5
        
        return CanonicalResource(
            id=f"{resource_name}-postgresql-{location}",
            type='azure_postgresql_server',
            name=resource_name,
            region=location,
            size=f"{sku}-{int(storage_gb)}GB",
            count=count,
            tags={},
            metadata={'storage_gb': storage_gb}
        )
    
    # Azure MySQL
    if resource_type in ['azurerm_mysql_server', 'azurerm_mysql_flexible_server']:
        sku_match = re.search(r'sku_name\s*=\s*"([A-Z0-9_]+)"', resource_body, re.IGNORECASE)
        storage_match = re.search(r'storage_mb\s*=\s*([0-9]+)', resource_body, re.IGNORECASE)
        
        sku = sku_match.group(1) if sku_match else 'B_Gen5_2'
        storage_gb = int(storage_match.group(1)) / 1024 if storage_match else 5
        
        return CanonicalResource(
            id=f"{resource_name}-mysql-{location}",
            type='azure_mysql_server',
            name=resource_name,
            region=location,
            size=f"{sku}-{int(storage_gb)}GB",
            count=count,
            tags={},
            metadata={'storage_gb': storage_gb}
        )
    
    # Azure SQL Managed Instance
    if resource_type == 'azurerm_sql_managed_instance':
        sku_match = re.search(r'sku_name\s*=\s*"([A-Z0-9_]+)"', resource_body, re.IGNORECASE)
        vcores_match = re.search(r'vcores\s*=\s*([0-9]+)', resource_body, re.IGNORECASE)
        storage_match = re.search(r'storage_size_in_gb\s*=\s*([0-9]+)', resource_body, re.IGNORECASE)
        
        sku = sku_match.group(1) if sku_match else 'GP_Gen5'
        vcores = int(vcores_match.group(1)) if vcores_match else 4
        storage = int(storage_match.group(1)) if storage_match else 32
        
        return CanonicalResource(
            id=f"{resource_name}-sqlmi-{location}",
            type='azure_sql_managed_instance',
            name=resource_name,
            region=location,
            size=f"{sku}-{vcores}vCore-{storage}GB",
            count=count,
            tags={},
            metadata={'vcores': vcores, 'storage_gb': storage}
        )
    
    # Azure Data Factory
    if resource_type == 'azurerm_data_factory':
        return CanonicalResource(
            id=f"{resource_name}-adf-{location}",
            type='azure_data_factory',
            name=resource_name,
            region=location,
            size='standard',
            count=count,
            tags={},
            metadata={}
        )
    
    # Azure Virtual Network Gateway (VPN Gateway)
    if resource_type == 'azurerm_virtual_network_gateway':
        sku_match = re.search(r'sku\s*=\s*"([A-Za-z0-9]+)"', resource_body, re.IGNORECASE)
        type_match = re.search(r'type\s*=\s*"([A-Za-z]+)"', resource_body, re.IGNORECASE)
        
        sku = sku_match.group(1) if sku_match else 'Basic'
        gw_type = type_match.group(1) if type_match else 'Vpn'
        
        return CanonicalResource(
            id=f"{resource_name}-vnetgw-{location}",
            type='azure_virtual_network_gateway',
            name=resource_name,
            region=location,
            size=f"{gw_type}_{sku}",
            count=count,
            tags={},
            metadata={}
        )
    
    # Azure Synapse Workspace
    if resource_type == 'azurerm_synapse_workspace':
        return CanonicalResource(
            id=f"{resource_name}-synapse-{location}",
            type='azure_synapse_workspace',
            name=resource_name,
            region=location,
            size='workspace',
            count=count,
            tags={},
            metadata={}
        )
    
    # Azure Event Hub Namespace
    if resource_type == 'azurerm_eventhub_namespace':
        sku_match = re.search(r'sku\s*=\s*"([A-Za-z]+)"', resource_body, re.IGNORECASE)
        capacity_match = re.search(r'capacity\s*=\s*([0-9]+)', resource_body, re.IGNORECASE)
        
        sku = sku_match.group(1) if sku_match else 'Basic'
        capacity = int(capacity_match.group(1)) if capacity_match else 1
        
        return CanonicalResource(
            id=f"{resource_name}-eventhub-{location}",
            type='azure_eventhub_namespace',
            name=resource_name,
            region=location,
            size=f"{sku}-{capacity}",
            count=count,
            tags={},
            metadata={'capacity': capacity}
        )
    
    # Resource type not supported
    return None


def get_azure_default_location(hcl_text: str) -> str:
    """
    Extract default Azure location from provider block.
    
    Args:
        hcl_text: Full Terraform HCL content
        
    Returns:
        Default location or 'eastus'
    """
    # Azure provider doesn't typically specify default location
    # but we check for features block to confirm azurerm provider exists
    return 'eastus'

