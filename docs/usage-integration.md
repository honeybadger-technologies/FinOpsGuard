# Usage Integration

FinOpsGuard can integrate with cloud provider monitoring and billing APIs to fetch historical usage data and actual cost information. This enables more accurate cost analysis by combining infrastructure-as-code predictions with real-world usage patterns.

## Overview

The usage integration feature provides:

- **Real-time Metrics**: CPU, memory, network, and disk utilization from CloudWatch, Cloud Monitoring, and Azure Monitor
- **Historical Billing Data**: Actual costs from AWS Cost Explorer, GCP Cloud Billing, and Azure Cost Management
- **Usage Analytics**: Identify underutilized resources and optimization opportunities
- **Trend Analysis**: Compare predicted costs against actual spending

## Supported Cloud Providers

### AWS
- **CloudWatch**: Resource metrics (CPU, network, disk I/O)
- **Cost Explorer**: Historical billing and usage data
- **Supported Resources**: EC2, RDS, Lambda, DynamoDB, S3, ELB/ALB

### GCP
- **Cloud Monitoring**: Resource metrics and performance data
- **Cloud Billing (BigQuery)**: Cost and usage reports
- **Supported Resources**: Compute Engine, Cloud SQL, Cloud Storage, GKE

### Azure
- **Azure Monitor**: Resource metrics and diagnostics
- **Cost Management**: Billing and cost analysis
- **Supported Resources**: Virtual Machines, SQL Database, Storage Accounts, App Services

## Configuration

### Enable Usage Integration

Add to your `.env` file:

```bash
# Enable usage integration globally
USAGE_INTEGRATION_ENABLED=true

# Cache TTL for usage data (default: 3600 seconds / 1 hour)
USAGE_CACHE_TTL_SECONDS=3600
```

### AWS Configuration

```bash
# Enable AWS usage integration
AWS_USAGE_ENABLED=true

# AWS credentials (if not using IAM roles)
AWS_ACCESS_KEY_ID=your-access-key
AWS_SECRET_ACCESS_KEY=your-secret-key
AWS_REGION=us-east-1
```

**Required AWS IAM Permissions:**

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "cloudwatch:GetMetricStatistics",
        "cloudwatch:ListMetrics",
        "ce:GetCostAndUsage",
        "ce:GetCostForecast"
      ],
      "Resource": "*"
    }
  ]
}
```

### GCP Configuration

```bash
# Enable GCP usage integration
GCP_USAGE_ENABLED=true

# GCP project and billing details
GCP_PROJECT_ID=your-project-id
GCP_BILLING_ACCOUNT_ID=012345-6789AB-CDEF01

# BigQuery dataset for billing export (must be configured in GCP Console)
GCP_BILLING_DATASET=billing_export
GCP_BILLING_TABLE=gcp_billing_export_v1

# Service account credentials
GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account.json
```

**Required GCP IAM Roles:**
- `roles/monitoring.viewer` - Read Cloud Monitoring metrics
- `roles/bigquery.dataViewer` - Read billing data from BigQuery
- `roles/bigquery.jobUser` - Run queries on billing data

**Setup Cloud Billing Export:**

1. Go to **Billing** → **Billing export** in GCP Console
2. Enable **BigQuery export**
3. Select or create a BigQuery dataset
4. Wait for data to populate (can take 24 hours)

### Azure Configuration

```bash
# Enable Azure usage integration
AZURE_USAGE_ENABLED=true

# Azure subscription and tenant
AZURE_SUBSCRIPTION_ID=your-subscription-id
AZURE_TENANT_ID=your-tenant-id
```

Azure credentials are automatically discovered via [DefaultAzureCredential](https://docs.microsoft.com/en-us/python/api/azure-identity/azure.identity.defaultazurecredential):
- Environment variables
- Managed Identity
- Azure CLI credentials
- Interactive browser

**Required Azure RBAC Roles:**
- `Monitoring Reader` - Read Azure Monitor metrics
- `Cost Management Reader` - Access cost and usage data

## Installation

Install cloud provider SDKs:

```bash
# Install all SDKs
pip install -r requirements.txt

# Or install individually
pip install boto3  # AWS
pip install google-cloud-monitoring google-cloud-bigquery  # GCP
pip install azure-mgmt-monitor azure-mgmt-costmanagement azure-identity  # Azure
```

## Usage

### Python API

#### Get Resource Usage Metrics

```python
from datetime import datetime, timedelta
from finopsguard.adapters.usage import get_usage_factory

# Initialize factory
factory = get_usage_factory()

