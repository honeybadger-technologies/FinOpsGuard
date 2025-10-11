"""Audit logging types and models."""

from datetime import datetime
from typing import Dict, List, Optional, Any
from enum import Enum
from pydantic import BaseModel, Field


class AuditEventType(str, Enum):
    """Types of audit events."""
    
    # Authentication events
    AUTH_LOGIN = "auth.login"
    AUTH_LOGOUT = "auth.logout"
    AUTH_FAILED = "auth.failed"
    AUTH_TOKEN_CREATED = "auth.token_created"
    AUTH_TOKEN_REVOKED = "auth.token_revoked"
    
    # API access events
    API_REQUEST = "api.request"
    API_RESPONSE = "api.response"
    API_ERROR = "api.error"
    
    # Policy events
    POLICY_CREATED = "policy.created"
    POLICY_UPDATED = "policy.updated"
    POLICY_DELETED = "policy.deleted"
    POLICY_EVALUATED = "policy.evaluated"
    POLICY_VIOLATED = "policy.violated"
    POLICY_ENFORCED = "policy.enforced"
    
    # Analysis events
    ANALYSIS_CREATED = "analysis.created"
    ANALYSIS_VIEWED = "analysis.viewed"
    ANALYSIS_EXPORTED = "analysis.exported"
    
    # Configuration events
    CONFIG_CHANGED = "config.changed"
    SETTINGS_UPDATED = "settings.updated"
    
    # Data access events
    DATA_ACCESSED = "data.accessed"
    DATA_EXPORTED = "data.exported"
    
    # Security events
    SECURITY_THREAT = "security.threat"
    SECURITY_VIOLATION = "security.violation"
    
    # System events
    SYSTEM_START = "system.start"
    SYSTEM_STOP = "system.stop"
    SYSTEM_ERROR = "system.error"


class AuditSeverity(str, Enum):
    """Severity levels for audit events."""
    
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class AuditEvent(BaseModel):
    """Single audit event."""
    
    # Event identification
    event_id: str = Field(default_factory=lambda: __import__('uuid').uuid4().hex)
    event_type: AuditEventType
    severity: AuditSeverity = AuditSeverity.INFO
    
    # Timestamp
    timestamp: datetime = Field(default_factory=datetime.now)
    
    # Actor (who)
    user_id: Optional[str] = None
    username: Optional[str] = None
    user_role: Optional[str] = None
    api_key_name: Optional[str] = None
    
    # Source (from where)
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    request_id: Optional[str] = None
    
    # Action (what)
    action: str
    resource_type: Optional[str] = None
    resource_id: Optional[str] = None
    
    # Details
    details: Dict[str, Any] = Field(default_factory=dict)
    
    # Result
    success: bool = True
    error_message: Optional[str] = None
    
    # HTTP context (if applicable)
    http_method: Optional[str] = None
    http_path: Optional[str] = None
    http_status: Optional[int] = None
    
    # Compliance tags
    compliance_tags: List[str] = Field(default_factory=list)
    
    # Additional metadata
    metadata: Dict[str, Any] = Field(default_factory=dict)


class AuditQuery(BaseModel):
    """Query parameters for retrieving audit logs."""
    
    # Time range
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    
    # Filters
    event_types: Optional[List[AuditEventType]] = None
    severities: Optional[List[AuditSeverity]] = None
    user_ids: Optional[List[str]] = None
    usernames: Optional[List[str]] = None
    actions: Optional[List[str]] = None
    resource_types: Optional[List[str]] = None
    success: Optional[bool] = None
    
    # Search
    search_term: Optional[str] = None
    
    # Compliance
    compliance_tags: Optional[List[str]] = None
    
    # Pagination
    limit: int = 100
    offset: int = 0
    
    # Sorting
    sort_by: str = "timestamp"
    sort_order: str = "desc"  # asc or desc


class ComplianceReport(BaseModel):
    """Compliance report for audit logs."""
    
    # Report metadata
    report_id: str = Field(default_factory=lambda: __import__('uuid').uuid4().hex)
    generated_at: datetime = Field(default_factory=datetime.now)
    
    # Time period
    start_time: datetime
    end_time: datetime
    
    # Summary statistics
    total_events: int
    total_api_requests: int
    total_policy_evaluations: int
    total_policy_violations: int
    total_auth_attempts: int
    failed_auth_attempts: int
    
    # Event breakdown
    events_by_type: Dict[str, int] = Field(default_factory=dict)
    events_by_severity: Dict[str, int] = Field(default_factory=dict)
    events_by_user: Dict[str, int] = Field(default_factory=dict)
    
    # Security metrics
    security_violations: int = 0
    blocked_requests: int = 0
    
    # Compliance metrics
    policy_compliance_rate: float = 100.0  # Percentage
    authentication_success_rate: float = 100.0  # Percentage
    
    # Top actors
    top_users: List[Dict[str, Any]] = Field(default_factory=list)
    top_ips: List[Dict[str, Any]] = Field(default_factory=list)
    
    # Policy violations
    policy_violations: List[Dict[str, Any]] = Field(default_factory=list)
    
    # Recent critical events
    critical_events: List[AuditEvent] = Field(default_factory=list)
    
    # Compliance status
    compliance_status: str = "compliant"  # compliant, non-compliant, review
    compliance_notes: List[str] = Field(default_factory=list)


class AuditLogResponse(BaseModel):
    """Response for audit log queries."""
    
    events: List[AuditEvent]
    total_count: int
    has_more: bool
    next_offset: Optional[int] = None

