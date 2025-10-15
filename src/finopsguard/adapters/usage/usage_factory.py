"""Usage adapter factory with automatic provider selection and caching."""

import os
import logging
from typing import Optional, Dict, Any
from datetime import datetime, timedelta

from ...types.usage import (
    ResourceUsage,
    UsageSummary,
    UsageQuery
)

logger = logging.getLogger(__name__)

# Configuration
USAGE_INTEGRATION_ENABLED = os.getenv("USAGE_INTEGRATION_ENABLED", "false").lower() == "true"


class UsageFactory:
    """
    Unified usage factory that automatically selects the appropriate adapter
    based on cloud provider.
    """
    
    def __init__(self):
        """Initialize usage factory."""
        self.enabled = USAGE_INTEGRATION_ENABLED
        
        # Lazy load adapters
        self._aws_adapter = None
        self._gcp_adapter = None
        self._azure_adapter = None
        
        # Simple in-memory cache
        self._cache = {}
        self._cache_ttl = int(os.getenv("USAGE_CACHE_TTL_SECONDS", "3600"))  # 1 hour default
    
    def _get_aws_adapter(self):
        """Get AWS usage adapter instance."""
        if self._aws_adapter is None:
            from .aws_usage import get_aws_usage_adapter
            self._aws_adapter = get_aws_usage_adapter()
        return self._aws_adapter
    
    def _get_gcp_adapter(self):
        """Get GCP usage adapter instance."""
        if self._gcp_adapter is None:
            from .gcp_usage import get_gcp_usage_adapter
            self._gcp_adapter = get_gcp_usage_adapter()
        return self._gcp_adapter
    
    def _get_azure_adapter(self):
        """Get Azure usage adapter instance."""
        if self._azure_adapter is None:
            from .azure_usage import get_azure_usage_adapter
            self._azure_adapter = get_azure_usage_adapter()
        return self._azure_adapter
    
    def _get_adapter(self, cloud_provider: str):
        """
        Get the appropriate usage adapter for a cloud provider.
        
        Args:
            cloud_provider: Cloud provider (aws, gcp, azure)
            
        Returns:
            Usage adapter instance
            
        Raises:
            ValueError: If cloud provider is unsupported
        """
        cloud = cloud_provider.lower()
        
        if cloud == "aws":
            return self._get_aws_adapter()
        elif cloud == "gcp":
            return self._get_gcp_adapter()
        elif cloud == "azure":
            return self._get_azure_adapter()
        else:
            raise ValueError(f"Unsupported cloud provider: {cloud_provider}")
    
    def _get_cache_key(self, prefix: str, **kwargs) -> str:
        """Generate cache key from parameters."""
        key_parts = [prefix]
        for k, v in sorted(kwargs.items()):
            if v is not None:
                if isinstance(v, datetime):
                    key_parts.append(f"{k}:{v.isoformat()}")
                else:
                    key_parts.append(f"{k}:{v}")
        return "|".join(key_parts)
    
    def _get_from_cache(self, key: str) -> Optional[Any]:
        """Get item from cache if not expired."""
        if key in self._cache:
            data, timestamp = self._cache[key]
            if datetime.now() - timestamp < timedelta(seconds=self._cache_ttl):
                logger.debug(f"Cache hit for key: {key}")
                return data
            else:
                # Expired
                del self._cache[key]
                logger.debug(f"Cache expired for key: {key}")
        return None
    
    def _set_cache(self, key: str, data: Any):
        """Set item in cache."""
        self._cache[key] = (data, datetime.now())
        logger.debug(f"Cached data for key: {key}")
    
    def is_available(self, cloud_provider: str) -> bool:
        """
        Check if usage integration is available for a cloud provider.
        
        Args:
            cloud_provider: Cloud provider (aws, gcp, azure)
            
        Returns:
            True if available
        """
        if not self.enabled:
            return False
        
        try:
            adapter = self._get_adapter(cloud_provider)
            return adapter.is_available()
        except Exception as e:
            logger.warning(f"Usage adapter not available for {cloud_provider}: {e}")
            return False
    
    def get_resource_usage(
        self,
        cloud_provider: str,
        resource_id: str,
        resource_type: str,
        start_time: datetime,
        end_time: datetime,
        region: Optional[str] = None,
        metrics: Optional[list] = None,
        use_cache: bool = True
    ) -> Optional[ResourceUsage]:
        """
        Get usage metrics for a specific resource.
        
        Args:
            cloud_provider: Cloud provider (aws, gcp, azure)
            resource_id: Resource identifier
            resource_type: Type of resource
            start_time: Start of time range
            end_time: End of time range
            region: Cloud region
            metrics: List of specific metrics to fetch
            use_cache: Whether to use cached data
            
        Returns:
            ResourceUsage object or None if not available
        """
        if not self.enabled:
            logger.debug("Usage integration is disabled")
            return None
        
        # Check cache
        if use_cache:
            cache_key = self._get_cache_key(
                "resource_usage",
                cloud=cloud_provider,
                resource_id=resource_id,
                resource_type=resource_type,
                start=start_time,
                end=end_time,
                region=region
            )
            cached = self._get_from_cache(cache_key)
            if cached:
                return cached
        
        try:
            adapter = self._get_adapter(cloud_provider)
            
            if not adapter.is_available():
                logger.warning(f"Usage adapter not available for {cloud_provider}")
                return None
            
            usage = adapter.get_resource_usage(
                resource_id=resource_id,
                resource_type=resource_type,
                start_time=start_time,
                end_time=end_time,
                region=region,
                metrics=metrics
            )
            
            # Cache result
            if use_cache:
                self._set_cache(cache_key, usage)
            
            logger.info(f"Fetched resource usage for {cloud_provider} {resource_id}")
            return usage
            
        except Exception as e:
            logger.error(f"Error fetching resource usage: {e}")
            return None
    
    def get_cost_usage(
        self,
        cloud_provider: str,
        start_time: datetime,
        end_time: datetime,
        granularity: str = "DAILY",
        group_by: Optional[list] = None,
        filters: Optional[Dict[str, Any]] = None,
        use_cache: bool = True
    ) -> Optional[list]:
        """
        Get cost and usage data from billing APIs.
        
        Args:
            cloud_provider: Cloud provider (aws, gcp, azure)
            start_time: Start of time range
            end_time: End of time range
            granularity: Time granularity (HOURLY, DAILY, MONTHLY)
            group_by: Dimensions to group by
            filters: Additional filters
            use_cache: Whether to use cached data
            
        Returns:
            List of CostUsageRecord objects or None if not available
        """
        if not self.enabled:
            logger.debug("Usage integration is disabled")
            return None
        
        # Check cache
        if use_cache:
            cache_key = self._get_cache_key(
                "cost_usage",
                cloud=cloud_provider,
                start=start_time,
                end=end_time,
                granularity=granularity,
                group_by=str(group_by) if group_by else None
            )
            cached = self._get_from_cache(cache_key)
            if cached:
                return cached
        
        try:
            adapter = self._get_adapter(cloud_provider)
            
            if not adapter.is_available():
                logger.warning(f"Usage adapter not available for {cloud_provider}")
                return None
            
            records = adapter.get_cost_usage(
                start_time=start_time,
                end_time=end_time,
                granularity=granularity,
                group_by=group_by,
                filters=filters
            )
            
            # Cache result
            if use_cache:
                self._set_cache(cache_key, records)
            
            logger.info(f"Fetched {len(records)} cost usage records for {cloud_provider}")
            return records
            
        except Exception as e:
            logger.error(f"Error fetching cost usage data: {e}")
            return None
    
    def get_usage_summary(
        self,
        query: UsageQuery,
        use_cache: bool = True
    ) -> Optional[UsageSummary]:
        """
        Get usage summary for a query.
        
        Args:
            query: Usage query parameters
            use_cache: Whether to use cached data
            
        Returns:
            UsageSummary object or None if not available
        """
        if not self.enabled:
            logger.debug("Usage integration is disabled")
            return None
        
        # Check cache
        if use_cache:
            cache_key = self._get_cache_key(
                "usage_summary",
                cloud=query.cloud_provider,
                start=query.start_time,
                end=query.end_time,
                granularity=query.granularity
            )
            cached = self._get_from_cache(cache_key)
            if cached:
                return cached
        
        try:
            adapter = self._get_adapter(query.cloud_provider)
            
            if not adapter.is_available():
                logger.warning(f"Usage adapter not available for {query.cloud_provider}")
                return None
            
            summary = adapter.get_usage_summary(query)
            
            # Cache result
            if use_cache:
                self._set_cache(cache_key, summary)
            
            logger.info(f"Generated usage summary for {query.cloud_provider}")
            return summary
            
        except Exception as e:
            logger.error(f"Error generating usage summary: {e}")
            return None
    
    def clear_cache(self):
        """Clear all cached data."""
        self._cache.clear()
        logger.info("Usage cache cleared")


# Global instance
_usage_factory = None


def get_usage_factory() -> UsageFactory:
    """
    Get global usage factory instance.
    
    Returns:
        UsageFactory instance
    """
    global _usage_factory
    if _usage_factory is None:
        _usage_factory = UsageFactory()
    return _usage_factory

