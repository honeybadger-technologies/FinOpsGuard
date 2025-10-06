"""
GCP Static Pricing Adapter

Provides static pricing data for Google Cloud Platform services.
This is a simplified pricing model for demonstration purposes.
In production, this would integrate with the GCP Pricing API.
"""

from typing import Dict, List, Optional


class GCPPricingData:
    """Static GCP pricing data for common services."""
    
    # Compute Engine pricing (us-central1, on-demand, per hour)
    COMPUTE_ENGINE_PRICING = {
        # General Purpose
        "e2-micro": {"cpu": 2, "memory": 1, "price": 0.006},
        "e2-small": {"cpu": 2, "memory": 2, "price": 0.012},
        "e2-medium": {"cpu": 2, "memory": 4, "price": 0.024},
        "e2-standard-2": {"cpu": 2, "memory": 8, "price": 0.067},
        "e2-standard-4": {"cpu": 4, "memory": 16, "price": 0.134},
        "e2-standard-8": {"cpu": 8, "memory": 32, "price": 0.268},
        "e2-standard-16": {"cpu": 16, "memory": 64, "price": 0.536},
        
        # Compute Optimized
        "c2-standard-4": {"cpu": 4, "memory": 16, "price": 0.208},
        "c2-standard-8": {"cpu": 8, "memory": 32, "price": 0.416},
        "c2-standard-16": {"cpu": 16, "memory": 64, "price": 0.832},
        "c2-standard-30": {"cpu": 30, "memory": 120, "price": 1.560},
        
        # Memory Optimized
        "m1-megamem-96": {"cpu": 96, "memory": 1433, "price": 6.303},
        "m1-ultramem-40": {"cpu": 40, "memory": 961, "price": 3.888},
        "m1-ultramem-80": {"cpu": 80, "memory": 1922, "price": 7.776},
        
        # GPU instances
        "n1-standard-4-gpu": {"cpu": 4, "memory": 15, "gpu": 1, "price": 1.18},
        "n1-standard-8-gpu": {"cpu": 8, "memory": 30, "gpu": 1, "price": 2.36},
    }
    
    # Cloud SQL pricing (us-central1, per hour)
    CLOUD_SQL_PRICING = {
        "db-f1-micro": {"cpu": 1, "memory": 0.6, "storage": 10, "price": 0.017},
        "db-g1-small": {"cpu": 1, "memory": 1.7, "storage": 10, "price": 0.025},
        "db-n1-standard-1": {"cpu": 1, "memory": 3.75, "storage": 10, "price": 0.041},
        "db-n1-standard-2": {"cpu": 2, "memory": 7.5, "storage": 10, "price": 0.082},
        "db-n1-standard-4": {"cpu": 4, "memory": 15, "storage": 10, "price": 0.164},
        "db-n1-standard-8": {"cpu": 8, "memory": 30, "storage": 10, "price": 0.328},
        "db-n1-standard-16": {"cpu": 16, "memory": 60, "storage": 10, "price": 0.656},
        "db-n1-standard-32": {"cpu": 32, "memory": 120, "storage": 10, "price": 1.312},
    }
    
    # Cloud Storage pricing (per GB per month)
    CLOUD_STORAGE_PRICING = {
        "standard": {"price": 0.020},
        "nearline": {"price": 0.010},
        "coldline": {"price": 0.004},
        "archive": {"price": 0.0012},
    }
    
    # Cloud Run pricing (per vCPU-hour and per GB-hour)
    CLOUD_RUN_PRICING = {
        "cpu_per_hour": 0.024,
        "memory_per_gb_hour": 0.0025,
        "requests_per_million": 0.40,
    }
    
    # Kubernetes Engine pricing (per cluster per hour)
    GKE_PRICING = {
        "standard_cluster": {"price": 0.10},  # Per cluster per hour
        "autopilot_cluster": {"price": 0.10},  # Per cluster per hour
    }
    
    # Cloud Functions pricing (per invocation and per GB-second)
    CLOUD_FUNCTIONS_PRICING = {
        "invocations_per_million": 0.40,
        "gb_seconds": 0.0000025,
    }
    
    # Cloud Load Balancer pricing (per hour)
    LOAD_BALANCER_PRICING = {
        "http_lb": {"price": 0.025},
        "tcp_lb": {"price": 0.025},
        "udp_lb": {"price": 0.025},
        "ssl_lb": {"price": 0.025},
    }


