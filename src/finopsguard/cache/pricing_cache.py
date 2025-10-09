"""Caching layer for pricing data."""

import hashlib
import json
from typing import Any, Dict, List, Optional
import logging

from .redis_client import get_cache

logger = logging.getLogger(__name__)

# Cache TTLs (in seconds)
PRICING_TTL = 24 * 60 * 60  # 24 hours - pricing data changes infrequently
PRICE_CATALOG_TTL = 12 * 60 * 60  # 12 hours
RESOURCE_PRICE_TTL = 24 * 60 * 60  # 24 hours


class PricingCache:
    """Cache layer for pricing data."""
    
    def __init__(self):
        """Initialize pricing cache."""
        self.cache = get_cache()
        self.prefix = "pricing"
    
    def _make_key(self, *parts: str) -> str:
        """
        Create cache key from parts.
        
        Args:
            *parts: Key components
            
        Returns:
            Cache key string
        """
        return f"{self.prefix}:{':'.join(str(p) for p in parts)}"
    
    def _hash_params(self, params: Dict[str, Any]) -> str:
        """
        Create deterministic hash from parameters.
        
        Args:
            params: Parameters dict
            
        Returns:
            Hash string
        """
        # Sort keys for consistency
        sorted_json = json.dumps(params, sort_keys=True)
        return hashlib.md5(sorted_json.encode()).hexdigest()[:16]
    
    def get_instance_price(
        self,
        cloud: str,
        instance_type: str,
        region: str = None
    ) -> Optional[Dict[str, Any]]:
        """
        Get cached instance price.
        
        Args:
            cloud: Cloud provider (aws, gcp, azure)
            instance_type: Instance type
            region: Region (optional)
            
        Returns:
            Cached price data or None
        """
        key = self._make_key("instance", cloud, instance_type, region or "default")
        return self.cache.get(key)
    
    def set_instance_price(
        self,
        cloud: str,
        instance_type: str,
        price_data: Dict[str, Any],
        region: str = None
    ) -> bool:
        """
        Cache instance price.
        
        Args:
            cloud: Cloud provider
            instance_type: Instance type
            price_data: Price data to cache
            region: Region (optional)
            
        Returns:
            True if cached successfully
        """
        key = self._make_key("instance", cloud, instance_type, region or "default")
        return self.cache.set(key, price_data, ttl=RESOURCE_PRICE_TTL)
    
    def get_database_price(
        self,
        cloud: str,
        db_type: str,
        region: str = None
    ) -> Optional[Dict[str, Any]]:
        """
        Get cached database price.
        
        Args:
            cloud: Cloud provider
            db_type: Database type
            region: Region (optional)
            
        Returns:
            Cached price data or None
        """
        key = self._make_key("database", cloud, db_type, region or "default")
        return self.cache.get(key)
    
    def set_database_price(
        self,
        cloud: str,
        db_type: str,
        price_data: Dict[str, Any],
        region: str = None
    ) -> bool:
        """
        Cache database price.
        
        Args:
            cloud: Cloud provider
            db_type: Database type
            price_data: Price data to cache
            region: Region (optional)
            
        Returns:
            True if cached successfully
        """
        key = self._make_key("database", cloud, db_type, region or "default")
        return self.cache.set(key, price_data, ttl=RESOURCE_PRICE_TTL)
    
    def get_storage_price(
        self,
        cloud: str,
        storage_class: str,
        region: str = None
    ) -> Optional[Dict[str, Any]]:
        """
        Get cached storage price.
        
        Args:
            cloud: Cloud provider
            storage_class: Storage class
            region: Region (optional)
            
        Returns:
            Cached price data or None
        """
        key = self._make_key("storage", cloud, storage_class, region or "default")
        return self.cache.get(key)
    
    def set_storage_price(
        self,
        cloud: str,
        storage_class: str,
        price_data: Dict[str, Any],
        region: str = None
    ) -> bool:
        """
        Cache storage price.
        
        Args:
            cloud: Cloud provider
            storage_class: Storage class
            price_data: Price data to cache
            region: Region (optional)
            
        Returns:
            True if cached successfully
        """
        key = self._make_key("storage", cloud, storage_class, region or "default")
        return self.cache.set(key, price_data, ttl=RESOURCE_PRICE_TTL)
    
    def get_price_catalog(
        self,
        cloud: str,
        instance_types: Optional[List[str]] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Get cached price catalog.
        
        Args:
            cloud: Cloud provider
            instance_types: Optional list of instance types to filter
            
        Returns:
            Cached catalog or None
        """
        params_hash = self._hash_params({
            "instance_types": instance_types or []
        })
        key = self._make_key("catalog", cloud, params_hash)
        return self.cache.get(key)
    
    def set_price_catalog(
        self,
        cloud: str,
        catalog_data: Dict[str, Any],
        instance_types: Optional[List[str]] = None
    ) -> bool:
        """
        Cache price catalog.
        
        Args:
            cloud: Cloud provider
            catalog_data: Catalog data to cache
            instance_types: Optional list of instance types to filter
            
        Returns:
            True if cached successfully
        """
        params_hash = self._hash_params({
            "instance_types": instance_types or []
        })
        key = self._make_key("catalog", cloud, params_hash)
        return self.cache.set(key, catalog_data, ttl=PRICE_CATALOG_TTL)
    
    def invalidate_cloud(self, cloud: str) -> int:
        """
        Invalidate all cached pricing for a cloud provider.
        
        Args:
            cloud: Cloud provider
            
        Returns:
            Number of keys invalidated
        """
        pattern = self._make_key("*", cloud, "*")
        count = self.cache.delete_pattern(pattern)
        logger.info(f"Invalidated {count} pricing cache entries for {cloud}")
        return count
    
    def invalidate_all(self) -> int:
        """
        Invalidate all pricing cache.
        
        Returns:
            Number of keys invalidated
        """
        pattern = self._make_key("*")
        count = self.cache.delete_pattern(pattern)
        logger.info(f"Invalidated all {count} pricing cache entries")
        return count


# Global instance
_pricing_cache_instance: Optional[PricingCache] = None


def get_pricing_cache() -> PricingCache:
    """
    Get global pricing cache instance.
    
    Returns:
        PricingCache instance
    """
    global _pricing_cache_instance
    if _pricing_cache_instance is None:
        _pricing_cache_instance = PricingCache()
    return _pricing_cache_instance

