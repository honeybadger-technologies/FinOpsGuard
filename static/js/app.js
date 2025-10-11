// FinOpsGuard Admin UI JavaScript
class FinOpsGuardAdmin {
    constructor() {
        this.apiBaseUrl = 'http://localhost:8080';
        this.currentPolicy = null;
        this.refreshInterval = null;
        this.analytics = null;
        this.init();
    }

    init() {
        this.setupNavigation();
        this.setupEventListeners();
        this.loadDashboard();
        this.startAutoRefresh();
        
        // Initialize analytics module when DOM is ready
        if (typeof FinOpsAnalytics !== 'undefined') {
            this.analytics = new FinOpsAnalytics(this);
        }
    }

    setupNavigation() {
        const navLinks = document.querySelectorAll('.nav-link');
        navLinks.forEach(link => {
            link.addEventListener('click', (e) => {
                e.preventDefault();
                const section = link.getAttribute('data-section');
                this.showSection(section);
            });
        });
    }

    setupEventListeners() {
        // Policy filters
        document.getElementById('policy-search')?.addEventListener('input', () => {
            this.filterPolicies();
        });
        document.getElementById('policy-status-filter')?.addEventListener('change', () => {
            this.filterPolicies();
        });

        // Analysis filters
        document.getElementById('analysis-search')?.addEventListener('input', () => {
            this.filterAnalyses();
        });
        document.getElementById('analysis-environment-filter')?.addEventListener('change', () => {
            this.filterAnalyses();
        });

        // Settings
        document.getElementById('api-base-url')?.addEventListener('change', (e) => {
            this.apiBaseUrl = e.target.value;
            localStorage.setItem('apiBaseUrl', this.apiBaseUrl);
        });

        // Load saved settings
        const savedApiUrl = localStorage.getItem('apiBaseUrl');
        if (savedApiUrl) {
            this.apiBaseUrl = savedApiUrl;
            document.getElementById('api-base-url').value = savedApiUrl;
        }
    }

    showSection(sectionName) {
        // Hide all sections
        document.querySelectorAll('.content-section').forEach(section => {
            section.classList.remove('active');
        });

        // Remove active class from nav links
        document.querySelectorAll('.nav-link').forEach(link => {
            link.classList.remove('active');
        });

        // Show target section
        document.getElementById(sectionName).classList.add('active');
        document.querySelector(`[data-section="${sectionName}"]`).classList.add('active');

        // Load section data
        switch (sectionName) {
            case 'dashboard':
                this.loadDashboard();
                break;
            case 'policies':
                this.loadPolicies();
                break;
            case 'analyses':
                this.loadAnalyses();
                break;
            case 'analytics':
                if (this.analytics) {
                    this.analytics.loadAnalytics();
                }
                break;
        }
    }

    async loadDashboard() {
        try {
            const [analyses, policies] = await Promise.all([
                this.fetchAnalyses(),
                this.fetchPolicies()
            ]);

            this.updateDashboardStats(analyses, policies);
            this.updateRecentAnalyses(analyses);
            this.updatePolicyStatus(policies);
        } catch (error) {
            console.error('Error loading dashboard:', error);
            this.showToast('Error loading dashboard', 'error');
        }
    }

    updateDashboardStats(analyses, policies) {
        const totalAnalyses = analyses.length;
        const activePolicies = policies.filter(p => p.enabled).length;
        const policyViolations = analyses.filter(a => 
            a.risk_flags && a.risk_flags.includes('policy_violation')
        ).length;
        const totalCost = analyses.reduce((sum, a) => sum + (a.estimated_monthly_cost || 0), 0);

        document.getElementById('total-analyses').textContent = totalAnalyses;
        document.getElementById('active-policies').textContent = activePolicies;
        document.getElementById('policy-violations').textContent = policyViolations;
        document.getElementById('total-cost').textContent = `$${totalCost.toFixed(2)}`;
    }

    updateRecentAnalyses(analyses) {
        const container = document.getElementById('recent-analyses');
        const recentAnalyses = analyses.slice(0, 5);

        if (recentAnalyses.length === 0) {
            container.innerHTML = '<div class="text-center text-muted">No recent analyses</div>';
            return;
        }

        container.innerHTML = recentAnalyses.map(analysis => `
            <div class="activity-item">
                <div class="activity-info">
                    <div class="activity-title">${analysis.environment || 'Unknown'} Environment</div>
                    <div class="activity-time">${new Date(analysis.timestamp).toLocaleString()}</div>
                </div>
                <div class="activity-detail-value">$${analysis.estimated_monthly_cost?.toFixed(2) || '0.00'}</div>
            </div>
        `).join('');
    }

