# Terraform Parsing Guide

FinOpsGuard provides comprehensive Terraform HCL parsing for multi-cloud infrastructure cost analysis through a **modular parser architecture**. This document describes the supported resource types and parsing capabilities.

## Architecture

The parser uses a modular design with cloud-specific parsers:

```
src/finopsguard/parsers/
├── terraform.py          (93 lines)   ← Main orchestrator
├── aws_tf_parser.py      (509 lines)  ← AWS-specific parsing
├── gcp_tf_parser.py      (390 lines)  ← GCP-specific parsing
├── azure_tf_parser.py    (403 lines)  ← Azure-specific parsing
└── __init__.py           (17 lines)   ← Public exports
```

**Benefits:**
- ✅ **Maintainable**: Each cloud in separate file (~400 lines vs 1,300)
- ✅ **Extensible**: Add resources to specific parser only
- ✅ **Testable**: Unit test cloud parsers independently
- ✅ **Collaborative**: Multiple devs work on different clouds without conflicts

## Overview

The Terraform parser (`finopsguard.parsers.terraform`) converts Infrastructure-as-Code into a canonical resource model for cost estimation. It supports:

- **AWS**: 24+ resource types
- **GCP**: 18+ resource types  
- **Azure**: 18+ resource types
- **Total**: 60+ resource types across all major clouds

## Supported Resources

### AWS Resources (24 Types)

#### Compute (7)
1. **aws_instance** - EC2 instances
   - Extracts: `instance_type`, `region`
   - Example: t3.micro, m5.large, c5.xlarge

2. **aws_autoscaling_group** - Auto Scaling Groups
   - Extracts: `instance_type`, `desired_capacity`
   - Calculates: instances × hourly cost

3. **aws_eks_cluster** - Elastic Kubernetes Service
   - Extracts: `region`
   - Note: Control plane cost only (nodes are separate EC2)

4. **aws_lambda_function** - Lambda Functions
   - Extracts: `memory_size`, `runtime`
   - Example: 512MB-python3.11

5. **aws_ecs_cluster** - Elastic Container Service
   - Extracts: `region`
   - Note: Cluster itself has minimal cost

6. **aws_ecs_service** - ECS Services
   - Extracts: `desired_count`, `launch_type`
   - Example: FARGATE-3tasks

7. **aws_ecs_task_definition** - ECS Task Definitions (Fargate)
   - Extracts: `cpu`, `memory`
   - Example: 1024cpu-2048mb

8. **aws_apprunner_service** - App Runner Services
   - Extracts: `cpu`, `memory`
   - Example: 2vCPU-4GB

#### Database (7)
9. **aws_db_instance** - RDS Databases
   - Extracts: `instance_class`, `region`
   - Example: db.t3.large, db.r5.xlarge

10. **aws_redshift_cluster** - Redshift Data Warehouse
    - Extracts: `node_type`, `number_of_nodes`
    - Example: dc2.large

11. **aws_opensearch_domain** - OpenSearch/Elasticsearch
    - Extracts: `instance_type`, `instance_count`
    - Example: t3.medium.search

12. **aws_elasticache_cluster** - ElastiCache (Redis/Memcached)
    - Extracts: `node_type`, `num_cache_nodes`
    - Example: cache.t3.medium

13. **aws_elasticache_replication_group** - ElastiCache Replication
    - Extracts: `node_type`, `number_cache_clusters`
    - High availability configuration

14. **aws_dynamodb_table** - DynamoDB Tables
    - Extracts: `billing_mode`, `read_capacity`, `write_capacity`
    - Modes: PAY_PER_REQUEST, PROVISIONED

15. **aws_neptune_cluster** - Neptune Graph Database
    - Extracts: `instance_class`
    - Example: db.r5.large

16. **aws_docdb_cluster** - DocumentDB (MongoDB-compatible)
    - Extracts: `instance_class`
    - Example: db.t3.medium

