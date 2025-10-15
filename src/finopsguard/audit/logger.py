"""Audit logging implementation."""

import os
import logging
import json
from typing import Optional, Dict, List
from pathlib import Path

from ..types.audit import (
    AuditEvent,
    AuditEventType,
    AuditSeverity
)

logger = logging.getLogger(__name__)

# Configuration
AUDIT_ENABLED = os.getenv("AUDIT_LOGGING_ENABLED", "true").lower() == "true"
AUDIT_LOG_FILE = os.getenv("AUDIT_LOG_FILE", "/var/log/finopsguard/audit.log")
AUDIT_CONSOLE_ENABLED = os.getenv("AUDIT_CONSOLE_LOGGING", "false").lower() == "true"
AUDIT_DB_ENABLED = os.getenv("AUDIT_DB_LOGGING", "true").lower() == "true"


class AuditLogger:
    """
    Audit logger for FinOpsGuard.
    
    Captures security-relevant events for compliance and monitoring.
    """
    
    def __init__(self):
        """Initialize audit logger."""
        self.enabled = AUDIT_ENABLED
        self.file_logging = True
        self.console_logging = AUDIT_CONSOLE_ENABLED
        self.db_logging = AUDIT_DB_ENABLED
        
        # Setup file logging
        if self.file_logging:
            self._setup_file_logging()
    
    def _setup_file_logging(self):
        """Setup file-based audit logging."""
        try:
            log_path = Path(AUDIT_LOG_FILE)
            log_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Create file handler
            self.file_handler = logging.FileHandler(AUDIT_LOG_FILE)
            self.file_handler.setLevel(logging.INFO)
            
            # JSON formatter for structured logging
            formatter = logging.Formatter(
                '{"timestamp": "%(asctime)s", "level": "%(levelname)s", "message": %(message)s}'
            )
            self.file_handler.setFormatter(formatter)
            
        except Exception as e:
            logger.warning(f"Could not setup file logging for audit: {e}")
            self.file_logging = False
    
    def log_event(
        self,
        event_type: AuditEventType,
        action: str,
        user_id: Optional[str] = None,
        username: Optional[str] = None,
        ip_address: Optional[str] = None,
        success: bool = True,
        **kwargs
    ) -> AuditEvent:
        """
        Log an audit event.
        
        Args:
            event_type: Type of event
            action: Action description
            user_id: User identifier
            username: Username
            ip_address: Client IP address
            success: Whether action succeeded
            **kwargs: Additional event details
            
        Returns:
            Created AuditEvent
        """
        if not self.enabled:
            return None
        
        # Create audit event
        event = AuditEvent(
            event_type=event_type,
            action=action,
            user_id=user_id,
            username=username,
            ip_address=ip_address,
            success=success,
            severity=kwargs.get('severity', AuditSeverity.INFO),
            user_role=kwargs.get('user_role'),
            user_agent=kwargs.get('user_agent'),
            request_id=kwargs.get('request_id'),
            resource_type=kwargs.get('resource_type'),
            resource_id=kwargs.get('resource_id'),
            details=kwargs.get('details', {}),
            error_message=kwargs.get('error_message'),
            http_method=kwargs.get('http_method'),
            http_path=kwargs.get('http_path'),
            http_status=kwargs.get('http_status'),
            compliance_tags=kwargs.get('compliance_tags', []),
            metadata=kwargs.get('metadata', {})
        )
        
        # Log to file
        if self.file_logging:
            self._log_to_file(event)
        
        # Log to console (if enabled)
        if self.console_logging:
            self._log_to_console(event)
        
        # Log to database (handled separately by storage layer)
        if self.db_logging:
            self._log_to_database(event)
        
        return event
    
    def _log_to_file(self, event: AuditEvent):
        """Write audit event to file."""
        try:
            log_entry = {
                "event_id": event.event_id,
                "timestamp": event.timestamp.isoformat(),
                "event_type": event.event_type.value,
                "severity": event.severity.value,
                "user": event.username or event.user_id or "anonymous",
                "action": event.action,
                "success": event.success,
                "ip_address": event.ip_address,
                "resource": f"{event.resource_type}:{event.resource_id}" if event.resource_type else None,
                "details": event.details,
                "error": event.error_message
            }
            
            # Write to file
            with open(AUDIT_LOG_FILE, 'a') as f:
                f.write(json.dumps(log_entry) + '\n')
                
        except Exception as e:
            logger.error(f"Error writing audit log to file: {e}")
    
    def _log_to_console(self, event: AuditEvent):
        """Write audit event to console."""
        log_msg = (
            f"[AUDIT] {event.event_type.value} | "
            f"User: {event.username or 'anonymous'} | "
            f"Action: {event.action} | "
            f"Success: {event.success}"
        )
        
        if event.severity == AuditSeverity.CRITICAL:
            logger.critical(log_msg)
        elif event.severity == AuditSeverity.ERROR:
            logger.error(log_msg)
        elif event.severity == AuditSeverity.WARNING:
            logger.warning(log_msg)
        else:
            logger.info(log_msg)
    
    def _log_to_database(self, event: AuditEvent):
        """Store audit event in database."""
        try:
            from .storage import get_audit_storage
            storage = get_audit_storage()
            if storage.is_available():
                storage.store_event(event)
        except Exception as e:
            logger.error(f"Error storing audit log in database: {e}")
    
    def log_api_request(
        self,
        method: str,
        path: str,
        user_id: Optional[str] = None,
        username: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        request_id: Optional[str] = None
    ) -> AuditEvent:
        """Log an API request."""
        return self.log_event(
            event_type=AuditEventType.API_REQUEST,
            action=f"{method} {path}",
            user_id=user_id,
            username=username,
            ip_address=ip_address,
            user_agent=user_agent,
            request_id=request_id,
            http_method=method,
            http_path=path,
            compliance_tags=["api_access"]
        )
    
    def log_authentication(
        self,
        username: str,
        success: bool,
        ip_address: Optional[str] = None,
        auth_method: str = "password",
        error_message: Optional[str] = None
    ) -> AuditEvent:
        """Log authentication attempt."""
        return self.log_event(
            event_type=AuditEventType.AUTH_LOGIN if success else AuditEventType.AUTH_FAILED,
            action=f"Authentication via {auth_method}",
            username=username,
            ip_address=ip_address,
            success=success,
            error_message=error_message,
            severity=AuditSeverity.INFO if success else AuditSeverity.WARNING,
            compliance_tags=["authentication"],
            details={"auth_method": auth_method}
        )
    
    def log_policy_violation(
        self,
        policy_id: str,
        policy_name: str,
        violated_rules: List[str],
        user_id: Optional[str] = None,
        environment: Optional[str] = None,
        details: Optional[Dict] = None
    ) -> AuditEvent:
        """Log policy violation."""
        return self.log_event(
            event_type=AuditEventType.POLICY_VIOLATED,
            action=f"Policy violation: {policy_name}",
            user_id=user_id,
            resource_type="policy",
            resource_id=policy_id,
            success=False,
            severity=AuditSeverity.WARNING,
            compliance_tags=["policy_violation", "compliance"],
            details={
                "policy_id": policy_id,
                "policy_name": policy_name,
                "violated_rules": violated_rules,
                "environment": environment,
                **(details or {})
            }
        )
    
    def log_policy_change(
        self,
        policy_id: str,
        policy_name: str,
        change_type: str,  # created, updated, deleted
        user_id: Optional[str] = None,
        username: Optional[str] = None,
        changes: Optional[Dict] = None
    ) -> AuditEvent:
        """Log policy configuration change."""
        event_type_map = {
            "created": AuditEventType.POLICY_CREATED,
            "updated": AuditEventType.POLICY_UPDATED,
            "deleted": AuditEventType.POLICY_DELETED
        }
        
        return self.log_event(
            event_type=event_type_map.get(change_type, AuditEventType.POLICY_UPDATED),
            action=f"Policy {change_type}: {policy_name}",
            user_id=user_id,
            username=username,
            resource_type="policy",
            resource_id=policy_id,
            severity=AuditSeverity.INFO,
            compliance_tags=["policy_change", "configuration"],
            details={
                "policy_id": policy_id,
                "policy_name": policy_name,
                "change_type": change_type,
                "changes": changes or {}
            }
        )
    
    def log_data_export(
        self,
        export_type: str,
        record_count: int,
        user_id: Optional[str] = None,
        username: Optional[str] = None,
        file_format: Optional[str] = None
    ) -> AuditEvent:
        """Log data export event."""
        return self.log_event(
            event_type=AuditEventType.DATA_EXPORTED,
            action=f"Exported {record_count} {export_type} records",
            user_id=user_id,
            username=username,
            severity=AuditSeverity.INFO,
            compliance_tags=["data_export", "data_access"],
            details={
                "export_type": export_type,
                "record_count": record_count,
                "file_format": file_format
            }
        )


# Global singleton
_audit_logger = None


def get_audit_logger() -> AuditLogger:
    """
    Get global audit logger instance.
    
    Returns:
        AuditLogger instance
    """
    global _audit_logger
    if _audit_logger is None:
        _audit_logger = AuditLogger()
    return _audit_logger


def log_audit_event(event_type: AuditEventType, action: str, **kwargs) -> Optional[AuditEvent]:
    """
    Convenience function to log an audit event.
    
    Args:
        event_type: Type of event
        action: Action description
        **kwargs: Additional event details
        
    Returns:
        Created AuditEvent or None if disabled
    """
    logger = get_audit_logger()
    return logger.log_event(event_type, action, **kwargs)

