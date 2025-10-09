"""
Azure static pricing adapter for FinOpsGuard.
Provides static pricing data for common Azure services.
"""

from typing import Dict, List, Optional, Any

# Static pricing data for Azure Virtual Machines (Pay-As-You-Go, East US)
AZURE_VM_PRICING = {
    # B-Series (Burstable)
    "Standard_B1s": {"vcpu": 1, "memory": 1, "hourly_price": 0.0104},
    "Standard_B1ms": {"vcpu": 1, "memory": 2, "hourly_price": 0.0207},
    "Standard_B2s": {"vcpu": 2, "memory": 4, "hourly_price": 0.0416},
    "Standard_B2ms": {"vcpu": 2, "memory": 8, "hourly_price": 0.0832},
    "Standard_B4ms": {"vcpu": 4, "memory": 16, "hourly_price": 0.166},
    "Standard_B8ms": {"vcpu": 8, "memory": 32, "hourly_price": 0.333},
    
    # D-Series (General Purpose)
    "Standard_D2s_v3": {"vcpu": 2, "memory": 8, "hourly_price": 0.096},
    "Standard_D4s_v3": {"vcpu": 4, "memory": 16, "hourly_price": 0.192},
    "Standard_D8s_v3": {"vcpu": 8, "memory": 32, "hourly_price": 0.384},
    "Standard_D16s_v3": {"vcpu": 16, "memory": 64, "hourly_price": 0.768},
    "Standard_D32s_v3": {"vcpu": 32, "memory": 128, "hourly_price": 1.536},
    "Standard_D48s_v3": {"vcpu": 48, "memory": 192, "hourly_price": 2.304},
    "Standard_D64s_v3": {"vcpu": 64, "memory": 256, "hourly_price": 3.072},
    
    # E-Series (Memory Optimized)
    "Standard_E2s_v3": {"vcpu": 2, "memory": 16, "hourly_price": 0.126},
    "Standard_E4s_v3": {"vcpu": 4, "memory": 32, "hourly_price": 0.252},
    "Standard_E8s_v3": {"vcpu": 8, "memory": 64, "hourly_price": 0.504},
    "Standard_E16s_v3": {"vcpu": 16, "memory": 128, "hourly_price": 1.008},
    "Standard_E32s_v3": {"vcpu": 32, "memory": 256, "hourly_price": 2.016},
    
    # F-Series (Compute Optimized)
    "Standard_F2s_v2": {"vcpu": 2, "memory": 4, "hourly_price": 0.085},
    "Standard_F4s_v2": {"vcpu": 4, "memory": 8, "hourly_price": 0.169},
    "Standard_F8s_v2": {"vcpu": 8, "memory": 16, "hourly_price": 0.338},
    "Standard_F16s_v2": {"vcpu": 16, "memory": 32, "hourly_price": 0.677},
    "Standard_F32s_v2": {"vcpu": 32, "memory": 64, "hourly_price": 1.354},
}

# Static pricing for Azure SQL Database
AZURE_SQL_PRICING = {
    # Basic tier
    "Basic": {"dtu": 5, "storage_gb": 2, "hourly_price": 0.0068},
    
    # Standard tier
    "S0": {"dtu": 10, "storage_gb": 250, "hourly_price": 0.0203},
    "S1": {"dtu": 20, "storage_gb": 250, "hourly_price": 0.0406},
    "S2": {"dtu": 50, "storage_gb": 250, "hourly_price": 0.102},
    "S3": {"dtu": 100, "storage_gb": 250, "hourly_price": 0.203},
    "S4": {"dtu": 200, "storage_gb": 250, "hourly_price": 0.406},
    
    # Premium tier
    "P1": {"dtu": 125, "storage_gb": 500, "hourly_price": 0.625},
    "P2": {"dtu": 250, "storage_gb": 500, "hourly_price": 1.25},
    "P4": {"dtu": 500, "storage_gb": 500, "hourly_price": 2.50},
    "P6": {"dtu": 1000, "storage_gb": 500, "hourly_price": 5.00},
}

# Static pricing for Azure Storage
AZURE_STORAGE_PRICING = {
    # Blob Storage (per GB/month)
    "Hot": {"price_per_gb": 0.0184},
    "Cool": {"price_per_gb": 0.0100},
    "Archive": {"price_per_gb": 0.00099},
    
    # Premium Storage
    "Premium_LRS": {"price_per_gb": 0.15},
    "Premium_ZRS": {"price_per_gb": 0.188},
}

