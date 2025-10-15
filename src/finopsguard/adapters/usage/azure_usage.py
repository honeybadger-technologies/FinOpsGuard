"""Azure Monitor and Cost Management usage adapter."""

import os
import logging
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any

from ...types.usage import (
    ResourceUsage,
    CostUsageRecord,
    UsageSummary,
    UsageQuery,
    UsageMetric
)
from .base import UsageAdapter

logger = logging.getLogger(__name__)


class AzureUsageAdapter(UsageAdapter):
    """Azure usage adapter using Azure Monitor and Cost Management APIs."""
    
    def __init__(self):
        """Initialize Azure usage adapter."""
        super().__init__("azure")
        self._monitor = None
        self._cost_mgmt = None
        self._enabled = os.getenv("AZURE_USAGE_ENABLED", "false").lower() == "true"
        self._subscription_id = os.getenv("AZURE_SUBSCRIPTION_ID")
        self._tenant_id = os.getenv("AZURE_TENANT_ID")
    
    def _get_credential(self):
        """Get Azure credential."""
        try:
            from azure.identity import DefaultAzureCredential
            return DefaultAzureCredential()
        except ImportError:
            logger.error("azure-identity not installed. Install with: pip install azure-identity")
            raise
        except Exception as e:
            logger.error(f"Error creating Azure credential: {e}")
            raise
    
    def _get_monitor_client(self):
        """Lazy load Azure Monitor client."""
        if self._monitor is None:
            try:
                from azure.mgmt.monitor import MonitorManagementClient
                credential = self._get_credential()
                self._monitor = MonitorManagementClient(credential, self._subscription_id)
                logger.info("Azure Monitor client initialized")
            except ImportError:
                logger.error("azure-mgmt-monitor not installed. Install with: pip install azure-mgmt-monitor")
                raise
            except Exception as e:
                logger.error(f"Error initializing Azure Monitor client: {e}")
                raise
        return self._monitor
    
    def _get_cost_mgmt_client(self):
        """Lazy load Azure Cost Management client."""
        if self._cost_mgmt is None:
            try:
                from azure.mgmt.costmanagement import CostManagementClient
                credential = self._get_credential()
                self._cost_mgmt = CostManagementClient(credential)
                logger.info("Azure Cost Management client initialized")
            except ImportError:
                logger.error("azure-mgmt-costmanagement not installed. Install with: pip install azure-mgmt-costmanagement")
                raise
            except Exception as e:
                logger.error(f"Error initializing Azure Cost Management client: {e}")
                raise
        return self._cost_mgmt
    
    def is_available(self) -> bool:
        """Check if Azure usage adapter is available."""
        if not self._enabled:
            return False
        
        if not self._subscription_id:
            logger.warning("AZURE_SUBSCRIPTION_ID not set")
            return False
        
        try:
            # Check if azure-mgmt-monitor is installed
            import azure.mgmt.monitor
            return True
        except ImportError:
            logger.warning("azure-mgmt-monitor not installed")
            return False
        except Exception as e:
            logger.warning(f"Azure credentials not configured: {e}")
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
        Get Azure Monitor metrics for a specific Azure resource.
        
        Args:
            resource_id: Azure resource ID (full ARM ID)
            resource_type: Resource type (virtual_machine, sql_database, etc.)
            start_time: Start time
            end_time: End time
            region: Azure region
            metrics: Specific metrics to fetch
            
        Returns:
            ResourceUsage object
        """
        if not self._enabled:
            raise ValueError("Azure usage adapter is not enabled")
        
        monitor = self._get_monitor_client()
        
        # Default metrics per resource type
        default_metrics_map = {
            "virtual_machine": ["Percentage CPU", "Network In Total", "Network Out Total"],
            "sql_database": ["cpu_percent", "connection_successful", "storage_percent"],
            "storage_account": ["Transactions", "UsedCapacity", "Availability"],
            "app_service": ["CpuTime", "Requests", "ResponseTime"],
        }
        
        metrics_to_fetch = metrics or default_metrics_map.get(resource_type, ["Percentage CPU"])
        
        usage_metrics = []
        
        # Format timespan for Azure Monitor
        timespan = f"{start_time.isoformat()}/{end_time.isoformat()}"
        
        for metric_name in metrics_to_fetch:
            try:
                # Query metrics
                metrics_data = monitor.metrics.list(
                    resource_uri=resource_id,
                    timespan=timespan,
                    interval='PT1H',  # 1 hour
                    metricnames=metric_name,
                    aggregation='Average'
                )
                
                for metric in metrics_data.value:
                    for timeseries in metric.timeseries:
                        for data_point in timeseries.data:
                            if data_point.average is not None:
                                usage_metrics.append(UsageMetric(
                                    timestamp=data_point.time_stamp,
                                    value=data_point.average,
                                    unit=metric.unit.value if metric.unit else "Count",
                                    metric_name=metric_name,
                                    dimensions={}
                                ))
                
                logger.debug(f"Fetched metrics for {metric_name}")
                
            except Exception as e:
                logger.error(f"Error fetching metric {metric_name}: {e}")
        
        # Calculate summary statistics
        cpu_metrics = [m for m in usage_metrics if 'cpu' in m.metric_name.lower()]
        network_in_metrics = [m for m in usage_metrics if 'network in' in m.metric_name.lower()]
        network_out_metrics = [m for m in usage_metrics if 'network out' in m.metric_name.lower()]
        
        avg_cpu = sum(m.value for m in cpu_metrics) / len(cpu_metrics) if cpu_metrics else None
        avg_net_in = sum(m.value for m in network_in_metrics) / len(network_in_metrics) / (1024**3) if network_in_metrics else None
        avg_net_out = sum(m.value for m in network_out_metrics) / len(network_out_metrics) / (1024**3) if network_out_metrics else None
        
        return ResourceUsage(
            resource_id=resource_id,
            resource_type=resource_type,
            region=region or "unknown",
            cloud_provider="azure",
            start_time=start_time,
            end_time=end_time,
            metrics=usage_metrics,
            avg_cpu_utilization=avg_cpu,
            avg_network_in_gb=avg_net_in,
            avg_network_out_gb=avg_net_out
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
        Get cost and usage data from Azure Cost Management.
        
        Args:
            start_time: Start date
            end_time: End date
            granularity: Daily or Monthly
            group_by: Group by dimensions (ResourceType, ResourceGroupName, etc.)
            filters: Additional filters
            
        Returns:
            List of cost usage records
        """
        if not self._enabled:
            raise ValueError("Azure usage adapter is not enabled")
        
        cost_mgmt = self._get_cost_mgmt_client()
        
        # Build scope for subscription
        scope = f"/subscriptions/{self._subscription_id}"
        
        # Build query parameters
        from azure.mgmt.costmanagement.models import (
            QueryDefinition,
            QueryTimePeriod,
            QueryDataset,
            QueryAggregation,
            QueryGrouping
        )
        
        # Map granularity
        granularity_map = {
            "DAILY": "Daily",
            "MONTHLY": "Monthly"
        }
        azure_granularity = granularity_map.get(granularity, "Daily")
        
        # Build aggregations
        aggregations = {
            "totalCost": QueryAggregation(name="Cost", function="Sum")
        }
        
        # Build groupings
        groupings = []
        if group_by:
            dimension_map = {
                "service": "ServiceName",
                "region": "ResourceLocation",
                "resource_group": "ResourceGroupName",
                "resource_type": "ResourceType"
            }
            for dim in group_by:
                azure_dim = dimension_map.get(dim.lower(), dim)
                groupings.append(QueryGrouping(
                    type="Dimension",
                    name=azure_dim
                ))
        
        # Build query
        query = QueryDefinition(
            type="Usage",
            timeframe="Custom",
            time_period=QueryTimePeriod(
                from_property=start_time,
                to=end_time
            ),
            dataset=QueryDataset(
                granularity=azure_granularity,
                aggregation=aggregations,
                grouping=groupings if groupings else None
            )
        )
        
        try:
            # Execute query
            result = cost_mgmt.query.usage(scope=scope, parameters=query)
            
            records = []
            
            if result.rows:
                # Parse column names
                columns = [col.name for col in result.columns]
                
                for row in result.rows:
                    row_dict = dict(zip(columns, row))
                    
                    # Extract data
                    cost = float(row_dict.get('Cost', 0))
                    usage_date = row_dict.get('UsageDate')
                    
                    # Parse date
                    if isinstance(usage_date, int):
                        # Azure returns date as YYYYMMDD integer
                        date_str = str(usage_date)
                        usage_datetime = datetime.strptime(date_str, '%Y%m%d')
                    else:
                        usage_datetime = datetime.now()
                    
                    dimensions = {}
                    service_name = "Unknown"
                    region = None
                    
                    # Extract grouping dimensions
                    for dim in (group_by or []):
                        dim_map = {
                            "service": "ServiceName",
                            "region": "ResourceLocation",
                            "resource_group": "ResourceGroupName"
                        }
                        col_name = dim_map.get(dim.lower(), dim)
                        if col_name in row_dict:
                            value = row_dict[col_name]
                            dimensions[dim] = value
                            if dim.lower() == "service":
                                service_name = value
                            elif dim.lower() == "region":
                                region = value
                    
                    records.append(CostUsageRecord(
                        date=usage_datetime,
                        start_time=usage_datetime,
                        end_time=usage_datetime + timedelta(days=1),
                        cost=cost,
                        currency=row_dict.get('Currency', 'USD'),
                        usage_amount=float(row_dict.get('UsageQuantity', 0)),
                        usage_unit="hours",
                        service=service_name,
                        region=region,
                        dimensions=dimensions
                    ))
            
            logger.info(f"Fetched {len(records)} cost usage records from Azure Cost Management")
            return records
            
        except Exception as e:
            logger.error(f"Error fetching cost usage data: {e}")
            return []
    
    def get_usage_summary(
        self,
        query: UsageQuery
    ) -> UsageSummary:
        """
        Get usage summary for Azure resources.
        
        Args:
            query: Usage query parameters
            
        Returns:
            Usage summary
        """
        if not self._enabled:
            raise ValueError("Azure usage adapter is not enabled")
        
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
                for resource_type in (query.resource_types or ["virtual_machine"]):
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
        
        # Calculate average CPU utilization
        all_cpu_values = []
        for ru in resource_usage_list:
            if ru.avg_cpu_utilization:
                all_cpu_values.append(ru.avg_cpu_utilization)
        
        avg_cpu = sum(all_cpu_values) / len(all_cpu_values) if all_cpu_values else None
        
        return UsageSummary(
            cloud_provider="azure",
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
            confidence="high" if cost_records else "low"
        )


# Singleton instance
_azure_usage_adapter = None


def get_azure_usage_adapter() -> AzureUsageAdapter:
    """
    Get singleton Azure usage adapter instance.
    
    Returns:
        AzureUsageAdapter instance
    """
    global _azure_usage_adapter
    if _azure_usage_adapter is None:
        _azure_usage_adapter = AzureUsageAdapter()
    return _azure_usage_adapter

