"""API endpoints for audit logging and compliance reporting."""

import logging
from datetime import datetime, timedelta
from typing import Optional, List

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from ..types.audit import (
    AuditEvent,
    AuditQuery,
    AuditLogResponse,
    ComplianceReport,
    AuditEventType,
    AuditSeverity
)
from ..audit import get_audit_logger, get_audit_storage
from ..audit.compliance import get_compliance_engine

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/audit", tags=["audit"])


# Request models
class AuditLogQueryRequest(BaseModel):
    """Request to query audit logs."""
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    event_types: Optional[List[str]] = None
    severities: Optional[List[str]] = None
    usernames: Optional[List[str]] = None
    search_term: Optional[str] = None
    limit: int = 100
    offset: int = 0


class ComplianceReportRequest(BaseModel):
    """Request to generate compliance report."""
    start_time: datetime
    end_time: datetime


@router.get("/status")
def get_audit_status():
    """
    Get audit logging status.
    
    Returns audit logging configuration and availability.
    """
    audit_logger = get_audit_logger()
    storage = get_audit_storage()
    
    return {
        "enabled": audit_logger.enabled,
        "file_logging": audit_logger.file_logging,
        "console_logging": audit_logger.console_logging,
        "database_logging": audit_logger.db_logging,
        "database_available": storage.is_available()
    }


@router.post("/query", response_model=AuditLogResponse)
def query_audit_logs(request: AuditLogQueryRequest):
    """
    Query audit logs with filters.
    
    Retrieves audit events based on time range, event types, users, etc.
    
    Args:
        request: Query parameters
        
    Returns:
        AuditLogResponse with matching events
    """
    storage = get_audit_storage()
    
    if not storage.is_available():
        raise HTTPException(
            status_code=503,
            detail="Audit log storage not available. Enable database to use audit logs."
        )
    
    # Convert string enums to enum objects
    event_types = None
    if request.event_types:
        try:
            event_types = [AuditEventType(et) for et in request.event_types]
        except ValueError as e:
            raise HTTPException(status_code=400, detail=f"Invalid event type: {e}")
    
    severities = None
    if request.severities:
        try:
            severities = [AuditSeverity(s) for s in request.severities]
        except ValueError as e:
            raise HTTPException(status_code=400, detail=f"Invalid severity: {e}")
    
    # Create query
    query = AuditQuery(
        start_time=request.start_time,
        end_time=request.end_time,
        event_types=event_types,
        severities=severities,
        usernames=request.usernames,
        search_term=request.search_term,
        limit=request.limit,
        offset=request.offset
    )
    
    try:
        return storage.query_events(query)
    except Exception as e:
        logger.error(f"Error querying audit logs: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/events/{event_id}", response_model=AuditEvent)
def get_audit_event(event_id: str):
    """
    Get a specific audit event by ID.
    
    Args:
        event_id: Audit event identifier
        
    Returns:
        AuditEvent
    """
    storage = get_audit_storage()
    
    if not storage.is_available():
        raise HTTPException(
            status_code=503,
            detail="Audit log storage not available"
        )
    
    event = storage.get_event(event_id)
    
    if not event:
        raise HTTPException(
            status_code=404,
            detail=f"Audit event {event_id} not found"
        )
    
    return event


@router.get("/recent")
def get_recent_audit_events(
    limit: int = Query(50, ge=1, le=1000, description="Number of events to retrieve"),
    event_type: Optional[str] = Query(None, description="Filter by event type")
):
    """
    Get recent audit events.
    
    Convenience endpoint for retrieving latest audit logs.
    
    Args:
        limit: Number of events
        event_type: Optional event type filter
        
    Returns:
        List of recent audit events
    """
    storage = get_audit_storage()
    
    if not storage.is_available():
        return {
            "message": "Audit log storage not available",
            "events": []
        }
    
    # Query recent events
    query = AuditQuery(
        limit=limit,
        sort_by="timestamp",
        sort_order="desc"
    )
    
    if event_type:
        try:
            query.event_types = [AuditEventType(event_type)]
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid event type: {event_type}")
    
    try:
        response = storage.query_events(query)
        return {
            "events": response.events,
            "total_count": response.total_count
        }
    except Exception as e:
        logger.error(f"Error retrieving recent audit events: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/compliance/report", response_model=ComplianceReport)
