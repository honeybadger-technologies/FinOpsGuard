# Ansible Parsing Guide

FinOpsGuard provides comprehensive Ansible YAML parsing for multi-cloud infrastructure cost analysis through a **modular parser architecture**. This document describes the supported resource types and parsing capabilities.

## Architecture

The parser uses a modular design with cloud-specific parsers:

```
src/finopsguard/parsers/
├── ansible.py              (210 lines)   ← Main orchestrator
├── aws_ansible_parser.py   (380 lines)   ← AWS-specific parsing
├── gcp_ansible_parser.py   (420 lines)   ← GCP-specific parsing
├── azure_ansible_parser.py (450 lines)   ← Azure-specific parsing
└── __init__.py             (28 lines)    ← Public exports
```

**Benefits:**
- ✅ **Maintainable**: Each cloud in separate file (~400 lines vs 1,500)
- ✅ **Extensible**: Add resources to specific parser only
- ✅ **Testable**: Unit test cloud parsers independently
- ✅ **Collaborative**: Multiple devs work on different clouds without conflicts

## Overview

The Ansible parser (`finopsguard.parsers.ansible`) converts Infrastructure-as-Code into a canonical resource model for cost estimation. It supports:

- **AWS**: 20+ module types
- **GCP**: 18+ module types  
- **Azure**: 20+ module types
- **Total**: 58+ module types across all major clouds

## Supported Resources

### AWS Resources (20 Types)

#### Compute (6)
1. **ec2_instance** - EC2 instances
   - Extracts: `instance_type`, `region`
   - Example: t3.micro, m5.large, c5.xlarge

2. **ec2_asg** - Auto Scaling Groups
   - Extracts: `instance_type`, `desired_capacity`
   - Calculates: instances × hourly cost

3. **eks_cluster** - Elastic Kubernetes Service
   - Extracts: `region`
   - Note: Control plane cost only (nodes are separate EC2)

4. **lambda_function** - Lambda Functions
   - Extracts: `memory_size`, `runtime`
   - Example: 512MB-python3.11

5. **ecs_cluster** - Elastic Container Service
   - Extracts: `region`
   - Note: Cluster management cost only

6. **ecs_service** - ECS Service definitions
   - Extracts: `desired_count`, `launch_type`

#### Database (4)
7. **rds_instance** - RDS instances
   - Extracts: `instance_class`, `engine`, `allocated_storage`

8. **dynamodb_table** - DynamoDB tables
   - Extracts: `billing_mode`, `read_capacity`, `write_capacity`

9. **elasticache_cluster** - ElastiCache Redis clusters
   - Extracts: `node_type`, `num_cache_nodes`

10. **elasticache_replication_group** - Redis replication groups
    - Extracts: `node_type`, `number_cache_clusters`

#### Storage (1)
11. **s3_bucket** - S3 buckets
    - Extracts: `region`, `versioning`, `encryption`

#### Networking (2)
12. **elb_application_lb** - Application Load Balancers
    - Extracts: `load_balancer_type`, `scheme`

13. **cloudfront_distribution** - CloudFront distributions
    - Extracts: `enabled`, `price_class`

#### Analytics & Data (3)
14. **kinesis_stream** - Kinesis data streams
    - Extracts: `shard_count`, `retention_period`

15. **sns_topic** - SNS notification topics
    - Extracts: `display_name`

16. **sqs_queue** - SQS message queues
    - Extracts: `delay_seconds`, `fifo_queue`

#### Integration (3)
17. **api_gateway** - API Gateway REST APIs
    - Extracts: `description`, `endpoint_configuration`

18. **stepfunctions_state_machine** - Step Functions workflows
    - Extracts: `role_arn`, `state_machine_type`

### GCP Resources (18 Types)

#### Compute (6)
1. **gcp_compute_instance** - Compute Engine instances
   - Extracts: `machine_type`, `zone`
   - Example: n1-standard-2, e2-medium

2. **gcp_compute_instance_group** - Instance groups
   - Extracts: `machine_type`, `size`

3. **gcp_container_cluster** - GKE clusters
   - Extracts: `cluster_version`, `node_config`

4. **gcp_cloudfunctions_function** - Cloud Functions
   - Extracts: `memory`, `runtime`
   - Example: 512MB-python39

5. **gcp_run_service** - Cloud Run services
   - Extracts: `cpu`, `memory` from template

6. **gcp_appengine_application** - App Engine applications
   - Extracts: `location_id`

#### Database (4)
7. **gcp_sql_instance** - Cloud SQL instances
   - Extracts: `database_version`, `settings.tier`

8. **gcp_bigquery_dataset** - BigQuery datasets
   - Extracts: `description`, `default_table_expiration_ms`

9. **gcp_redis_instance** - Memorystore Redis
   - Extracts: `memory_size_gb`, `tier`

10. **gcp_spanner_instance** - Cloud Spanner instances
    - Extracts: `config.num_nodes`

#### Storage (1)
11. **gcp_storage_bucket** - Cloud Storage buckets
    - Extracts: `storage_class`, `versioning`

#### Networking (2)
12. **gcp_compute_url_map** - Load balancers
    - Extracts: `default_service`

13. **gcp_endpoints_service** - Cloud Endpoints services
    - Extracts: `service_name`, `openapi_spec`