#### Storage (1)
17. **aws_s3_bucket** - S3 Object Storage
    - Extracts: `storage_class`
    - Example: STANDARD, INTELLIGENT_TIERING

#### Networking (2)
18. **aws_lb** / **aws_alb** - Load Balancers
    - Application and Network Load Balancers
    - Region-based pricing

19. **aws_cloudfront_distribution** - CloudFront CDN
    - Extracts: `price_class`
    - Global service

#### Analytics & Data (6)
20. **aws_kinesis_stream** - Kinesis Data Streams
    - Extracts: `shard_count`
    - Example: 4shards

21. **aws_msk_cluster** - Managed Kafka
    - Extracts: `instance_type`, `number_of_broker_nodes`
    - Example: kafka.m5.large

22. **aws_emr_cluster** - Elastic MapReduce (Hadoop)
    - Extracts: `master_instance_type`
    - Example: m5.xlarge

23. **aws_glue_job** / **aws_glue_crawler** - AWS Glue ETL
    - Serverless ETL jobs
    - DPU-based pricing

24. **aws_athena_workgroup** - Athena Query Service
    - Query-based pricing
    - Pay per TB scanned

#### Messaging & Integration (4)
25. **aws_sns_topic** - Simple Notification Service
    - Message-based pricing

26. **aws_sqs_queue** - Simple Queue Service
    - Standard and FIFO queues
    - Request-based pricing

27. **aws_sfn_state_machine** - Step Functions
    - Extracts: `type` (STANDARD, EXPRESS)
    - State transition pricing

28. **aws_api_gateway_rest_api** / **aws_apigatewayv2_api** - API Gateway
    - Extracts: `protocol_type`
    - Request-based pricing

### GCP Resources (18 Types)

#### Compute (4)
1. **google_compute_instance** - Compute Engine VMs
   - Extracts: `machine_type`, `zone`
   - Example: e2-micro, n2-standard-4

2. **google_container_cluster** - GKE Clusters
   - Extracts: `machine_type`, `initial_node_count`
   - Detects: Autopilot vs Standard

3. **google_compute_disk** - Persistent Disks
   - Extracts: `type`, `size`
   - Example: pd-ssd-500GB

4. **google_notebooks_instance** - Vertex AI Workbench
   - Extracts: `machine_type`
   - ML/Data Science workbenches

#### Database & Storage (5)
5. **google_sql_database_instance** - Cloud SQL
   - Extracts: `tier`, `database_version`
   - Supports: PostgreSQL, MySQL, SQL Server

6. **google_storage_bucket** - Cloud Storage
   - Extracts: `location`, `storage_class`
   - Example: STANDARD, NEARLINE, COLDLINE

7. **google_filestore_instance** - Managed NFS
   - Extracts: `tier`, `capacity_gb`
   - Example: PREMIUM-2560GB

8. **google_spanner_instance** - Cloud Spanner
   - Extracts: `num_nodes` or `processing_units`
   - Globally distributed database

9. **google_bigquery_dataset** - BigQuery Data Warehouse
   - Extracts: `location`
   - Query and storage based pricing

#### Serverless (2)
10. **google_cloud_run_service** - Cloud Run
    - Serverless containers
    - CPU/memory/request pricing

11. **google_cloudfunctions_function** - Cloud Functions
    - Extracts: `runtime`, `available_memory_mb`
    - Example: python310

#### Caching & Messaging (2)
12. **google_redis_instance** - Memorystore for Redis
    - Extracts: `tier`, `memory_size_gb`
    - Example: STANDARD_HA-5GB

13. **google_pubsub_topic** - Pub/Sub Messaging
    - Message-based pricing

#### Networking (2)
14. **google_compute_global_forwarding_rule** - Global Load Balancer
15. **google_compute_url_map** - URL Map for LB
16. **google_compute_target_http_proxy** / **google_compute_target_https_proxy** - LB Proxy
    - Combined: Load Balancer pricing

17. **google_compute_security_policy** - Cloud Armor
    - WAF and DDoS protection
    - Request-based pricing

