"""Caching layer for cost analysis results."""

import hashlib
import json
from typing import Any, Dict, Optional
import logging

from .redis_client import get_cache

logger = logging.getLogger(__name__)

# Cache TTLs (in seconds)
ANALYSIS_TTL = 60 * 60  # 1 hour - analysis results can be cached briefly
TERRAFORM_PARSE_TTL = 30 * 60  # 30 minutes - parsed Terraform
COST_SIMULATION_TTL = 60 * 60  # 1 hour - cost simulations
POLICY_EVAL_TTL = 30 * 60  # 30 minutes - policy evaluations


class AnalysisCache:
    """Cache layer for cost analysis results."""
    
    def __init__(self):
        """Initialize analysis cache."""
        self.cache = get_cache()
        self.prefix = "analysis"
    
    def _make_key(self, *parts: str) -> str:
        """
        Create cache key from parts.
        
        Args:
            *parts: Key components
            
        Returns:
            Cache key string
        """
        return f"{self.prefix}:{':'.join(str(p) for p in parts)}"
    
    def _hash_content(self, content: str) -> str:
        """
        Create deterministic hash from content.
        
        Args:
            content: Content to hash
            
        Returns:
            Hash string
        """
        return hashlib.sha256(content.encode()).hexdigest()[:32]
    
    def _hash_params(self, params: Dict[str, Any]) -> str:
        """
        Create deterministic hash from parameters.
        
        Args:
            params: Parameters dict
            
        Returns:
            Hash string
        """
        sorted_json = json.dumps(params, sort_keys=True)
        return hashlib.md5(sorted_json.encode()).hexdigest()[:16]
    
    def get_parsed_terraform(
        self,
        iac_content: str
    ) -> Optional[Dict[str, Any]]:
        """
        Get cached parsed Terraform.
        
        Args:
            iac_content: Terraform content
            
        Returns:
            Cached parsed result or None
        """
        content_hash = self._hash_content(iac_content)
        key = self._make_key("terraform", content_hash)
        return self.cache.get(key)
    
    def set_parsed_terraform(
        self,
        iac_content: str,
        parsed_data: Dict[str, Any]
    ) -> bool:
        """
        Cache parsed Terraform.
        
        Args:
            iac_content: Terraform content
            parsed_data: Parsed data to cache
            
        Returns:
            True if cached successfully
        """
        content_hash = self._hash_content(iac_content)
        key = self._make_key("terraform", content_hash)
        return self.cache.set(key, parsed_data, ttl=TERRAFORM_PARSE_TTL)
    
    def get_cost_simulation(
        self,
        resource_model_hash: str
    ) -> Optional[Dict[str, Any]]:
        """
        Get cached cost simulation.
        
        Args:
            resource_model_hash: Hash of resource model
            
        Returns:
            Cached simulation or None
        """
        key = self._make_key("simulation", resource_model_hash)
        return self.cache.get(key)
    
    def set_cost_simulation(
        self,
        resource_model_hash: str,
        simulation_data: Dict[str, Any]
    ) -> bool:
        """
        Cache cost simulation.
        
        Args:
            resource_model_hash: Hash of resource model
            simulation_data: Simulation data to cache
            
        Returns:
            True if cached successfully
        """
        key = self._make_key("simulation", resource_model_hash)
        return self.cache.set(key, simulation_data, ttl=COST_SIMULATION_TTL)
    
    def get_policy_evaluation(
        self,
        policy_id: str,
        context_hash: str
    ) -> Optional[Dict[str, Any]]:
        """
        Get cached policy evaluation.
        
        Args:
            policy_id: Policy ID
            context_hash: Hash of evaluation context
            
        Returns:
            Cached evaluation or None
        """
        key = self._make_key("policy", policy_id, context_hash)
        return self.cache.get(key)
    
    def set_policy_evaluation(
        self,
        policy_id: str,
        context_hash: str,
        evaluation_data: Dict[str, Any]
    ) -> bool:
        """
        Cache policy evaluation.
        
        Args:
            policy_id: Policy ID
            context_hash: Hash of evaluation context
            evaluation_data: Evaluation data to cache
            
        Returns:
            True if cached successfully
        """
        key = self._make_key("policy", policy_id, context_hash)
        return self.cache.set(key, evaluation_data, ttl=POLICY_EVAL_TTL)
    
    def get_full_analysis(
        self,
        request_hash: str
    ) -> Optional[Dict[str, Any]]:
        """
        Get cached full cost impact analysis.
        
        Args:
            request_hash: Hash of request parameters
            
        Returns:
            Cached analysis or None
        """
        key = self._make_key("full", request_hash)
        return self.cache.get(key)
    
    def set_full_analysis(
        self,
        request_hash: str,
        analysis_data: Dict[str, Any]
    ) -> bool:
        """
        Cache full cost impact analysis.
        
        Args:
            request_hash: Hash of request parameters
            analysis_data: Analysis data to cache
            
        Returns:
            True if cached successfully
        """
        key = self._make_key("full", request_hash)
        return self.cache.set(key, analysis_data, ttl=ANALYSIS_TTL)
    
    def invalidate_policy(self, policy_id: str) -> int:
        """
        Invalidate all cached evaluations for a policy.
        
        Args:
            policy_id: Policy ID
            
        Returns:
            Number of keys invalidated
        """
        pattern = self._make_key("policy", policy_id, "*")
        count = self.cache.delete_pattern(pattern)
        logger.info(f"Invalidated {count} policy cache entries for {policy_id}")
        return count
    
    def invalidate_all(self) -> int:
        """
        Invalidate all analysis cache.
        
        Returns:
            Number of keys invalidated
        """
        pattern = self._make_key("*")
        count = self.cache.delete_pattern(pattern)
        logger.info(f"Invalidated all {count} analysis cache entries")
        return count


# Global instance
_analysis_cache_instance: Optional[AnalysisCache] = None


def get_analysis_cache() -> AnalysisCache:
    """
    Get global analysis cache instance.
    
    Returns:
        AnalysisCache instance
    """
    global _analysis_cache_instance
    if _analysis_cache_instance is None:
        _analysis_cache_instance = AnalysisCache()
    return _analysis_cache_instance

