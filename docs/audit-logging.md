### Audit Logging & Compliance Reporting

FinOpsGuard provides comprehensive audit logging and compliance reporting capabilities for enterprise deployments, regulatory compliance, and security monitoring.

## Overview

The audit logging system automatically tracks:
- **API Access**: All HTTP requests with user, IP, timestamps
- **Authentication**: Login attempts, successes, failures
- **Policy Events**: Evaluations, violations, changes
- **Data Access**: Exports, sensitive data views
- **Configuration Changes**: Settings and policy updates
- **Security Events**: Threats, violations, blocked requests

## Features

### 1. **Automatic Request Logging**
- Middleware captures all API requests automatically
- Records user, IP address, request details, response status
- Tracks request duration and performance
- Skips health checks and metrics endpoints

### 2. **Event Classification**
40+ event types across categories:
- Authentication (login, logout, failed, token events)
- API access (requests, responses, errors)
- Policy events (created, updated, deleted, violated)
- Data access (viewed, exported)
- Security events (threats, violations)
- System events (start, stop, errors)

### 3. **Severity Levels**
- **DEBUG**: Detailed diagnostic information
- **INFO**: Normal operations
- **WARNING**: Unusual but handled situations
- **ERROR**: Errors that need attention
- **CRITICAL**: Security threats requiring immediate action

### 4. **Multi-Channel Logging**
- **Database**: PostgreSQL for queryable history
- **File**: JSON-formatted log files
- **Console**: Real-time console output (dev mode)

### 5. **Compliance Reporting**
- Automated compliance report generation
- Policy compliance rate tracking
- Authentication success metrics
- Security violation detection
- Top users and activity tracking

### 6. **Search & Filtering**
- Time range queries
- Event type filtering
- User-based filtering
- Full-text search
- Severity filtering
- Resource-based queries

### 7. **Export Capabilities**
- JSON export for analysis
- CSV export for spreadsheets
- Configurable time ranges
- Large dataset support (10,000+ events)

## Configuration

### Enable Audit Logging

Add to `.env`:

```bash
# Enable audit logging
AUDIT_LOGGING_ENABLED=true

# Enable automatic API request logging
AUDIT_MIDDLEWARE_ENABLED=true

# Enable database storage (recommended)
AUDIT_DB_LOGGING=true

# Audit log file path
AUDIT_LOG_FILE=/var/log/finopsguard/audit.log

# Console logging (development only)
AUDIT_CONSOLE_LOGGING=false
```

### Database Setup

Audit logs require PostgreSQL:

```bash
# Enable database
DB_ENABLED=true
DATABASE_URL=postgresql://user:password@localhost:5432/finopsguard

# Run migrations to create audit_logs table
make db-upgrade
```

## API Endpoints

### Check Audit Status

```bash
curl http://localhost:8080/audit/status
```

Response:
```json
{
  "enabled": true,
  "file_logging": true,
  "console_logging": false,
  "database_logging": true,
  "database_available": true
}
```

### Query Audit Logs

```bash
curl -X POST http://localhost:8080/audit/query \
  -H 'Content-Type: application/json' \
  -d '{
    "start_time": "2024-01-01T00:00:00Z",
    "end_time": "2024-01-31T23:59:59Z",
    "event_types": ["api.request", "policy.violated"],
    "limit": 100
  }'
```

### Get Recent Events

```bash
curl "http://localhost:8080/audit/recent?limit=50"
```

### Generate Compliance Report

```bash
curl -X POST http://localhost:8080/audit/compliance/report \
  -H 'Content-Type: application/json' \
  -d '{
    "start_time": "2024-01-01T00:00:00Z",
    "end_time": "2024-01-31T23:59:59Z"
  }'
```

### Get 30-Day Compliance Report

```bash
curl http://localhost:8080/audit/compliance/report/last-30-days
```

### Export Audit Logs

```bash
# Export as JSON
curl -X POST "http://localhost:8080/audit/export?format=json" \
  -d 'start_time=2024-01-01T00:00:00Z&end_time=2024-01-31T23:59:59Z'

# Export as CSV
curl -X POST "http://localhost:8080/audit/export?format=csv" \
  -d 'start_time=2024-01-01T00:00:00Z&end_time=2024-01-31T23:59:59Z'
```

## Python API

### Log Custom Events

```python
from finopsguard.audit import get_audit_logger
from finopsguard.types.audit import AuditEventType

logger = get_audit_logger()

# Log API request
logger.log_event(
    event_type=AuditEventType.API_REQUEST,
    action="POST /api/resource",
    username="admin",
    ip_address="192.168.1.1",
    success=True
)

# Log authentication
logger.log_authentication(
    username="admin",
    success=True,
    ip_address="192.168.1.1",
    auth_method="api_key"
)

# Log policy violation
logger.log_policy_violation(
    policy_id="budget_limit",
    policy_name="Monthly Budget Limit",
    violated_rules=["max_monthly_cost"],
    user_id="user123",
    environment="production"
)
```

### Query Audit Logs

```python
from datetime import datetime, timedelta
from finopsguard.audit import get_audit_storage
from finopsguard.types.audit import AuditQuery, AuditEventType

storage = get_audit_storage()

# Create query
query = AuditQuery(
    start_time=datetime.now() - timedelta(days=7),
    end_time=datetime.now(),
    event_types=[AuditEventType.POLICY_VIOLATED],
    limit=100
)

# Execute query
response = storage.query_events(query)

print(f"Found {response.total_count} policy violations")
for event in response.events:
    print(f"  {event.timestamp}: {event.action}")
```

