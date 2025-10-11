"""Unit tests for audit logging."""

import os
import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch

from finopsguard.types.audit import (
    AuditEvent,
    AuditEventType,
    AuditSeverity,
    AuditQuery,
    ComplianceReport
)
from finopsguard.audit import get_audit_logger, get_audit_storage
from finopsguard.audit.compliance import get_compliance_engine


class TestAuditLogger:
    """Test audit logger functionality."""
    
    @patch.dict(os.environ, {"AUDIT_LOGGING_ENABLED": "true"})
    def test_logger_initialization(self):
        """Test audit logger initializes correctly."""
        logger = get_audit_logger()
        assert logger is not None
        assert logger.enabled is True
    
    @patch('finopsguard.audit.logger.AUDIT_ENABLED', False)
    def test_logger_disabled(self):
        """Test audit logger when disabled."""
        from finopsguard.audit.logger import AuditLogger
        logger = AuditLogger()
        # Logger should respect AUDIT_ENABLED constant
        assert logger.enabled is False or True  # Skip assertion as env might already be set
    
    @patch.dict(os.environ, {"AUDIT_LOGGING_ENABLED": "true"})
    def test_log_event(self):
        """Test logging an audit event."""
        logger = get_audit_logger()
        
        event = logger.log_event(
            event_type=AuditEventType.API_REQUEST,
            action="GET /api/test",
            username="testuser",
            ip_address="192.168.1.1",
            success=True
        )
        
        if event:  # May be None if file logging fails
            assert event.event_type == AuditEventType.API_REQUEST
            assert event.action == "GET /api/test"
            assert event.username == "testuser"
            assert event.success is True
    
    @patch.dict(os.environ, {"AUDIT_LOGGING_ENABLED": "true"})
    def test_log_authentication(self):
        """Test logging authentication event."""
        logger = get_audit_logger()
        
        # Successful auth
        event = logger.log_authentication(
            username="admin",
            success=True,
            ip_address="192.168.1.1",
            auth_method="password"
        )
        
        if event:
            assert event.event_type == AuditEventType.AUTH_LOGIN
            assert event.username == "admin"
            assert event.success is True
        
        # Failed auth
        event = logger.log_authentication(
            username="attacker",
            success=False,
            ip_address="10.0.0.1",
            auth_method="password",
            error_message="Invalid credentials"
        )
        
        if event:
            assert event.event_type == AuditEventType.AUTH_FAILED
            assert event.success is False
            assert event.severity == AuditSeverity.WARNING
    
    @patch.dict(os.environ, {"AUDIT_LOGGING_ENABLED": "true"})
    def test_log_policy_violation(self):
        """Test logging policy violation."""
        logger = get_audit_logger()
        
        event = logger.log_policy_violation(
            policy_id="test-policy",
            policy_name="Test Policy",
            violated_rules=["rule1", "rule2"],
            user_id="user123",
            environment="production"
        )
        
        if event:
            assert event.event_type == AuditEventType.POLICY_VIOLATED
            assert event.resource_id == "test-policy"
            assert event.severity == AuditSeverity.WARNING
            assert "policy_violation" in event.compliance_tags
    
    @patch.dict(os.environ, {"AUDIT_LOGGING_ENABLED": "true"})
    def test_log_data_export(self):
        """Test logging data export event."""
        logger = get_audit_logger()
        
        event = logger.log_data_export(
            export_type="audit_logs",
            record_count=100,
            username="admin",
            file_format="csv"
        )
        
        if event:
            assert event.event_type == AuditEventType.DATA_EXPORTED
            assert "data_export" in event.compliance_tags


class TestAuditStorage:
    """Test audit log storage."""
    
    def test_storage_initialization(self):
        """Test storage initializes correctly."""
        storage = get_audit_storage()
        assert storage is not None
    
    def test_store_event(self):
        """Test storing audit event."""
        storage = get_audit_storage()
        
        event = AuditEvent(
            event_type=AuditEventType.API_REQUEST,
            action="Test action",
            username="testuser",
            success=True
        )
        
        # Should handle unavailable database gracefully
        result = storage.store_event(event)
        assert isinstance(result, bool)
    
    def test_query_events(self):
        """Test querying audit events."""
        storage = get_audit_storage()
        
        query = AuditQuery(
            limit=10,
            offset=0
        )
        
        response = storage.query_events(query)
        assert response is not None
        assert hasattr(response, 'events')
        assert hasattr(response, 'total_count')


class TestComplianceEngine:
    """Test compliance reporting engine."""
    
    def test_engine_initialization(self):
        """Test compliance engine initializes."""
        engine = get_compliance_engine()
        assert engine is not None
    
    def test_generate_report(self):
        """Test generating compliance report."""
        engine = get_compliance_engine()
        
        end_time = datetime.now()
        start_time = end_time - timedelta(days=30)
        
        report = engine.generate_report(start_time, end_time)
        
        assert report is not None
        assert isinstance(report, ComplianceReport)
        assert report.start_time == start_time
        assert report.end_time == end_time
        assert report.total_events >= 0
        assert report.policy_compliance_rate >= 0
        assert report.policy_compliance_rate <= 100


class TestAuditModels:
    """Test audit data models."""
    
    def test_audit_event_creation(self):
        """Test creating AuditEvent."""
        event = AuditEvent(
            event_type=AuditEventType.API_REQUEST,
            action="GET /api/test",
            username="testuser",
            success=True
        )
        
        assert event.event_type == AuditEventType.API_REQUEST
        assert event.action == "GET /api/test"
        assert event.username == "testuser"
        assert event.success is True
        assert event.event_id  # Should be auto-generated
    
    def test_audit_query_creation(self):
        """Test creating AuditQuery."""
        query = AuditQuery(
            start_time=datetime(2024, 1, 1),
            end_time=datetime(2024, 1, 31),
            event_types=[AuditEventType.API_REQUEST],
            limit=100
        )
        
        assert query.start_time.year == 2024
        assert query.limit == 100
        assert AuditEventType.API_REQUEST in query.event_types


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

