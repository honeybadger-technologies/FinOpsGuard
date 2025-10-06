"""
Minimal heuristic Terraform parser for MVP
Extracts aws instance type, region, count from a simple HCL string
"""

import re
from typing import List
from ..types.models import CanonicalResource, CanonicalResourceModel


def parse_terraform_to_crmodel(hcl_text: str) -> CanonicalResourceModel:
    """Parse Terraform HCL text into canonical resource model"""
    resources: List[CanonicalResource] = []

    # Extract default region from provider block
    region_match_global = re.search(r'provider\s+"aws"\s*\{[^}]*region\s*=\s*"([a-z0-9-]+)"', hcl_text, re.IGNORECASE)
    default_region = region_match_global.group(1) if region_match_global else 'us-east-1'

    # Extract resource blocks
    resource_regex = re.compile(r'resource\s+"([^"]+)"\s+"([^"]+)"\s*\{([\s\S]*?)\}', re.MULTILINE)
    
    for match in resource_regex.finditer(hcl_text):
        r_type, r_name, body = match.groups()
        name = r_name
        
        # Extract region from resource block
        region_match = re.search(r'region\s*=\s*"([a-z0-9-]+)"', body, re.IGNORECASE)
        region = region_match.group(1) if region_match else default_region
        
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

    return CanonicalResourceModel(resources=resources)
