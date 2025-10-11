#!/usr/bin/env python3
"""
Example usage of FinOpsGuard Usage Integration

This script demonstrates how to use the usage integration feature to:
1. Fetch resource metrics from CloudWatch/Cloud Monitoring/Azure Monitor
2. Get historical billing data from Cost Explorer/Cloud Billing/Cost Management
3. Generate usage summaries and analytics

Prerequisites:
- Configure cloud credentials (AWS_ACCESS_KEY_ID, GOOGLE_APPLICATION_CREDENTIALS, etc.)
- Enable usage integration in environment (USAGE_INTEGRATION_ENABLED=true)
- Install cloud SDKs: pip install boto3 google-cloud-monitoring azure-mgmt-monitor
"""

import os
from datetime import datetime, timedelta
from finopsguard.adapters.usage import get_usage_factory
from finopsguard.types.usage import UsageQuery


def setup_environment():
    """Setup environment variables for testing."""
    # Enable usage integration
    os.environ["USAGE_INTEGRATION_ENABLED"] = "true"
    
    # AWS configuration
    os.environ["AWS_USAGE_ENABLED"] = "true"
    os.environ["AWS_REGION"] = "us-east-1"
    # AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY should be set in your environment
    
    # GCP configuration
    os.environ["GCP_USAGE_ENABLED"] = "true"
    os.environ["GCP_PROJECT_ID"] = "your-project-id"
    os.environ["GCP_BILLING_ACCOUNT_ID"] = "012345-6789AB-CDEF01"
    # GOOGLE_APPLICATION_CREDENTIALS should point to your service account JSON
    
    # Azure configuration
    os.environ["AZURE_USAGE_ENABLED"] = "true"
    os.environ["AZURE_SUBSCRIPTION_ID"] = "your-subscription-id"
    os.environ["AZURE_TENANT_ID"] = "your-tenant-id"


def example_check_availability():
    """Example: Check which cloud providers are available."""
    print("=" * 80)
    print("Example 1: Check Usage Integration Availability")
    print("=" * 80)
    
    factory = get_usage_factory()
    
    print(f"\nUsage integration enabled: {factory.enabled}")
    print(f"AWS available: {factory.is_available('aws')}")
    print(f"GCP available: {factory.is_available('gcp')}")
    print(f"Azure available: {factory.is_available('azure')}")


def example_get_resource_usage():
    """Example: Get CloudWatch metrics for an EC2 instance."""
    print("\n" + "=" * 80)
    print("Example 2: Get Resource Usage Metrics (AWS EC2)")
    print("=" * 80)
    
    factory = get_usage_factory()
    
    if not factory.is_available("aws"):
        print("\nAWS usage integration not available. Configure credentials to use this feature.")
        return
    
    # Get usage data for an EC2 instance over the last 7 days
    end_time = datetime.now()
    start_time = end_time - timedelta(days=7)
    
    print(f"\nFetching metrics from {start_time.date()} to {end_time.date()}")
    
    try:
        usage = factory.get_resource_usage(
            cloud_provider="aws",
            resource_id="i-1234567890abcdef0",  # Replace with your instance ID
            resource_type="ec2",
            start_time=start_time,
            end_time=end_time,
            region="us-east-1",
            metrics=["CPUUtilization", "NetworkIn", "NetworkOut"]
        )
        
        if usage:
            print(f"\nResource: {usage.resource_id}")
            print(f"Type: {usage.resource_type}")
            print(f"Region: {usage.region}")
            print(f"Metrics collected: {len(usage.metrics)}")
            
            if usage.avg_cpu_utilization:
                print(f"\nAverage CPU Utilization: {usage.avg_cpu_utilization:.2f}%")
            
            if usage.avg_network_in_gb:
                print(f"Average Network In: {usage.avg_network_in_gb:.4f} GB")
            
            if usage.avg_network_out_gb:
                print(f"Average Network Out: {usage.avg_network_out_gb:.4f} GB")
            
            # Show first few metrics
            if usage.metrics:
                print(f"\nSample metrics (first 5):")
                for metric in usage.metrics[:5]:
                    print(f"  {metric.timestamp}: {metric.metric_name} = {metric.value:.2f} {metric.unit}")
        else:
            print("\nNo usage data found.")
            
    except Exception as e:
        print(f"\nError: {e}")


