// FinOpsGuard Audit Logging Module

// Global functions for audit dashboard
async function loadAuditStatus() {
    try {
        const response = await fetch(`${app.apiBaseUrl}/audit/status`);
        const data = await response.json();
        
        const banner = document.getElementById('audit-status-banner');
        if (data.enabled && data.database_available) {
            banner.innerHTML = `
                <div class="status-success">
                    <i class="fas fa-check-circle"></i>
                    <span>Audit Logging Active - Database: ✓ File: ${data.file_logging ? '✓' : '✗'}</span>
                </div>
            `;
        } else if (data.enabled) {
            banner.innerHTML = `
                <div class="status-warning">
                    <i class="fas fa-exclamation-triangle"></i>
                    <span>Audit Logging Enabled but Database Not Available - Using file logging only</span>
                </div>
            `;
        } else {
            banner.innerHTML = `
                <div class="status-error">
                    <i class="fas fa-times-circle"></i>
                    <span>Audit Logging Disabled - Set AUDIT_LOGGING_ENABLED=true to enable</span>
                </div>
            `;
        }
    } catch (error) {
        console.error('Error loading audit status:', error);
        document.getElementById('audit-status-banner').innerHTML = `
            <div class="status-error">
                <i class="fas fa-times-circle"></i>
                <span>Unable to check audit status</span>
            </div>
        `;
    }
}

async function loadAuditLogs() {
    const tbody = document.getElementById('audit-table-body');
    tbody.innerHTML = '<tr><td colspan="7" class="loading">Loading...</td></tr>';
    
    try {
        const days = document.getElementById('audit-date-range').value;
        const eventType = document.getElementById('audit-event-type').value;
        const severity = document.getElementById('audit-severity').value;
        
        const response = await fetch(`${app.apiBaseUrl}/audit/recent?limit=50&event_type=${eventType || ''}`);
        const data = await response.json();
        
        if (!data.events || data.events.length === 0) {
            tbody.innerHTML = '<tr><td colspan="7" class="no-data">No audit events found</td></tr>';
            return;
        }
        
        tbody.innerHTML = data.events.map(event => {
            const timestamp = new Date(event.timestamp).toLocaleString();
            const statusBadge = event.success 
                ? '<span class="status-badge success">Success</span>'
                : '<span class="status-badge error">Failed</span>';
            
            const severityClass = event.severity || 'info';
            
            return `
                <tr class="severity-${severityClass}">
                    <td>${timestamp}</td>
                    <td><span class="event-type-badge">${event.event_type}</span></td>
                    <td>${event.username || event.user_id || 'anonymous'}</td>
                    <td title="${event.action}">${truncate(event.action, 50)}</td>
                    <td>${statusBadge}</td>
                    <td>${event.ip_address || '—'}</td>
                    <td><button class="btn-link" onclick="showEventDetails('${event.event_id}')">View</button></td>
                </tr>
            `;
        }).join('');
        
        // Update stats
        await loadComplianceStats();
        
    } catch (error) {
        console.error('Error loading audit logs:', error);
        tbody.innerHTML = '<tr><td colspan="7" class="error">Error loading audit logs</td></tr>';
        app.showToast('Error loading audit logs', 'error');
    }
}

async function loadComplianceStats() {
    try {
        const response = await fetch(`${app.apiBaseUrl}/audit/compliance/report/last-30-days`);
        const report = await response.json();
        
        document.getElementById('compliance-rate').textContent = 
            report.policy_compliance_rate.toFixed(1) + '%';
        document.getElementById('policy-violations-count').textContent = 
            report.total_policy_violations;
        document.getElementById('auth-success-rate').textContent = 
            report.authentication_success_rate.toFixed(1) + '%';
        document.getElementById('total-audit-events').textContent = 
            report.total_events.toLocaleString();
        
        // Update trends
        const complianceClass = report.policy_compliance_rate >= 95 ? 'trend-good' : 
                               report.policy_compliance_rate >= 80 ? 'trend-warning' : 'trend-bad';
        document.getElementById('compliance-trend').className = `compliance-trend ${complianceClass}`;
        document.getElementById('compliance-trend').textContent = 
            report.compliance_status.charAt(0).toUpperCase() + report.compliance_status.slice(1);
        
    } catch (error) {
        console.error('Error loading compliance stats:', error);
    }
}