# Check if usage integration is available for AWS
if factory.is_available("aws"):
    # Get CloudWatch metrics for an EC2 instance
    usage = factory.get_resource_usage(
        cloud_provider="aws",
        resource_id="i-1234567890abcdef0",
        resource_type="ec2",
        start_time=datetime.now() - timedelta(days=7),
        end_time=datetime.now(),
        region="us-east-1",
        metrics=["CPUUtilization", "NetworkIn", "NetworkOut"]
    )
    
    if usage:
        print(f"Average CPU: {usage.avg_cpu_utilization}%")
        print(f"Metrics collected: {len(usage.metrics)}")
```

#### Get Historical Cost Data

```python
from datetime import datetime
from finopsguard.adapters.usage import get_usage_factory

factory = get_usage_factory()

# Get cost data from AWS Cost Explorer
cost_records = factory.get_cost_usage(
    cloud_provider="aws",
    start_time=datetime(2024, 1, 1),
    end_time=datetime(2024, 1, 31),
    granularity="DAILY",
    group_by=["service", "region"]
)

if cost_records:
    total_cost = sum(r.cost for r in cost_records)
    print(f"Total cost in January: ${total_cost:.2f}")
    
    # Group by service
    by_service = {}
    for record in cost_records:
        service = record.service
        by_service[service] = by_service.get(service, 0) + record.cost
    
    print("\nCost by service:")
    for service, cost in sorted(by_service.items(), key=lambda x: x[1], reverse=True):
        print(f"  {service}: ${cost:.2f}")
```

#### Get Usage Summary

```python
from datetime import datetime
from finopsguard.types.usage import UsageQuery
from finopsguard.adapters.usage import get_usage_factory

factory = get_usage_factory()

# Create query
query = UsageQuery(
    cloud_provider="aws",
    start_time=datetime(2024, 1, 1),
    end_time=datetime(2024, 1, 31),
    resource_types=["ec2"],
    regions=["us-east-1", "us-west-2"],
    granularity="DAILY",
    group_by=["service", "region"]
)

# Get summary
summary = factory.get_usage_summary(query)

if summary:
    print(f"Total resources: {summary.total_resources}")
    print(f"Total cost: ${summary.total_cost:.2f}")
    print(f"Average CPU utilization: {summary.avg_cpu_utilization}%")
    print(f"Data confidence: {summary.confidence}")
```

### Direct Adapter Usage

You can also use adapters directly:

#### AWS Adapter

```python
from datetime import datetime, timedelta
from finopsguard.adapters.usage import get_aws_usage_adapter

adapter = get_aws_usage_adapter()

# Get EC2 instance metrics
usage = adapter.get_resource_usage(
    resource_id="i-1234567890abcdef0",
    resource_type="ec2",
    start_time=datetime.now() - timedelta(days=7),
    end_time=datetime.now(),
    region="us-east-1"
)

# Get cost data from Cost Explorer
cost_records = adapter.get_cost_usage(
    start_time=datetime(2024, 1, 1),
    end_time=datetime(2024, 1, 31),
    granularity="DAILY",
    group_by=["service"]
)
```

#### GCP Adapter

```python
from datetime import datetime, timedelta
from finopsguard.adapters.usage import get_gcp_usage_adapter

adapter = get_gcp_usage_adapter()

# Get Compute Engine instance metrics
usage = adapter.get_resource_usage(
    resource_id="instance-1",
    resource_type="gce_instance",
    start_time=datetime.now() - timedelta(days=7),
    end_time=datetime.now(),
    region="us-central1"
)

# Get billing data from BigQuery
cost_records = adapter.get_cost_usage(
    start_time=datetime(2024, 1, 1),
    end_time=datetime(2024, 1, 31),
    granularity="DAILY",
    group_by=["service", "project"]
)
```

#### Azure Adapter

```python
from datetime import datetime, timedelta
from finopsguard.adapters.usage import get_azure_usage_adapter

adapter = get_azure_usage_adapter()

# Get VM metrics
usage = adapter.get_resource_usage(
    resource_id="/subscriptions/{sub-id}/resourceGroups/{rg}/providers/Microsoft.Compute/virtualMachines/{vm-name}",
    resource_type="virtual_machine",
    start_time=datetime.now() - timedelta(days=7),
    end_time=datetime.now(),
    region="eastus"
)

# Get cost data
cost_records = adapter.get_cost_usage(
    start_time=datetime(2024, 1, 1),
    end_time=datetime(2024, 1, 31),
    granularity="DAILY",
    group_by=["service", "region"]
)
```

## Caching

Usage data is automatically cached to reduce API calls and improve performance:

- **Default TTL**: 1 hour (3600 seconds)
- **Configurable**: Set `USAGE_CACHE_TTL_SECONDS` in environment
- **In-memory**: Cache is stored in application memory
- **Per-query**: Each unique query is cached separately

Clear cache programmatically:

```python
from finopsguard.adapters.usage import get_usage_factory

