"""Base interface for usage adapters."""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from datetime import datetime

from finopsguard.types.usage import (
    ResourceUsage,
    CostUsageRecord,
    UsageSummary,
    UsageQuery
)


class UsageAdapter(ABC):
    """Abstract base class for cloud usage adapters."""
    
    def __init__(self, cloud_provider: str):
        """
        Initialize usage adapter.
        
        Args:
            cloud_provider: Cloud provider name (aws, gcp, azure)
        """
        self.cloud_provider = cloud_provider
    
    @abstractmethod
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
        Get usage metrics for a specific resource.
        
        Args:
            resource_id: Resource identifier
            resource_type: Type of resource (ec2, rds, gcs_bucket, etc.)
            start_time: Start of time range
            end_time: End of time range
            region: Cloud region
            metrics: List of specific metrics to fetch
            
        Returns:
            ResourceUsage object with metrics
        """
        pass
    
    @abstractmethod
    def get_cost_usage(
        self,
        start_time: datetime,
        end_time: datetime,
        granularity: str = "DAILY",
        group_by: Optional[List[str]] = None,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[CostUsageRecord]:
        """
        Get cost and usage data from billing APIs.
        
        Args:
            start_time: Start of time range
            end_time: End of time range
            granularity: Time granularity (HOURLY, DAILY, MONTHLY)
            group_by: Dimensions to group by (service, region, etc.)
            filters: Additional filters
            
        Returns:
            List of cost usage records
        """
        pass
    
    @abstractmethod
    def get_usage_summary(
        self,
        query: UsageQuery
    ) -> UsageSummary:
        """
        Get usage summary for a query.
        
        Args:
            query: Usage query parameters
            
        Returns:
            Usage summary
        """
        pass
    
    def is_available(self) -> bool:
        """
        Check if the adapter is available and properly configured.
        
        Returns:
            True if adapter can be used
        """
        return True