#### Analytics & Data (4)
14. **gcp_pubsub_topic** - Pub/Sub topics
    - Extracts: `message_retention_duration`

15. **gcp_pubsub_subscription** - Pub/Sub subscriptions
    - Extracts: `topic`, `ack_deadline_seconds`

16. **gcp_cloudscheduler_job** - Cloud Scheduler jobs
    - Extracts: `schedule`, `http_target`

17. **gcp_cloudtasks_queue** - Cloud Tasks queues
    - Extracts: `rate_limits`, `retry_config`

### Azure Resources (20 Types)

#### Compute (7)
1. **azure_rm_virtualmachine** - Virtual machines
   - Extracts: `vm_size`, `location`
   - Example: Standard_B2s, Standard_D2s_v3

2. **azure_rm_virtualmachinescaleset** - VM scale sets
   - Extracts: `vm_size`, `capacity`

3. **azure_rm_containerinstance** - Container instances
   - Extracts: `cpu_cores`, `memory_gb`

4. **azure_rm_aks** - AKS clusters
   - Extracts: `kubernetes_version`, `agent_pool_profiles`

5. **azure_rm_appserviceplan** - App Service plans
   - Extracts: `sku`, `kind`

6. **azure_rm_webapp** - App Services
   - Extracts: `app_service_plan`

7. **azure_rm_functionapp** - Function Apps
   - Extracts: `app_service_plan`, `storage_account`

#### Database (5)
8. **azure_rm_sqlserver** - SQL servers
   - Extracts: `version`

9. **azure_rm_sqldatabase** - SQL databases
   - Extracts: `service_objective`

10. **azure_rm_storageaccount** - Storage accounts
    - Extracts: `account_type`, `access_tier`

11. **azure_rm_rediscache** - Redis Cache
    - Extracts: `sku`, `capacity`

12. **azure_rm_cosmosdbaccount** - Cosmos DB accounts
    - Extracts: `offer_type`, `kind`

#### Messaging & Integration (4)
13. **azure_rm_servicebus** - Service Bus namespaces
    - Extracts: `sku`, `capacity`

14. **azure_rm_servicebustopic** - Service Bus topics
    - Extracts: `enable_partitioning`

15. **azure_rm_servicebusqueue** - Service Bus queues
    - Extracts: `enable_express`

16. **azure_rm_eventhub** - Event Hubs
    - Extracts: `message_retention`, `partition_count`

#### API Management & Integration (3)
17. **azure_rm_apimanagement** - API Management
    - Extracts: `sku`, `publisher_name`

18. **azure_rm_loadbalancer** - Load balancers
    - Extracts: `sku`, `frontend_ip_configurations`

19. **azure_rm_logicapp** - Logic Apps
    - Extracts: `app_service_plan`, `workflow_state`

## Usage Examples

### Basic AWS Playbook
```yaml
- hosts: localhost
  vars:
    aws_region: us-east-1
  tasks:
    - name: Create EC2 instance
      ec2_instance:
        instance_type: t3.medium
        region: "{{ aws_region }}"
        tags:
          Environment: production
```

### Multi-Cloud Playbook
```yaml
- hosts: localhost
  tasks:
    # AWS resources
    - name: Create AWS Lambda
      lambda_function:
        runtime: python3.11
        memory_size: 512
        region: us-east-1
    
    # GCP resources  
    - name: Create GCP VM
      gcp_compute_instance:
        machine_type: n1-standard-1
        zone: us-central1-a
    
    # Azure resources
    - name: Create Azure VM
      azure_rm_virtualmachine:
        vm_size: Standard_B2s
        location: eastus
```

## Variable Support

The parser supports Ansible variable substitution:

```yaml
- hosts: localhost
  vars:
    aws_region: us-west-2
    instance_type: t3.large
  tasks:
    - name: Create instance with variables
      ec2_instance:
        instance_type: "{{ instance_type }}"
        region: "{{ aws_region }}"
```

## Integration with FinOpsGuard

The Ansible parser integrates seamlessly with FinOpsGuard's cost analysis pipeline:

1. **Parse**: Convert Ansible playbooks to canonical resources
2. **Price**: Apply cloud-specific pricing data
3. **Analyze**: Generate cost estimates and recommendations
4. **Report**: Create detailed cost breakdowns

### API Usage
```python
from finopsguard.parsers import parse_ansible_to_crmodel

# Parse Ansible playbook
with open('playbook.yml', 'r') as f:
    playbook_content = f.read()

model = parse_ansible_to_crmodel(playbook_content)

# Access parsed resources
for resource in model.resources:
    print(f"{resource.type}: {resource.size} in {resource.region}")
```

## Testing

Comprehensive test coverage includes:
- Unit tests for each cloud parser
- Integration tests for multi-cloud scenarios
- Variable substitution testing
- Error handling for invalid YAML

Run tests with:
```bash
python -m pytest tests/unit/test_ansible_parser.py -v
```

## Contributing

To add support for new Ansible modules:

1. **Identify the cloud provider** (AWS/GCP/Azure)
2. **Add to appropriate parser** (`*_ansible_parser.py`)
3. **Extract key parameters** (size, region, count)
4. **Add comprehensive tests**
5. **Update documentation**

The modular architecture makes it easy to extend support for new cloud providers or additional module types.