# Static pricing for Azure Kubernetes Service (AKS)
AZURE_AKS_PRICING = {
    # Control plane is free, only pay for nodes
    "control_plane": {"hourly_price": 0.0},
    # Node pool pricing uses VM pricing
}

# Static pricing for Azure App Service
AZURE_APP_SERVICE_PRICING = {
    # Free tier
    "F1": {"cores": 1, "memory": 1, "hourly_price": 0.0},
    
    # Basic tier
    "B1": {"cores": 1, "memory": 1.75, "hourly_price": 0.075},
    "B2": {"cores": 2, "memory": 3.5, "hourly_price": 0.15},
    "B3": {"cores": 4, "memory": 7, "hourly_price": 0.30},
    
    # Standard tier
    "S1": {"cores": 1, "memory": 1.75, "hourly_price": 0.10},
    "S2": {"cores": 2, "memory": 3.5, "hourly_price": 0.20},
    "S3": {"cores": 4, "memory": 7, "hourly_price": 0.40},
    
    # Premium tier
    "P1v2": {"cores": 1, "memory": 3.5, "hourly_price": 0.146},
    "P2v2": {"cores": 2, "memory": 7, "hourly_price": 0.292},
    "P3v2": {"cores": 4, "memory": 14, "hourly_price": 0.584},
}

# Static pricing for Azure Functions
AZURE_FUNCTIONS_PRICING = {
    # Consumption plan
    "consumption": {
        "execution_price_per_million": 0.20,
        "gb_seconds_price": 0.000016
    },
    # Premium plan (EP1, EP2, EP3)
    "EP1": {"vcpu": 1, "memory": 3.5, "hourly_price": 0.169},
    "EP2": {"vcpu": 2, "memory": 7, "hourly_price": 0.338},
    "EP3": {"vcpu": 4, "memory": 14, "hourly_price": 0.676},
}

# Static pricing for Azure Load Balancer
AZURE_LB_PRICING = {
    "Basic": {"hourly_price": 0.0, "per_rule": 0.0},
    "Standard": {"hourly_price": 0.025, "per_rule": 0.005},
}

# Static pricing for Azure Redis Cache
AZURE_REDIS_PRICING = {
    "C0": {"memory_gb": 0.25, "hourly_price": 0.02},
    "C1": {"memory_gb": 1, "hourly_price": 0.08},
    "C2": {"memory_gb": 2.5, "hourly_price": 0.188},
    "C3": {"memory_gb": 6, "hourly_price": 0.375},
    "C4": {"memory_gb": 13, "hourly_price": 0.75},
    "C5": {"memory_gb": 26, "hourly_price": 1.50},
    "C6": {"memory_gb": 53, "hourly_price": 3.0},
}

# Static pricing for Azure Cosmos DB
AZURE_COSMOS_PRICING = {
    # Provisioned throughput (per 100 RU/s per hour)
    "provisioned_throughput_100ru": 0.008,
    # Storage (per GB/month)
    "storage_per_gb": 0.25,
}


def get_azure_vm_price(vm_size: str, region: str = "eastus") -> Dict[str, Any]:
    """
    Get Azure VM pricing.
    
    Args:
        vm_size: VM size (e.g., Standard_D2s_v3)
        region: Azure region
        
    Returns:
        Pricing information dict
    """
    pricing = AZURE_VM_PRICING.get(vm_size)
    
    if not pricing:
        # Return fallback pricing
        return {
            "hourly_price": 0.10,
            "monthly_price": 73.0,
            "vcpu": 2,
            "memory": 4,
            "confidence": "low"
        }
    
    return {
        "hourly_price": pricing["hourly_price"],
        "monthly_price": pricing["hourly_price"] * 730,
        "vcpu": pricing["vcpu"],
        "memory": pricing["memory"],
        "confidence": "high"
    }


