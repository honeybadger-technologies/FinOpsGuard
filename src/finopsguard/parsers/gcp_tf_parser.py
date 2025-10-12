"""GCP Terraform resource parser."""

import re
from typing import Optional
from ..types.models import CanonicalResource


def parse_gcp_resource(
    resource_type: str,
    resource_name: str,
    resource_body: str,
    default_region: str,
    count: int
) -> Optional[CanonicalResource]:
    """
    Parse GCP Terraform resource into canonical format.
    
    Args:
        resource_type: GCP resource type (e.g., 'google_compute_instance')
        resource_name: Terraform resource name
        resource_body: Resource body (HCL content)
        default_region: Default GCP region
        count: Resource count from count parameter
        
    Returns:
        CanonicalResource if parsed, None if not supported
    """
    # Extract region/zone from resource body
    region_match = re.search(r'region\s*=\s*"([a-z0-9-]+)"', resource_body, re.IGNORECASE)
    location_match = re.search(r'location\s*=\s*"([a-z0-9-]+)"', resource_body, re.IGNORECASE)
    zone_match = re.search(r'zone\s*=\s*"([a-z0-9-]+)"', resource_body, re.IGNORECASE)
    
    if region_match:
        region = region_match.group(1)
    elif location_match:
        region = location_match.group(1)
    elif zone_match:
        # Extract region from zone (e.g., us-central1-a -> us-central1)
        zone = zone_match.group(1)
        region = '-'.join(zone.split('-')[:-1])
    else:
        region = default_region
    
    # GCP Compute Engine instances
    if resource_type == 'google_compute_instance':
        machine_type_match = re.search(r'machine_type\s*=\s*"([a-z0-9.\-]+)"', resource_body, re.IGNORECASE)
        machine_type = machine_type_match.group(1) if machine_type_match else 'e2-micro'
        
        return CanonicalResource(
            id=f"{resource_name}-gce-{region}",
            type='gcp_compute_instance',
            name=resource_name,
            region=region,
            size=machine_type,
            count=count,
            tags={},
            metadata={}
        )
    
    # GCP Cloud SQL Database Instance
    if resource_type == 'google_sql_database_instance':
        tier_match = re.search(r'tier\s*=\s*"([a-z0-9.\-]+)"', resource_body, re.IGNORECASE)
        tier = tier_match.group(1) if tier_match else 'db-f1-micro'
        
        return CanonicalResource(
            id=f"{resource_name}-sql-{region}",
            type='gcp_sql_database_instance',
            name=resource_name,
            region=region,
            size=tier,
            count=count,
            tags={},
            metadata={}
        )
    
    # GCP Cloud Storage Buckets
    if resource_type == 'google_storage_bucket':
        location_match = re.search(r'location\s*=\s*"([A-Z0-9\-]+)"', resource_body, re.IGNORECASE)
        storage_location = location_match.group(1) if location_match else 'US'
        storage_class_match = re.search(r'storage_class\s*=\s*"([A-Z_]+)"', resource_body, re.IGNORECASE)
        storage_class = storage_class_match.group(1).lower() if storage_class_match else 'standard'
        
        return CanonicalResource(
            id=f"{resource_name}-storage-{storage_location}",
            type='gcp_storage_bucket',
            name=resource_name,
            region=storage_location,
            size=storage_class,
            count=count,
            tags={},
            metadata={}
        )
    
    # GCP Kubernetes Engine (GKE) Clusters
    if resource_type == 'google_container_cluster':
        cluster_type = 'standard_cluster'
        
        # Check for autopilot
        if re.search(r'enable_autopilot\s*=\s*true', resource_body, re.IGNORECASE):
            cluster_type = 'autopilot_cluster'
        
        return CanonicalResource(
            id=f"{resource_name}-gke-{region}",
            type='gcp_container_cluster',
            name=resource_name,
            region=region,
            size=cluster_type,
            count=count,
            tags={},
            metadata={}
        )
    
    # GCP Cloud Run services
    if resource_type == 'google_cloud_run_service':
        location_match = re.search(r'location\s*=\s*"([a-z0-9\-]+)"', resource_body, re.IGNORECASE)
        service_location = location_match.group(1) if location_match else region
        
        return CanonicalResource(
            id=f"{resource_name}-run-{service_location}",
            type='gcp_cloud_run_service',
            name=resource_name,
            region=service_location,
            size='serverless',
            count=count,
            tags={},
            metadata={}
        )
    
    # GCP Cloud Functions
    if resource_type == 'google_cloudfunctions_function':
        runtime_match = re.search(r'runtime\s*=\s*"([a-z0-9.\-]+)"', resource_body, re.IGNORECASE)
        runtime = runtime_match.group(1) if runtime_match else 'python39'
        
        return CanonicalResource(
            id=f"{resource_name}-functions-{region}",
            type='gcp_cloudfunctions_function',
            name=resource_name,
            region=region,
            size=runtime,
            count=count,
            tags={},
            metadata={}
        )
    
    # GCP Load Balancers
    if resource_type in ['google_compute_global_forwarding_rule', 'google_compute_url_map',
                         'google_compute_target_http_proxy', 'google_compute_target_https_proxy']:
        lb_type = 'http_lb'
        if 'https' in resource_type:
            lb_type = 'ssl_lb'
        elif 'tcp' in resource_type:
            lb_type = 'tcp_lb'
        elif 'udp' in resource_type:
            lb_type = 'udp_lb'
        
        return CanonicalResource(
            id=f"{resource_name}-lb-{region}",
            type='gcp_load_balancer',
            name=resource_name,
            region=region,
            size=lb_type,
            count=count,
            tags={},
            metadata={}
        )
    
    # GCP BigQuery datasets
    if resource_type == 'google_bigquery_dataset':
        location_match = re.search(r'location\s*=\s*"([A-Z0-9\-]+)"', resource_body, re.IGNORECASE)
        dataset_location = location_match.group(1) if location_match else region
        
        return CanonicalResource(
            id=f"{resource_name}-bigquery-{dataset_location}",
            type='gcp_bigquery_dataset',
            name=resource_name,
            region=dataset_location,
            size='standard',
            count=count,
            tags={},
            metadata={}
        )
    
    # GCP Compute Engine Persistent Disks
    if resource_type == 'google_compute_disk':
        type_match = re.search(r'type\s*=\s*"([a-z0-9\-]+)"', resource_body, re.IGNORECASE)
        size_match = re.search(r'size\s*=\s*([0-9]+)', resource_body, re.IGNORECASE)
        
        disk_type = type_match.group(1) if type_match else 'pd-standard'
        size_gb = int(size_match.group(1)) if size_match else 100
        
        return CanonicalResource(
            id=f"{resource_name}-disk-{region}",
            type='gcp_compute_disk',
            name=resource_name,
            region=region,
            size=f"{disk_type}-{size_gb}GB",
            count=count,
            tags={},
            metadata={'size_gb': size_gb}
        )
    
    # GCP Filestore Instances
    if resource_type == 'google_filestore_instance':
        tier_match = re.search(r'tier\s*=\s*"([A-Z_]+)"', resource_body, re.IGNORECASE)
        capacity_match = re.search(r'capacity_gb\s*=\s*([0-9]+)', resource_body, re.IGNORECASE)
        
        tier = tier_match.group(1).upper() if tier_match else 'BASIC_HDD'
        capacity = int(capacity_match.group(1)) if capacity_match else 1024
        
        return CanonicalResource(
            id=f"{resource_name}-filestore-{region}",
            type='gcp_filestore_instance',
            name=resource_name,
            region=region,
            size=f"{tier}-{capacity}GB",
            count=count,
            tags={},
            metadata={'capacity_gb': capacity}
        )
    
    # GCP Cloud Pub/Sub Topics
    if resource_type == 'google_pubsub_topic':
        return CanonicalResource(
            id=f"{resource_name}-pubsub-{region}",
            type='gcp_pubsub_topic',
            name=resource_name,
            region=region,
            size='topic',
            count=count,
            tags={},
            metadata={}
        )
    
    # GCP Cloud Dataflow Jobs
    if resource_type == 'google_dataflow_job':
        machine_type_match = re.search(r'machine_type\s*=\s*"([a-z0-9\-]+)"', resource_body, re.IGNORECASE)
        max_workers_match = re.search(r'max_workers\s*=\s*([0-9]+)', resource_body, re.IGNORECASE)
        
        machine_type = machine_type_match.group(1) if machine_type_match else 'n1-standard-1'
        max_workers = int(max_workers_match.group(1)) if max_workers_match else 1
        
        return CanonicalResource(
            id=f"{resource_name}-dataflow-{region}",
            type='gcp_dataflow_job',
            name=resource_name,
            region=region,
            size=f"{machine_type}-{max_workers}workers",
            count=count,
            tags={},
            metadata={'max_workers': max_workers}
        )
    
    # GCP Cloud Composer (Airflow)
    if resource_type == 'google_composer_environment':
        node_count_match = re.search(r'node_count\s*=\s*([0-9]+)', resource_body, re.IGNORECASE)
        machine_type_match = re.search(r'machine_type\s*=\s*"([a-z0-9\-]+)"', resource_body, re.IGNORECASE)
        
        node_count = int(node_count_match.group(1)) if node_count_match else 3
        machine_type = machine_type_match.group(1) if machine_type_match else 'n1-standard-1'
        
        return CanonicalResource(
            id=f"{resource_name}-composer-{region}",
            type='gcp_composer_environment',
            name=resource_name,
            region=region,
            size=f"{machine_type}-{node_count}nodes",
            count=count,
            tags={},
            metadata={'node_count': node_count}
        )
    
    # GCP Cloud Dataproc Clusters
    if resource_type == 'google_dataproc_cluster':
        master_machine_match = re.search(
            r'master_config\s*\{[^}]*machine_type\s*=\s*"([a-z0-9\-]+)"',
            resource_body,
            re.IGNORECASE | re.DOTALL
        )
        worker_count_match = re.search(
            r'worker_config\s*\{[^}]*num_instances\s*=\s*([0-9]+)',
            resource_body,
            re.IGNORECASE | re.DOTALL
        )
        
        master_machine = master_machine_match.group(1) if master_machine_match else 'n1-standard-4'
        worker_count = int(worker_count_match.group(1)) if worker_count_match else 2
        
        return CanonicalResource(
            id=f"{resource_name}-dataproc-{region}",
            type='gcp_dataproc_cluster',
            name=resource_name,
            region=region,
            size=f"{master_machine}-{worker_count}workers",
            count=count,
            tags={},
            metadata={'worker_count': worker_count}
        )
    
    # GCP Cloud Spanner Instances
    if resource_type == 'google_spanner_instance':
        num_nodes_match = re.search(r'num_nodes\s*=\s*([0-9]+)', resource_body, re.IGNORECASE)
        processing_units_match = re.search(r'processing_units\s*=\s*([0-9]+)', resource_body, re.IGNORECASE)
        
        if processing_units_match:
            size = f"{processing_units_match.group(1)}PU"
        elif num_nodes_match:
            size = f"{num_nodes_match.group(1)}nodes"
        else:
            size = "1node"
        
        return CanonicalResource(
            id=f"{resource_name}-spanner-{region}",
            type='gcp_spanner_instance',
            name=resource_name,
            region=region,
            size=size,
            count=count,
            tags={},
            metadata={}
        )
    
    # GCP Vertex AI Workbench Instances
    if resource_type == 'google_notebooks_instance':
        machine_type_match = re.search(r'machine_type\s*=\s*"([a-z0-9\-]+)"', resource_body, re.IGNORECASE)
        machine_type = machine_type_match.group(1) if machine_type_match else 'n1-standard-4'
        
        return CanonicalResource(
            id=f"{resource_name}-notebooks-{region}",
            type='gcp_notebooks_instance',
            name=resource_name,
            region=region,
            size=machine_type,
            count=count,
            tags={},
            metadata={}
        )
    
    # GCP Cloud Memorystore (Redis)
    if resource_type == 'google_redis_instance':
        tier_match = re.search(r'tier\s*=\s*"([A-Z_]+)"', resource_body, re.IGNORECASE)
        memory_size_match = re.search(r'memory_size_gb\s*=\s*([0-9]+)', resource_body, re.IGNORECASE)
        
        tier = tier_match.group(1).upper() if tier_match else 'BASIC'
        memory = int(memory_size_match.group(1)) if memory_size_match else 1
        
        return CanonicalResource(
            id=f"{resource_name}-redis-{region}",
            type='gcp_redis_instance',
            name=resource_name,
            region=region,
            size=f"{tier}-{memory}GB",
            count=count,
            tags={},
            metadata={}
        )
    
    # GCP Cloud Armor Security Policies
    if resource_type == 'google_compute_security_policy':
        return CanonicalResource(
            id=f"{resource_name}-armor-global",
            type='gcp_cloud_armor',
            name=resource_name,
            region='global',
            size='security_policy',
            count=count,
            tags={},
            metadata={}
        )
    
    # Resource type not supported
    return None


def get_gcp_default_region(hcl_text: str) -> str:
    """
    Extract default GCP region from provider block.
    
    Args:
        hcl_text: Full Terraform HCL content
        
    Returns:
        Default region or 'us-central1'
    """
    gcp_region_match = re.search(
        r'provider\s+"google"\s*\{[^}]*region\s*=\s*"([a-z0-9-]+)"',
        hcl_text,
        re.IGNORECASE
    )
    return gcp_region_match.group(1) if gcp_region_match else 'us-central1'