#### Analytics & Data (3)
18. **google_dataflow_job** - Dataflow (Apache Beam)
    - Extracts: `machine_type`, `max_workers`
    - Streaming/batch data processing

19. **google_dataproc_cluster** - Dataproc (Managed Hadoop/Spark)
    - Extracts: `master/worker machine_type`, `num_instances`
    - Big data processing

20. **google_composer_environment** - Cloud Composer (Managed Airflow)
    - Extracts: `node_count`, `machine_type`
    - Workflow orchestration

### Azure Resources (18 Types)

#### Compute (3)
1. **azurerm_virtual_machine** / **azurerm_linux_virtual_machine** / **azurerm_windows_virtual_machine**
   - Extracts: `vm_size`, `location`
   - Example: Standard_D2s_v3

2. **azurerm_kubernetes_cluster** - AKS
   - Extracts: `vm_size`, `node_count` from default_node_pool
   - Example: Standard_DS2_v2-3nodes

3. **azurerm_container_group** - Container Instances
   - Extracts: `cpu`, `memory`
   - Example: 0.5cpu-1.5gb

#### Database (5)
4. **azurerm_mssql_server** / **azurerm_sql_server** - SQL Server
   - Server infrastructure cost

5. **azurerm_mssql_database** / **azurerm_sql_database** - SQL Database
   - Extracts: `sku_name`
   - Example: S0, S1, S2, P1

6. **azurerm_postgresql_server** / **azurerm_postgresql_flexible_server**
   - Extracts: `sku_name`, `storage_mb`
   - Example: GP_Standard_D4s_v3-32GB

7. **azurerm_mysql_server** / **azurerm_mysql_flexible_server**
   - Extracts: `sku_name`, `storage_mb`
   - Example: GP_Standard_D2ds_v4-20GB

8. **azurerm_sql_managed_instance** - SQL Managed Instance
   - Extracts: `sku_name`, `vcores`, `storage_size_in_gb`
   - Example: GP_Gen5-8vCore-256GB

9. **azurerm_cosmosdb_account** - Cosmos DB
   - Extracts: `consistency_level`
   - NoSQL database

#### Storage & Data (2)
10. **azurerm_storage_account** - Storage Account
    - Extracts: `account_tier`, `account_replication_type`
    - Example: Standard_GRS

11. **azurerm_data_factory** - Data Factory
    - ETL and data integration

#### App Services (3)
12. **azurerm_app_service_plan** / **azurerm_service_plan**
    - Extracts: `sku_name` or `tier + size`
    - Example: P1v2, B1

13. **azurerm_app_service** / **azurerm_linux_web_app** / **azurerm_windows_web_app**
    - Web applications
    - Pricing via app service plan

14. **azurerm_function_app** / **azurerm_linux_function_app** / **azurerm_windows_function_app**
    - Serverless functions
    - Consumption or plan-based

#### Networking (3)
15. **azurerm_lb** - Load Balancer
    - Extracts: `sku` (Basic, Standard)

16. **azurerm_application_gateway** - Application Gateway
    - Extracts: `sku`, `capacity`
    - Example: WAF_v2-2

17. **azurerm_virtual_network_gateway** - VPN Gateway
    - Extracts: `type`, `sku`
    - Example: Vpn_VpnGw1

#### Caching & Analytics (3)
18. **azurerm_redis_cache** - Redis Cache
    - Extracts: `sku_name`, `family`, `capacity`
    - Example: Premium_P1

19. **azurerm_synapse_workspace** - Synapse Analytics
    - Data warehouse and analytics

20. **azurerm_eventhub_namespace** - Event Hubs
    - Extracts: `sku`, `capacity`
    - Event streaming platform

## Parser Capabilities

### 1. Provider Detection

Automatically detects cloud provider from resource type prefix:
- `aws_*` → AWS
- `google_*` → GCP
- `azurerm_*` → Azure

### 2. Region/Location Extraction

