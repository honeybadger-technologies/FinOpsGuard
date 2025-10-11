"""Compliance reporting engine."""

import logging
from datetime import datetime

from finopsguard.types.audit import (
    ComplianceReport,
    AuditQuery,
    AuditEventType,
    AuditSeverity
)
from .storage import get_audit_storage

logger = logging.getLogger(__name__)


class ComplianceEngine:
    """Generate compliance reports from audit logs."""
    
    def __init__(self):
        """Initialize compliance engine."""
        self.storage = get_audit_storage()
    
    def generate_report(
        self,
        start_time: datetime,
        end_time: datetime
    ) -> ComplianceReport:
        """
        Generate compliance report for a time period.
        
        Args:
            start_time: Start of reporting period
            end_time: End of reporting period
            
        Returns:
            ComplianceReport
        """
        # Query all events in period
        query = AuditQuery(
            start_time=start_time,
            end_time=end_time,
            limit=10000  # Large limit for reporting
        )
        
        response = self.storage.query_events(query)
        events = response.events
        
        # Initialize counters
        total_events = len(events)
        total_api_requests = 0
        total_policy_evaluations = 0
        total_policy_violations = 0
        total_auth_attempts = 0
        failed_auth_attempts = 0
        security_violations = 0
        blocked_requests = 0
        
        events_by_type = {}
        events_by_severity = {}
        events_by_user = {}
        
        policy_violations = []
        critical_events = []
        
        # Process events
        for event in events:
            # Count by type
            event_type_str = event.event_type.value
            events_by_type[event_type_str] = events_by_type.get(event_type_str, 0) + 1
            
            # Count by severity
            severity_str = event.severity.value
            events_by_severity[severity_str] = events_by_severity.get(severity_str, 0) + 1
            
            # Count by user
            user_key = event.username or event.user_id or "anonymous"
            events_by_user[user_key] = events_by_user.get(user_key, 0) + 1
            
            # API requests
            if event.event_type == AuditEventType.API_REQUEST:
                total_api_requests += 1
                if not event.success or (event.http_status and event.http_status >= 400):
                    blocked_requests += 1
            
            # Policy evaluations and violations
            if event.event_type == AuditEventType.POLICY_EVALUATED:
                total_policy_evaluations += 1
            
            if event.event_type == AuditEventType.POLICY_VIOLATED:
                total_policy_violations += 1
                policy_violations.append({
                    "timestamp": event.timestamp.isoformat(),
                    "policy_id": event.resource_id,
                    "policy_name": event.details.get("policy_name", "Unknown"),
                    "user": event.username or "anonymous",
                    "environment": event.details.get("environment")
                })
            
            # Authentication
            if event.event_type in [AuditEventType.AUTH_LOGIN, AuditEventType.AUTH_FAILED]:
                total_auth_attempts += 1
                if not event.success:
                    failed_auth_attempts += 1
            
            # Security violations
            if event.event_type == AuditEventType.SECURITY_VIOLATION:
                security_violations += 1
            
            # Critical events
            if event.severity == AuditSeverity.CRITICAL:
                critical_events.append(event)
        
        # Calculate compliance metrics
        if total_policy_evaluations > 0:
            policy_compliance_rate = ((total_policy_evaluations - total_policy_violations) / 
                                     total_policy_evaluations * 100)
        else:
            policy_compliance_rate = 100.0
        
        if total_auth_attempts > 0:
            authentication_success_rate = ((total_auth_attempts - failed_auth_attempts) / 
                                          total_auth_attempts * 100)
        else:
            authentication_success_rate = 100.0
        
        # Top users
        top_users = [
            {"user": user, "event_count": count}
            for user, count in sorted(events_by_user.items(), key=lambda x: x[1], reverse=True)[:10]
        ]
        
        # Determine compliance status
        compliance_status = "compliant"
        compliance_notes = []
        
        if total_policy_violations > 0:
            compliance_status = "review"
            compliance_notes.append(f"{total_policy_violations} policy violations detected")
        
        if failed_auth_attempts > (total_auth_attempts * 0.1):  # >10% failure rate
            compliance_status = "review"
            compliance_notes.append("High authentication failure rate")
        
        if security_violations > 0:
            compliance_status = "non-compliant"
            compliance_notes.append(f"{security_violations} security violations detected")
        
        # Create report
        report = ComplianceReport(
            start_time=start_time,
            end_time=end_time,
            total_events=total_events,
            total_api_requests=total_api_requests,
            total_policy_evaluations=total_policy_evaluations,
            total_policy_violations=total_policy_violations,
            total_auth_attempts=total_auth_attempts,
            failed_auth_attempts=failed_auth_attempts,
            events_by_type=events_by_type,
            events_by_severity=events_by_severity,
            events_by_user=events_by_user,
            security_violations=security_violations,
            blocked_requests=blocked_requests,
            policy_compliance_rate=policy_compliance_rate,
            authentication_success_rate=authentication_success_rate,
            top_users=top_users,
            policy_violations=policy_violations[:100],  # Limit to 100
            critical_events=critical_events[:50],  # Limit to 50
            compliance_status=compliance_status,
            compliance_notes=compliance_notes
        )
        
        return report


# Global singleton
_compliance_engine = None


def get_compliance_engine() -> ComplianceEngine:
    """
    Get global compliance engine instance.
    
    Returns:
        ComplianceEngine instance
    """
    global _compliance_engine
    if _compliance_engine is None:
        _compliance_engine = ComplianceEngine()
    return _compliance_engine