def example_get_cost_usage():
    """Example: Get historical cost data from AWS Cost Explorer."""
    print("\n" + "=" * 80)
    print("Example 3: Get Historical Cost and Usage Data")
    print("=" * 80)
    
    factory = get_usage_factory()
    
    if not factory.is_available("aws"):
        print("\nAWS usage integration not available. Configure credentials to use this feature.")
        return
    
    # Get cost data for January 2024
    start_time = datetime(2024, 1, 1)
    end_time = datetime(2024, 1, 31)
    
    print(f"\nFetching cost data from {start_time.date()} to {end_time.date()}")
    
    try:
        cost_records = factory.get_cost_usage(
            cloud_provider="aws",
            start_time=start_time,
            end_time=end_time,
            granularity="DAILY",
            group_by=["service", "region"]
        )
        
        if cost_records:
            print(f"\nTotal records: {len(cost_records)}")
            
            # Calculate total cost
            total_cost = sum(r.cost for r in cost_records)
            print(f"Total cost: ${total_cost:.2f}")
            
            # Group by service
            by_service = {}
            for record in cost_records:
                service = record.service
                by_service[service] = by_service.get(service, 0) + record.cost
            
            print("\nCost by service (top 10):")
            for service, cost in sorted(by_service.items(), key=lambda x: x[1], reverse=True)[:10]:
                print(f"  {service:30s}: ${cost:10.2f}")
            
            # Show sample records
            print(f"\nSample records (first 3):")
            for record in cost_records[:3]:
                print(f"  Date: {record.date.date()}")
                print(f"  Service: {record.service}")
                print(f"  Cost: ${record.cost:.2f}")
                print(f"  Usage: {record.usage_amount:.2f} {record.usage_unit}")
                print()
        else:
            print("\nNo cost data found.")
            
    except Exception as e:
        print(f"\nError: {e}")


def example_usage_summary():
    """Example: Get comprehensive usage summary."""
    print("\n" + "=" * 80)
    print("Example 4: Get Usage Summary")
    print("=" * 80)
    
    factory = get_usage_factory()
    
    if not factory.is_available("aws"):
        print("\nAWS usage integration not available. Configure credentials to use this feature.")
        return
    
    # Create query for January 2024
    query = UsageQuery(
        cloud_provider="aws",
        start_time=datetime(2024, 1, 1),
        end_time=datetime(2024, 1, 31),
        resource_types=["ec2"],
        regions=["us-east-1", "us-west-2"],
        granularity="DAILY",
        group_by=["service", "region"]
    )
    
    print(f"\nGenerating summary for {query.cloud_provider}")
    print(f"Time range: {query.start_time.date()} to {query.end_time.date()}")
    
    try:
        summary = factory.get_usage_summary(query)
        
        if summary:
            print(f"\n{'Summary Statistics':=^60}")
            print(f"Cloud Provider: {summary.cloud_provider.upper()}")
            print(f"Resource Type: {summary.resource_type}")
            print(f"Total Resources: {summary.total_resources}")
            print(f"Total Cost: ${summary.total_cost:.2f}")
            
            if summary.total_resources > 0:
                print(f"Average Cost per Resource: ${summary.average_cost_per_resource:.2f}")
            
            print(f"Total Usage: {summary.total_usage:.2f} {summary.usage_unit}")
            
            if summary.avg_cpu_utilization:
                print(f"Average CPU Utilization: {summary.avg_cpu_utilization:.2f}%")
            
            print(f"Data Confidence: {summary.confidence}")
            print(f"Cost Records: {len(summary.records)}")
            print(f"Resource Details: {len(summary.resources)}")
        else:
            print("\nCould not generate usage summary.")
            
    except Exception as e:
        print(f"\nError: {e}")