def get_azure_sql_price(tier: str, region: str = "eastus") -> Dict[str, Any]:
    """
    Get Azure SQL Database pricing.
    
    Args:
        tier: SQL tier (e.g., S1, P1)
        region: Azure region
        
    Returns:
        Pricing information dict
    """
    pricing = AZURE_SQL_PRICING.get(tier)
    
    if not pricing:
        return {
            "hourly_price": 0.05,
            "monthly_price": 36.5,
            "dtu": 20,
            "storage_gb": 250,
            "confidence": "low"
        }
    
    return {
        "hourly_price": pricing["hourly_price"],
        "monthly_price": pricing["hourly_price"] * 730,
        "dtu": pricing["dtu"],
        "storage_gb": pricing["storage_gb"],
        "confidence": "high"
    }


def get_azure_storage_price(storage_class: str = "Hot", size_gb: float = 100) -> Dict[str, Any]:
    """
    Get Azure Storage pricing.
    
    Args:
        storage_class: Storage class (Hot, Cool, Archive)
        size_gb: Storage size in GB
        
    Returns:
        Pricing information dict
    """
    pricing = AZURE_STORAGE_PRICING.get(storage_class, AZURE_STORAGE_PRICING["Hot"])
    
    monthly_price = pricing["price_per_gb"] * size_gb
    
    return {
        "price_per_gb": pricing["price_per_gb"],
        "monthly_price": monthly_price,
        "storage_class": storage_class,
        "size_gb": size_gb,
        "confidence": "high"
    }


def get_azure_aks_price(node_size: str, node_count: int = 3, region: str = "eastus") -> Dict[str, Any]:
    """
    Get Azure Kubernetes Service pricing.
    
    Args:
        node_size: VM size for nodes
        node_count: Number of nodes
        region: Azure region
        
    Returns:
        Pricing information dict
    """
    # Control plane is free, calculate node costs
    node_pricing = get_azure_vm_price(node_size, region)
    
    return {
        "control_plane_hourly": 0.0,
        "node_hourly": node_pricing["hourly_price"],
        "total_hourly": node_pricing["hourly_price"] * node_count,
        "total_monthly": node_pricing["monthly_price"] * node_count,
        "node_count": node_count,
        "node_size": node_size,
        "confidence": node_pricing["confidence"]
    }


def get_azure_app_service_price(sku: str, region: str = "eastus") -> Dict[str, Any]:
    """
    Get Azure App Service pricing.
    
    Args:
        sku: App Service SKU (e.g., S1, P1v2)
        region: Azure region
        
    Returns:
        Pricing information dict
    """
    pricing = AZURE_APP_SERVICE_PRICING.get(sku)
    
    if not pricing:
        return {
            "hourly_price": 0.10,
            "monthly_price": 73.0,
            "cores": 1,
            "memory": 1.75,
            "confidence": "low"
        }
    
    return {
        "hourly_price": pricing["hourly_price"],
        "monthly_price": pricing["hourly_price"] * 730,
        "cores": pricing["cores"],
        "memory": pricing["memory"],
        "confidence": "high"
    }


def get_azure_functions_price(plan: str = "consumption") -> Dict[str, Any]:
    """
    Get Azure Functions pricing.
    
    Args:
        plan: Plan type (consumption, EP1, EP2, EP3)
        
    Returns:
        Pricing information dict
    """
    if plan == "consumption":
        return {
            "plan": "consumption",
            "execution_price_per_million": AZURE_FUNCTIONS_PRICING["consumption"]["execution_price_per_million"],
            "gb_seconds_price": AZURE_FUNCTIONS_PRICING["consumption"]["gb_seconds_price"],
            "monthly_estimate": 5.0,  # Estimate for low usage
            "confidence": "medium"
        }
    
    pricing = AZURE_FUNCTIONS_PRICING.get(plan)
    if not pricing:
        return {
            "hourly_price": 0.15,
            "monthly_price": 109.5,
            "confidence": "low"
        }
    
    return {
        "hourly_price": pricing["hourly_price"],
        "monthly_price": pricing["hourly_price"] * 730,
        "vcpu": pricing["vcpu"],
        "memory": pricing["memory"],
        "confidence": "high"
    }


def get_azure_load_balancer_price(sku: str = "Standard") -> Dict[str, Any]:
    """
    Get Azure Load Balancer pricing.
    
    Args:
        sku: Load balancer SKU (Basic, Standard)
        
    Returns:
        Pricing information dict
    """
    pricing = AZURE_LB_PRICING.get(sku, AZURE_LB_PRICING["Standard"])
    
    # Estimate with 5 rules
    estimated_monthly = (pricing["hourly_price"] + pricing["per_rule"] * 5) * 730
    
    return {
        "hourly_price": pricing["hourly_price"],
        "per_rule_hourly": pricing["per_rule"],
        "monthly_estimate": estimated_monthly,
        "sku": sku,
        "confidence": "high"
    }


