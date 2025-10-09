"""Unit tests for database layer."""

import pytest
import os
from datetime import datetime

# Skip all tests if database is not available
pytestmark = pytest.mark.skipif(
    os.getenv('DB_ENABLED', 'false').lower() != 'true',
    reason="Database not enabled"
)


class TestDatabaseConnection:
    """Test database connection and initialization."""
    
    def test_database_availability(self):
        """Test checking database availability."""
        from finopsguard.database import is_db_available
        
        # Should return True or False based on DB_ENABLED
        result = is_db_available()
        assert isinstance(result, bool)
    
    def test_get_engine(self):
        """Test getting database engine."""
        from finopsguard.database import get_engine
        
        engine = get_engine()
        # Engine can be None if database is disabled
        assert engine is not None or os.getenv('DB_ENABLED', 'false').lower() != 'true'
    
    def test_init_db(self):
        """Test database initialization."""
        from finopsguard.database import init_db
        
        # Should not raise exception
        init_db()


class TestPolicyStorage:
    """Test PostgreSQL policy storage."""
    
    def test_policy_store_initialization(self):
        """Test policy store initializes correctly."""
        from finopsguard.database import get_policy_store
        
        store = get_policy_store()
        assert store is not None
        assert hasattr(store, 'db_available')
    
    def test_create_and_get_policy(self):
        """Test creating and retrieving a policy."""
        from finopsguard.database import get_policy_store
        from finopsguard.types.policy import Policy, PolicyViolationAction
        
        store = get_policy_store()
        if not store.db_available:
            pytest.skip("Database not available")
        
        # Create test policy
        policy = Policy(
            id="test_policy_db",
            name="Test Database Policy",
            description="Testing PostgreSQL storage",
            budget=1000.0,
            on_violation=PolicyViolationAction.ADVISORY,
            enabled=True
        )
        
        # Create
        success = store.create_policy(policy)
        assert success
        
        # Retrieve
        retrieved = store.get_policy("test_policy_db")
        assert retrieved is not None
        assert retrieved.id == "test_policy_db"
        assert retrieved.name == "Test Database Policy"
        assert retrieved.budget == 1000.0
        
        # Clean up
        store.delete_policy("test_policy_db")
    
    def test_update_policy(self):
        """Test updating a policy."""
        from finopsguard.database import get_policy_store
        from finopsguard.types.policy import Policy, PolicyViolationAction
        
        store = get_policy_store()
        if not store.db_available:
            pytest.skip("Database not available")
        
        # Create policy
        policy = Policy(
            id="test_update_policy",
            name="Original Name",
            budget=1000.0,
            on_violation=PolicyViolationAction.ADVISORY,
            enabled=True
        )
        store.create_policy(policy)
        
        # Update
        updated_policy = Policy(
            id="test_update_policy",
            name="Updated Name",
            budget=2000.0,
            on_violation=PolicyViolationAction.BLOCK,
            enabled=False
        )
        success = store.update_policy("test_update_policy", updated_policy)
        assert success
        
        # Verify
        retrieved = store.get_policy("test_update_policy")
        assert retrieved.name == "Updated Name"
        assert retrieved.budget == 2000.0
        assert retrieved.on_violation == PolicyViolationAction.BLOCK
        assert retrieved.enabled == False
        
        # Clean up
        store.delete_policy("test_update_policy")
    
    def test_delete_policy(self):
        """Test deleting a policy."""
        from finopsguard.database import get_policy_store
        from finopsguard.types.policy import Policy
        
        store = get_policy_store()
        if not store.db_available:
            pytest.skip("Database not available")
        
        # Create policy
        policy = Policy(
            id="test_delete_policy",
            name="To Be Deleted",
            budget=500.0,
            enabled=True
        )
        store.create_policy(policy)
        
        # Verify it exists
        assert store.policy_exists("test_delete_policy")
        
        # Delete
        success = store.delete_policy("test_delete_policy")
        assert success
        
        # Verify it's gone
        assert not store.policy_exists("test_delete_policy")
        retrieved = store.get_policy("test_delete_policy")
        assert retrieved is None
    
    def test_list_policies(self):
        """Test listing policies."""
        from finopsguard.database import get_policy_store
        from finopsguard.types.policy import Policy
        
        store = get_policy_store()
        if not store.db_available:
            pytest.skip("Database not available")
        
        # Create multiple policies
        for i in range(3):
            policy = Policy(
                id=f"test_list_policy_{i}",
                name=f"Test Policy {i}",
                budget=float(1000 + i * 500),
                enabled=(i % 2 == 0)  # Alternate enabled/disabled
            )
            store.create_policy(policy)
        
        # List all
        all_policies = store.list_policies(enabled_only=False)
        assert len(all_policies) >= 3
        
        # List only enabled
        enabled_policies = store.list_policies(enabled_only=True)
        assert all(p.enabled for p in enabled_policies)
        
        # Clean up
        for i in range(3):
            store.delete_policy(f"test_list_policy_{i}")


