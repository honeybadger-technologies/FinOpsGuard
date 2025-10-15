"""Audit log storage implementation."""

import logging
from typing import Optional
from sqlalchemy import desc, and_, or_

from ..types.audit import AuditEvent, AuditQuery, AuditLogResponse
from ..database.connection import is_db_available, get_session_factory

logger = logging.getLogger(__name__)


class AuditLogStorage:
    """Storage layer for audit logs."""
    
    def __init__(self):
        """Initialize audit log storage."""
        pass
    
    def is_available(self) -> bool:
        """Check if audit log storage is available."""
        return is_db_available()
    
    def store_event(self, event: AuditEvent) -> bool:
        """
        Store an audit event.
        
        Args:
            event: Audit event to store
            
        Returns:
            True if stored successfully
        """
        if not self.is_available():
            logger.debug("Database not available for audit logging")
            return False
        
        session = None
        try:
            from ..database.models import AuditLog
            
            SessionFactory = get_session_factory()
            if not SessionFactory:
                return False
            
            session = SessionFactory()
            
            # Create database record
            audit_log = AuditLog(
                event_id=event.event_id,
                event_type=event.event_type.value,
                severity=event.severity.value,
                timestamp=event.timestamp,
                user_id=event.user_id,
                username=event.username,
                user_role=event.user_role,
                api_key_name=event.api_key_name,
                ip_address=event.ip_address,
                user_agent=event.user_agent,
                request_id=event.request_id,
                action=event.action,
                resource_type=event.resource_type,
                resource_id=event.resource_id,
                details=event.details,
                success=event.success,
                error_message=event.error_message,
                http_method=event.http_method,
                http_path=event.http_path,
                http_status=event.http_status,
                compliance_tags=event.compliance_tags,
                event_metadata=event.metadata
            )
            
            session.add(audit_log)
            session.commit()
            
            logger.debug(f"Stored audit event: {event.event_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error storing audit event: {e}")
            if session:
                session.rollback()
            return False
        finally:
            if session:
                session.close()
    
    def query_events(self, query: AuditQuery) -> AuditLogResponse:
        """
        Query audit events.
        
        Args:
            query: Query parameters
            
        Returns:
            AuditLogResponse with matching events
        """
        if not self.is_available():
            return AuditLogResponse(
                events=[],
                total_count=0,
                has_more=False
            )
        
        try:
            from ..database.models import AuditLog
            
            session = self.db.get_session()
            
            # Build query
            db_query = session.query(AuditLog)
            
            # Apply filters
            filters = []
            
            if query.start_time:
                filters.append(AuditLog.timestamp >= query.start_time)
            
            if query.end_time:
                filters.append(AuditLog.timestamp <= query.end_time)
            
            if query.event_types:
                event_type_values = [et.value for et in query.event_types]
                filters.append(AuditLog.event_type.in_(event_type_values))
            
            if query.severities:
                severity_values = [s.value for s in query.severities]
                filters.append(AuditLog.severity.in_(severity_values))
            
            if query.user_ids:
                filters.append(AuditLog.user_id.in_(query.user_ids))
            
            if query.usernames:
                filters.append(AuditLog.username.in_(query.usernames))
            
            if query.resource_types:
                filters.append(AuditLog.resource_type.in_(query.resource_types))
            
            if query.success is not None:
                filters.append(AuditLog.success == query.success)
            
            # Search term (searches action, username, resource_id)
            if query.search_term:
                search_pattern = f"%{query.search_term}%"
                filters.append(
                    or_(
                        AuditLog.action.like(search_pattern),
                        AuditLog.username.like(search_pattern),
                        AuditLog.resource_id.like(search_pattern)
                    )
                )
            
            # Apply all filters
            if filters:
                db_query = db_query.filter(and_(*filters))
            
            # Get total count
            total_count = db_query.count()
            
            # Apply sorting
            if query.sort_by == "timestamp":
                sort_column = AuditLog.timestamp
            elif query.sort_by == "severity":
                sort_column = AuditLog.severity
            else:
                sort_column = AuditLog.timestamp
            
            if query.sort_order == "desc":
                db_query = db_query.order_by(desc(sort_column))
            else:
                db_query = db_query.order_by(sort_column)
            
            # Apply pagination
            db_query = db_query.offset(query.offset).limit(query.limit + 1)
            
            # Execute query
            records = db_query.all()
            
            # Check if there are more results
            has_more = len(records) > query.limit
            if has_more:
                records = records[:query.limit]
            
            # Convert to AuditEvent objects
            events = []
            for record in records:
                event = AuditEvent(
                    event_id=record.event_id,
                    event_type=record.event_type,
                    severity=record.severity,
                    timestamp=record.timestamp,
                    user_id=record.user_id,
                    username=record.username,
                    user_role=record.user_role,
                    api_key_name=record.api_key_name,
                    ip_address=record.ip_address,
                    user_agent=record.user_agent,
                    request_id=record.request_id,
                    action=record.action,
                    resource_type=record.resource_type,
                    resource_id=record.resource_id,
                    details=record.details or {},
                    success=record.success,
                    error_message=record.error_message,
                    http_method=record.http_method,
                    http_path=record.http_path,
                    http_status=record.http_status,
                    compliance_tags=record.compliance_tags or [],
                    metadata=record.event_metadata or {}
                )
                events.append(event)
            
            next_offset = query.offset + query.limit if has_more else None
            
            return AuditLogResponse(
                events=events,
                total_count=total_count,
                has_more=has_more,
                next_offset=next_offset
            )
            
        except Exception as e:
            logger.error(f"Error querying audit events: {e}")
            return AuditLogResponse(
                events=[],
                total_count=0,
                has_more=False
            )
        finally:
            if session:
                session.close()
    
    def get_event(self, event_id: str) -> Optional[AuditEvent]:
        """
        Get a specific audit event by ID.
        
        Args:
            event_id: Event identifier
            
        Returns:
            AuditEvent if found
        """
        if not self.is_available():
            return None
        
        session = None
        try:
            from ..database.models import AuditLog
            
            SessionFactory = get_session_factory()
            if not SessionFactory:
                return None
            
            session = SessionFactory()
            record = session.query(AuditLog).filter(AuditLog.event_id == event_id).first()
            
            if not record:
                return None
            
            return AuditEvent(
                event_id=record.event_id,
                event_type=record.event_type,
                severity=record.severity,
                timestamp=record.timestamp,
                user_id=record.user_id,
                username=record.username,
                action=record.action,
                success=record.success,
                details=record.details or {}
            )
            
        except Exception as e:
            logger.error(f"Error retrieving audit event: {e}")
            return None
        finally:
            if session:
                session.close()


# Global singleton
_audit_storage = None


def get_audit_storage() -> AuditLogStorage:
    """
    Get global audit storage instance.
    
    Returns:
        AuditLogStorage instance
    """
    global _audit_storage
    if _audit_storage is None:
        _audit_storage = AuditLogStorage()
    return _audit_storage

