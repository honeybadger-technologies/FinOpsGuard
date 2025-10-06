"""
Minimal heuristic Terraform parser for MVP
Extracts AWS and GCP instance types, regions, counts from HCL strings
"""

import re
from typing import List
from ..types.models import CanonicalResource, CanonicalResourceModel


def parse_terraform_to_crmodel(hcl_text: str) -> CanonicalResourceModel:
    """Parse Terraform HCL text into canonical resource model"""
    resources: List[CanonicalResource] = []

    # Extract default region from AWS provider block
    aws_region_match = re.search(r'provider\s+"aws"\s*\{[^}]*region\s*=\s*"([a-z0-9-]+)"', hcl_text, re.IGNORECASE)
    aws_default_region = aws_region_match.group(1) if aws_region_match else 'us-east-1'
    
    # Extract default region from GCP provider block
    gcp_region_match = re.search(r'provider\s+"google"\s*\{[^}]*region\s*=\s*"([a-z0-9-]+)"', hcl_text, re.IGNORECASE)
    gcp_default_region = gcp_region_match.group(1) if gcp_region_match else 'us-central1'

    # Extract resource blocks
    resource_regex = re.compile(r'resource\s+"([^"]+)"\s+"([^"]+)"\s*\{([\s\S]*?)\}', re.MULTILINE)
    
    for match in resource_regex.finditer(hcl_text):
        r_type, r_name, body = match.groups()
        name = r_name
        
        # Determine provider and default region
        if r_type.startswith('google_'):
            default_region = gcp_default_region
        else:
            default_region = aws_default_region
        
        # Extract region from resource block
        region_match = re.search(r'region\s*=\s*"([a-z0-9-]+)"', body, re.IGNORECASE)
        zone_match = re.search(r'zone\s*=\s*"([a-z0-9-]+)"', body, re.IGNORECASE)
        
        if region_match:
            region = region_match.group(1)
        elif zone_match:
            # Extract region from zone (e.g., us-central1-a -> us-central1)
            zone = zone_match.group(1)
            region = '-'.join(zone.split('-')[:-1])
        else:
            region = default_region
        
        # Extract count
        count_match = re.search(r'count\s*=\s*([0-9]+)', body, re.IGNORECASE)
        count = int(count_match.group(1)) if count_match else 1

        # Handle different resource types
        if r_type == 'aws_instance':
            inst_match = re.search(r'instance_type\s*=\s*"([a-z0-9.\-]+)"', body, re.IGNORECASE)
            instance_type = inst_match.group(1) if inst_match else 't3.micro'
            
            resources.append(CanonicalResource(
                id=f"{name}-{instance_type}-{region}",
                type='aws_instance',
                name=name,
                region=region,
                size=instance_type,
                count=count,
                tags={},
                metadata={}
            ))
            continue

        if r_type in ['aws_lb', 'aws_alb', 'aws_lb_listener']:
            resources.append(CanonicalResource(
                id=f"{name}-lb-{region}",
                type='aws_lb',
                name=name,
                region=region,
                size='application',
                count=count,
                tags={},
                metadata={}
            ))
            continue

        if r_type == 'aws_autoscaling_group':
            desired = re.search(r'desired_capacity\s*=\s*([0-9]+)', body, re.IGNORECASE)
            launch_type = re.search(r'instance_type\s*=\s*"([a-z0-9.\-]+)"', body, re.IGNORECASE)
            instance_type = launch_type.group(1) if launch_type else 't3.medium'
            desired_count = int(desired.group(1)) if desired else count
            
            resources.append(CanonicalResource(
                id=f"{name}-asg-{region}",
                type='aws_asg',
                name=name,
                region=region,
                size=instance_type,
                count=desired_count,
                tags={},
                metadata={}
            ))
            continue

        if r_type == 'aws_eks_cluster':
            resources.append(CanonicalResource(
                id=f"{name}-eks-{region}",
                type='aws_eks_cluster',
                name=name,
                region=region,
                size='control_plane',
                count=count,
                tags={},
                metadata={}
            ))
            continue

        # RDS instance
        if r_type == 'aws_db_instance':
            cl_match = re.search(r'instance_class\s*=\s*"([a-z0-9.\-]+)"', body, re.IGNORECASE)
            instance_class = cl_match.group(1) if cl_match else 'db.t3.micro'
            
            resources.append(CanonicalResource(
                id=f"{name}-rds-{region}",
                type='aws_rds_instance',
                name=name,
                region=region,
                size=instance_class,
                count=count,
                tags={},
                metadata={}
            ))
            continue

        # Redshift cluster
        if r_type == 'aws_redshift_cluster':
            node_type_match = re.search(r'node_type\s*=\s*"([a-z0-9.\-]+)"', body, re.IGNORECASE)
            node_type = node_type_match.group(1) if node_type_match else 'dc2.large'
            
            nodes_match = re.search(r'number_of_nodes\s*=\s*([0-9]+)', body, re.IGNORECASE)
            num_nodes = int(nodes_match.group(1)) if nodes_match else 1
            
            resources.append(CanonicalResource(
                id=f"{name}-redshift-{region}",
                type='aws_redshift_cluster',
                name=name,
                region=region,
                size=node_type,
                count=num_nodes,
                tags={},
                metadata={}
            ))
            continue

        # OpenSearch domain
        if r_type == 'aws_opensearch_domain':
            inst_match = re.search(r'instance_type\s*=\s*"([a-z0-9.\-]+)"', body, re.IGNORECASE)
            instance_type = inst_match.group(1) if inst_match else 't3.small.search'
            
            inst_count_match = re.search(r'instance_count\s*=\s*([0-9]+)', body, re.IGNORECASE)
            replicas = int(inst_count_match.group(1)) if inst_count_match else 1
            
            resources.append(CanonicalResource(
                id=f"{name}-os-{region}",
                type='aws_opensearch',
                name=name,
                region=region,
                size=instance_type,
                count=replicas,
                tags={},
                metadata={}
            ))
            continue

        # ElastiCache cluster
        if r_type == 'aws_elasticache_cluster':
            node_type_match = re.search(r'node_type\s*=\s*"([a-z0-9.\-]+)"', body, re.IGNORECASE)
            node_type = node_type_match.group(1) if node_type_match else 'cache.t3.micro'
            
            nodes_match = re.search(r'num_cache_nodes\s*=\s*([0-9]+)', body, re.IGNORECASE)
            num_nodes = int(nodes_match.group(1)) if nodes_match else 1
            
            resources.append(CanonicalResource(
                id=f"{name}-elasticache-{region}",
                type='aws_elasticache',
                name=name,
                region=region,
                size=node_type,
                count=num_nodes,
                tags={},
                metadata={}
            ))
            continue

        # ElastiCache replication group
        if r_type == 'aws_elasticache_replication_group':
            node_type_match = re.search(r'node_type\s*=\s*"([a-z0-9.\-]+)"', body, re.IGNORECASE)
            node_type = node_type_match.group(1) if node_type_match else 'cache.t3.micro'
            
            replicas_match = re.search(r'replicas_per_node_group\s*=\s*([0-9]+)', body, re.IGNORECASE)
            shard_count_match = re.search(r'num_node_groups\s*=\s*([0-9]+)', body, re.IGNORECASE)
            
            count_nodes = (int(replicas_match.group(1)) if replicas_match else 0) + 1
            total = (int(shard_count_match.group(1)) if shard_count_match else 1) * count_nodes
            
            resources.append(CanonicalResource(
                id=f"{name}-elasticache-rg-{region}",
                type='aws_elasticache',
                name=name,
                region=region,
                size=node_type,
                count=total,
                tags={},
                metadata={}
            ))
            continue

        # DynamoDB table
        if r_type == 'aws_dynamodb_table':
            billing_match = re.search(r'billing_mode\s*=\s*"([A-Z_]+)"', body, re.IGNORECASE)
            billing = billing_match.group(1).upper() if billing_match else 'PAY_PER_REQUEST'
            
            read_match = re.search(r'read_capacity\s*=\s*([0-9]+)', body, re.IGNORECASE)
            write_match = re.search(r'write_capacity\s*=\s*([0-9]+)', body, re.IGNORECASE)
            
            resources.append(CanonicalResource(
                id=f"{name}-dynamodb-{region}",
                type='aws_dynamodb_table',
                name=name,
                region=region,
                size=billing,
                count=1,
                tags={},
                metadata={
                    'read_capacity': int(read_match.group(1)) if read_match else None,
                    'write_capacity': int(write_match.group(1)) if write_match else None,
                }
            ))
            continue

        # GCP Compute Engine instances
        if r_type == 'google_compute_instance':
            machine_type_match = re.search(r'machine_type\s*=\s*"([a-z0-9.\-]+)"', body, re.IGNORECASE)
            machine_type = machine_type_match.group(1) if machine_type_match else 'e2-micro'
            
            resources.append(CanonicalResource(
                id=f"{name}-gce-{region}",
                type='gcp_compute_instance',
                name=name,
                region=region,
                size=machine_type,
                count=count,
                tags={},
                metadata={}
            ))
            continue

        # GCP Cloud SQL instances
        if r_type == 'google_sql_database_instance':
            # Look for tier in settings block first
            # Since the body extraction stops at the first closing brace,
            # we need to look for tier directly in the settings block
            settings_match = re.search(r'settings\s*\{([\s\S]*)', body, re.MULTILINE)
            tier = 'db-f1-micro'  # default
            
            if settings_match:
                settings_body = settings_match.group(1)
                tier_match = re.search(r'tier\s*=\s*"([a-z0-9.\-_]+)"', settings_body, re.IGNORECASE)
                if tier_match:
                    tier = tier_match.group(1)
            
            resources.append(CanonicalResource(
                id=f"{name}-sql-{region}",
                type='gcp_sql_database_instance',
                name=name,
                region=region,
                size=tier,
                count=count,
                tags={},
                metadata={}
            ))
            continue

        # GCP Cloud Storage buckets
        if r_type == 'google_storage_bucket':
            location_match = re.search(r'location\s*=\s*"([A-Z0-9\-]+)"', body, re.IGNORECASE)
            storage_location = location_match.group(1) if location_match else 'US'
            
            resources.append(CanonicalResource(
                id=f"{name}-storage-{storage_location}",
                type='gcp_storage_bucket',
                name=name,
                region=storage_location,
                size='standard',
                count=count,
                tags={},
                metadata={}
            ))
            continue

        # GCP Kubernetes Engine clusters
        if r_type == 'google_container_cluster':
            cluster_type = 'standard_cluster'  # Default to standard
            
            # Check for autopilot
            if re.search(r'enable_autopilot\s*=\s*true', body, re.IGNORECASE):
                cluster_type = 'autopilot_cluster'
            
            resources.append(CanonicalResource(
                id=f"{name}-gke-{region}",
                type='gcp_container_cluster',
                name=name,
                region=region,
                size=cluster_type,
                count=count,
                tags={},
                metadata={}
            ))
            continue

        # GCP Cloud Run services
        if r_type == 'google_cloud_run_service':
            # Cloud Run services can have location parameter
            location_match = re.search(r'location\s*=\s*"([a-z0-9\-]+)"', body, re.IGNORECASE)
            service_location = location_match.group(1) if location_match else region
            
            resources.append(CanonicalResource(
                id=f"{name}-run-{service_location}",
                type='gcp_cloud_run_service',
                name=name,
                region=service_location,
                size='serverless',
                count=count,
                tags={},
                metadata={}
            ))
            continue

        # GCP Cloud Functions
        if r_type == 'google_cloudfunctions_function':
            runtime_match = re.search(r'runtime\s*=\s*"([a-z0-9.\-]+)"', body, re.IGNORECASE)
            runtime = runtime_match.group(1) if runtime_match else 'python39'
            
            resources.append(CanonicalResource(
                id=f"{name}-functions-{region}",
                type='gcp_cloudfunctions_function',
                name=name,
                region=region,
                size=runtime,
                count=count,
                tags={},
                metadata={}
            ))
            continue

        # GCP Load Balancers
        if r_type in ['google_compute_global_forwarding_rule', 'google_compute_url_map', 'google_compute_target_http_proxy', 'google_compute_target_https_proxy']:
            lb_type = 'http_lb'
            if 'https' in r_type:
                lb_type = 'ssl_lb'
            elif 'tcp' in r_type:
                lb_type = 'tcp_lb'
            elif 'udp' in r_type:
                lb_type = 'udp_lb'
            
            resources.append(CanonicalResource(
                id=f"{name}-lb-{region}",
                type='gcp_load_balancer',
                name=name,
                region=region,
                size=lb_type,
                count=count,
                tags={},
                metadata={}
            ))
            continue

        # GCP Redis instances
        if r_type == 'google_redis_instance':
            tier_match = re.search(r'tier\s*=\s*"([A-Z_]+)"', body, re.IGNORECASE)
            memory_size_match = re.search(r'memory_size_gb\s*=\s*([0-9]+)', body, re.IGNORECASE)
            
            tier = tier_match.group(1).upper() if tier_match else 'BASIC'
            memory = int(memory_size_match.group(1)) if memory_size_match else 1
            
            resources.append(CanonicalResource(
                id=f"{name}-redis-{region}",
                type='gcp_redis_instance',
                name=name,
                region=region,
                size=f"{tier}-{memory}GB",
                count=count,
                tags={},
                metadata={}
            ))
            continue

        # GCP BigQuery datasets
        if r_type == 'google_bigquery_dataset':
            # BigQuery datasets can have location parameter
            location_match = re.search(r'location\s*=\s*"([A-Z0-9\-]+)"', body, re.IGNORECASE)
            dataset_location = location_match.group(1) if location_match else region
            
            resources.append(CanonicalResource(
                id=f"{name}-bigquery-{dataset_location}",
                type='gcp_bigquery_dataset',
                name=name,
                region=dataset_location,
                size='standard',
                count=count,
                tags={},
                metadata={}
            ))
            continue

    return CanonicalResourceModel(resources=resources)