def get_gcp_instance_price(instance_type: str, region: str = "us-central1") -> Dict:
    """
    Get pricing for a GCP Compute Engine instance.
    
    Args:
        instance_type: The GCP instance type (e.g., 'e2-standard-4')
        region: The GCP region (default: us-central1)
        
    Returns:
        Dict with pricing information including price per hour, CPU, memory
    """
    pricing_data = GCPPricingData.COMPUTE_ENGINE_PRICING.get(instance_type)
    
    if not pricing_data:
        # Return default pricing for unknown instance types
        return {
            "price_per_hour": 0.10,  # Default fallback
            "cpu": 2,
            "memory": 8,
            "region": region,
            "confidence": "low",
            "note": f"Unknown instance type: {instance_type}"
        }
    
    return {
        "price_per_hour": pricing_data["price"],
        "cpu": pricing_data["cpu"],
        "memory": pricing_data["memory"],
        "region": region,
            "confidence": "high",
        "gpu": pricing_data.get("gpu", 0)
    }


def get_gcp_database_price(instance_type: str, region: str = "us-central1") -> Dict:
    """
    Get pricing for a GCP Cloud SQL instance.
    
    Args:
        instance_type: The Cloud SQL instance type (e.g., 'db-n1-standard-2')
        region: The GCP region (default: us-central1)
        
    Returns:
        Dict with pricing information
    """
    pricing_data = GCPPricingData.CLOUD_SQL_PRICING.get(instance_type)
    
    if not pricing_data:
        return {
            "price_per_hour": 0.05,  # Default fallback
            "cpu": 1,
            "memory": 4,
            "storage": 10,
            "region": region,
            "confidence": "low",
            "note": f"Unknown database instance type: {instance_type}"
        }
    
    return {
        "price_per_hour": pricing_data["price"],
        "cpu": pricing_data["cpu"],
        "memory": pricing_data["memory"],
        "storage": pricing_data["storage"],
        "region": region,
        "confidence": "high"
    }


def get_gcp_storage_price(storage_class: str = "standard") -> Dict:
    """
    Get pricing for GCP Cloud Storage.
    
    Args:
        storage_class: Storage class (standard, nearline, coldline, archive)
        
    Returns:
        Dict with pricing information per GB per month
    """
    pricing_data = GCPPricingData.CLOUD_STORAGE_PRICING.get(storage_class)
    
    if not pricing_data:
        return {
            "price_per_gb_month": 0.020,  # Default to standard
            "storage_class": "standard",
            "confidence": "low",
            "note": f"Unknown storage class: {storage_class}"
        }
    
    return {
        "price_per_gb_month": pricing_data["price"],
        "storage_class": storage_class,
        "confidence": "high"
    }


def get_gcp_load_balancer_price(lb_type: str = "http_lb") -> Dict:
    """
    Get pricing for GCP Load Balancer.
    
    Args:
        lb_type: Load balancer type (http_lb, tcp_lb, udp_lb, ssl_lb)
        
    Returns:
        Dict with pricing information per hour
    """
    pricing_data = GCPPricingData.LOAD_BALANCER_PRICING.get(lb_type)
    
    if not pricing_data:
        return {
            "price_per_hour": 0.025,  # Default fallback
            "lb_type": "http_lb",
            "confidence": "low",
            "note": f"Unknown load balancer type: {lb_type}"
        }
    
    return {
        "price_per_hour": pricing_data["price"],
        "lb_type": lb_type,
        "confidence": "high"
    }


def get_gcp_kubernetes_price(cluster_type: str = "standard_cluster") -> Dict:
    """
    Get pricing for GCP Kubernetes Engine.
    
    Args:
        cluster_type: Cluster type (standard_cluster, autopilot_cluster)
        
    Returns:
        Dict with pricing information per cluster per hour
    """
    pricing_data = GCPPricingData.GKE_PRICING.get(cluster_type)
    
    if not pricing_data:
        return {
            "price_per_cluster_hour": 0.10,  # Default fallback
            "cluster_type": "standard_cluster",
            "confidence": "low",
            "note": f"Unknown cluster type: {cluster_type}"
        }
    
    return {
        "price_per_cluster_hour": pricing_data["price"],
        "cluster_type": cluster_type,
        "confidence": "high"
    }