factory = get_usage_factory()
factory.clear_cache()
```

## Resource Type Mappings

### AWS CloudWatch Namespaces

| Resource Type | Namespace | Default Metrics |
|--------------|-----------|----------------|
| `ec2` | AWS/EC2 | CPUUtilization, NetworkIn, NetworkOut |
| `rds` | AWS/RDS | CPUUtilization, DatabaseConnections, ReadIOPS |
| `lambda` | AWS/Lambda | Invocations, Duration, Errors |
| `dynamodb` | AWS/DynamoDB | ConsumedReadCapacityUnits, ConsumedWriteCapacityUnits |
| `s3` | AWS/S3 | NumberOfObjects, BucketSizeBytes |
| `elb` | AWS/ELB | RequestCount, HealthyHostCount |
| `alb` | AWS/ApplicationELB | RequestCount, ActiveConnectionCount |

### GCP Cloud Monitoring Metrics

| Resource Type | Metric Prefix | Default Metrics |
|--------------|---------------|----------------|
| `gce_instance` | compute.googleapis.com/instance | cpu/utilization, network/received_bytes_count |
| `cloudsql_database` | cloudsql.googleapis.com/database | cpu/utilization, memory/utilization |
| `gcs_bucket` | storage.googleapis.com/storage | total_bytes, request_count |
| `gke_container` | container.googleapis.com | cpu/usage_time, memory/usage_bytes |

### Azure Monitor Metrics

| Resource Type | Default Metrics |
|--------------|----------------|
| `virtual_machine` | Percentage CPU, Network In Total, Network Out Total |
| `sql_database` | cpu_percent, connection_successful, storage_percent |
| `storage_account` | Transactions, UsedCapacity, Availability |
| `app_service` | CpuTime, Requests, ResponseTime |

## Error Handling

The usage integration gracefully handles errors:

- **Missing credentials**: Returns `None` and logs warning
- **API errors**: Returns `None` and logs error
- **Unavailable resources**: Returns empty metrics list
- **Rate limiting**: Automatically handled by cloud SDKs

Check availability before using:

```python
from finopsguard.adapters.usage import get_usage_factory

factory = get_usage_factory()

if factory.is_available("aws"):
    # Safe to use AWS usage adapter
    usage = factory.get_resource_usage(...)
else:
    # Fall back to estimated data
    print("AWS usage integration not available")
```

## Best Practices

1. **Enable Caching**: Use default caching to minimize API calls
2. **Limit Time Ranges**: Query smaller time windows for faster responses
3. **Filter Resources**: Use resource IDs and types to narrow queries
4. **Group Wisely**: Use `group_by` strategically to avoid large result sets
5. **Monitor Costs**: Cloud APIs may incur charges (CloudWatch, BigQuery queries)
6. **IAM Least Privilege**: Grant only necessary permissions
7. **Handle Failures**: Always check for `None` returns and handle gracefully

## Troubleshooting

### AWS Issues

**Problem**: `boto3` import error
```bash
# Solution: Install boto3
pip install boto3
```

**Problem**: Authentication error
```bash
# Solution: Configure AWS credentials
aws configure
# Or set environment variables
export AWS_ACCESS_KEY_ID=your-key
export AWS_SECRET_ACCESS_KEY=your-secret
```

**Problem**: No Cost Explorer data
- Cost Explorer must be enabled in AWS Console (Billing → Cost Explorer)
- Data can take 24 hours to appear
- Requires IAM permission `ce:GetCostAndUsage`

### GCP Issues

**Problem**: No billing data in BigQuery
- Enable Cloud Billing export in GCP Console
- Data export can take 24-48 hours initially
- Verify dataset and table names match configuration

**Problem**: Authentication error
```bash
# Solution: Set service account credentials
export GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account.json
```

### Azure Issues

**Problem**: Authentication error
```bash
# Solution: Login with Azure CLI
az login
```

**Problem**: Subscription not found
- Verify `AZURE_SUBSCRIPTION_ID` is correct
- Ensure your account has access to the subscription

**Problem**: No cost data
- Azure Cost Management data can lag 24-72 hours
- Verify you have `Cost Management Reader` role

## Performance Considerations

- **API Rate Limits**: Cloud APIs have rate limits; use caching
- **Query Complexity**: More metrics = more API calls = slower response
- **Time Ranges**: Larger ranges = more data = slower queries
- **BigQuery Costs**: GCP billing queries cost money; optimize query frequency

## Security

- **Credentials**: Never commit credentials to version control
- **Least Privilege**: Use minimal IAM permissions
- **Encryption**: Use TLS for API communications (handled by SDKs)
- **Audit Logging**: Enable CloudTrail (AWS), Cloud Audit Logs (GCP), Activity Logs (Azure)

## See Also

- [Live Pricing Integration](pricing.md)
- [API Documentation](api/openapi.yaml)
- [Database Schema](database.md)
- [Deployment Guide](deployment.md)