class TestAnalysisStorage:
    """Test PostgreSQL analysis storage."""
    
    def test_analysis_store_initialization(self):
        """Test analysis store initializes correctly."""
        from finopsguard.database import get_analysis_store
        
        store = get_analysis_store()
        assert store is not None
        assert hasattr(store, 'db_available')
    
    def test_add_and_list_analysis(self):
        """Test adding and listing analyses."""
        from finopsguard.database import get_analysis_store
        from finopsguard.storage.analyses import AnalysisRecord
        
        store = get_analysis_store()
        if not store.db_available:
            pytest.skip("Database not available")
        
        # Create test analysis
        record = AnalysisRecord(
            request_id=f"test_analysis_{int(datetime.now().timestamp())}",
            started_at=datetime.now().isoformat(),
            duration_ms=123,
            summary="monthly=100.50 resources=5"
        )
        
        result_data = {
            "estimated_monthly_cost": 100.50,
            "estimated_first_week_cost": 25.0,
            "breakdown_by_resource": [{"resource_id": "test", "monthly_cost": 100.50}],
            "risk_flags": [],
            "policy_eval": {"status": "pass", "policy_id": "default"}
        }
        
        # Add
        success = store.add_analysis(record, result_data)
        assert success
        
        # List
        analyses, _ = store.list_analyses(limit=10)
        assert len(analyses) > 0
        
        # Find our analysis
        found = any(a.request_id == record.request_id for a in analyses)
        assert found
    
    def test_get_analysis_statistics(self):
        """Test getting analysis statistics."""
        from finopsguard.database import get_analysis_store
        
        store = get_analysis_store()
        if not store.db_available:
            pytest.skip("Database not available")
        
        stats = store.get_statistics()
        assert "total_analyses" in stats or "total" in stats
        assert stats.get("enabled", False) or "total" in stats


class TestHybridStorage:
    """Test hybrid in-memory + database storage."""
    
    def test_add_analysis_hybrid(self):
        """Test that analysis is added to both stores."""
        from finopsguard.storage.analyses import add_analysis, list_analyses, AnalysisRecord
        
        record = AnalysisRecord(
            request_id=f"test_hybrid_{int(datetime.now().timestamp())}",
            started_at=datetime.now().isoformat(),
            duration_ms=100,
            summary="monthly=50.0 resources=2"
        )
        
        result_data = {
            "estimated_monthly_cost": 50.0,
            "risk_flags": []
        }
        
        # Add (goes to both in-memory and database if available)
        add_analysis(record, result_data)
        
        # List from hybrid storage
        items, _ = list_analyses(limit=10)
        assert len(items) > 0
        
        # Find our record
        found = any(item.request_id == record.request_id for item in items)
        assert found


class TestPolicyEngineDatabase:
    """Test policy engine database integration."""
    
    def test_policy_engine_with_database(self):
        """Test policy engine uses database when available."""
        from finopsguard.engine.policy_engine import PolicyEngine
        from finopsguard.types.policy import Policy
        
        engine = PolicyEngine(use_database=True)
        
        # Add policy
        policy = Policy(
            id="test_engine_policy",
            name="Engine Test Policy",
            budget=750.0,
            enabled=True
        )
        
        engine.add_policy(policy)
        
        # Retrieve
        retrieved = engine.get_policy("test_engine_policy")
        assert retrieved is not None
        assert retrieved.name == "Engine Test Policy"
        
        # Clean up
        engine.remove_policy("test_engine_policy")
    
    def test_policy_engine_sync_from_database(self):
        """Test that policy engine syncs from database on init."""
        from finopsguard.engine.policy_engine import PolicyEngine
        from finopsguard.database import get_policy_store
        from finopsguard.types.policy import Policy
        
        # Create policy directly in database
        db_store = get_policy_store()
        if not db_store or not db_store.db_available:
            pytest.skip("Database not available")
        
        policy = Policy(
            id="test_sync_policy",
            name="Sync Test Policy",
            budget=1500.0,
            enabled=True
        )
        db_store.create_policy(policy)
        
        # Create new policy engine instance (should sync from database)
        new_engine = PolicyEngine(use_database=True)
        
        # Should have the policy
        retrieved = new_engine.get_policy("test_sync_policy")
        assert retrieved is not None
        assert retrieved.name == "Sync Test Policy"
        
        # Clean up
        db_store.delete_policy("test_sync_policy")

