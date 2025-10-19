"""AWS Ansible module parser."""

import re
from typing import Optional, Dict, Any
from ..types.models import CanonicalResource


def parse_aws_ansible_task(
    module_name: str,
    module_params: Dict[str, Any],
    task_name: str,
    task_vars: Dict[str, Any],
    default_region: str
) -> Optional[CanonicalResource]:
    """
    Parse AWS Ansible task into canonical format.
    
    Args:
        module_name: Ansible module name (e.g., 'ec2_instance')
        module_params: Module parameters
        task_name: Task name
        task_vars: Task variables
        default_region: Default AWS region
        
    Returns:
        CanonicalResource if parsed, None if not supported
    """
    # Extract region from module params or use default
    region = module_params.get('region', default_region)
    if not region:
        region = 'us-east-1'  # Fallback
    
    # AWS EC2 Instances
    if module_name == 'ec2_instance':
        instance_type = module_params.get('instance_type', 't3.micro')
        
        return CanonicalResource(
            id=f"{task_name}-{instance_type}-{region}",
            type='aws_instance',
            name=task_name,
            region=region,
            size=instance_type,
            count=1,
            tags=module_params.get('tags', {}),
            metadata={
                'module': 'ec2_instance',
                'image_id': module_params.get('image_id'),
                'key_name': module_params.get('key_name'),
                'security_groups': module_params.get('security_groups', []),
                'subnet_id': module_params.get('subnet_id')
            }
        )
    
    # AWS Auto Scaling Groups
    elif module_name == 'ec2_asg':
        instance_type = module_params.get('launch_template', {}).get('instance_type', 't3.micro')
        desired_capacity = module_params.get('desired_capacity', 1)
        
        return CanonicalResource(
            id=f"{task_name}-asg-{instance_type}-{region}",
            type='aws_autoscaling_group',
            name=task_name,
            region=region,
            size=instance_type,
            count=desired_capacity,
            tags=module_params.get('tags', {}),
            metadata={
                'module': 'ec2_asg',
                'min_size': module_params.get('min_size', 1),
                'max_size': module_params.get('max_size', 10),
                'desired_capacity': desired_capacity
            }
        )
    
    # AWS EKS Clusters
    elif module_name == 'eks_cluster':
        return CanonicalResource(
            id=f"{task_name}-eks-{region}",
            type='aws_eks_cluster',
            name=task_name,
            region=region,
            size='standard',  # EKS control plane
            count=1,
            tags=module_params.get('tags', {}),
            metadata={
                'module': 'eks_cluster',
                'version': module_params.get('version'),
                'role_arn': module_params.get('role_arn'),
                'subnets': module_params.get('subnets', [])
            }
        )
    
    # AWS Lambda Functions
    elif module_name == 'lambda_function':
        memory_size = module_params.get('memory_size', 128)
        runtime = module_params.get('runtime', 'python3.9')
        
        return CanonicalResource(
            id=f"{task_name}-lambda-{memory_size}MB-{runtime}-{region}",
            type='aws_lambda_function',
            name=task_name,
            region=region,
            size=f"{memory_size}MB-{runtime}",
            count=1,
            tags=module_params.get('tags', {}),
            metadata={
                'module': 'lambda_function',
                'handler': module_params.get('handler'),
                'timeout': module_params.get('timeout', 3),
                'environment': module_params.get('environment', {})
            }
        )
    
    # AWS ECS Clusters
    elif module_name == 'ecs_cluster':
        return CanonicalResource(
            id=f"{task_name}-ecs-{region}",
            type='aws_ecs_cluster',
            name=task_name,
            region=region,
            size='standard',
            count=1,
            tags=module_params.get('tags', {}),
            metadata={
                'module': 'ecs_cluster',
                'capacity_providers': module_params.get('capacity_providers', []),
                'default_capacity_provider_strategy': module_params.get('default_capacity_provider_strategy', [])
            }
        )
    
    # AWS ECS Services
    elif module_name == 'ecs_service':
        desired_count = module_params.get('desired_count', 1)
        
        return CanonicalResource(
            id=f"{task_name}-ecs-service-{region}",
            type='aws_ecs_service',
            name=task_name,
            region=region,
            size='standard',
            count=desired_count,
            tags=module_params.get('tags', {}),
            metadata={
                'module': 'ecs_service',
                'cluster': module_params.get('cluster'),
                'task_definition': module_params.get('task_definition'),
                'launch_type': module_params.get('launch_type', 'EC2')
            }
        )
    
    # AWS RDS Instances
    elif module_name in ['rds_instance', 'rds']:
        instance_class = module_params.get('instance_class', 'db.t3.micro')
        
        return CanonicalResource(
            id=f"{task_name}-rds-{instance_class}-{region}",
            type='aws_db_instance',
            name=task_name,
            region=region,
            size=instance_class,
            count=1,
            tags=module_params.get('tags', {}),
            metadata={
                'module': 'rds_instance',
                'engine': module_params.get('engine'),
                'engine_version': module_params.get('engine_version'),
                'allocated_storage': module_params.get('allocated_storage'),
                'storage_type': module_params.get('storage_type')
            }
        )
    
    # AWS DynamoDB Tables
    elif module_name == 'dynamodb_table':
        return CanonicalResource(
            id=f"{task_name}-dynamodb-{region}",
            type='aws_dynamodb_table',
            name=task_name,
            region=region,
            size='standard',
            count=1,
            tags=module_params.get('tags', {}),
            metadata={
                'module': 'dynamodb_table',
                'billing_mode': module_params.get('billing_mode', 'PAY_PER_REQUEST'),
                'read_capacity': module_params.get('read_capacity'),
                'write_capacity': module_params.get('write_capacity')
            }
        )
    
    # AWS S3 Buckets
    elif module_name in ['s3_bucket', 'aws_s3']:
        return CanonicalResource(
            id=f"{task_name}-s3-{region}",
            type='aws_s3_bucket',
            name=task_name,
            region=region,
            size='standard',
            count=1,
            tags=module_params.get('tags', {}),
            metadata={
                'module': 's3_bucket',
                'versioning': module_params.get('versioning'),
                'encryption': module_params.get('encryption'),
                'lifecycle': module_params.get('lifecycle')
            }
        )
    
    # AWS Load Balancers
    elif module_name == 'elb_application_lb':
        lb_type = module_params.get('load_balancer_type', 'application')
        
        return CanonicalResource(
            id=f"{task_name}-alb-{region}",
            type='aws_lb',
            name=task_name,
            region=region,
            size=lb_type,
            count=1,
            tags=module_params.get('tags', {}),
            metadata={
                'module': 'elb_application_lb',
                'subnets': module_params.get('subnets', []),
                'security_groups': module_params.get('security_groups', []),
                'scheme': module_params.get('scheme', 'internet-facing')
            }
        )
    
    # AWS SNS Topics
    elif module_name == 'sns_topic':
        return CanonicalResource(
            id=f"{task_name}-sns-{region}",
            type='aws_sns_topic',
            name=task_name,
            region=region,
            size='standard',
            count=1,
            tags=module_params.get('tags', {}),
            metadata={
                'module': 'sns_topic',
                'display_name': module_params.get('display_name'),
                'delivery_policy': module_params.get('delivery_policy')
            }
        )
    
    # AWS SQS Queues
    elif module_name == 'sqs_queue':
        return CanonicalResource(
            id=f"{task_name}-sqs-{region}",
            type='aws_sqs_queue',
            name=task_name,
            region=region,
            size='standard',
            count=1,
            tags=module_params.get('tags', {}),
            metadata={
                'module': 'sqs_queue',
                'delay_seconds': module_params.get('delay_seconds'),
                'max_message_size': module_params.get('max_message_size'),
                'message_retention_seconds': module_params.get('message_retention_seconds'),
                'fifo_queue': module_params.get('fifo_queue', False)
            }
        )
    
    # AWS API Gateway
    elif module_name == 'api_gateway':
        return CanonicalResource(
            id=f"{task_name}-apigw-{region}",
            type='aws_api_gateway_rest_api',
            name=task_name,
            region=region,
            size='standard',
            count=1,
            tags=module_params.get('tags', {}),
            metadata={
                'module': 'api_gateway',
                'description': module_params.get('description'),
                'endpoint_configuration': module_params.get('endpoint_configuration')
            }
        )
    
    # AWS CloudFront Distributions
    elif module_name == 'cloudfront_distribution':
        return CanonicalResource(
            id=f"{task_name}-cloudfront-{region}",
            type='aws_cloudfront_distribution',
            name=task_name,
            region=region,
            size='standard',
            count=1,
            tags=module_params.get('tags', {}),
            metadata={
                'module': 'cloudfront_distribution',
                'enabled': module_params.get('enabled', True),
                'price_class': module_params.get('price_class'),
                'origins': module_params.get('origins', [])
            }
        )
    
    # AWS ElastiCache Redis
    elif module_name == 'elasticache_cluster':
        node_type = module_params.get('node_type', 'cache.t3.micro')
        num_cache_nodes = module_params.get('num_cache_nodes', 1)
        
        return CanonicalResource(
            id=f"{task_name}-elasticache-{node_type}-{region}",
            type='aws_elasticache_cluster',
            name=task_name,
            region=region,
            size=node_type,
            count=num_cache_nodes,
            tags=module_params.get('tags', {}),
            metadata={
                'module': 'elasticache_cluster',
                'engine': module_params.get('engine', 'redis'),
                'engine_version': module_params.get('engine_version'),
                'parameter_group_name': module_params.get('parameter_group_name')
            }
        )
    
    # AWS Kinesis Streams
    elif module_name == 'kinesis_stream':
        shard_count = module_params.get('shard_count', 1)
        
        return CanonicalResource(
            id=f"{task_name}-kinesis-{shard_count}shards-{region}",
            type='aws_kinesis_stream',
            name=task_name,
            region=region,
            size=f"{shard_count}-shards",
            count=1,
            tags=module_params.get('tags', {}),
            metadata={
                'module': 'kinesis_stream',
                'retention_period': module_params.get('retention_period'),
                'stream_mode': module_params.get('stream_mode')
            }
        )
    
    # AWS Step Functions
    elif module_name == 'stepfunctions_state_machine':
        return CanonicalResource(
            id=f"{task_name}-sfn-{region}",
            type='aws_sfn_state_machine',
            name=task_name,
            region=region,
            size='standard',
            count=1,
            tags=module_params.get('tags', {}),
            metadata={
                'module': 'stepfunctions_state_machine',
                'role_arn': module_params.get('role_arn'),
                'definition': module_params.get('definition'),
                'state_machine_type': module_params.get('state_machine_type', 'STANDARD')
            }
        )
    
    return None


def get_aws_default_region(content: str) -> str:
    """
    Extract default AWS region from Ansible playbook content.
    
    Args:
        content: Ansible playbook YAML content
        
    Returns:
        Default AWS region or empty string if not found
    """
    # Look for AWS region in variables
    region_patterns = [
        r'aws_region:\s*["\']?([a-z0-9-]+)["\']?',
        r'region:\s*["\']?([a-z0-9-]+)["\']?',
        r'AWS_DEFAULT_REGION:\s*["\']?([a-z0-9-]+)["\']?'
    ]
    
    for pattern in region_patterns:
        match = re.search(pattern, content, re.IGNORECASE)
        if match:
            return match.group(1)
    
    return ''
