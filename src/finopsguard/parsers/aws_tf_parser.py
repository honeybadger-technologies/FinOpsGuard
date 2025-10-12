"""AWS Terraform resource parser."""

import re
from typing import Optional
from ..types.models import CanonicalResource


def parse_aws_resource(
    resource_type: str,
    resource_name: str,
    resource_body: str,
    default_region: str,
    count: int
) -> Optional[CanonicalResource]:
    """
    Parse AWS Terraform resource into canonical format.
    
    Args:
        resource_type: AWS resource type (e.g., 'aws_instance')
        resource_name: Terraform resource name
        resource_body: Resource body (HCL content)
        default_region: Default AWS region
        count: Resource count from count parameter
        
    Returns:
        CanonicalResource if parsed, None if not supported
    """
    # Extract region from resource body (override default)
    region_match = re.search(r'region\s*=\s*"([a-z0-9-]+)"', resource_body, re.IGNORECASE)
    region = region_match.group(1) if region_match else default_region
    
    # AWS EC2 Instances
    if resource_type == 'aws_instance':
        inst_match = re.search(r'instance_type\s*=\s*"([a-z0-9.\-]+)"', resource_body, re.IGNORECASE)
        instance_type = inst_match.group(1) if inst_match else 't3.micro'
        
        return CanonicalResource(
            id=f"{resource_name}-{instance_type}-{region}",
            type='aws_instance',
            name=resource_name,
            region=region,
            size=instance_type,
            count=count,
            tags={},
            metadata={}
        )
    
    # AWS Load Balancers
    if resource_type in ['aws_lb', 'aws_alb', 'aws_lb_listener']:
        return CanonicalResource(
            id=f"{resource_name}-lb-{region}",
            type='aws_load_balancer',
            name=resource_name,
            region=region,
            size='application',
            count=count,
            tags={},
            metadata={}
        )
    
    # AWS Auto Scaling Groups
    if resource_type == 'aws_autoscaling_group':
        desired = re.search(r'desired_capacity\s*=\s*([0-9]+)', resource_body, re.IGNORECASE)
        launch_type = re.search(r'instance_type\s*=\s*"([a-z0-9.\-]+)"', resource_body, re.IGNORECASE)
        capacity = int(desired.group(1)) if desired else 1
        instance_type = launch_type.group(1) if launch_type else 't3.micro'
        
        return CanonicalResource(
            id=f"{resource_name}-asg-{region}",
            type='aws_autoscaling_group',
            name=resource_name,
            region=region,
            size=instance_type,
            count=capacity,
            tags={},
            metadata={}
        )
    
    # AWS EKS Cluster
    if resource_type == 'aws_eks_cluster':
        return CanonicalResource(
            id=f"{resource_name}-eks-{region}",
            type='aws_eks_cluster',
            name=resource_name,
            region=region,
            size='cluster',
            count=count,
            tags={},
            metadata={}
        )
    
    # AWS RDS Database Instance
    if resource_type == 'aws_db_instance':
        cl_match = re.search(r'instance_class\s*=\s*"([a-z0-9.\-]+)"', resource_body, re.IGNORECASE)
        instance_class = cl_match.group(1) if cl_match else 'db.t3.micro'
        
        return CanonicalResource(
            id=f"{resource_name}-rds-{region}",
            type='aws_db_instance',
            name=resource_name,
            region=region,
            size=instance_class,
            count=count,
            tags={},
            metadata={}
        )
    
    # AWS Redshift Cluster
    if resource_type == 'aws_redshift_cluster':
        node_type_match = re.search(r'node_type\s*=\s*"([a-z0-9.\-]+)"', resource_body, re.IGNORECASE)
        node_type = node_type_match.group(1) if node_type_match else 'dc2.large'
        num_nodes_match = re.search(r'number_of_nodes\s*=\s*([0-9]+)', resource_body, re.IGNORECASE)
        num_nodes = int(num_nodes_match.group(1)) if num_nodes_match else 1
        
        return CanonicalResource(
            id=f"{resource_name}-redshift-{region}",
            type='aws_redshift_cluster',
            name=resource_name,
            region=region,
            size=node_type,
            count=num_nodes,
            tags={},
            metadata={}
        )
    
    # AWS OpenSearch Domain
    if resource_type == 'aws_opensearch_domain':
        inst_match = re.search(r'instance_type\s*=\s*"([a-z0-9.\-]+)"', resource_body, re.IGNORECASE)
        instance_type = inst_match.group(1) if inst_match else 't3.small.search'
        inst_count_match = re.search(r'instance_count\s*=\s*([0-9]+)', resource_body, re.IGNORECASE)
        instance_count = int(inst_count_match.group(1)) if inst_count_match else 1
        
        return CanonicalResource(
            id=f"{resource_name}-opensearch-{region}",
            type='aws_opensearch_domain',
            name=resource_name,
            region=region,
            size=instance_type,
            count=instance_count,
            tags={},
            metadata={}
        )
    
    # AWS ElastiCache Cluster
    if resource_type == 'aws_elasticache_cluster':
        node_type_match = re.search(r'node_type\s*=\s*"([a-z0-9.\-]+)"', resource_body, re.IGNORECASE)
        node_type = node_type_match.group(1) if node_type_match else 'cache.t3.micro'
        num_nodes_match = re.search(r'num_cache_nodes\s*=\s*([0-9]+)', resource_body, re.IGNORECASE)
        num_nodes = int(num_nodes_match.group(1)) if num_nodes_match else 1
        
        return CanonicalResource(
            id=f"{resource_name}-elasticache-{region}",
            type='aws_elasticache_cluster',
            name=resource_name,
            region=region,
            size=node_type,
            count=num_nodes,
            tags={},
            metadata={}
        )
    
    # AWS ElastiCache Replication Group
    if resource_type == 'aws_elasticache_replication_group':
        node_type_match = re.search(r'node_type\s*=\s*"([a-z0-9.\-]+)"', resource_body, re.IGNORECASE)
        node_type = node_type_match.group(1) if node_type_match else 'cache.t3.micro'
        num_cache_clusters_match = re.search(r'number_cache_clusters\s*=\s*([0-9]+)', resource_body, re.IGNORECASE)
        num_cache_clusters = int(num_cache_clusters_match.group(1)) if num_cache_clusters_match else 2
        
        return CanonicalResource(
            id=f"{resource_name}-elasticache-rg-{region}",
            type='aws_elasticache_replication_group',
            name=resource_name,
            region=region,
            size=node_type,
            count=num_cache_clusters,
            tags={},
            metadata={}
        )
    
    # AWS DynamoDB Table
    if resource_type == 'aws_dynamodb_table':
        billing_match = re.search(r'billing_mode\s*=\s*"([A-Z_]+)"', resource_body, re.IGNORECASE)
        billing = billing_match.group(1).upper() if billing_match else 'PAY_PER_REQUEST'
        read_match = re.search(r'read_capacity\s*=\s*([0-9]+)', resource_body, re.IGNORECASE)
        write_match = re.search(r'write_capacity\s*=\s*([0-9]+)', resource_body, re.IGNORECASE)
        
        return CanonicalResource(
            id=f"{resource_name}-dynamodb-{region}",
            type='aws_dynamodb_table',
            name=resource_name,
            region=region,
            size=billing,
            count=1,
            tags={},
            metadata={
                'read_capacity': int(read_match.group(1)) if read_match else None,
                'write_capacity': int(write_match.group(1)) if write_match else None,
            }
        )
    
    # AWS Lambda Functions
    if resource_type == 'aws_lambda_function':
        memory_match = re.search(r'memory_size\s*=\s*([0-9]+)', resource_body, re.IGNORECASE)
        runtime_match = re.search(r'runtime\s*=\s*"([a-z0-9.\-]+)"', resource_body, re.IGNORECASE)
        
        memory = int(memory_match.group(1)) if memory_match else 128
        runtime = runtime_match.group(1) if runtime_match else 'python3.9'
        
        return CanonicalResource(
            id=f"{resource_name}-lambda-{region}",
            type='aws_lambda_function',
            name=resource_name,
            region=region,
            size=f"{memory}MB-{runtime}",
            count=count,
            tags={},
            metadata={'memory_mb': memory, 'runtime': runtime}
        )
    
    # AWS S3 Buckets
    if resource_type == 'aws_s3_bucket':
        storage_class_match = re.search(r'storage_class\s*=\s*"([A-Z_]+)"', resource_body, re.IGNORECASE)
        storage_class = storage_class_match.group(1).upper() if storage_class_match else 'STANDARD'
        
        return CanonicalResource(
            id=f"{resource_name}-s3-{region}",
            type='aws_s3_bucket',
            name=resource_name,
            region=region,
            size=storage_class,
            count=count,
            tags={},
            metadata={}
        )
    
    # AWS ECS Clusters
    if resource_type == 'aws_ecs_cluster':
        return CanonicalResource(
            id=f"{resource_name}-ecs-{region}",
            type='aws_ecs_cluster',
            name=resource_name,
            region=region,
            size='cluster',
            count=count,
            tags={},
            metadata={}
        )
    
    # AWS ECS Services
    if resource_type == 'aws_ecs_service':
        desired_count_match = re.search(r'desired_count\s*=\s*([0-9]+)', resource_body, re.IGNORECASE)
        launch_type_match = re.search(r'launch_type\s*=\s*"([A-Z]+)"', resource_body, re.IGNORECASE)
        
        desired_count = int(desired_count_match.group(1)) if desired_count_match else 1
        launch_type = launch_type_match.group(1).upper() if launch_type_match else 'EC2'
        
        return CanonicalResource(
            id=f"{resource_name}-ecs-service-{region}",
            type='aws_ecs_service',
            name=resource_name,
            region=region,
            size=f"{launch_type}-{desired_count}tasks",
            count=count,
            tags={},
            metadata={'desired_count': desired_count, 'launch_type': launch_type}
        )
    
    # AWS Fargate Task Definitions
    if resource_type == 'aws_ecs_task_definition':
        cpu_match = re.search(r'cpu\s*=\s*"?([0-9]+)"?', resource_body, re.IGNORECASE)
        memory_match = re.search(r'memory\s*=\s*"?([0-9]+)"?', resource_body, re.IGNORECASE)
        
        cpu = int(cpu_match.group(1)) if cpu_match else 256
        memory = int(memory_match.group(1)) if memory_match else 512
        
        return CanonicalResource(
            id=f"{resource_name}-fargate-{region}",
            type='aws_ecs_task_definition',
            name=resource_name,
            region=region,
            size=f"{cpu}cpu-{memory}mb",
            count=count,
            tags={},
            metadata={'cpu': cpu, 'memory': memory}
        )
    
    # AWS Kinesis Streams
    if resource_type == 'aws_kinesis_stream':
        shard_count_match = re.search(r'shard_count\s*=\s*([0-9]+)', resource_body, re.IGNORECASE)
        shard_count = int(shard_count_match.group(1)) if shard_count_match else 1
        
        return CanonicalResource(
            id=f"{resource_name}-kinesis-{region}",
            type='aws_kinesis_stream',
            name=resource_name,
            region=region,
            size=f"{shard_count}shards",
            count=count,
            tags={},
            metadata={'shard_count': shard_count}
        )
    
    # AWS SNS Topics
    if resource_type == 'aws_sns_topic':
        return CanonicalResource(
            id=f"{resource_name}-sns-{region}",
            type='aws_sns_topic',
            name=resource_name,
            region=region,
            size='topic',
            count=count,
            tags={},
            metadata={}
        )
    
    # AWS SQS Queues
    if resource_type == 'aws_sqs_queue':
        fifo_match = re.search(r'fifo_queue\s*=\s*true', resource_body, re.IGNORECASE)
        queue_type = 'fifo' if fifo_match else 'standard'
        
        return CanonicalResource(
            id=f"{resource_name}-sqs-{region}",
            type='aws_sqs_queue',
            name=resource_name,
            region=region,
            size=queue_type,
            count=count,
            tags={},
            metadata={}
        )
    
    # AWS Step Functions
    if resource_type == 'aws_sfn_state_machine':
        type_match = re.search(r'type\s*=\s*"([A-Z]+)"', resource_body, re.IGNORECASE)
        sfn_type = type_match.group(1).upper() if type_match else 'STANDARD'
        
        return CanonicalResource(
            id=f"{resource_name}-stepfunctions-{region}",
            type='aws_sfn_state_machine',
            name=resource_name,
            region=region,
            size=sfn_type,
            count=count,
            tags={},
            metadata={}
        )
    
    # AWS API Gateway
    if resource_type in ['aws_api_gateway_rest_api', 'aws_apigatewayv2_api']:
        protocol_match = re.search(r'protocol_type\s*=\s*"([A-Z]+)"', resource_body, re.IGNORECASE)
        protocol = protocol_match.group(1).upper() if protocol_match else 'HTTP'
        
        return CanonicalResource(
            id=f"{resource_name}-apigateway-{region}",
            type='aws_api_gateway',
            name=resource_name,
            region=region,
            size=protocol,
            count=count,
            tags={},
            metadata={}
        )
    
    # AWS CloudFront Distribution
    if resource_type == 'aws_cloudfront_distribution':
        price_class_match = re.search(r'price_class\s*=\s*"([A-Za-z0-9_]+)"', resource_body, re.IGNORECASE)
        price_class = price_class_match.group(1) if price_class_match else 'PriceClass_All'
        
        return CanonicalResource(
            id=f"{resource_name}-cloudfront-global",
            type='aws_cloudfront_distribution',
            name=resource_name,
            region='global',
            size=price_class,
            count=count,
            tags={},
            metadata={}
        )
    
    # AWS Neptune Cluster
    if resource_type == 'aws_neptune_cluster':
        instance_class_match = re.search(r'instance_class\s*=\s*"([a-z0-9.\-]+)"', resource_body, re.IGNORECASE)
        instance_class = instance_class_match.group(1) if instance_class_match else 'db.t3.medium'
        
        return CanonicalResource(
            id=f"{resource_name}-neptune-{region}",
            type='aws_neptune_cluster',
            name=resource_name,
            region=region,
            size=instance_class,
            count=count,
            tags={},
            metadata={}
        )
    
    # AWS DocumentDB Cluster
    if resource_type == 'aws_docdb_cluster':
        instance_class_match = re.search(r'instance_class\s*=\s*"([a-z0-9.\-]+)"', resource_body, re.IGNORECASE)
        instance_class = instance_class_match.group(1) if instance_class_match else 'db.t3.medium'
        
        return CanonicalResource(
            id=f"{resource_name}-documentdb-{region}",
            type='aws_docdb_cluster',
            name=resource_name,
            region=region,
            size=instance_class,
            count=count,
            tags={},
            metadata={}
        )
    
    # AWS MSK (Managed Kafka)
    if resource_type == 'aws_msk_cluster':
        instance_type_match = re.search(r'instance_type\s*=\s*"([a-z0-9.\-]+)"', resource_body, re.IGNORECASE)
        instance_type = instance_type_match.group(1) if instance_type_match else 'kafka.t3.small'
        
        return CanonicalResource(
            id=f"{resource_name}-msk-{region}",
            type='aws_msk_cluster',
            name=resource_name,
            region=region,
            size=instance_type,
            count=count,
            tags={},
            metadata={}
        )
    
    # AWS EMR Cluster
    if resource_type == 'aws_emr_cluster':
        master_type_match = re.search(r'master_instance_type\s*=\s*"([a-z0-9.\-]+)"', resource_body, re.IGNORECASE)
        master_type = master_type_match.group(1) if master_type_match else 'm5.xlarge'
        
        return CanonicalResource(
            id=f"{resource_name}-emr-{region}",
            type='aws_emr_cluster',
            name=resource_name,
            region=region,
            size=master_type,
            count=count,
            tags={},
            metadata={}
        )
    
    # AWS Glue Crawler/Job
    if resource_type in ['aws_glue_crawler', 'aws_glue_job']:
        return CanonicalResource(
            id=f"{resource_name}-glue-{region}",
            type='aws_glue',
            name=resource_name,
            region=region,
            size='job',
            count=count,
            tags={},
            metadata={}
        )
    
    # AWS Athena Workgroup
    if resource_type == 'aws_athena_workgroup':
        return CanonicalResource(
            id=f"{resource_name}-athena-{region}",
            type='aws_athena_workgroup',
            name=resource_name,
            region=region,
            size='workgroup',
            count=count,
            tags={},
            metadata={}
        )
    
    # AWS App Runner Service
    if resource_type == 'aws_apprunner_service':
        cpu_match = re.search(r'cpu\s*=\s*"?([0-9]+)"?', resource_body, re.IGNORECASE)
        memory_match = re.search(r'memory\s*=\s*"?([0-9]+)"?', resource_body, re.IGNORECASE)
        
        cpu = int(cpu_match.group(1)) if cpu_match else 1
        memory = int(memory_match.group(1)) if memory_match else 2
        
        return CanonicalResource(
            id=f"{resource_name}-apprunner-{region}",
            type='aws_apprunner_service',
            name=resource_name,
            region=region,
            size=f"{cpu}vCPU-{memory}GB",
            count=count,
            tags={},
            metadata={'cpu': cpu, 'memory': memory}
        )
    
    # Resource type not supported
    return None


def get_aws_default_region(hcl_text: str) -> str:
    """
    Extract default AWS region from provider block.
    
    Args:
        hcl_text: Full Terraform HCL content
        
    Returns:
        Default region or 'us-east-1'
    """
    aws_region_match = re.search(
        r'provider\s+"aws"\s*\{[^}]*region\s*=\s*"([a-z0-9-]+)"',
        hcl_text,
        re.IGNORECASE
    )
    return aws_region_match.group(1) if aws_region_match else 'us-east-1'