def get_gcp_cloud_run_price() -> Dict:
    """
    Get pricing for GCP Cloud Run.
    
    Returns:
        Dict with Cloud Run pricing information
    """
    return {
        "cpu_per_hour": GCPPricingData.CLOUD_RUN_PRICING["cpu_per_hour"],
        "memory_per_gb_hour": GCPPricingData.CLOUD_RUN_PRICING["memory_per_gb_hour"],
        "requests_per_million": GCPPricingData.CLOUD_RUN_PRICING["requests_per_million"],
        "confidence": "high"
    }


def get_gcp_cloud_functions_price() -> Dict:
    """
    Get pricing for GCP Cloud Functions.
    
    Returns:
        Dict with Cloud Functions pricing information
    """
    return {
        "invocations_per_million": GCPPricingData.CLOUD_FUNCTIONS_PRICING["invocations_per_million"],
        "gb_seconds": GCPPricingData.CLOUD_FUNCTIONS_PRICING["gb_seconds"],
        "confidence": "high"
    }


def get_gcp_price_catalog() -> Dict:
    """
    Get a comprehensive price catalog for GCP services.
    
    Returns:
        Dict containing pricing information for all supported GCP services
    """
    return {
        "provider": "gcp",
        "region": "us-central1",
        "services": {
            "compute_engine": {
                "instances": GCPPricingData.COMPUTE_ENGINE_PRICING,
                "description": "Compute Engine instance pricing (per hour)"
            },
            "cloud_sql": {
                "instances": GCPPricingData.CLOUD_SQL_PRICING,
                "description": "Cloud SQL instance pricing (per hour)"
            },
            "cloud_storage": {
                "storage_classes": GCPPricingData.CLOUD_STORAGE_PRICING,
                "description": "Cloud Storage pricing (per GB per month)"
            },
            "cloud_run": {
                "pricing": GCPPricingData.CLOUD_RUN_PRICING,
                "description": "Cloud Run pricing (per vCPU-hour and per GB-hour)"
            },
            "kubernetes_engine": {
                "clusters": GCPPricingData.GKE_PRICING,
                "description": "GKE cluster pricing (per cluster per hour)"
            },
            "cloud_functions": {
                "pricing": GCPPricingData.CLOUD_FUNCTIONS_PRICING,
                "description": "Cloud Functions pricing (per invocation and per GB-second)"
            },
            "load_balancer": {
                "types": GCPPricingData.LOAD_BALANCER_PRICING,
                "description": "Load Balancer pricing (per hour)"
            }
        },
        "last_updated": "2024-01-01T00:00:00Z",
        "confidence": "high"
    }


def is_gcp_resource(resource_type: str) -> bool:
    """
    Check if a resource type is a GCP resource.
    
    Args:
        resource_type: The resource type to check
        
    Returns:
        bool: True if it's a GCP resource, False otherwise
    """
    gcp_resources = {
        "google_compute_instance",
        "google_compute_disk",
        "google_compute_address",
        "google_compute_network",
        "google_compute_subnetwork",
        "google_compute_firewall",
        "google_compute_router",
        "google_sql_database_instance",
        "google_sql_database",
        "google_storage_bucket",
        "google_container_cluster",
        "google_container_node_pool",
        "google_cloud_run_service",
        "google_cloudfunctions_function",
        "google_compute_global_forwarding_rule",
        "google_compute_url_map",
        "google_compute_target_http_proxy",
        "google_compute_target_https_proxy",
        "google_compute_ssl_certificate",
        "google_compute_health_check",
        "google_compute_backend_service",
        "google_compute_instance_group",
        "google_compute_autoscaler",
        "google_redis_instance",
        "google_bigquery_dataset",
        "google_bigquery_table",
        "google_pubsub_topic",
        "google_pubsub_subscription",
        "google_cloud_scheduler_job",
        "google_monitoring_alert_policy",
        "google_logging_metric"
    }
    
    return resource_type in gcp_resources