def get_azure_redis_price(sku: str = "C1") -> Dict[str, Any]:
    """
    Get Azure Redis Cache pricing.
    
    Args:
        sku: Redis SKU (C0-C6, P1-P5)
        
    Returns:
        Pricing information dict
    """
    pricing = AZURE_REDIS_PRICING.get(sku)
    
    if not pricing:
        return {
            "hourly_price": 0.10,
            "monthly_price": 73.0,
            "memory_gb": 1,
            "confidence": "low"
        }
    
    return {
        "hourly_price": pricing["hourly_price"],
        "monthly_price": pricing["hourly_price"] * 730,
        "memory_gb": pricing["memory_gb"],
        "sku": sku,
        "confidence": "high"
    }


def get_azure_cosmos_price(throughput_ru: int = 400, storage_gb: float = 10) -> Dict[str, Any]:
    """
    Get Azure Cosmos DB pricing.
    
    Args:
        throughput_ru: Provisioned throughput in RU/s
        storage_gb: Storage size in GB
        
    Returns:
        Pricing information dict
    """
    # Calculate throughput cost (per 100 RU/s)
    throughput_cost = (throughput_ru / 100) * AZURE_COSMOS_PRICING["provisioned_throughput_100ru"] * 730
    
    # Calculate storage cost
    storage_cost = storage_gb * AZURE_COSMOS_PRICING["storage_per_gb"]
    
    return {
        "throughput_monthly": throughput_cost,
        "storage_monthly": storage_cost,
        "total_monthly": throughput_cost + storage_cost,
        "throughput_ru": throughput_ru,
        "storage_gb": storage_gb,
        "confidence": "high"
    }


def get_azure_price_catalog(region: str = "eastus") -> List[Dict[str, Any]]:
    """
    Get complete Azure pricing catalog.
    
    Args:
        region: Azure region
        
    Returns:
        List of pricing items
    """
    catalog = []
    
    # Virtual Machines
    for vm_size, pricing in AZURE_VM_PRICING.items():
        catalog.append({
            "service": "Virtual Machines",
            "sku": vm_size,
            "region": region,
            "vcpu": pricing["vcpu"],
            "memory": pricing["memory"],
            "hourly_price": pricing["hourly_price"],
            "monthly_price": pricing["hourly_price"] * 730
        })
    
    # SQL Database
    for tier, pricing in AZURE_SQL_PRICING.items():
        catalog.append({
            "service": "SQL Database",
            "sku": tier,
            "region": region,
            "dtu": pricing["dtu"],
            "storage_gb": pricing["storage_gb"],
            "hourly_price": pricing["hourly_price"],
            "monthly_price": pricing["hourly_price"] * 730
        })
    
    # Storage
    for storage_class, pricing in AZURE_STORAGE_PRICING.items():
        catalog.append({
            "service": "Blob Storage",
            "sku": storage_class,
            "region": region,
            "price_per_gb": pricing["price_per_gb"],
            "monthly_100gb": pricing["price_per_gb"] * 100
        })
    
    # App Service
    for sku, pricing in AZURE_APP_SERVICE_PRICING.items():
        if pricing["hourly_price"] > 0:  # Skip free tier
            catalog.append({
                "service": "App Service",
                "sku": sku,
                "region": region,
                "cores": pricing["cores"],
                "memory": pricing["memory"],
                "hourly_price": pricing["hourly_price"],
                "monthly_price": pricing["hourly_price"] * 730
            })
    
    return catalog


def is_azure_resource(resource_type: str) -> bool:
    """
    Check if a resource type is Azure.
    
    Args:
        resource_type: Resource type string
        
    Returns:
        True if Azure resource
    """
    azure_prefixes = [
        "azure_virtual_machine",
        "azure_sql_database",
        "azure_storage_account",
        "azure_kubernetes_cluster",
        "azure_app_service",
        "azure_function_app",
        "azure_load_balancer",
        "azure_redis_cache",
        "azure_cosmosdb_account",
        "azurerm_",  # Terraform azurerm provider
    ]
    
    return any(resource_type.startswith(prefix) for prefix in azure_prefixes)

