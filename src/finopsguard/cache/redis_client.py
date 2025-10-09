"""Redis cache client for FinOpsGuard."""

import json
import os
from typing import Any, Optional, Union
import redis
from redis.connection import ConnectionPool
import logging

logger = logging.getLogger(__name__)


class RedisCache:
    """Redis cache client with connection pooling and error handling."""
    
    def __init__(
        self,
        host: str = None,
        port: int = None,
        db: int = None,
        password: str = None,
        max_connections: int = 50,
        decode_responses: bool = True
    ):
        """
        Initialize Redis cache client.
        
        Args:
            host: Redis host (default from env: REDIS_HOST or 'localhost')
            port: Redis port (default from env: REDIS_PORT or 6379)
            db: Redis database (default from env: REDIS_DB or 0)
            password: Redis password (default from env: REDIS_PASSWORD)
            max_connections: Maximum connections in pool
            decode_responses: Decode responses to strings
        """
        self.host = host or os.getenv('REDIS_HOST', 'localhost')
        self.port = int(port or os.getenv('REDIS_PORT', 6379))
        self.db = int(db or os.getenv('REDIS_DB', 0))
        self.password = password or os.getenv('REDIS_PASSWORD')
        self.enabled = os.getenv('REDIS_ENABLED', 'false').lower() == 'true'
        
        self._pool: Optional[ConnectionPool] = None
        self._client: Optional[redis.Redis] = None
        
        if self.enabled:
            try:
                self._pool = ConnectionPool(
                    host=self.host,
                    port=self.port,
                    db=self.db,
                    password=self.password,
                    max_connections=max_connections,
                    decode_responses=decode_responses,
                    socket_connect_timeout=5,
                    socket_timeout=5,
                    retry_on_timeout=True
                )
                self._client = redis.Redis(connection_pool=self._pool)
                # Test connection
                self._client.ping()
                logger.info(f"Redis cache enabled: {self.host}:{self.port}/{self.db}")
            except Exception as e:
                logger.warning(f"Redis connection failed: {e}. Caching disabled.")
                self.enabled = False
                self._client = None
        else:
            logger.info("Redis cache disabled")
    
    def _is_available(self) -> bool:
        """Check if Redis is available."""
        if not self.enabled or not self._client:
            return False
        try:
            self._client.ping()
            return True
        except Exception as e:
            logger.warning(f"Redis ping failed: {e}")
            return False
    
    def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache.
        
        Args:
            key: Cache key
            
        Returns:
            Cached value or None if not found or error
        """
        if not self._is_available():
            return None
        
        try:
            value = self._client.get(key)
            if value is None:
                return None
            
            # Try to deserialize JSON
            try:
                return json.loads(value)
            except (json.JSONDecodeError, TypeError):
                return value
        except Exception as e:
            logger.error(f"Cache get error for key '{key}': {e}")
            return None
    
    def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None
    ) -> bool:
        """
        Set value in cache.
        
        Args:
            key: Cache key
            value: Value to cache (will be JSON serialized if dict/list)
            ttl: Time to live in seconds (None for no expiration)
            
        Returns:
            True if successful, False otherwise
        """
        if not self._is_available():
            return False
        
        try:
            # Serialize to JSON if needed
            if isinstance(value, (dict, list)):
                value = json.dumps(value)
            elif not isinstance(value, (str, bytes, int, float)):
                value = str(value)
            
            if ttl is not None:
                self._client.setex(key, ttl, value)
            else:
                self._client.set(key, value)
            return True
        except Exception as e:
            logger.error(f"Cache set error for key '{key}': {e}")
            return False
    
    def delete(self, key: str) -> bool:
        """
        Delete key from cache.
        
        Args:
            key: Cache key
            
        Returns:
            True if key was deleted, False otherwise
        """
        if not self._is_available():
            return False
        
        try:
            self._client.delete(key)
            return True
        except Exception as e:
            logger.error(f"Cache delete error for key '{key}': {e}")
            return False
    
    def delete_pattern(self, pattern: str) -> int:
        """
        Delete all keys matching pattern.
        
        Args:
            pattern: Key pattern (e.g., 'pricing:*')
            
        Returns:
            Number of keys deleted
        """
        if not self._is_available():
            return 0
        
        try:
            keys = self._client.keys(pattern)
            if keys:
                return self._client.delete(*keys)
            return 0
        except Exception as e:
            logger.error(f"Cache delete pattern error for '{pattern}': {e}")
            return 0
    
    def exists(self, key: str) -> bool:
        """
        Check if key exists in cache.
        
        Args:
            key: Cache key
            
        Returns:
            True if key exists, False otherwise
        """
        if not self._is_available():
            return False
        
        try:
            return self._client.exists(key) > 0
        except Exception as e:
            logger.error(f"Cache exists error for key '{key}': {e}")
            return False
    
    def ttl(self, key: str) -> int:
        """
        Get time to live for key.
        
        Args:
            key: Cache key
            
        Returns:
            TTL in seconds, -1 if no expiration, -2 if key doesn't exist
        """
        if not self._is_available():
            return -2
        
        try:
            return self._client.ttl(key)
        except Exception as e:
            logger.error(f"Cache TTL error for key '{key}': {e}")
            return -2
    
    def incr(self, key: str, amount: int = 1) -> Optional[int]:
        """
        Increment value by amount.
        
        Args:
            key: Cache key
            amount: Amount to increment by
            
        Returns:
            New value or None on error
        """
        if not self._is_available():
            return None
        
        try:
            return self._client.incrby(key, amount)
        except Exception as e:
            logger.error(f"Cache incr error for key '{key}': {e}")
            return None
    
    def flush(self) -> bool:
        """
        Flush entire cache database.
        
        Returns:
            True if successful, False otherwise
        """
        if not self._is_available():
            return False
        
        try:
            self._client.flushdb()
            logger.info("Cache flushed")
            return True
        except Exception as e:
            logger.error(f"Cache flush error: {e}")
            return False
    
    def info(self) -> dict:
        """
        Get cache statistics.
        
        Returns:
            Dict with cache stats or empty dict on error
        """
        if not self._is_available():
            return {"enabled": False}
        
        try:
            info = self._client.info()
            return {
                "enabled": True,
                "host": self.host,
                "port": self.port,
                "db": self.db,
                "connected_clients": info.get("connected_clients", 0),
                "used_memory": info.get("used_memory_human", "0"),
                "used_memory_peak": info.get("used_memory_peak_human", "0"),
                "total_commands_processed": info.get("total_commands_processed", 0),
                "keyspace_hits": info.get("keyspace_hits", 0),
                "keyspace_misses": info.get("keyspace_misses", 0),
                "evicted_keys": info.get("evicted_keys", 0),
                "expired_keys": info.get("expired_keys", 0),
            }
        except Exception as e:
            logger.error(f"Cache info error: {e}")
            return {"enabled": False, "error": str(e)}
    
    def close(self):
        """Close Redis connection."""
        if self._client:
            try:
                self._client.close()
                logger.info("Redis connection closed")
            except Exception as e:
                logger.error(f"Error closing Redis connection: {e}")


# Global cache instance
_cache_instance: Optional[RedisCache] = None


def get_cache() -> RedisCache:
    """
    Get global cache instance (singleton pattern).
    
    Returns:
        RedisCache instance
    """
    global _cache_instance
    if _cache_instance is None:
        _cache_instance = RedisCache()
    return _cache_instance