    updatePolicyStatus(policies) {
        const container = document.getElementById('policy-status');
        const enabledPolicies = policies.filter(p => p.enabled);
        const disabledPolicies = policies.filter(p => !p.enabled);

        container.innerHTML = `
            <div class="policy-status-item">
                <span>Enabled Policies</span>
                <span class="policy-status enabled">${enabledPolicies.length}</span>
            </div>
            <div class="policy-status-item">
                <span>Disabled Policies</span>
                <span class="policy-status disabled">${disabledPolicies.length}</span>
            </div>
            <div class="policy-status-item">
                <span>Total Policies</span>
                <span class="policy-status">${policies.length}</span>
            </div>
        `;
    }

    async loadPolicies() {
        try {
            const policies = await this.fetchPolicies();
            this.renderPolicies(policies);
        } catch (error) {
            console.error('Error loading policies:', error);
            this.showToast('Error loading policies', 'error');
        }
    }

    async fetchPolicies() {
        const response = await fetch(`${this.apiBaseUrl}/mcp/policies`);
        if (!response.ok) {
            throw new Error('Failed to fetch policies');
        }
        return await response.json();
    }

    renderPolicies(policies) {
        const container = document.getElementById('policies-list');
        
        if (policies.length === 0) {
            container.innerHTML = '<div class="text-center text-muted">No policies found</div>';
            return;
        }

        container.innerHTML = policies.map(policy => `
            <div class="policy-item">
                <div class="policy-info">
                    <h4>${policy.name}</h4>
                    <p>${policy.description || 'No description'}</p>
                    <div class="policy-meta">
                        <span>${policy.rules?.length || 0} rules</span>
                        <span>Created: ${new Date(policy.created_at).toLocaleDateString()}</span>
                    </div>
                </div>
                <div class="policy-actions">
                    <span class="policy-status ${policy.enabled ? 'enabled' : 'disabled'}">
                        ${policy.enabled ? 'Enabled' : 'Disabled'}
                    </span>
                    <button class="btn btn-primary btn-sm" onclick="admin.editPolicy('${policy.id}')">
                        <i class="fas fa-edit"></i> Edit
                    </button>
                    <button class="btn btn-danger btn-sm" onclick="admin.deletePolicy('${policy.id}')">
                        <i class="fas fa-trash"></i> Delete
                    </button>
                </div>
            </div>
        `).join('');
    }

    filterPolicies() {
        const searchTerm = document.getElementById('policy-search').value.toLowerCase();
        const statusFilter = document.getElementById('policy-status-filter').value;
        
        const policyItems = document.querySelectorAll('.policy-item');
        
        policyItems.forEach(item => {
            const title = item.querySelector('h4').textContent.toLowerCase();
            const status = item.querySelector('.policy-status').classList.contains('enabled') ? 'enabled' : 'disabled';
            
            const matchesSearch = title.includes(searchTerm);
            const matchesStatus = !statusFilter || status === statusFilter;
            
            item.style.display = matchesSearch && matchesStatus ? 'flex' : 'none';
        });
    }

    async loadAnalyses() {
        try {
            const analyses = await this.fetchAnalyses();
            this.renderAnalyses(analyses);
        } catch (error) {
            console.error('Error loading analyses:', error);
            this.showToast('Error loading analyses', 'error');
        }
    }

