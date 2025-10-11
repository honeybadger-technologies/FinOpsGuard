"""AWS CloudWatch and Cost Explorer usage adapter."""

import os
import logging
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any

from finopsguard.types.usage import (
    ResourceUsage,
    CostUsageRecord,
    UsageSummary,
    UsageQuery,
    UsageMetric
)
from .base import UsageAdapter

logger = logging.getLogger(__name__)


class AWSUsageAdapter(UsageAdapter):
    """AWS usage adapter using CloudWatch and Cost Explorer APIs."""
    
    def __init__(self):
        """Initialize AWS usage adapter."""
        super().__init__("aws")
        self._cloudwatch = None
        self._ce = None  # Cost Explorer client
        self._enabled = os.getenv("AWS_USAGE_ENABLED", "false").lower() == "true"
        self._region = os.getenv("AWS_REGION", "us-east-1")
    
    def _get_cloudwatch_client(self):
        """Lazy load CloudWatch client."""
        if self._cloudwatch is None:
            try:
                import boto3
                self._cloudwatch = boto3.client('cloudwatch', region_name=self._region)
                logger.info("CloudWatch client initialized")
            except ImportError:
                logger.error("boto3 not installed. Install with: pip install boto3")
                raise
            except Exception as e:
                logger.error(f"Error initializing CloudWatch client: {e}")
                raise
        return self._cloudwatch
    
    def _get_cost_explorer_client(self):
        """Lazy load Cost Explorer client."""
        if self._ce is None:
            try:
                import boto3
                # Cost Explorer is only available in us-east-1
                self._ce = boto3.client('ce', region_name='us-east-1')
                logger.info("Cost Explorer client initialized")
            except ImportError:
                logger.error("boto3 not installed. Install with: pip install boto3")
                raise
            except Exception as e:
                logger.error(f"Error initializing Cost Explorer client: {e}")
                raise
        return self._ce
    
    def is_available(self) -> bool:
        """Check if AWS usage adapter is available."""
        if not self._enabled:
            return False
        
        try:
            # Check if boto3 is installed
            import boto3
            # Try to create a client to validate credentials
            boto3.client('sts').get_caller_identity()
            return True
        except ImportError:
            logger.warning("boto3 not installed")
            return False
        except Exception as e:
            logger.warning(f"AWS credentials not configured: {e}")
            return False
    
    def get_resource_usage(
        self,
        resource_id: str,
        resource_type: str,
        start_time: datetime,
        end_time: datetime,
        region: Optional[str] = None,
        metrics: Optional[List[str]] = None
    ) -> ResourceUsage:
        """
        Get CloudWatch metrics for a specific AWS resource.
        
        Args:
            resource_id: AWS resource ID (e.g., i-1234567890abcdef0)
            resource_type: Resource type (ec2, rds, lambda, etc.)
            start_time: Start time
            end_time: End time
            region: AWS region
            metrics: Specific metrics to fetch
            
        Returns:
            ResourceUsage object
        """
        if not self._enabled:
            raise ValueError("AWS usage adapter is not enabled")
        
        region = region or self._region
        cloudwatch = self._get_cloudwatch_client()
        
        # Map resource types to CloudWatch namespace and dimensions
        namespace_map = {
            "ec2": ("AWS/EC2", {"InstanceId": resource_id}),
            "rds": ("AWS/RDS", {"DBInstanceIdentifier": resource_id}),
            "lambda": ("AWS/Lambda", {"FunctionName": resource_id}),
            "dynamodb": ("AWS/DynamoDB", {"TableName": resource_id}),
            "s3": ("AWS/S3", {"BucketName": resource_id}),
            "elb": ("AWS/ELB", {"LoadBalancerName": resource_id}),
            "alb": ("AWS/ApplicationELB", {"LoadBalancer": resource_id}),
        }
        
        if resource_type not in namespace_map:
            logger.warning(f"Unknown resource type: {resource_type}")
            namespace = "AWS/EC2"
            dimensions = [{"Name": "ResourceId", "Value": resource_id}]
        else:
            namespace, dim_dict = namespace_map[resource_type]
            dimensions = [{"Name": k, "Value": v} for k, v in dim_dict.items()]
        
        # Default metrics per resource type
        default_metrics = {
            "ec2": ["CPUUtilization", "NetworkIn", "NetworkOut", "DiskReadBytes", "DiskWriteBytes"],
            "rds": ["CPUUtilization", "DatabaseConnections", "ReadIOPS", "WriteIOPS"],
            "lambda": ["Invocations", "Duration", "Errors", "Throttles"],
            "dynamodb": ["ConsumedReadCapacityUnits", "ConsumedWriteCapacityUnits"],
            "s3": ["NumberOfObjects", "BucketSizeBytes"],
            "elb": ["RequestCount", "HealthyHostCount", "UnHealthyHostCount"],
            "alb": ["RequestCount", "ActiveConnectionCount", "TargetResponseTime"],
        }
        
        metrics_to_fetch = metrics or default_metrics.get(resource_type, ["CPUUtilization"])
        
        # Fetch metrics from CloudWatch
        usage_metrics = []
        
        for metric_name in metrics_to_fetch:
            try:
                response = cloudwatch.get_metric_statistics(
                    Namespace=namespace,
                    MetricName=metric_name,
                    Dimensions=dimensions,
                    StartTime=start_time,
                    EndTime=end_time,
                    Period=3600,  # 1 hour
                    Statistics=['Average', 'Maximum', 'Minimum']
                )
                
                for datapoint in response.get('Datapoints', []):
                    usage_metrics.append(UsageMetric(
                        timestamp=datapoint['Timestamp'],
                        value=datapoint.get('Average', 0),
                        unit=datapoint.get('Unit', 'None'),
                        metric_name=metric_name,
                        dimensions={d['Name']: d['Value'] for d in dimensions}
                    ))
                
                logger.debug(f"Fetched {len(response.get('Datapoints', []))} datapoints for {metric_name}")
                
            except Exception as e:
                logger.error(f"Error fetching metric {metric_name}: {e}")
        
        # Calculate summary statistics
        cpu_metrics = [m for m in usage_metrics if 'CPU' in m.metric_name]
        network_in_metrics = [m for m in usage_metrics if 'NetworkIn' in m.metric_name]
        network_out_metrics = [m for m in usage_metrics if 'NetworkOut' in m.metric_name]
        
        avg_cpu = sum(m.value for m in cpu_metrics) / len(cpu_metrics) if cpu_metrics else None
        avg_network_in = sum(m.value for m in network_in_metrics) / len(network_in_metrics) / (1024**3) if network_in_metrics else None
        avg_network_out = sum(m.value for m in network_out_metrics) / len(network_out_metrics) / (1024**3) if network_out_metrics else None
        
        return ResourceUsage(
            resource_id=resource_id,
            resource_type=resource_type,
            region=region,
            cloud_provider="aws",
            start_time=start_time,
            end_time=end_time,
            metrics=usage_metrics,
            avg_cpu_utilization=avg_cpu,
            avg_network_in_gb=avg_network_in,
            avg_network_out_gb=avg_network_out
        )
    
    def get_cost_usage(
        self,
        start_time: datetime,
        end_time: datetime,
        granularity: str = "DAILY",
        group_by: Optional[List[str]] = None,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[CostUsageRecord]:
        """
        Get cost and usage data from AWS Cost Explorer.
        
        Args:
            start_time: Start date
            end_time: End date
            granularity: DAILY or MONTHLY
            group_by: Group by dimensions (SERVICE, REGION, etc.)
            filters: Cost Explorer filters
            
        Returns:
            List of cost usage records
        """
        if not self._enabled:
            raise ValueError("AWS usage adapter is not enabled")
        
        ce = self._get_cost_explorer_client()
        
        # Format dates for Cost Explorer API
        start_date = start_time.strftime('%Y-%m-%d')
        end_date = end_time.strftime('%Y-%m-%d')
        
        # Build request parameters
        params = {
            'TimePeriod': {
                'Start': start_date,
                'End': end_date
            },
            'Granularity': granularity,
            'Metrics': ['UnblendedCost', 'UsageQuantity']
        }
        
        # Add group by
        if group_by:
            params['GroupBy'] = [
                {'Type': 'DIMENSION', 'Key': dim.upper()}
                for dim in group_by
            ]
        
        # Add filters
        if filters:
            params['Filter'] = filters
        
        try:
            response = ce.get_cost_and_usage(**params)
            
            records = []
            
            for result in response.get('ResultsByTime', []):
                time_period = result['TimePeriod']
                start = datetime.strptime(time_period['Start'], '%Y-%m-%d')
                end = datetime.strptime(time_period['End'], '%Y-%m-%d')
                
                # Handle grouped results
                if 'Groups' in result:
                    for group in result['Groups']:
                        dimensions = {}
                        for i, key in enumerate(group.get('Keys', [])):
                            if group_by and i < len(group_by):
                                dimensions[group_by[i]] = key
                        
                        cost = float(group['Metrics']['UnblendedCost']['Amount'])
                        usage = float(group['Metrics']['UsageQuantity']['Amount'])
                        
                        records.append(CostUsageRecord(
                            date=start,
                            start_time=start,
                            end_time=end,
                            cost=cost,
                            currency="USD",
                            usage_amount=usage,
                            usage_unit=group['Metrics']['UsageQuantity'].get('Unit', 'hours'),
                            service=dimensions.get('service', 'Unknown'),
                            region=dimensions.get('region'),
                            dimensions=dimensions
                        ))
                else:
                    # Non-grouped results
                    total = result.get('Total', {})
                    cost = float(total.get('UnblendedCost', {}).get('Amount', 0))
                    usage = float(total.get('UsageQuantity', {}).get('Amount', 0))
                    
                    records.append(CostUsageRecord(
                        date=start,
                        start_time=start,
                        end_time=end,
                        cost=cost,
                        currency="USD",
                        usage_amount=usage,
                        usage_unit=total.get('UsageQuantity', {}).get('Unit', 'hours'),
                        service="All Services"
                    ))
            
            logger.info(f"Fetched {len(records)} cost usage records from Cost Explorer")
            return records
            
        except Exception as e:
            logger.error(f"Error fetching cost usage data: {e}")
            raise
    
    def get_usage_summary(
        self,
        query: UsageQuery
    ) -> UsageSummary:
        """
        Get usage summary for AWS resources.
        
        Args:
            query: Usage query parameters
            
        Returns:
            Usage summary
        """
        if not self._enabled:
            raise ValueError("AWS usage adapter is not enabled")
        
        # Fetch cost usage data
        cost_records = self.get_cost_usage(
            start_time=query.start_time,
            end_time=query.end_time,
            granularity=query.granularity,
            group_by=query.group_by
        )
        
        # Calculate summary statistics
        total_cost = sum(r.cost for r in cost_records)
        total_usage = sum(r.usage_amount for r in cost_records)
        
        resource_usage_list = []
        
        # Fetch detailed resource usage if resource IDs provided
        if query.resource_ids:
            for resource_id in query.resource_ids:
                for resource_type in (query.resource_types or ["ec2"]):
                    try:
                        usage = self.get_resource_usage(
                            resource_id=resource_id,
                            resource_type=resource_type,
                            start_time=query.start_time,
                            end_time=query.end_time,
                            region=query.regions[0] if query.regions else None,
                            metrics=query.metric_names
                        )
                        resource_usage_list.append(usage)
                    except Exception as e:
                        logger.error(f"Error fetching usage for {resource_id}: {e}")
        
        # Calculate average CPU utilization across all resources
        all_cpu_values = []
        for ru in resource_usage_list:
            if ru.avg_cpu_utilization:
                all_cpu_values.append(ru.avg_cpu_utilization)
        
        avg_cpu = sum(all_cpu_values) / len(all_cpu_values) if all_cpu_values else None
        
        return UsageSummary(
            cloud_provider="aws",
            resource_type=query.resource_types[0] if query.resource_types else "all",
            region=query.regions[0] if query.regions else None,
            start_time=query.start_time,
            end_time=query.end_time,
            total_resources=len(resource_usage_list),
            total_cost=total_cost,
            average_cost_per_resource=total_cost / len(resource_usage_list) if resource_usage_list else 0,
            total_usage=total_usage,
            average_usage=total_usage / len(cost_records) if cost_records else 0,
            usage_unit="hours",
            avg_cpu_utilization=avg_cpu,
            records=cost_records[:query.max_results],
            resources=resource_usage_list,
            confidence="high"
        )


# Singleton instance
_aws_usage_adapter = None


def get_aws_usage_adapter() -> AWSUsageAdapter:
    """
    Get singleton AWS usage adapter instance.
    
    Returns:
        AWSUsageAdapter instance
    """
    global _aws_usage_adapter
    if _aws_usage_adapter is None:
        _aws_usage_adapter = AWSUsageAdapter()
    return _aws_usage_adapter