### Generate Compliance Report

```python
from datetime import datetime, timedelta
from finopsguard.audit.compliance import get_compliance_engine

engine = get_compliance_engine()

# Generate report for last 30 days
end_time = datetime.now()
start_time = end_time - timedelta(days=30)

report = engine.generate_report(start_time, end_time)

print(f"Compliance Status: {report.compliance_status}")
print(f"Policy Compliance Rate: {report.policy_compliance_rate:.1f}%")
print(f"Total Events: {report.total_events}")
print(f"Policy Violations: {report.total_policy_violations}")
```

## Audit Event Structure

### Event Fields

```json
{
  "event_id": "a1b2c3d4e5f6...",
  "event_type": "api.request",
  "severity": "info",
  "timestamp": "2024-01-15T10:30:00Z",
  "user_id": "user123",
  "username": "admin",
  "user_role": "admin",
  "ip_address": "192.168.1.1",
  "user_agent": "curl/7.68.0",
  "request_id": "req-abc123",
  "action": "POST /mcp/checkCostImpact",
  "resource_type": "analysis",
  "resource_id": "analysis-123",
  "success": true,
  "http_method": "POST",
  "http_path": "/mcp/checkCostImpact",
  "http_status": 200,
  "compliance_tags": ["api_access"],
  "details": {},
  "metadata": {"duration_ms": 245}
}
```

## Compliance Report Structure

```json
{
  "report_id": "report-xyz789",
  "generated_at": "2024-02-01T00:00:00Z",
  "start_time": "2024-01-01T00:00:00Z",
  "end_time": "2024-01-31T23:59:59Z",
  "total_events": 5000,
  "total_api_requests": 3500,
  "total_policy_evaluations": 150,
  "total_policy_violations": 5,
  "total_auth_attempts": 100,
  "failed_auth_attempts": 2,
  "policy_compliance_rate": 96.7,
  "authentication_success_rate": 98.0,
  "compliance_status": "compliant",
  "events_by_type": {...},
  "events_by_user": {...},
  "top_users": [...],
  "policy_violations": [...],
  "critical_events": [...]
}
```

## Use Cases

### 1. Security Monitoring
- Track all authentication attempts
- Detect suspicious IP addresses
- Monitor failed API requests
- Identify security violations

### 2. Compliance Auditing
- Prove policy enforcement
- Track configuration changes
- Generate audit trails
- Meet regulatory requirements

### 3. Incident Investigation
- Reconstruct event timelines
- Identify root causes
- Track user actions
- Debug issues

### 4. Performance Monitoring
- Track API request volumes
- Identify slow endpoints
- Monitor error rates
- Capacity planning

## Best Practices

### 1. Regular Compliance Reports
```python
# Schedule monthly compliance reports
from finopsguard.audit.compliance import get_compliance_engine
import schedule

def generate_monthly_report():
    engine = get_compliance_engine()
    end_time = datetime.now()
    start_time = end_time - timedelta(days=30)
    report = engine.generate_report(start_time, end_time)
    # Email or store report
    ...

schedule.every().month.do(generate_monthly_report)
```

### 2. Alert on Critical Events
Monitor for critical severity events and send alerts.

### 3. Retention Policies
Implement log retention to manage database size:
```sql
-- Delete audit logs older than 1 year
DELETE FROM audit_logs WHERE timestamp < NOW() - INTERVAL '365 days';
```

### 4. Regular Exports
Export audit logs regularly for long-term archival.

## Security Considerations

### Access Control
- Audit log access should be restricted to admin users
- Implement RBAC for audit endpoints
- Encrypt audit log files at rest

### Data Privacy
- Consider PII in audit logs
- Implement data retention policies
- Comply with GDPR/CCPA if applicable

### Tamper Protection
- Audit logs should be append-only
- Consider write-once storage
- Regular integrity checks

## Troubleshooting

### No Audit Logs Appearing

1. **Check if enabled**:
   ```bash
   curl http://localhost:8080/audit/status
   ```

2. **Verify database connection**:
   ```bash
   curl http://localhost:8080/healthz
   ```

3. **Check file permissions**:
   ```bash
   ls -la /var/log/finopsguard/audit.log
   ```

### Database Storage Not Working

1. Enable database in `.env`:
   ```bash
   DB_ENABLED=true
   DATABASE_URL=postgresql://...
   ```

2. Run migrations:
   ```bash
   make db-upgrade
   ```

### High Log Volume

1. Adjust retention policies
2. Implement log rotation
3. Use time-based partitioning
4. Archive old logs to object storage

## Performance

### Database Indexes
Audit log table has optimized indexes:
- Timestamp + Event Type (common query)
- Username + Timestamp (user activity)
- Resource Type + Resource ID (resource tracking)

### Caching
Compliance reports can be cached for frequently accessed periods.

### Async Logging
Audit logging is designed to minimize impact on request latency.

## Regulatory Compliance

Audit logging supports compliance with:
- **SOC 2**: Access logging and monitoring
- **GDPR**: Data access tracking
- **HIPAA**: Audit trail requirements
- **PCI DSS**: Logging and monitoring
- **ISO 27001**: Information security management

## See Also

- [Authentication Guide](authentication.md)
- [Database Configuration](database.md)
- [Deployment Guide](deployment.md)
- [API Documentation](api/openapi.yaml)

---

**Last Updated**: October 2025
**Version**: 0.3.0
**Status**: Production Ready ✅