    async fetchAnalyses() {
        const response = await fetch(`${this.apiBaseUrl}/mcp/listRecentAnalyses`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ limit: 100 })
        });
        if (!response.ok) {
            throw new Error('Failed to fetch analyses');
        }
        const data = await response.json();
        return data.analyses || [];
    }

    renderAnalyses(analyses) {
        const container = document.getElementById('analyses-list');
        
        if (analyses.length === 0) {
            container.innerHTML = '<div class="text-center text-muted">No analyses found</div>';
            return;
        }

        container.innerHTML = analyses.map(analysis => `
            <div class="analysis-item" onclick="admin.showAnalysisDetails('${analysis.id}')">
                <div class="analysis-header">
                    <div class="analysis-title">${analysis.environment || 'Unknown'} Environment</div>
                    <div class="analysis-date">${new Date(analysis.timestamp).toLocaleString()}</div>
                </div>
                <div class="analysis-details">
                    <div class="analysis-detail">
                        <div class="analysis-detail-label">Monthly Cost</div>
                        <div class="analysis-detail-value">$${analysis.estimated_monthly_cost?.toFixed(2) || '0.00'}</div>
                    </div>
                    <div class="analysis-detail">
                        <div class="analysis-detail-label">Resources</div>
                        <div class="analysis-detail-value">${analysis.resource_count || 0}</div>
                    </div>
                    <div class="analysis-detail">
                        <div class="analysis-detail-label">Risk Flags</div>
                        <div class="analysis-detail-value">
                            ${(analysis.risk_flags || []).map(flag => 
                                `<span class="risk-flag ${flag.replace('_', '-')}">${flag}</span>`
                            ).join('')}
                        </div>
                    </div>
                </div>
            </div>
        `).join('');
    }

    filterAnalyses() {
        const searchTerm = document.getElementById('analysis-search').value.toLowerCase();
        const environmentFilter = document.getElementById('analysis-environment-filter').value;
        
        const analysisItems = document.querySelectorAll('.analysis-item');
        
        analysisItems.forEach(item => {
            const title = item.querySelector('.analysis-title').textContent.toLowerCase();
            const environment = title.split(' ')[0].toLowerCase();
            
            const matchesSearch = title.includes(searchTerm);
            const matchesEnvironment = !environmentFilter || environment === environmentFilter;
            
            item.style.display = matchesSearch && matchesEnvironment ? 'block' : 'none';
        });
    }

    async showAnalysisDetails(analysisId) {
        try {
            const analyses = await this.fetchAnalyses();
            const analysis = analyses.find(a => a.id === analysisId);
            
            if (!analysis) {
                this.showToast('Analysis not found', 'error');
                return;
            }

            this.renderAnalysisModal(analysis);
            this.openAnalysisModal();
        } catch (error) {
            console.error('Error loading analysis details:', error);
            this.showToast('Error loading analysis details', 'error');
        }
    }

    renderAnalysisModal(analysis) {
        const container = document.getElementById('analysis-details');
        
        container.innerHTML = `
            <div class="analysis-detail-grid">
                <div class="detail-section">
                    <h4>Basic Information</h4>
                    <div class="detail-item">
                        <strong>Environment:</strong> ${analysis.environment || 'Unknown'}
                    </div>
                    <div class="detail-item">
                        <strong>Timestamp:</strong> ${new Date(analysis.timestamp).toLocaleString()}
                    </div>
                    <div class="detail-item">
                        <strong>Duration:</strong> ${analysis.duration_ms || 0}ms
                    </div>
                </div>

                <div class="detail-section">
                    <h4>Cost Information</h4>
                    <div class="detail-item">
                        <strong>Monthly Cost:</strong> $${analysis.estimated_monthly_cost?.toFixed(2) || '0.00'}
                    </div>
                    <div class="detail-item">
                        <strong>Weekly Cost:</strong> $${analysis.estimated_first_week_cost?.toFixed(2) || '0.00'}
                    </div>
                    <div class="detail-item">
                        <strong>Pricing Confidence:</strong> ${analysis.pricing_confidence || 'Unknown'}
                    </div>
                </div>

                <div class="detail-section">
                    <h4>Resources (${analysis.resource_count || 0})</h4>
                    ${analysis.breakdown_by_resource ? analysis.breakdown_by_resource.map(resource => `
                        <div class="resource-item">
                            <strong>${resource.type}</strong> - ${resource.size || 'N/A'}
                            <span class="resource-cost">$${resource.estimated_monthly_cost?.toFixed(2) || '0.00'}</span>
                        </div>
                    `).join('') : '<div class="text-muted">No resource breakdown available</div>'}
                </div>

                ${analysis.risk_flags && analysis.risk_flags.length > 0 ? `
                <div class="detail-section">
                    <h4>Risk Flags</h4>
                    ${analysis.risk_flags.map(flag => `
                        <span class="risk-flag ${flag.replace('_', '-')}">${flag}</span>
                    `).join('')}
                </div>
                ` : ''}

                ${analysis.recommendations && analysis.recommendations.length > 0 ? `
                <div class="detail-section">
                    <h4>Recommendations</h4>
                    <ul>
                        ${analysis.recommendations.map(rec => `<li>${rec}</li>`).join('')}
                    </ul>
                </div>
                ` : ''}

                ${analysis.policy_eval ? `
                <div class="detail-section">
                    <h4>Policy Evaluation</h4>
                    <div class="detail-item">
                        <strong>Status:</strong> 
                        <span class="policy-status ${analysis.policy_eval.status === 'pass' ? 'enabled' : 'disabled'}">
                            ${analysis.policy_eval.status}
                        </span>
                    </div>
                    <div class="detail-item">
                        <strong>Policy ID:</strong> ${analysis.policy_eval.policy_id || 'N/A'}
                    </div>
                    ${analysis.policy_eval.message ? `
                        <div class="detail-item">
                            <strong>Message:</strong> ${analysis.policy_eval.message}
                        </div>
                    ` : ''}
                </div>
                ` : ''}
            </div>
        `;
    }

    openAnalysisModal() {
        document.getElementById('analysis-modal').classList.add('show');
        document.getElementById('analysis-modal').style.display = 'flex';
    }

    closeAnalysisModal() {
        document.getElementById('analysis-modal').classList.remove('show');
        document.getElementById('analysis-modal').style.display = 'none';
    }

    openPolicyModal(policyId = null) {
        this.currentPolicy = policyId;
        
        if (policyId) {
            document.getElementById('modal-title').textContent = 'Edit Policy';
            this.loadPolicyForEdit(policyId);
        } else {
            document.getElementById('modal-title').textContent = 'Create New Policy';
            this.resetPolicyForm();
        }
        
        document.getElementById('policy-modal').classList.add('show');
        document.getElementById('policy-modal').style.display = 'flex';
    }

    closePolicyModal() {
        document.getElementById('policy-modal').classList.remove('show');
        document.getElementById('policy-modal').style.display = 'none';
        this.currentPolicy = null;
    }

    async loadPolicyForEdit(policyId) {
        try {
            const response = await fetch(`${this.apiBaseUrl}/mcp/policies/${policyId}`);
            if (!response.ok) {
                throw new Error('Failed to fetch policy');
            }
            
            const policy = await response.json();
            
            document.getElementById('policy-name').value = policy.name;
            document.getElementById('policy-description').value = policy.description || '';
            document.getElementById('policy-enabled').value = policy.enabled.toString();
            
            // Clear existing rules
            const rulesContainer = document.getElementById('policy-rules');
            rulesContainer.innerHTML = '';
            
            // Add policy rules
            policy.rules.forEach(rule => {
                this.addRule(rule);
            });
            
            // If no rules, add one empty rule
            if (policy.rules.length === 0) {
                this.addRule();
            }
        } catch (error) {
            console.error('Error loading policy:', error);
            this.showToast('Error loading policy', 'error');
        }
    }

    resetPolicyForm() {
        document.getElementById('policy-form').reset();
        
        // Reset rules to one empty rule
        const rulesContainer = document.getElementById('policy-rules');
        rulesContainer.innerHTML = '';
        this.addRule();
    }

    addRule(ruleData = null) {
        const rulesContainer = document.getElementById('policy-rules');
        const ruleIndex = rulesContainer.children.length;
        
        const ruleHtml = `
            <div class="rule-item">
                <div class="rule-header">
                    <input type="text" placeholder="Rule name" class="rule-name" 
                           value="${ruleData?.name || ''}" required>
                    <button type="button" class="btn btn-danger btn-sm" onclick="admin.removeRule(this)">
                        <i class="fas fa-trash"></i>
                    </button>
                </div>
                <div class="rule-content">
                    <div class="form-group">
                        <label>Description:</label>
                        <input type="text" class="rule-description" 
                               placeholder="Rule description" value="${ruleData?.description || ''}">
                    </div>
                    <div class="form-row">
                        <div class="form-group">
                            <label>Field:</label>
                            <select class="rule-field">
                                <option value="resource.size" ${ruleData?.expression?.field === 'resource.size' ? 'selected' : ''}>Resource Size</option>
                                <option value="resource.type" ${ruleData?.expression?.field === 'resource.type' ? 'selected' : ''}>Resource Type</option>
                                <option value="resource.region" ${ruleData?.expression?.field === 'resource.region' ? 'selected' : ''}>Resource Region</option>
                                <option value="resource.tags.Environment" ${ruleData?.expression?.field === 'resource.tags.Environment' ? 'selected' : ''}>Environment Tag</option>
                                <option value="cost.monthly" ${ruleData?.expression?.field === 'cost.monthly' ? 'selected' : ''}>Monthly Cost</option>
                            </select>
                        </div>
                        <div class="form-group">
                            <label>Operator:</label>
                            <select class="rule-operator">
                                <option value="equals" ${ruleData?.expression?.operator === 'equals' ? 'selected' : ''}>Equals</option>
                                <option value="not_equals" ${ruleData?.expression?.operator === 'not_equals' ? 'selected' : ''}>Not Equals</option>
                                <option value="in" ${ruleData?.expression?.operator === 'in' ? 'selected' : ''}>In</option>
                                <option value="not_in" ${ruleData?.expression?.operator === 'not_in' ? 'selected' : ''}>Not In</option>
                                <option value="greater_than" ${ruleData?.expression?.operator === 'greater_than' ? 'selected' : ''}>Greater Than</option>
                                <option value="less_than" ${ruleData?.expression?.operator === 'less_than' ? 'selected' : ''}>Less Than</option>
                            </select>
                        </div>
                        <div class="form-group">
                            <label>Value:</label>
                            <input type="text" class="rule-value" 
                                   placeholder="e.g., t3.large,t3.xlarge" 
                                   value="${ruleData?.expression?.value || ''}" required>
                        </div>
                        <div class="form-group">
                            <label>Action:</label>
                            <select class="rule-action">
                                <option value="block" ${ruleData?.action === 'block' ? 'selected' : ''}>Block</option>
                                <option value="advisory" ${ruleData?.action === 'advisory' ? 'selected' : ''}>Advisory</option>
                                <option value="warning" ${ruleData?.action === 'warning' ? 'selected' : ''}>Warning</option>
                            </select>
                        </div>
                    </div>
                </div>
            </div>
        `;
        
        rulesContainer.insertAdjacentHTML('beforeend', ruleHtml);
    }

    removeRule(button) {
        const ruleItem = button.closest('.rule-item');
        const rulesContainer = document.getElementById('policy-rules');
        
        // Don't allow removing the last rule
        if (rulesContainer.children.length > 1) {
            ruleItem.remove();
        } else {
            this.showToast('At least one rule is required', 'warning');
        }
    }

    async savePolicy() {
        try {
            const formData = this.collectPolicyFormData();
            
            if (!formData.name.trim()) {
                this.showToast('Policy name is required', 'warning');
                return;
            }
            
            if (formData.rules.length === 0) {
                this.showToast('At least one rule is required', 'warning');
                return;
            }

            const url = this.currentPolicy 
                ? `${this.apiBaseUrl}/mcp/policies/${this.currentPolicy}`
                : `${this.apiBaseUrl}/mcp/policies`;
            
            const method = this.currentPolicy ? 'PUT' : 'POST';
            
            const response = await fetch(url, {
                method: method,
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(formData)
            });

            if (!response.ok) {
                throw new Error('Failed to save policy');
            }

            this.showToast(`Policy ${this.currentPolicy ? 'updated' : 'created'} successfully`, 'success');
            this.closePolicyModal();
            this.loadPolicies();
            this.loadDashboard(); // Refresh dashboard stats
        } catch (error) {
            console.error('Error saving policy:', error);
            this.showToast('Error saving policy', 'error');
        }
    }

    collectPolicyFormData() {
        const rules = [];
        const ruleItems = document.querySelectorAll('.rule-item');
        
        ruleItems.forEach(item => {
            const name = item.querySelector('.rule-name').value;
            const description = item.querySelector('.rule-description').value;
            const field = item.querySelector('.rule-field').value;
            const operator = item.querySelector('.rule-operator').value;
            const value = item.querySelector('.rule-value').value;
            const action = item.querySelector('.rule-action').value;
            
            if (name.trim() && value.trim()) {
                rules.push({
                    name: name.trim(),
                    description: description.trim(),
                    expression: {
                        field,
                        operator,
                        value: value.split(',').map(v => v.trim())
                    },
                    action
                });
            }
        });

        return {
            name: document.getElementById('policy-name').value.trim(),
            description: document.getElementById('policy-description').value.trim(),
            enabled: document.getElementById('policy-enabled').value === 'true',
            rules
        };
    }

    async deletePolicy(policyId) {
        if (!confirm('Are you sure you want to delete this policy?')) {
            return;
        }

        try {
            const response = await fetch(`${this.apiBaseUrl}/mcp/policies/${policyId}`, {
                method: 'DELETE'
            });

            if (!response.ok) {
                throw new Error('Failed to delete policy');
            }

            this.showToast('Policy deleted successfully', 'success');
            this.loadPolicies();
            this.loadDashboard(); // Refresh dashboard stats
        } catch (error) {
            console.error('Error deleting policy:', error);
            this.showToast('Error deleting policy', 'error');
        }
    }

    editPolicy(policyId) {
        this.openPolicyModal(policyId);
    }

    showToast(message, type = 'success') {
        const toastContainer = document.getElementById('toast-container');
        const toast = document.createElement('div');
        toast.className = `toast ${type}`;
        
        const icon = type === 'success' ? 'check-circle' : 
                    type === 'error' ? 'exclamation-circle' : 'exclamation-triangle';
        
        toast.innerHTML = `
            <i class="fas fa-${icon}"></i>
            <span>${message}</span>
        `;
        
        toastContainer.appendChild(toast);
        
        setTimeout(() => {
            toast.remove();
        }, 5000);
    }

    startAutoRefresh() {
        const refreshInterval = document.getElementById('dashboard-refresh');
        if (refreshInterval) {
            refreshInterval.addEventListener('change', (e) => {
                this.stopAutoRefresh();
                const interval = parseInt(e.target.value);
                if (interval > 0) {
                    this.refreshInterval = setInterval(() => {
                        if (document.querySelector('#dashboard').classList.contains('active')) {
                            this.loadDashboard();
                        }
                    }, interval * 1000);
                }
            });
            
            // Start with default interval
            const defaultInterval = parseInt(refreshInterval.value);
            if (defaultInterval > 0) {
                this.refreshInterval = setInterval(() => {
                    if (document.querySelector('#dashboard').classList.contains('active')) {
                        this.loadDashboard();
                    }
                }, defaultInterval * 1000);
            }
        }
    }

    stopAutoRefresh() {
        if (this.refreshInterval) {
            clearInterval(this.refreshInterval);
            this.refreshInterval = null;
        }
    }
}