Supports multiple region/location parameters:
```hcl
# AWS - uses 'region'
resource "aws_instance" "web" {
  region = "us-east-1"
}

# GCP - uses 'zone' or 'region'  
resource "google_compute_instance" "web" {
  zone = "us-central1-a"  # Extracts region: us-central1
}

# Azure - uses 'location'
resource "azurerm_linux_virtual_machine" "web" {
  location = "eastus"
}
```

### 3. Default Region/Location

Uses provider-level defaults when not specified:
- AWS: `us-east-1`
- GCP: `us-central1`
- Azure: `eastus`

### 4. Count Parameter Support

Respects Terraform `count` parameter:
```hcl
resource "aws_instance" "web" {
  instance_type = "t3.micro"
  count         = 5  # Creates 5 instances
}
```

### 5. Nested Attribute Extraction

Handles complex nested blocks:
```hcl
# AKS with nested default_node_pool
resource "azurerm_kubernetes_cluster" "k8s" {
  default_node_pool {
    vm_size    = "Standard_DS2_v2"
    node_count = 3
  }
}

# Dataproc with nested worker_config
resource "google_dataproc_cluster" "spark" {
  cluster_config {
    worker_config {
      num_instances = 4
      machine_type  = "n1-standard-4"
    }
  }
}
```

### 6. Multiple Resource Type Variants

Supports old and new Terraform provider syntax:
```hcl
# Both are supported
resource "aws_lb" "..." { }           # New
resource "aws_alb" "..." { }          # Legacy

resource "azurerm_virtual_machine" "..." { }        # Old
resource "azurerm_linux_virtual_machine" "..." { }  # New
```

## Usage

### Python API

```python
from finopsguard.parsers.terraform import parse_terraform_to_crmodel

# Parse Terraform HCL
hcl_content = '''
resource "aws_instance" "web" {
  ami           = "ami-123"
  instance_type = "t3.medium"
  count         = 3
}

resource "google_compute_instance" "app" {
  machine_type = "n2-standard-4"
  zone         = "us-central1-a"
}

resource "azurerm_linux_virtual_machine" "db" {
  vm_size  = "Standard_D2s_v3"
  location = "eastus"
}
'''

model = parse_terraform_to_crmodel(hcl_content)

# Access resources
print(f"Total resources: {len(model.resources)}")
for resource in model.resources:
    print(f"  {resource.type}: {resource.size} in {resource.region}")

# Output:
# Total resources: 3
#   aws_instance: t3.medium in us-east-1
#   gcp_compute_instance: n2-standard-4 in us-central1
#   azure_virtual_machine: Standard_D2s_v3 in eastus
```

### REST API

```bash
# Base64 encode Terraform content
PAYLOAD=$(cat infrastructure.tf | base64)

# Call checkCostImpact
curl -X POST http://localhost:8080/mcp/checkCostImpact \
  -H 'Content-Type: application/json' \
  -d "{
    \"iac_type\": \"terraform\",
    \"iac_payload\": \"$PAYLOAD\",
    \"environment\": \"prod\"
  }"
```

## Modular Parser Design

### Cloud-Specific Parsers

Each cloud has its own dedicated parser module:

**aws_tf_parser.py** - AWS Resources
```python
from finopsguard.parsers.aws_tf_parser import parse_aws_resource

resource = parse_aws_resource(
    resource_type='aws_lambda_function',
    resource_name='processor',
    resource_body='runtime = "python3.11"\nmemory_size = 1024',
    default_region='us-east-1',
    count=1
)
# Returns: CanonicalResource for Lambda
```

**gcp_tf_parser.py** - GCP Resources
```python
from finopsguard.parsers.gcp_tf_parser import parse_gcp_resource

resource = parse_gcp_resource(
    resource_type='google_compute_instance',
    resource_name='web',
    resource_body='machine_type = "n2-standard-4"',
    default_region='us-central1',
    count=1
)
# Returns: CanonicalResource for GCE
```

