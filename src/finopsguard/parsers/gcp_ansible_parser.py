"""GCP Ansible module parser."""

import re
from typing import Optional, Dict, Any
from ..types.models import CanonicalResource


def parse_gcp_ansible_task(
    module_name: str,
    module_params: Dict[str, Any],
    task_name: str,
    task_vars: Dict[str, Any],
    default_region: str
) -> Optional[CanonicalResource]:
    """
    Parse GCP Ansible task into canonical format.
    
    Args:
        module_name: Ansible module name (e.g., 'gcp_compute_instance')
        module_params: Module parameters
        task_name: Task name
        task_vars: Task variables
        default_region: Default GCP region
        
    Returns:
        CanonicalResource if parsed, None if not supported
    """
    # Extract region from module params or use default
    region = module_params.get('region', default_region)
    if not region:
        region = 'us-central1'  # Fallback
    
    # GCP Compute Engine Instances
    if module_name == 'gcp_compute_instance':
        machine_type = module_params.get('machine_type', 'n1-standard-1')
        
        return CanonicalResource(
            id=f"{task_name}-{machine_type}-{region}",
            type='google_compute_instance',
            name=task_name,
            region=region,
            size=machine_type,
            count=1,
            tags=module_params.get('labels', {}),
            metadata={
                'module': 'gcp_compute_instance',
                'zone': module_params.get('zone'),
                'image': module_params.get('image'),
                'network': module_params.get('network'),
                'subnetwork': module_params.get('subnetwork'),
                'disk_size_gb': module_params.get('disk_size_gb'),
                'disk_type': module_params.get('disk_type')
            }
        )
    
    # GCP Compute Engine Instance Groups
    elif module_name == 'gcp_compute_instance_group':
        machine_type = module_params.get('template', {}).get('machine_type', 'n1-standard-1')
        size = module_params.get('size', 1)
        
        return CanonicalResource(
            id=f"{task_name}-ig-{machine_type}-{region}",
            type='google_compute_instance_group',
            name=task_name,
            region=region,
            size=machine_type,
            count=size,
            tags=module_params.get('labels', {}),
            metadata={
                'module': 'gcp_compute_instance_group',
                'zone': module_params.get('zone'),
                'network': module_params.get('network')
            }
        )
    
    # GCP Kubernetes Engine Clusters
    elif module_name == 'gcp_container_cluster':
        node_count = module_params.get('initial_node_count', 1)
        machine_type = module_params.get('node_config', {}).get('machine_type', 'e2-medium')
        
        return CanonicalResource(
            id=f"{task_name}-gke-{region}",
            type='google_container_cluster',
            name=task_name,
            region=region,
            size=machine_type,
            count=node_count,
            tags=module_params.get('labels', {}),
            metadata={
                'module': 'gcp_container_cluster',
                'zone': module_params.get('zone'),
                'cluster_version': module_params.get('cluster_version'),
                'num_nodes': node_count,
                'machine_type': machine_type,
                'disk_size_gb': module_params.get('node_config', {}).get('disk_size_gb'),
                'disk_type': module_params.get('node_config', {}).get('disk_type')
            }
        )
    
    # GCP Cloud Functions
    elif module_name == 'gcp_cloudfunctions_function':
        memory = module_params.get('memory', 256)
        runtime = module_params.get('runtime', 'python39')
        
        return CanonicalResource(
            id=f"{task_name}-cf-{memory}MB-{runtime}-{region}",
            type='google_cloudfunctions_function',
            name=task_name,
            region=region,
            size=f"{memory}MB-{runtime}",
            count=1,
            tags=module_params.get('labels', {}),
            metadata={
                'module': 'gcp_cloudfunctions_function',
                'source_archive_url': module_params.get('source_archive_url'),
                'entry_point': module_params.get('entry_point'),
                'timeout': module_params.get('timeout', 60),
                'available_memory_mb': memory,
                'runtime': runtime,
                'trigger': module_params.get('trigger', {})
            }
        )
    
    # GCP Cloud Run Services
    elif module_name == 'gcp_run_service':
        cpu = module_params.get('template', {}).get('spec', {}).get('container_concurrency', 1000)
        memory = module_params.get('template', {}).get('spec', {}).get('containers', [{}])[0].get('resources', {}).get('limits', {}).get('memory', '512Mi')
        
        return CanonicalResource(
            id=f"{task_name}-run-{region}",
            type='google_cloud_run_service',
            name=task_name,
            region=region,
            size=f"{cpu}-{memory}",
            count=1,
            tags=module_params.get('labels', {}),
            metadata={
                'module': 'gcp_run_service',
                'image': module_params.get('template', {}).get('spec', {}).get('containers', [{}])[0].get('image'),
                'port': module_params.get('template', {}).get('spec', {}).get('containers', [{}])[0].get('ports', [{}])[0].get('container_port')
            }
        )
    
    # GCP App Engine Applications
    elif module_name == 'gcp_appengine_application':
        return CanonicalResource(
            id=f"{task_name}-appengine-{region}",
            type='google_app_engine_application',
            name=task_name,
            region=region,
            size='standard',
            count=1,
            tags=module_params.get('labels', {}),
            metadata={
                'module': 'gcp_appengine_application',
                'location_id': module_params.get('location_id')
            }
        )
    
    # GCP Cloud SQL Instances
    elif module_name == 'gcp_sql_instance':
        instance_type = module_params.get('settings', {}).get('tier', 'db-n1-standard-1')
        
        return CanonicalResource(
            id=f"{task_name}-sql-{instance_type}-{region}",
            type='google_sql_database_instance',
            name=task_name,
            region=region,
            size=instance_type,
            count=1,
            tags=module_params.get('labels', {}),
            metadata={
                'module': 'gcp_sql_instance',
                'database_version': module_params.get('database_version'),
                'disk_size': module_params.get('settings', {}).get('disk_size'),
                'disk_type': module_params.get('settings', {}).get('disk_type'),
                'backup_configuration': module_params.get('settings', {}).get('backup_configuration')
            }
        )
    
    # GCP BigQuery Datasets
    elif module_name == 'gcp_bigquery_dataset':
        return CanonicalResource(
            id=f"{task_name}-bigquery-{region}",
            type='google_bigquery_dataset',
            name=task_name,
            region=region,
            size='standard',
            count=1,
            tags=module_params.get('labels', {}),
            metadata={
                'module': 'gcp_bigquery_dataset',
                'description': module_params.get('description'),
                'default_table_expiration_ms': module_params.get('default_table_expiration_ms')
            }
        )
    
    # GCP Cloud Storage Buckets
    elif module_name == 'gcp_storage_bucket':
        return CanonicalResource(
            id=f"{task_name}-storage-{region}",
            type='google_storage_bucket',
            name=task_name,
            region=region,
            size='standard',
            count=1,
            tags=module_params.get('labels', {}),
            metadata={
                'module': 'gcp_storage_bucket',
                'storage_class': module_params.get('storage_class', 'STANDARD'),
                'versioning': module_params.get('versioning'),
                'lifecycle': module_params.get('lifecycle')
            }
        )
    
    # GCP Cloud Pub/Sub Topics
    elif module_name == 'gcp_pubsub_topic':
        return CanonicalResource(
            id=f"{task_name}-pubsub-{region}",
            type='google_pubsub_topic',
            name=task_name,
            region=region,
            size='standard',
            count=1,
            tags=module_params.get('labels', {}),
            metadata={
                'module': 'gcp_pubsub_topic',
                'message_retention_duration': module_params.get('message_retention_duration')
            }
        )
    
    # GCP Cloud Pub/Sub Subscriptions
    elif module_name == 'gcp_pubsub_subscription':
        return CanonicalResource(
            id=f"{task_name}-pubsub-sub-{region}",
            type='google_pubsub_subscription',
            name=task_name,
            region=region,
            size='standard',
            count=1,
            tags=module_params.get('labels', {}),
            metadata={
                'module': 'gcp_pubsub_subscription',
                'topic': module_params.get('topic'),
                'ack_deadline_seconds': module_params.get('ack_deadline_seconds')
            }
        )
    
    # GCP Load Balancers
    elif module_name == 'gcp_compute_url_map':
        return CanonicalResource(
            id=f"{task_name}-lb-{region}",
            type='google_compute_url_map',
            name=task_name,
            region=region,
            size='standard',
            count=1,
            tags=module_params.get('labels', {}),
            metadata={
                'module': 'gcp_compute_url_map',
                'default_service': module_params.get('default_service'),
                'description': module_params.get('description')
            }
        )
    
    # GCP Cloud Endpoints
    elif module_name == 'gcp_endpoints_service':
        return CanonicalResource(
            id=f"{task_name}-endpoints-{region}",
            type='google_endpoints_service',
            name=task_name,
            region=region,
            size='standard',
            count=1,
            tags=module_params.get('labels', {}),
            metadata={
                'module': 'gcp_endpoints_service',
                'service_name': module_params.get('service_name'),
                'openapi_spec': module_params.get('openapi_spec')
            }
        )
    
    # GCP Cloud Scheduler Jobs
    elif module_name == 'gcp_cloudscheduler_job':
        return CanonicalResource(
            id=f"{task_name}-scheduler-{region}",
            type='google_cloud_scheduler_job',
            name=task_name,
            region=region,
            size='standard',
            count=1,
            tags=module_params.get('labels', {}),
            metadata={
                'module': 'gcp_cloudscheduler_job',
                'schedule': module_params.get('schedule'),
                'time_zone': module_params.get('time_zone'),
                'http_target': module_params.get('http_target', {}),
                'pubsub_target': module_params.get('pubsub_target', {})
            }
        )
    
    # GCP Cloud Tasks Queues
    elif module_name == 'gcp_cloudtasks_queue':
        return CanonicalResource(
            id=f"{task_name}-tasks-{region}",
            type='google_cloud_tasks_queue',
            name=task_name,
            region=region,
            size='standard',
            count=1,
            tags=module_params.get('labels', {}),
            metadata={
                'module': 'gcp_cloudtasks_queue',
                'rate_limits': module_params.get('rate_limits', {}),
                'retry_config': module_params.get('retry_config', {})
            }
        )
    
    # GCP Cloud Memorystore Redis
    elif module_name == 'gcp_redis_instance':
        memory_size = module_params.get('memory_size_gb', 1)
        tier = module_params.get('tier', 'STANDARD_HA')
        
        return CanonicalResource(
            id=f"{task_name}-redis-{memory_size}GB-{tier}-{region}",
            type='google_redis_instance',
            name=task_name,
            region=region,
            size=f"{memory_size}GB-{tier}",
            count=1,
            tags=module_params.get('labels', {}),
            metadata={
                'module': 'gcp_redis_instance',
                'display_name': module_params.get('display_name'),
                'redis_version': module_params.get('redis_version'),
                'authorized_network': module_params.get('authorized_network')
            }
        )
    
    # GCP Cloud Spanner Instances
    elif module_name == 'gcp_spanner_instance':
        node_count = module_params.get('config', {}).get('num_nodes', 1)
        
        return CanonicalResource(
            id=f"{task_name}-spanner-{node_count}nodes-{region}",
            type='google_spanner_instance',
            name=task_name,
            region=region,
            size=f"{node_count}-nodes",
            count=1,
            tags=module_params.get('labels', {}),
            metadata={
                'module': 'gcp_spanner_instance',
                'display_name': module_params.get('display_name'),
                'config': module_params.get('config', {}),
                'processing_units': module_params.get('config', {}).get('processing_units')
            }
        )
    
    return None


def get_gcp_default_region(content: str) -> str:
    """
    Extract default GCP region from Ansible playbook content.
    
    Args:
        content: Ansible playbook YAML content
        
    Returns:
        Default GCP region or empty string if not found
    """
    # Look for GCP region in variables
    region_patterns = [
        r'gcp_region:\s*["\']?([a-z0-9-]+)["\']?',
        r'region:\s*["\']?([a-z0-9-]+)["\']?',
        r'GCP_REGION:\s*["\']?([a-z0-9-]+)["\']?',
        r'zone:\s*["\']?([a-z0-9-]+)["\']?'
    ]
    
    for pattern in region_patterns:
        match = re.search(pattern, content, re.IGNORECASE)
        if match:
            region = match.group(1)
            # Convert zone to region if needed
            if region.count('-') == 2:  # zone format like us-central1-a
                region = '-'.join(region.split('-')[:-1])
            return region
    
    return ''