async function generateComplianceReport() {
    const reportCard = document.getElementById('compliance-report');
    const reportContent = document.getElementById('compliance-report-content');
    
    reportContent.innerHTML = '<div class="loading">Generating compliance report...</div>';
    reportCard.style.display = 'block';
    
    try {
        const response = await fetch(`${app.apiBaseUrl}/audit/compliance/report/last-30-days`);
        const report = await response.json();
        
        reportContent.innerHTML = `
            <div class="report-summary">
                <h4>Compliance Summary (Last 30 Days)</h4>
                <div class="report-metrics">
                    <div class="report-metric">
                        <span class="metric-label">Total Events:</span>
                        <span class="metric-value">${report.total_events.toLocaleString()}</span>
                    </div>
                    <div class="report-metric">
                        <span class="metric-label">API Requests:</span>
                        <span class="metric-value">${report.total_api_requests.toLocaleString()}</span>
                    </div>
                    <div class="report-metric">
                        <span class="metric-label">Policy Evaluations:</span>
                        <span class="metric-value">${report.total_policy_evaluations}</span>
                    </div>
                    <div class="report-metric">
                        <span class="metric-label">Policy Violations:</span>
                        <span class="metric-value">${report.total_policy_violations}</span>
                    </div>
                    <div class="report-metric">
                        <span class="metric-label">Policy Compliance:</span>
                        <span class="metric-value ${report.policy_compliance_rate >= 95 ? 'good' : 'warning'}">
                            ${report.policy_compliance_rate.toFixed(1)}%
                        </span>
                    </div>
                    <div class="report-metric">
                        <span class="metric-label">Auth Success Rate:</span>
                        <span class="metric-value ${report.authentication_success_rate >= 95 ? 'good' : 'warning'}">
                            ${report.authentication_success_rate.toFixed(1)}%
                        </span>
                    </div>
                </div>
            </div>
            
            ${report.policy_violations.length > 0 ? `
                <div class="report-section">
                    <h4><i class="fas fa-exclamation-triangle"></i> Policy Violations</h4>
                    <div class="violations-list">
                        ${report.policy_violations.slice(0, 10).map(v => `
                            <div class="violation-item">
                                <span class="violation-time">${new Date(v.timestamp).toLocaleString()}</span>
                                <span class="violation-policy">${v.policy_name}</span>
                                <span class="violation-user">${v.user}</span>
                                <span class="violation-env">${v.environment || 'N/A'}</span>
                            </div>
                        `).join('')}
                    </div>
                </div>
            ` : ''}
            
            <div class="report-section">
                <h4><i class="fas fa-users"></i> Top Users</h4>
                <div class="top-users-list">
                    ${report.top_users.slice(0, 5).map(u => `
                        <div class="top-user-item">
                            <span class="user-name">${u.user}</span>
                            <span class="user-count">${u.event_count} events</span>
                        </div>
                    `).join('')}
                </div>
            </div>
            
            <div class="report-actions">
                <button class="btn btn-primary" onclick="exportComplianceReport()">
                    <i class="fas fa-download"></i> Export Report
                </button>
            </div>
        `;
        
    } catch (error) {
        console.error('Error generating compliance report:', error);
        reportContent.innerHTML = '<div class="error">Error generating report</div>';
        app.showToast('Error generating compliance report', 'error');
    }
}

function closeComplianceReport() {
    document.getElementById('compliance-report').style.display = 'none';
}

async function exportAuditLogs() {
    try {
        const days = parseInt(document.getElementById('audit-date-range').value);
        const endTime = new Date();
        const startTime = new Date();
        startTime.setDate(endTime.getDate() - days);
        
        const response = await fetch(
            `${app.apiBaseUrl}/audit/export?format=csv` +
            `&start_time=${startTime.toISOString()}` +
            `&end_time=${endTime.toISOString()}`,
            { method: 'POST' }
        );
        
        const data = await response.json();
        
        // Download CSV
        const blob = new Blob([data.data], { type: 'text/csv' });
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `audit-logs-${new Date().toISOString().split('T')[0]}.csv`;
        a.click();
        window.URL.revokeObjectURL(url);
        
        app.showToast(`Exported ${data.record_count} audit events`, 'success');
        
    } catch (error) {
        console.error('Error exporting audit logs:', error);
        app.showToast('Error exporting audit logs', 'error');
    }
}

async function exportComplianceReport() {
    // Download compliance report as JSON
    try {
        const response = await fetch(`${app.apiBaseUrl}/audit/compliance/report/last-30-days`);
        const report = await response.json();
        
        const blob = new Blob([JSON.stringify(report, null, 2)], { type: 'application/json' });
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `compliance-report-${new Date().toISOString().split('T')[0]}.json`;
        a.click();
        window.URL.revokeObjectURL(url);
        
        app.showToast('Compliance report downloaded', 'success');
        
    } catch (error) {
        console.error('Error exporting compliance report:', error);
        app.showToast('Error exporting report', 'error');
    }
}

function showEventDetails(eventId) {
    app.showToast('Event details view coming soon', 'info');
}

function truncate(str, maxLength) {
    if (!str) return '';
    return str.length > maxLength ? str.substring(0, maxLength) + '...' : str;
}

// Initialize audit dashboard when section is loaded
document.addEventListener('DOMContentLoaded', () => {
    // Event listeners for audit filters
    document.getElementById('audit-date-range')?.addEventListener('change', loadAuditLogs);
    document.getElementById('audit-event-type')?.addEventListener('change', loadAuditLogs);
    document.getElementById('audit-severity')?.addEventListener('change', loadAuditLogs);
});