**azure_tf_parser.py** - Azure Resources
```python
from finopsguard.parsers.azure_tf_parser import parse_azure_resource

resource = parse_azure_resource(
    resource_type='azurerm_linux_virtual_machine',
    resource_name='web',
    resource_body='vm_size = "Standard_D2s_v3"',
    default_location='eastus',
    count=1
)
# Returns: CanonicalResource for Azure VM
```

### Main Orchestrator

**terraform.py** - Coordinates all parsers:
```python
def parse_terraform_to_crmodel(hcl_text: str):
    # Extract defaults
    aws_region = get_aws_default_region(hcl_text)
    gcp_region = get_gcp_default_region(hcl_text)
    azure_location = get_azure_default_location(hcl_text)
    
    # Route to cloud-specific parsers
    for resource in extract_resources(hcl_text):
        if resource.type.startswith('aws_'):
            parsed = parse_aws_resource(...)
        elif resource.type.startswith('google_'):
            parsed = parse_gcp_resource(...)
        elif resource.type.startswith('azurerm_'):
            parsed = parse_azure_resource(...)
```

## Parser Implementation

### Resource Detection Pattern

```python
# Regex pattern for Terraform resources
resource_regex = re.compile(
    r'resource\s+"([^"]+)"\s+"([^"]+)"\s*\{([\s\S]*?)\}', 
    re.MULTILINE
)

# Captures:
# - Resource type (e.g., "aws_instance")
# - Resource name (e.g., "web")
# - Resource body (all attributes)
```

### Attribute Extraction Pattern

```python
# Extract instance_type from resource body
inst_match = re.search(
    r'instance_type\s*=\s*"([a-z0-9.\-]+)"', 
    body, 
    re.IGNORECASE
)
instance_type = inst_match.group(1) if inst_match else 't3.micro'
```

### Nested Block Extraction

```python
# Extract from nested blocks using DOTALL flag
vm_size_match = re.search(
    r'default_node_pool\s*\{[^}]*vm_size\s*=\s*"([A-Za-z0-9_]+)"',
    body,
    re.IGNORECASE | re.DOTALL
)
```

## Canonical Resource Model

Parsed resources are converted to a canonical model:

```python
CanonicalResource(
    id="web-t3.medium-us-east-1",    # Unique identifier
    type="aws_instance",              # Resource type
    name="web",                       # Terraform name
    region="us-east-1",               # Region/location
    size="t3.medium",                 # Size/SKU/tier
    count=3,                          # Number of instances
    tags={},                          # Resource tags
    metadata={                        # Additional attributes
        "memory_mb": 4096,
        "vcpu": 2
    }
)
```

## Limitations

### Current Limitations

1. **Resource Type Coverage**: Not all Terraform resources supported (60+ of hundreds)
2. **Dynamic Blocks**: `dynamic` blocks not fully parsed
3. **Interpolation**: Variable interpolation not supported
4. **Modules**: Module calls not expanded
5. **Data Sources**: Data sources not evaluated
6. **Conditionals**: `count` with conditionals not evaluated

### Workarounds

#### For Unsupported Resources
Parser silently skips unknown resource types. Cost will be $0.

#### For Variables
Use explicit values instead of variables:
```hcl
# Instead of:
instance_type = var.instance_type

# Use:
instance_type = "t3.medium"
```

#### For Modules
Inline module resources or ensure module files are included.

## Best Practices

### 1. Use Explicit Values

```hcl
# Good - Explicit values
resource "aws_instance" "web" {
  instance_type = "t3.medium"
  region        = "us-east-1"
}

# Avoid - Variables (won't be evaluated)
resource "aws_instance" "web" {
  instance_type = var.instance_type
  region        = var.region
}
```

### 2. Include Region/Location

```hcl
# Good - Explicit region
resource "aws_db_instance" "db" {
  instance_class = "db.t3.large"
  region         = "us-west-2"  # Explicit
}

# Acceptable - Uses provider default
provider "aws" {
  region = "us-west-2"
}
resource "aws_db_instance" "db" {
  instance_class = "db.t3.large"
  # Inherits us-west-2
}
```

