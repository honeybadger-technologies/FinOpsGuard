"""Redis cache client for FinOpsGuard."""

import json
import logging
import os
from typing import Any, Dict, List, Optional

import redis
from redis.connection import ConnectionPool
from redis.cluster import RedisCluster

logger = logging.getLogger(__name__)


class RedisCache:
    """Redis cache client with support for standalone or cluster deployments."""

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
        self.cluster_enabled = os.getenv('REDIS_CLUSTER_ENABLED', 'false').lower() == 'true'
        self.cluster_nodes = self._parse_cluster_nodes(os.getenv('REDIS_CLUSTER_NODES', ''))
        self.mode = "cluster" if self.cluster_enabled else "standalone"

        self._pool: Optional[ConnectionPool] = None
        self._client: Optional[redis.Redis] = None

        if self.enabled:
            self._initialize_client(max_connections, decode_responses)
        else:
            logger.info("Redis cache disabled")

    def _initialize_client(self, max_connections: int, decode_responses: bool) -> None:
        """Initialize the appropriate Redis client based on deployment mode."""
        if self.cluster_enabled:
            startup_nodes = self.cluster_nodes or [{"host": self.host, "port": self.port}]
            try:
                self._client = RedisCluster(
                    startup_nodes=startup_nodes,
                    password=self.password,
                    max_connections=max_connections,
                    decode_responses=decode_responses,
                    socket_connect_timeout=5,
                    socket_timeout=5,
                    retry_on_timeout=True,
                )
                self._client.ping()
                node_list = ", ".join(f"{node['host']}:{node['port']}" for node in startup_nodes)
                logger.info(f"Redis cluster cache enabled: {node_list}")
            except Exception as e:
                logger.warning(f"Redis cluster connection failed: {e}. Caching disabled.")
                self.enabled = False
                self._client = None
        else:
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
                self._client.ping()
                logger.info(f"Redis cache enabled: {self.host}:{self.port}/{self.db}")
            except Exception as e:
                logger.warning(f"Redis connection failed: {e}. Caching disabled.")
                self.enabled = False
                self._client = None

    def _parse_cluster_nodes(self, nodes: str) -> List[Dict[str, int]]:
        """Parse cluster nodes definition from env into host/port pairs."""
        parsed_nodes: List[Dict[str, int]] = []
        if not nodes:
            return parsed_nodes

        for raw_node in nodes.split(','):
            node = raw_node.strip()
            if not node:
                continue
            if ':' not in node:
                logger.warning(f"Ignoring invalid Redis cluster node '{node}'")
                continue
            host, port = node.split(':', 1)
            try:
                parsed_nodes.append({"host": host.strip(), "port": int(port)})
            except ValueError:
                logger.warning(f"Ignoring Redis cluster node '{node}' with invalid port")
        return parsed_nodes
    
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
        Delete all keys matching pattern using incremental scans for cluster safety.

        Args:
            pattern: Key pattern (e.g., 'pricing:*')

        Returns:
            Number of keys deleted
        """
        if not self._is_available():
            return 0

        deleted = 0
        batch: List[str] = []
        try:
            for key in self._client.scan_iter(match=pattern, count=500):
                batch.append(key)
                if len(batch) >= 500:
                    deleted += self._client.delete(*batch) or 0
                    batch.clear()
            if batch:
                deleted += self._client.delete(*batch) or 0
            return deleted
        except Exception as e:
            logger.error(f"Cache delete pattern error for '{pattern}': {e}")
            return deleted
    
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
        Flush entire cache database (all nodes when running in cluster mode).

        Returns:
            True if successful, False otherwise
        """
        if not self._is_available():
            return False

        try:
            if self.cluster_enabled:
                self._client.flushall()
            else:
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

        stats = {
            "enabled": True,
            "mode": self.mode,
            "host": self.host,
            "port": self.port,
            "db": self.db if not self.cluster_enabled else None,
        }

        try:
            info = self._client.info()
            info_data = self._normalize_info(info)
            stats.update({
                "connected_clients": info_data.get("connected_clients", 0),
                "used_memory": info_data.get("used_memory_human", "0"),
                "used_memory_peak": info_data.get("used_memory_peak_human", "0"),
                "total_commands_processed": info_data.get("total_commands_processed", 0),
                "keyspace_hits": info_data.get("keyspace_hits", 0),
                "keyspace_misses": info_data.get("keyspace_misses", 0),
                "evicted_keys": info_data.get("evicted_keys", 0),
                "expired_keys": info_data.get("expired_keys", 0),
            })

            if self.cluster_enabled:
                stats["cluster_nodes"] = [
                    f"{node['host']}:{node['port']}" for node in (self.cluster_nodes or [{"host": self.host, "port": self.port}])
                ]
                stats.update(self._cluster_stats())
            return stats
        except Exception as e:
            logger.error(f"Cache info error: {e}")
            return {"enabled": False, "error": str(e)}

    def _normalize_info(self, info: Any) -> Dict[str, Any]:
        """Normalize INFO responses for both standalone and cluster Redis deployments."""
        if not isinstance(info, dict):
            return {}
        if info and all(isinstance(value, dict) for value in info.values()):
            # Cluster mode returns per-node info; take the first node for summary stats
            first_key = next(iter(info.keys()), None)
            if first_key:
                return info[first_key]
        return info

    def _cluster_stats(self) -> Dict[str, Any]:
        """Fetch additional cluster metadata."""
        try:
            cluster_info = self._client.cluster_info()
            if not isinstance(cluster_info, dict):
                return {}
            return {
                "cluster_state": cluster_info.get("cluster_state", "unknown"),
                "cluster_size": cluster_info.get("cluster_size"),
                "cluster_slots_assigned": cluster_info.get("cluster_slots_assigned"),
                "cluster_slots_ok": cluster_info.get("cluster_slots_ok"),
            }
        except Exception as exc:
            logger.debug(f"Cluster info unavailable: {exc}")
            return {}
    
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

