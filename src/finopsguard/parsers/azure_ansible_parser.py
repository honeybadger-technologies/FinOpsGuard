"""Azure Ansible module parser."""

import re
from typing import Optional, Dict, Any
from ..types.models import CanonicalResource


def parse_azure_ansible_task(
    module_name: str,
    module_params: Dict[str, Any],
    task_name: str,
    task_vars: Dict[str, Any],
    default_location: str
) -> Optional[CanonicalResource]:
    """
    Parse Azure Ansible task into canonical format.
    
    Args:
        module_name: Ansible module name (e.g., 'azure_rm_virtualmachine')
        module_params: Module parameters
        task_name: Task name
        task_vars: Task variables
        default_location: Default Azure location
        
    Returns:
        CanonicalResource if parsed, None if not supported
    """
    # Extract location from module params or use default
    location = module_params.get('location', default_location)
    if not location:
        location = 'eastus'  # Fallback
    
    # Azure Virtual Machines
    if module_name == 'azure_rm_virtualmachine':
        vm_size = module_params.get('vm_size', 'Standard_B1s')
        
        return CanonicalResource(
            id=f"{task_name}-{vm_size}-{location}",
            type='azurerm_virtual_machine',
            name=task_name,
            region=location,
            size=vm_size,
            count=1,
            tags=module_params.get('tags', {}),
            metadata={
                'module': 'azure_rm_virtualmachine',
                'resource_group': module_params.get('resource_group'),
                'image': module_params.get('image'),
                'admin_username': module_params.get('admin_username'),
                'ssh_password_enabled': module_params.get('ssh_password_enabled'),
                'storage_account': module_params.get('storage_account'),
                'storage_container': module_params.get('storage_container')
            }
        )
    
    # Azure Virtual Machine Scale Sets
    elif module_name == 'azure_rm_virtualmachinescaleset':
        vm_size = module_params.get('vm_size', 'Standard_B1s')
        capacity = module_params.get('capacity', 1)
        
        return CanonicalResource(
            id=f"{task_name}-vmss-{vm_size}-{location}",
            type='azurerm_virtual_machine_scale_set',
            name=task_name,
            region=location,
            size=vm_size,
            count=capacity,
            tags=module_params.get('tags', {}),
            metadata={
                'module': 'azure_rm_virtualmachinescaleset',
                'resource_group': module_params.get('resource_group'),
                'image': module_params.get('image'),
                'admin_username': module_params.get('admin_username'),
                'upgrade_policy': module_params.get('upgrade_policy')
            }
        )
    
    # Azure Container Instances
    elif module_name == 'azure_rm_containerinstance':
        cpu_cores = module_params.get('cpu_cores', 1)
        memory_gb = module_params.get('memory_gb', 1.5)
        
        return CanonicalResource(
            id=f"{task_name}-aci-{cpu_cores}cpu-{memory_gb}gb-{location}",
            type='azurerm_container_group',
            name=task_name,
            region=location,
            size=f"{cpu_cores}CPU-{memory_gb}GB",
            count=1,
            tags=module_params.get('tags', {}),
            metadata={
                'module': 'azure_rm_containerinstance',
                'resource_group': module_params.get('resource_group'),
                'image': module_params.get('image'),
                'ports': module_params.get('ports', []),
                'environment_variables': module_params.get('environment_variables', {})
            }
        )
    
    # Azure Kubernetes Service
    elif module_name == 'azure_rm_aks':
        node_count = module_params.get('agent_pool_profiles', [{}])[0].get('count', 1)
        vm_size = module_params.get('agent_pool_profiles', [{}])[0].get('vm_size', 'Standard_D2s_v3')
        
        return CanonicalResource(
            id=f"{task_name}-aks-{location}",
            type='azurerm_kubernetes_cluster',
            name=task_name,
            region=location,
            size=vm_size,
            count=node_count,
            tags=module_params.get('tags', {}),
            metadata={
                'module': 'azure_rm_aks',
                'resource_group': module_params.get('resource_group'),
                'dns_prefix': module_params.get('dns_prefix'),
                'kubernetes_version': module_params.get('kubernetes_version'),
                'agent_pool_profiles': module_params.get('agent_pool_profiles', [])
            }
        )
    
    # Azure App Service Plans
    elif module_name == 'azure_rm_appserviceplan':
        sku = module_params.get('sku', 'F1')
        
        return CanonicalResource(
            id=f"{task_name}-asp-{sku}-{location}",
            type='azurerm_app_service_plan',
            name=task_name,
            region=location,
            size=sku,
            count=1,
            tags=module_params.get('tags', {}),
            metadata={
                'module': 'azure_rm_appserviceplan',
                'resource_group': module_params.get('resource_group'),
                'kind': module_params.get('kind'),
                'reserved': module_params.get('reserved', False)
            }
        )
    
    # Azure App Services
    elif module_name == 'azure_rm_webapp':
        return CanonicalResource(
            id=f"{task_name}-webapp-{location}",
            type='azurerm_app_service',
            name=task_name,
            region=location,
            size='standard',
            count=1,
            tags=module_params.get('tags', {}),
            metadata={
                'module': 'azure_rm_webapp',
                'resource_group': module_params.get('resource_group'),
                'app_service_plan': module_params.get('app_service_plan'),
                'deployment_source': module_params.get('deployment_source', {})
            }
        )
    
    # Azure Function Apps
    elif module_name == 'azure_rm_functionapp':
        return CanonicalResource(
            id=f"{task_name}-func-{location}",
            type='azurerm_function_app',
            name=task_name,
            region=location,
            size='standard',
            count=1,
            tags=module_params.get('tags', {}),
            metadata={
                'module': 'azure_rm_functionapp',
                'resource_group': module_params.get('resource_group'),
                'app_service_plan': module_params.get('app_service_plan'),
                'storage_account': module_params.get('storage_account'),
                'app_settings': module_params.get('app_settings', {})
            }
        )
    
    # Azure SQL Servers
    elif module_name == 'azure_rm_sqlserver':
        return CanonicalResource(
            id=f"{task_name}-sqlserver-{location}",
            type='azurerm_sql_server',
            name=task_name,
            region=location,
            size='standard',
            count=1,
            tags=module_params.get('tags', {}),
            metadata={
                'module': 'azure_rm_sqlserver',
                'resource_group': module_params.get('resource_group'),
                'admin_username': module_params.get('admin_username'),
                'version': module_params.get('version', '12.0')
            }
        )
    
    # Azure SQL Databases
    elif module_name == 'azure_rm_sqldatabase':
        service_objective = module_params.get('service_objective', 'S0')
        
        return CanonicalResource(
            id=f"{task_name}-sqldb-{service_objective}-{location}",
            type='azurerm_sql_database',
            name=task_name,
            region=location,
            size=service_objective,
            count=1,
            tags=module_params.get('tags', {}),
            metadata={
                'module': 'azure_rm_sqldatabase',
                'resource_group': module_params.get('resource_group'),
                'server_name': module_params.get('server_name'),
                'collation': module_params.get('collation'),
                'max_size_bytes': module_params.get('max_size_bytes')
            }
        )
    
    # Azure Storage Accounts
    elif module_name == 'azure_rm_storageaccount':
        account_type = module_params.get('account_type', 'Standard_LRS')
        
        return CanonicalResource(
            id=f"{task_name}-storage-{account_type}-{location}",
            type='azurerm_storage_account',
            name=task_name,
            region=location,
            size=account_type,
            count=1,
            tags=module_params.get('tags', {}),
            metadata={
                'module': 'azure_rm_storageaccount',
                'resource_group': module_params.get('resource_group'),
                'account_type': account_type,
                'access_tier': module_params.get('access_tier', 'Hot'),
                'https_traffic_only': module_params.get('https_traffic_only', True)
            }
        )
    
    # Azure Service Bus Namespaces
    elif module_name == 'azure_rm_servicebus':
        sku = module_params.get('sku', 'Standard')
        
        return CanonicalResource(
            id=f"{task_name}-sb-{sku}-{location}",
            type='azurerm_servicebus_namespace',
            name=task_name,
            region=location,
            size=sku,
            count=1,
            tags=module_params.get('tags', {}),
            metadata={
                'module': 'azure_rm_servicebus',
                'resource_group': module_params.get('resource_group'),
                'capacity': module_params.get('capacity')
            }
        )
    
    # Azure Service Bus Topics
    elif module_name == 'azure_rm_servicebustopic':
        return CanonicalResource(
            id=f"{task_name}-sbtopic-{location}",
            type='azurerm_servicebus_topic',
            name=task_name,
            region=location,
            size='standard',
            count=1,
            tags=module_params.get('tags', {}),
            metadata={
                'module': 'azure_rm_servicebustopic',
                'resource_group': module_params.get('resource_group'),
                'namespace': module_params.get('namespace'),
                'enable_partitioning': module_params.get('enable_partitioning', False),
                'enable_express': module_params.get('enable_express', False)
            }
        )
    
    # Azure Service Bus Queues
    elif module_name == 'azure_rm_servicebusqueue':
        return CanonicalResource(
            id=f"{task_name}-sbqueue-{location}",
            type='azurerm_servicebus_queue',
            name=task_name,
            region=location,
            size='standard',
            count=1,
            tags=module_params.get('tags', {}),
            metadata={
                'module': 'azure_rm_servicebusqueue',
                'resource_group': module_params.get('resource_group'),
                'namespace': module_params.get('namespace'),
                'enable_partitioning': module_params.get('enable_partitioning', False),
                'enable_express': module_params.get('enable_express', False)
            }
        )
    
    # Azure API Management
    elif module_name == 'azure_rm_apimanagement':
        sku = module_params.get('sku', 'Developer')
        
        return CanonicalResource(
            id=f"{task_name}-apim-{sku}-{location}",
            type='azurerm_api_management',
            name=task_name,
            region=location,
            size=sku,
            count=1,
            tags=module_params.get('tags', {}),
            metadata={
                'module': 'azure_rm_apimanagement',
                'resource_group': module_params.get('resource_group'),
                'sku': sku,
                'publisher_name': module_params.get('publisher_name'),
                'publisher_email': module_params.get('publisher_email')
            }
        )
    
    # Azure Load Balancers
    elif module_name == 'azure_rm_loadbalancer':
        return CanonicalResource(
            id=f"{task_name}-lb-{location}",
            type='azurerm_lb',
            name=task_name,
            region=location,
            size='standard',
            count=1,
            tags=module_params.get('tags', {}),
            metadata={
                'module': 'azure_rm_loadbalancer',
                'resource_group': module_params.get('resource_group'),
                'sku': module_params.get('sku', 'Basic'),
                'frontend_ip_configurations': module_params.get('frontend_ip_configurations', [])
            }
        )
    
    # Azure Redis Cache
    elif module_name == 'azure_rm_rediscache':
        sku = module_params.get('sku', 'Standard')
        capacity = module_params.get('capacity', 1)
        
        return CanonicalResource(
            id=f"{task_name}-redis-{sku}-{capacity}-{location}",
            type='azurerm_redis_cache',
            name=task_name,
            region=location,
            size=f"{sku}-{capacity}",
            count=1,
            tags=module_params.get('tags', {}),
            metadata={
                'module': 'azure_rm_rediscache',
                'resource_group': module_params.get('resource_group'),
                'sku': sku,
                'capacity': capacity,
                'family': module_params.get('family', 'C'),
                'enable_non_ssl_port': module_params.get('enable_non_ssl_port', False)
            }
        )
    
    # Azure Cosmos DB
    elif module_name == 'azure_rm_cosmosdbaccount':
        offer_type = module_params.get('offer_type', 'Standard')
        
        return CanonicalResource(
            id=f"{task_name}-cosmos-{offer_type}-{location}",
            type='azurerm_cosmosdb_account',
            name=task_name,
            region=location,
            size=offer_type,
            count=1,
            tags=module_params.get('tags', {}),
            metadata={
                'module': 'azure_rm_cosmosdbaccount',
                'resource_group': module_params.get('resource_group'),
                'offer_type': offer_type,
                'kind': module_params.get('kind', 'GlobalDocumentDB'),
                'consistency_policy': module_params.get('consistency_policy', {})
            }
        )
    
    # Azure Event Hubs
    elif module_name == 'azure_rm_eventhub':
        return CanonicalResource(
            id=f"{task_name}-eh-{location}",
            type='azurerm_eventhub',
            name=task_name,
            region=location,
            size='standard',
            count=1,
            tags=module_params.get('tags', {}),
            metadata={
                'module': 'azure_rm_eventhub',
                'resource_group': module_params.get('resource_group'),
                'namespace_name': module_params.get('namespace_name'),
                'message_retention': module_params.get('message_retention', 1),
                'partition_count': module_params.get('partition_count', 2)
            }
        )
    
    # Azure Logic Apps
    elif module_name == 'azure_rm_logicapp':
        return CanonicalResource(
            id=f"{task_name}-logic-{location}",
            type='azurerm_logic_app_workflow',
            name=task_name,
            region=location,
            size='standard',
            count=1,
            tags=module_params.get('tags', {}),
            metadata={
                'module': 'azure_rm_logicapp',
                'resource_group': module_params.get('resource_group'),
                'app_service_plan': module_params.get('app_service_plan'),
                'workflow_state': module_params.get('workflow_state', 'Enabled')
            }
        )
    
    return None


def get_azure_default_location(content: str) -> str:
    """
    Extract default Azure location from Ansible playbook content.
    
    Args:
        content: Ansible playbook YAML content
        
    Returns:
        Default Azure location or empty string if not found
    """
    # Look for Azure location in variables
    location_patterns = [
        r'azure_location:\s*["\']?([a-z0-9-]+)["\']?',
        r'location:\s*["\']?([a-z0-9-]+)["\']?',
        r'AZURE_LOCATION:\s*["\']?([a-z0-9-]+)["\']?'
    ]
    
    for pattern in location_patterns:
        match = re.search(pattern, content, re.IGNORECASE)
        if match:
            return match.group(1)
    
    return ''