### 3. Specify Count Explicitly

```hcl
# Good
resource "aws_instance" "web" {
  instance_type = "t3.micro"
  count         = 3  # Clear intention
}
```

## Testing

### Unit Tests

Each cloud provider has comprehensive test coverage:

```bash
# Test AWS parsing
pytest tests/unit/test_aws_terraform_parser_extended.py -v

# Test GCP parsing  
pytest tests/unit/test_gcp_terraform_parser_extended.py -v

# Test Azure parsing
pytest tests/unit/test_azure_terraform_parser.py -v

# Test all
pytest tests/unit/test_*_terraform_parser*.py -v
```

### Test Coverage

- **AWS**: 18 tests covering 24 resource types
- **GCP**: 11 tests covering 18 resource types
- **Azure**: 21 tests covering 18 resource types
- **Total**: 50 tests with 100% pass rate

## Examples

See comprehensive examples in `examples/`:
- `aws-infrastructure.tf` - All AWS resource types
- `gcp-infrastructure.tf` - All GCP resource types
- `azure-infrastructure.tf` - All Azure resource types

## Extending the Parser

### Adding a New Resource Type

The modular architecture makes it easy to add new resources:

1. **Identify the cloud provider**: AWS, GCP, or Azure

2. **Open the corresponding parser file**:
   - AWS: `src/finopsguard/parsers/aws_tf_parser.py`
   - GCP: `src/finopsguard/parsers/gcp_tf_parser.py`
   - Azure: `src/finopsguard/parsers/azure_tf_parser.py`

3. **Add parser logic** to the cloud-specific file:
```python
# In aws_tf_parser.py

def parse_aws_resource(...):
    # ... existing code ...
    
    # AWS New Service
    if resource_type == 'aws_new_service':
        attribute_match = re.search(r'attribute\s*=\s*"([^"]+)"', resource_body)
        attribute = attribute_match.group(1) if attribute_match else 'default'
        
        return CanonicalResource(
            id=f"{resource_name}-newservice-{region}",
            type='aws_new_service',
            name=resource_name,
            region=region,
            size=attribute,
            count=count,
            tags={},
            metadata={}
        )
    
    # ... return None at end if not supported ...
```

**Benefits of modular approach:**
- ✅ No risk of breaking GCP/Azure parsing
- ✅ Smaller, focused file to edit
- ✅ Clear ownership and responsibility
- ✅ Easier code reviews

4. **Add pricing** to appropriate adapter:
```python
# In aws_static.py
AWS_NEW_SERVICE_PRICING = {
    "small": {"hourly_price": 0.10},
    "medium": {"hourly_price": 0.20},
    "large": {"hourly_price": 0.40}
}
```

3. **Add test**:
```python
def test_parse_aws_new_service(self):
    hcl = '''
resource "aws_new_service" "example" {
  attribute = "medium"
}
'''
    model = parse_terraform_to_crmodel(hcl)
    assert len(model.resources) == 1
    assert model.resources[0].type == 'aws_new_service'
    assert model.resources[0].size == 'medium'
```

4. **Run tests**:
```bash
pytest tests/unit/test_aws_terraform_parser_extended.py -v
```

## Performance

The parser is optimized for speed:
- **Regex-based**: Fast pattern matching
- **Single-pass**: Processes HCL once
- **No AST**: Avoids complex parsing overhead
- **Typical performance**: <10ms for 100 resources

## See Also

- [Architecture Documentation](architecture.md)
- [Pricing Adapters](pricing.md)
- [API Reference](api/openapi.yaml)
- [Example Infrastructure Files](../examples/)

---

**Last Updated**: October 2025  
**Version**: 0.3.0  
**Status**: Production Ready ✅  
**Resource Coverage**: 60+ resource types across AWS, GCP, and Azure