def example_clear_cache():
    """Example: Clear usage data cache."""
    print("\n" + "=" * 80)
    print("Example 5: Clear Usage Cache")
    print("=" * 80)
    
    factory = get_usage_factory()
    
    print("\nClearing usage cache...")
    factory.clear_cache()
    print("Cache cleared. Next requests will fetch fresh data from cloud APIs.")


def example_gcp_usage():
    """Example: Get GCP Cloud Monitoring metrics."""
    print("\n" + "=" * 80)
    print("Example 6: Get GCP Resource Usage")
    print("=" * 80)
    
    factory = get_usage_factory()
    
    if not factory.is_available("gcp"):
        print("\nGCP usage integration not available. Configure credentials to use this feature.")
        return
    
    end_time = datetime.now()
    start_time = end_time - timedelta(days=7)
    
    print(f"\nFetching GCP metrics from {start_time.date()} to {end_time.date()}")
    
    try:
        usage = factory.get_resource_usage(
            cloud_provider="gcp",
            resource_id="instance-1",  # Replace with your instance name
            resource_type="gce_instance",
            start_time=start_time,
            end_time=end_time,
            region="us-central1"
        )
        
        if usage:
            print(f"\nResource: {usage.resource_id}")
            print(f"Metrics collected: {len(usage.metrics)}")
            
            if usage.avg_cpu_utilization:
                print(f"Average CPU Utilization: {usage.avg_cpu_utilization:.2f}%")
        else:
            print("\nNo usage data found.")
            
    except Exception as e:
        print(f"\nError: {e}")


def example_azure_cost():
    """Example: Get Azure Cost Management data."""
    print("\n" + "=" * 80)
    print("Example 7: Get Azure Cost Data")
    print("=" * 80)
    
    factory = get_usage_factory()
    
    if not factory.is_available("azure"):
        print("\nAzure usage integration not available. Configure credentials to use this feature.")
        return
    
    start_time = datetime(2024, 1, 1)
    end_time = datetime(2024, 1, 31)
    
    print(f"\nFetching Azure cost data from {start_time.date()} to {end_time.date()}")
    
    try:
        cost_records = factory.get_cost_usage(
            cloud_provider="azure",
            start_time=start_time,
            end_time=end_time,
            granularity="DAILY",
            group_by=["service"]
        )
        
        if cost_records:
            total_cost = sum(r.cost for r in cost_records)
            print(f"\nTotal cost: ${total_cost:.2f}")
            print(f"Total records: {len(cost_records)}")
        else:
            print("\nNo cost data found.")
            
    except Exception as e:
        print(f"\nError: {e}")


def main():
    """Run all examples."""
    print("\n" + "=" * 80)
    print("FinOpsGuard Usage Integration Examples")
    print("=" * 80)
    
    # Note: Setup is commented out because it would override actual credentials
    # Uncomment and modify if you want to test with specific credentials
    # setup_environment()
    
    # Run examples
    example_check_availability()
    example_get_resource_usage()
    example_get_cost_usage()
    example_usage_summary()
    example_gcp_usage()
    example_azure_cost()
    example_clear_cache()
    
    print("\n" + "=" * 80)
    print("Examples complete!")
    print("=" * 80)
    print("\nNote: Some examples may show errors if:")
    print("  - Cloud credentials are not configured")
    print("  - Usage integration is not enabled")
    print("  - Resource IDs don't exist in your account")
    print("  - Cost Explorer/Cloud Billing data is not available yet")
    print("\nSee docs/usage-integration.md for setup instructions.")
    print("=" * 80 + "\n")


if __name__ == "__main__":
    main()

