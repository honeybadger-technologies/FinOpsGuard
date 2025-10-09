"""PostgreSQL-backed policy storage."""

import json
import logging
from typing import List, Optional
from datetime import datetime

from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from .connection import get_db_session, is_db_available
from .models import Policy as DBPolicy
from ..types.policy import Policy, PolicyExpression

logger = logging.getLogger(__name__)


class PostgreSQLPolicyStore:
    """PostgreSQL-backed policy storage."""
    
    def __init__(self):
        """Initialize PostgreSQL policy store."""
        self.db_available = is_db_available()
        if not self.db_available:
            logger.info("PostgreSQL not available - policies will use in-memory storage")
    
    def get_policy(self, policy_id: str) -> Optional[Policy]:
        """
        Get policy by ID.
        
        Args:
            policy_id: Policy ID
            
        Returns:
            Policy object or None if not found
        """
        if not self.db_available:
            return None
        
        try:
            with get_db_session() as db:
                if db is None:
                    return None
                
                db_policy = db.query(DBPolicy).filter(DBPolicy.id == policy_id).first()
                if not db_policy:
                    return None
                
                return self._db_to_policy(db_policy)
        except Exception as e:
            logger.error(f"Error getting policy {policy_id}: {e}")
            return None
    
    def list_policies(self, enabled_only: bool = False) -> List[Policy]:
        """
        List all policies.
        
        Args:
            enabled_only: Only return enabled policies
            
        Returns:
            List of Policy objects
        """
        if not self.db_available:
            return []
        
        try:
            with get_db_session() as db:
                if db is None:
                    return []
                
                query = db.query(DBPolicy)
                if enabled_only:
                    query = query.filter(DBPolicy.enabled == True)
                
                query = query.order_by(DBPolicy.created_at.desc())
                db_policies = query.all()
                
                return [self._db_to_policy(p) for p in db_policies]
        except Exception as e:
            logger.error(f"Error listing policies: {e}")
            return []
    
    def create_policy(self, policy: Policy) -> bool:
        """
        Create a new policy.
        
        Args:
            policy: Policy object
            
        Returns:
            True if created successfully
        """
        if not self.db_available:
            return False
        
        try:
            with get_db_session() as db:
                if db is None:
                    return False
                
                db_policy = DBPolicy(
                    id=policy.id,
                    name=policy.name,
                    description=policy.description,
                    budget=policy.budget,
                    expression_json=policy.expression.model_dump() if policy.expression else None,
                    on_violation=policy.on_violation,
                    enabled=policy.enabled
                )
                
                db.add(db_policy)
                db.commit()
                logger.info(f"Created policy {policy.id}")
                return True
        except Exception as e:
            logger.error(f"Error creating policy {policy.id}: {e}")
            return False
    
    def update_policy(self, policy_id: str, policy: Policy) -> bool:
        """
        Update an existing policy.
        
        Args:
            policy_id: Policy ID to update
            policy: New policy data
            
        Returns:
            True if updated successfully
        """
        if not self.db_available:
            return False
        
        try:
            with get_db_session() as db:
                if db is None:
                    return False
                
                db_policy = db.query(DBPolicy).filter(DBPolicy.id == policy_id).first()
                if not db_policy:
                    logger.warning(f"Policy {policy_id} not found for update")
                    return False
                
                # Update fields
                db_policy.name = policy.name
                db_policy.description = policy.description
                db_policy.budget = policy.budget
                db_policy.expression_json = policy.expression.model_dump() if policy.expression else None
                db_policy.on_violation = policy.on_violation
                db_policy.enabled = policy.enabled
                db_policy.updated_at = datetime.now()
                
                db.commit()
                logger.info(f"Updated policy {policy_id}")
                return True
        except Exception as e:
            logger.error(f"Error updating policy {policy_id}: {e}")
            return False
    
    def delete_policy(self, policy_id: str) -> bool:
        """
        Delete a policy.
        
        Args:
            policy_id: Policy ID
            
        Returns:
            True if deleted successfully
        """
        if not self.db_available:
            return False
        
        try:
            with get_db_session() as db:
                if db is None:
                    return False
                
                db_policy = db.query(DBPolicy).filter(DBPolicy.id == policy_id).first()
                if not db_policy:
                    logger.warning(f"Policy {policy_id} not found for deletion")
                    return False
                
                db.delete(db_policy)
                db.commit()
                logger.info(f"Deleted policy {policy_id}")
                return True
        except Exception as e:
            logger.error(f"Error deleting policy {policy_id}: {e}")
            return False
    
    def policy_exists(self, policy_id: str) -> bool:
        """
        Check if policy exists.
        
        Args:
            policy_id: Policy ID
            
        Returns:
            True if policy exists
        """
        if not self.db_available:
            return False
        
        try:
            with get_db_session() as db:
                if db is None:
                    return False
                
                count = db.query(DBPolicy).filter(DBPolicy.id == policy_id).count()
                return count > 0
        except Exception as e:
            logger.error(f"Error checking policy existence {policy_id}: {e}")
            return False
    
    def _db_to_policy(self, db_policy: DBPolicy) -> Policy:
        """
        Convert database policy to Policy object.
        
        Args:
            db_policy: Database policy
            
        Returns:
            Policy object
        """
        expression = None
        if db_policy.expression_json:
            expression = PolicyExpression(**db_policy.expression_json)
        
        return Policy(
            id=db_policy.id,
            name=db_policy.name,
            description=db_policy.description,
            budget=db_policy.budget,
            expression=expression,
            on_violation=db_policy.on_violation,
            enabled=db_policy.enabled
        )


# Global instance
_policy_store_instance: Optional[PostgreSQLPolicyStore] = None


def get_policy_store() -> PostgreSQLPolicyStore:
    """
    Get global policy store instance.
    
    Returns:
        PostgreSQLPolicyStore instance
    """
    global _policy_store_instance
    if _policy_store_instance is None:
        _policy_store_instance = PostgreSQLPolicyStore()
    return _policy_store_instance

