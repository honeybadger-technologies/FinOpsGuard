"""GCP Cloud Monitoring and Billing usage adapter."""

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


class GCPUsageAdapter(UsageAdapter):
    """GCP usage adapter using Cloud Monitoring and Billing APIs."""
    
    def __init__(self):
        """Initialize GCP usage adapter."""
        super().__init__("gcp")
        self._monitoring = None
        self._billing = None
        self._enabled = os.getenv("GCP_USAGE_ENABLED", "false").lower() == "true"
        self._project_id = os.getenv("GCP_PROJECT_ID")
        self._billing_account_id = os.getenv("GCP_BILLING_ACCOUNT_ID")
    
    def _get_monitoring_client(self):
        """Lazy load Cloud Monitoring client."""
        if self._monitoring is None:
            try:
                from google.cloud import monitoring_v3
                self._monitoring = monitoring_v3.MetricServiceClient()
                logger.info("GCP Cloud Monitoring client initialized")
            except ImportError:
                logger.error("google-cloud-monitoring not installed. Install with: pip install google-cloud-monitoring")
                raise
            except Exception as e:
                logger.error(f"Error initializing Cloud Monitoring client: {e}")
                raise
        return self._monitoring
    
    def _get_billing_client(self):
        """Lazy load Cloud Billing client."""
        if self._billing is None:
            try:
                from google.cloud import bigquery
                # Cloud Billing exports data to BigQuery
                self._billing = bigquery.Client(project=self._project_id)
                logger.info("GCP BigQuery client initialized for billing data")
            except ImportError:
                logger.error("google-cloud-bigquery not installed. Install with: pip install google-cloud-bigquery")
                raise
            except Exception as e:
                logger.error(f"Error initializing BigQuery client: {e}")
                raise
        return self._billing
    
    def is_available(self) -> bool:
        """Check if GCP usage adapter is available."""
        if not self._enabled:
            return False
        
        if not self._project_id:
            logger.warning("GCP_PROJECT_ID not set")
            return False
        
        try:
            # Check if google-cloud-monitoring is installed
            import google.cloud.monitoring_v3
            return True
        except ImportError:
            logger.warning("google-cloud-monitoring not installed")
            return False
        except Exception as e:
            logger.warning(f"GCP credentials not configured: {e}")
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
        Get Cloud Monitoring metrics for a specific GCP resource.
        
        Args:
            resource_id: GCP resource ID
            resource_type: Resource type (gce_instance, cloudsql_database, etc.)
            start_time: Start time
            end_time: End time
            region: GCP region/zone
            metrics: Specific metrics to fetch
            
        Returns:
            ResourceUsage object
        """
        if not self._enabled:
            raise ValueError("GCP usage adapter is not enabled")
        
        monitoring = self._get_monitoring_client()
        project_name = f"projects/{self._project_id}"
        
        # Map resource types to metric prefixes
        metric_map = {
            "gce_instance": "compute.googleapis.com/instance",
            "cloudsql_database": "cloudsql.googleapis.com/database",
            "gcs_bucket": "storage.googleapis.com/storage",
            "gke_container": "container.googleapis.com",
        }
        
        metric_prefix = metric_map.get(resource_type, "compute.googleapis.com/instance")
        
        # Default metrics per resource type
        default_metrics = {
            "gce_instance": ["cpu/utilization", "network/received_bytes_count", "network/sent_bytes_count"],
            "cloudsql_database": ["database/cpu/utilization", "database/memory/utilization"],
            "gcs_bucket": ["storage/total_bytes", "api/request_count"],
            "gke_container": ["container/cpu/usage_time", "container/memory/usage_bytes"],
        }
        
        metrics_to_fetch = metrics or default_metrics.get(resource_type, ["cpu/utilization"])
        
        usage_metrics = []
        
        for metric_name in metrics_to_fetch:
            try:
                # Build metric type
                if not metric_name.startswith(metric_prefix):
                    full_metric = f"{metric_prefix}/{metric_name}"
                else:
                    full_metric = metric_name
                
                # Create time interval
                from google.cloud.monitoring_v3 import query
                interval = query.Interval(
                    end_time=end_time,
                    start_time=start_time
                )
                
                # Build filter
                filter_str = f'resource.type = "{resource_type}" AND metric.type = "{full_metric}"'
                if resource_id:
                    filter_str += f' AND resource.labels.instance_id = "{resource_id}"'
                
                # Query metrics
                results = monitoring.list_time_series(
                    request={
                        "name": project_name,
                        "filter": filter_str,
                        "interval": {
                            "start_time": start_time,
                            "end_time": end_time
                        },
                        "view": "FULL"
                    }
                )
                
                for result in results:
                    for point in result.points:
                        value = point.value.double_value or point.value.int64_value or 0
                        
                        usage_metrics.append(UsageMetric(
                            timestamp=point.interval.end_time,
                            value=value,
                            unit=result.metric.type.split('/')[-1],
                            metric_name=metric_name,
                            dimensions=dict(result.resource.labels)
                        ))
                
                logger.debug(f"Fetched metrics for {metric_name}")
                
            except Exception as e:
                logger.error(f"Error fetching metric {metric_name}: {e}")
        
        # Calculate summary statistics
        cpu_metrics = [m for m in usage_metrics if 'cpu' in m.metric_name.lower()]
        memory_metrics = [m for m in usage_metrics if 'memory' in m.metric_name.lower()]
        network_rx = [m for m in usage_metrics if 'received' in m.metric_name.lower()]
        network_tx = [m for m in usage_metrics if 'sent' in m.metric_name.lower()]
        
        avg_cpu = sum(m.value for m in cpu_metrics) / len(cpu_metrics) if cpu_metrics else None
        avg_memory = sum(m.value for m in memory_metrics) / len(memory_metrics) if memory_metrics else None
        avg_net_in = sum(m.value for m in network_rx) / len(network_rx) / (1024**3) if network_rx else None
        avg_net_out = sum(m.value for m in network_tx) / len(network_tx) / (1024**3) if network_tx else None
        
        return ResourceUsage(
            resource_id=resource_id,
            resource_type=resource_type,
            region=region or "unknown",
            cloud_provider="gcp",
            start_time=start_time,
            end_time=end_time,
            metrics=usage_metrics,
            avg_cpu_utilization=avg_cpu * 100 if avg_cpu and avg_cpu <= 1 else avg_cpu,  # Convert to percentage
            avg_memory_utilization=avg_memory,
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
        Get cost and usage data from GCP Billing (via BigQuery export).
        
        Note: Requires Cloud Billing export to BigQuery to be configured.
        
        Args:
            start_time: Start date
            end_time: End date
            granularity: DAILY or MONTHLY
            group_by: Group by dimensions (service, project, region, etc.)
            filters: Additional filters
            
        Returns:
            List of cost usage records
        """
        if not self._enabled:
            raise ValueError("GCP usage adapter is not enabled")
        
        if not self._billing_account_id:
            logger.warning("GCP_BILLING_ACCOUNT_ID not set, returning empty results")
            return []
        
        bigquery = self._get_billing_client()
        
        # Build BigQuery query for billing data
        # Assumes billing data is exported to BigQuery dataset
        dataset_id = os.getenv("GCP_BILLING_DATASET", "billing_export")
        table_id = os.getenv("GCP_BILLING_TABLE", "gcp_billing_export_v1")
        
        # Format dates
        start_date = start_time.strftime('%Y-%m-%d')
        end_date = end_time.strftime('%Y-%m-%d')
        
        # Build group by clause
        group_by_clause = ""
        select_dimensions = ""
        if group_by:
            group_by_fields = []
            for dim in group_by:
                if dim.lower() == "service":
                    group_by_fields.append("service.description")
                    select_dimensions += ", service.description as service"
                elif dim.lower() == "project":
                    group_by_fields.append("project.id")
                    select_dimensions += ", project.id as project_id"
                elif dim.lower() == "region":
                    group_by_fields.append("location.region")
                    select_dimensions += ", location.region as region"
            if group_by_fields:
                group_by_clause = f"GROUP BY {', '.join(group_by_fields)}"
        
        query = f"""
        SELECT
            DATE(usage_start_time) as usage_date,
            SUM(cost) as total_cost,
            SUM(usage.amount) as usage_amount,
            usage.unit as usage_unit
            {select_dimensions}
        FROM `{self._project_id}.{dataset_id}.{table_id}`
        WHERE DATE(usage_start_time) >= '{start_date}'
          AND DATE(usage_start_time) < '{end_date}'
        {group_by_clause}
        ORDER BY usage_date
        """
        
        try:
            query_job = bigquery.query(query)
            results = query_job.result()
            
            records = []
            for row in results:
                dimensions = {}
                service_name = "Unknown"
                region = None
                
                if group_by:
                    if "service" in [g.lower() for g in group_by]:
                        service_name = row.get('service', 'Unknown')
                        dimensions['service'] = service_name
                    if "project" in [g.lower() for g in group_by]:
                        dimensions['project'] = row.get('project_id', 'Unknown')
                    if "region" in [g.lower() for g in group_by]:
                        region = row.get('region')
                        dimensions['region'] = region
                
                usage_date = row['usage_date']
                
                records.append(CostUsageRecord(
                    date=usage_date,
                    start_time=datetime.combine(usage_date, datetime.min.time()),
                    end_time=datetime.combine(usage_date, datetime.max.time()),
                    cost=float(row['total_cost']),
                    currency="USD",
                    usage_amount=float(row.get('usage_amount', 0)),
                    usage_unit=row.get('usage_unit', 'hours'),
                    service=service_name,
                    region=region,
                    dimensions=dimensions
                ))
            
            logger.info(f"Fetched {len(records)} cost usage records from BigQuery")
            return records
            
        except Exception as e:
            logger.error(f"Error fetching cost usage data from BigQuery: {e}")
            logger.info("Note: Ensure Cloud Billing export to BigQuery is configured")
            return []
    
    def get_usage_summary(
        self,
        query: UsageQuery
    ) -> UsageSummary:
        """
        Get usage summary for GCP resources.
        
        Args:
            query: Usage query parameters
            
        Returns:
            Usage summary
        """
        if not self._enabled:
            raise ValueError("GCP usage adapter is not enabled")
        
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
                for resource_type in (query.resource_types or ["gce_instance"]):
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
            cloud_provider="gcp",
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
_gcp_usage_adapter = None


def get_gcp_usage_adapter() -> GCPUsageAdapter:
    """
    Get singleton GCP usage adapter instance.
    
    Returns:
        GCPUsageAdapter instance
    """
    global _gcp_usage_adapter
    if _gcp_usage_adapter is None:
        _gcp_usage_adapter = GCPUsageAdapter()
    return _gcp_usage_adapter