// Global functions for HTML onclick handlers
function openPolicyModal() {
    admin.openPolicyModal();
}

function closePolicyModal() {
    admin.closePolicyModal();
}

function closeAnalysisModal() {
    admin.closeAnalysisModal();
}

function savePolicy() {
    admin.savePolicy();
}

function addRule() {
    admin.addRule();
}

function removeRule(button) {
    admin.removeRule(button);
}

// Initialize the admin interface when the page loads
let admin;
let app; // Global reference for analytics module
document.addEventListener('DOMContentLoaded', () => {
    admin = new FinOpsGuardAdmin();
    app = admin; // Make admin available as app for analytics module
});

// Close modals when clicking outside
document.addEventListener('click', (e) => {
    if (e.target.classList.contains('modal')) {
        if (e.target.id === 'policy-modal') {
            admin.closePolicyModal();
        } else if (e.target.id === 'analysis-modal') {
            admin.closeAnalysisModal();
        }
    }
});

// Handle escape key for modal closing
document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') {
        if (document.getElementById('policy-modal').classList.contains('show')) {
            admin.closePolicyModal();
        }
        if (document.getElementById('analysis-modal').classList.contains('show')) {
            admin.closeAnalysisModal();
        }
    }
});

// Global analytics functions (called from HTML)
window.refreshAnalytics = function() {
    if (app && app.analytics) {
        app.analytics.refreshAnalytics();
    }
};

window.exportAnalytics = function() {
    if (app && app.analytics) {
        app.analytics.exportAnalytics();
    }
};

window.changeUsagePage = function(delta) {
    if (app && app.analytics) {
        app.analytics.changeUsagePage(delta);
    }
};