def generate_compliance_report(request: ComplianceReportRequest):
    """
    Generate compliance report for a time period.
    
    Analyzes audit logs to produce compliance metrics, statistics,
    and security insights.
    
    Args:
        request: Report parameters with time range
        
    Returns:
        ComplianceReport with comprehensive metrics
    """
    storage = get_audit_storage()
    
    if not storage.is_available():
        raise HTTPException(
            status_code=503,
            detail="Audit log storage not available. Enable database for compliance reporting."
        )
    
    engine = get_compliance_engine()
    
    try:
        report = engine.generate_report(
            start_time=request.start_time,
            end_time=request.end_time
        )
        
        return report
        
    except Exception as e:
        logger.error(f"Error generating compliance report: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/compliance/report/last-30-days", response_model=ComplianceReport)
def get_last_30_days_compliance():
    """
    Generate compliance report for the last 30 days.
    
    Convenience endpoint for monthly compliance reporting.
    
    Returns:
        ComplianceReport for last 30 days
    """
    end_time = datetime.now()
    start_time = end_time - timedelta(days=30)
    
    engine = get_compliance_engine()
    
    try:
        return engine.generate_report(start_time, end_time)
    except Exception as e:
        logger.error(f"Error generating 30-day compliance report: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/statistics")
def get_audit_statistics(
    days: int = Query(7, ge=1, le=365, description="Number of days to analyze")
):
    """
    Get audit log statistics.
    
    Provides quick insights into audit log activity.
    
    Args:
        days: Number of days to analyze
        
    Returns:
        Statistics summary
    """
    storage = get_audit_storage()
    
    if not storage.is_available():
        return {
            "message": "Audit log storage not available",
            "statistics": {}
        }
    
    end_time = datetime.now()
    start_time = end_time - timedelta(days=days)
    
    query = AuditQuery(
        start_time=start_time,
        end_time=end_time,
        limit=10000
    )
    
    try:
        response = storage.query_events(query)
        events = response.events
        
        # Calculate statistics
        total_events = len(events)
        successful_events = sum(1 for e in events if e.success)
        failed_events = total_events - successful_events
        
        events_by_type = {}
        for event in events:
            et = event.event_type.value
            events_by_type[et] = events_by_type.get(et, 0) + 1
        
        return {
            "time_range": {
                "start": start_time.isoformat(),
                "end": end_time.isoformat(),
                "days": days
            },
            "summary": {
                "total_events": total_events,
                "successful_events": successful_events,
                "failed_events": failed_events,
                "success_rate": (successful_events / total_events * 100) if total_events > 0 else 100
            },
            "events_by_type": events_by_type
        }
        
    except Exception as e:
        logger.error(f"Error calculating audit statistics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/export")
def export_audit_logs(
    start_time: datetime,
    end_time: datetime,
    format: str = Query("json", description="Export format (json, csv)")
):
    """
    Export audit logs to file.
    
    Args:
        start_time: Start of time range
        end_time: End of time range
        format: Export format (json or csv)
        
    Returns:
        Export data or download link
    """
    storage = get_audit_storage()
    
    if not storage.is_available():
        raise HTTPException(
            status_code=503,
            detail="Audit log storage not available"
        )
    
    query = AuditQuery(
        start_time=start_time,
        end_time=end_time,
        limit=10000
    )
    
    try:
        response = storage.query_events(query)
        events = response.events
        
        if format == "csv":
            # Generate CSV
            import io
            import csv
            
            output = io.StringIO()
            writer = csv.writer(output)
            
            # Header
            writer.writerow([
                "Event ID", "Timestamp", "Event Type", "Severity",
                "User", "Action", "Success", "IP Address",
                "Resource Type", "Resource ID", "Error"
            ])
            
            # Data
            for event in events:
                writer.writerow([
                    event.event_id,
                    event.timestamp.isoformat(),
                    event.event_type.value,
                    event.severity.value,
                    event.username or event.user_id or "anonymous",
                    event.action,
                    event.success,
                    event.ip_address or "",
                    event.resource_type or "",
                    event.resource_id or "",
                    event.error_message or ""
                ])
            
            # Log export event
            audit_logger = get_audit_logger()
            audit_logger.log_data_export(
                export_type="audit_logs",
                record_count=len(events),
                file_format="csv"
            )
            
            return {
                "format": "csv",
                "record_count": len(events),
                "data": output.getvalue()
            }
        
        else:  # JSON format
            # Log export event
            audit_logger = get_audit_logger()
            audit_logger.log_data_export(
                export_type="audit_logs",
                record_count=len(events),
                file_format="json"
            )
            
            return {
                "format": "json",
                "record_count": len(events),
                "events": [event.dict() for event in events]
            }
        
    except Exception as e:
        logger.error(f"Error exporting audit logs: {e}")
        raise HTTPException(status_code=500, detail=str(e))

