// FinOpsGuard Analytics Module
class FinOpsAnalytics {
    constructor(app) {
        this.app = app;
        this.charts = {};
        this.usageData = [];
        this.currentPage = 1;
        this.itemsPerPage = 10;
        this.init();
    }

    init() {
        this.setupEventListeners();
        this.initializeCharts();
    }

    setupEventListeners() {
        // Date range selector
        const dateRangeSelect = document.getElementById('analytics-date-range');
        if (dateRangeSelect) {
            dateRangeSelect.addEventListener('change', (e) => {
                const customRange = document.querySelector('.custom-date-range');
                if (e.target.value === 'custom') {
                    customRange.style.display = 'flex';
                } else {
                    customRange.style.display = 'none';
                    this.refreshAnalytics();
                }
            });
        }

        // Cloud provider filter
        document.getElementById('analytics-cloud-filter')?.addEventListener('change', () => {
            this.refreshAnalytics();
        });

        // Custom date inputs
        document.getElementById('analytics-start-date')?.addEventListener('change', () => {
            this.refreshAnalytics();
        });
        document.getElementById('analytics-end-date')?.addEventListener('change', () => {
            this.refreshAnalytics();
        });

        // Usage table search and sort
        document.getElementById('usage-table-search')?.addEventListener('input', () => {
            this.filterUsageTable();
        });
        document.getElementById('usage-table-sort')?.addEventListener('change', () => {
            this.sortUsageTable();
        });

        // Chart type switchers
        document.querySelectorAll('.chart-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const chartName = e.currentTarget.getAttribute('data-chart');
                const chartType = e.currentTarget.getAttribute('data-type');
                this.switchChartType(chartName, chartType);
            });
        });
    }

    initializeCharts() {
        // Cost Trend Chart
        const costTrendCtx = document.getElementById('cost-trend-chart');
        if (costTrendCtx) {
            this.charts.costTrend = new Chart(costTrendCtx, {
                type: 'line',
                data: {
                    labels: [],
                    datasets: [{
                        label: 'Daily Cost',
                        data: [],
                        borderColor: 'rgb(102, 126, 234)',
                        backgroundColor: 'rgba(102, 126, 234, 0.1)',
                        tension: 0.4,
                        fill: true
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: {
                            display: true,
                            position: 'top'
                        },
                        tooltip: {
                            mode: 'index',
                            intersect: false,
                            callbacks: {
                                label: function(context) {
                                    return context.dataset.label + ': $' + context.parsed.y.toFixed(2);
                                }
                            }
                        }
                    },
                    scales: {
                        y: {
                            beginAtZero: true,
                            ticks: {
                                callback: function(value) {
                                    return '$' + value;
                                }
                            }
                        }
                    }
                }
            });
        }

        // Cost by Service Chart
        const costServiceCtx = document.getElementById('cost-service-chart');
        if (costServiceCtx) {
            this.charts.costService = new Chart(costServiceCtx, {
                type: 'pie',
                data: {
                    labels: [],
                    datasets: [{
                        data: [],
                        backgroundColor: [
                            'rgb(255, 99, 132)',
                            'rgb(54, 162, 235)',
                            'rgb(255, 205, 86)',
                            'rgb(75, 192, 192)',
                            'rgb(153, 102, 255)',
                            'rgb(255, 159, 64)',
                            'rgb(199, 199, 199)',
                            'rgb(83, 102, 255)',
                            'rgb(255, 99, 255)',
                            'rgb(99, 255, 132)'
                        ]
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: {
                            position: 'right'
                        },
                        tooltip: {
                            callbacks: {
                                label: function(context) {
                                    const label = context.label || '';
                                    const value = context.parsed || 0;
                                    const total = context.dataset.data.reduce((a, b) => a + b, 0);
                                    const percentage = ((value / total) * 100).toFixed(1);
                                    return label + ': $' + value.toFixed(2) + ' (' + percentage + '%)';
                                }
                            }
                        }
                    }
                }
            });
        }

        // Resource Utilization Chart
        const utilizationCtx = document.getElementById('utilization-chart');
        if (utilizationCtx) {
            this.charts.utilization = new Chart(utilizationCtx, {
                type: 'bar',
                data: {
                    labels: [],
                    datasets: [{
                        label: 'CPU Utilization (%)',
                        data: [],
                        backgroundColor: 'rgba(75, 192, 192, 0.8)',
                        borderColor: 'rgb(75, 192, 192)',
                        borderWidth: 1
                    }, {
                        label: 'Memory Utilization (%)',
                        data: [],
                        backgroundColor: 'rgba(255, 99, 132, 0.8)',
                        borderColor: 'rgb(255, 99, 132)',
                        borderWidth: 1
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: {
                            display: true,
                            position: 'top'
                        }
                    },
                    scales: {
                        y: {
                            beginAtZero: true,
                            max: 100,
                            ticks: {
                                callback: function(value) {
                                    return value + '%';
                                }
                            }
                        }
                    }
                }
            });
        }

        // Cost by Region Chart
        const costRegionCtx = document.getElementById('cost-region-chart');
        if (costRegionCtx) {
            this.charts.costRegion = new Chart(costRegionCtx, {
                type: 'doughnut',
                data: {
                    labels: [],
                    datasets: [{
                        data: [],
                        backgroundColor: [
                            'rgb(54, 162, 235)',
                            'rgb(255, 99, 132)',
                            'rgb(255, 205, 86)',
                            'rgb(75, 192, 192)',
                            'rgb(153, 102, 255)'
                        ]
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: {
                            position: 'right'
                        },
                        tooltip: {
                            callbacks: {
                                label: function(context) {
                                    const label = context.label || '';
                                    const value = context.parsed || 0;
                                    return label + ': $' + value.toFixed(2);
                                }
                            }
                        }
                    }
                }
            });
        }

        // Forecast Chart
        const forecastCtx = document.getElementById('forecast-chart');
        if (forecastCtx) {
            this.charts.forecast = new Chart(forecastCtx, {
                type: 'line',
                data: {
                    labels: [],
                    datasets: [{
                        label: 'Historical',
                        data: [],
                        borderColor: 'rgb(102, 126, 234)',
                        backgroundColor: 'rgba(102, 126, 234, 0.1)',
                        tension: 0.4
                    }, {
                        label: 'Forecast',
                        data: [],
                        borderColor: 'rgb(255, 159, 64)',
                        backgroundColor: 'rgba(255, 159, 64, 0.1)',
                        borderDash: [5, 5],
                        tension: 0.4
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: {
                            display: true,
                            position: 'top'
                        }
                    },
                    scales: {
                        y: {
                            beginAtZero: true,
                            ticks: {
                                callback: function(value) {
                                    return '$' + value;
                                }
                            }
                        }
                    }
                }
            });
        }
    }

    async loadAnalytics() {
        try {
            // Check usage integration availability
            await this.checkUsageAvailability();

            // Load cost and usage data
            await this.loadCostData();
            await this.loadUsageMetrics();
            await this.loadRecommendations();
            
            this.updateAnalyticsDashboard();
        } catch (error) {
            console.error('Error loading analytics:', error);
            this.app.showToast('Error loading analytics data', 'error');
        }
    }

    async checkUsageAvailability() {
        try {
            const response = await fetch(`${this.app.apiBaseUrl}/usage/availability`);
            const data = await response.json();

            const statusDiv = document.getElementById('usage-status');
            if (data.enabled) {
                const providers = [];
                if (data.aws_available) providers.push('AWS');
                if (data.gcp_available) providers.push('GCP');
                if (data.azure_available) providers.push('Azure');

                statusDiv.innerHTML = `
                    <div class="status-success">
                        <i class="fas fa-check-circle"></i>
                        <span>Usage Integration Active: ${providers.join(', ')}</span>
                    </div>
                `;
            } else {
                statusDiv.innerHTML = `
                    <div class="status-warning">
                        <i class="fas fa-exclamation-triangle"></i>
                        <span>Usage Integration Disabled - Configure credentials to enable historical data</span>
                    </div>
                `;
            }
        } catch (error) {
            console.error('Error checking usage availability:', error);
            document.getElementById('usage-status').innerHTML = `
                <div class="status-error">
                    <i class="fas fa-times-circle"></i>
                    <span>Unable to check usage integration status</span>
                </div>
            `;
        }
    }

    async loadCostData() {
        const cloudFilter = document.getElementById('analytics-cloud-filter').value;
        const dateRange = this.getDateRange();

        try {
            // Try to get actual cost data from usage integration
            const response = await fetch(`${this.app.apiBaseUrl}/usage/cost`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    cloud_provider: cloudFilter === 'all' ? 'aws' : cloudFilter,
                    start_time: dateRange.start.toISOString(),
                    end_time: dateRange.end.toISOString(),
                    granularity: 'DAILY',
                    group_by: ['service', 'region']
                })
            });

            if (response.ok) {
                const costData = await response.json();
                this.processCostData(costData);
            } else {
                // Fall back to analysis data
                await this.loadAnalysisBasedCosts();
            }
        } catch (error) {
            console.error('Error loading cost data:', error);
            await this.loadAnalysisBasedCosts();
        }
    }

    async loadAnalysisBasedCosts() {
        // Fallback: use cost projections from analyses
        try {
            const analyses = await this.app.fetchAnalyses();
            if (!analyses || analyses.length === 0) {
                // No analyses available, use empty cost data
                this.processCostData([]);
                return;
            }
            const dateRange = this.getDateRange();

        const filteredAnalyses = analyses.filter(a => {
            const analysisDate = new Date(a.timestamp);
            return analysisDate >= dateRange.start && analysisDate <= dateRange.end;
        });

        // Generate mock cost trend data from analyses
        const mockCostData = [];
        for (let d = new Date(dateRange.start); d <= dateRange.end; d.setDate(d.getDate() + 1)) {
            const dayAnalyses = filteredAnalyses.filter(a => {
                const aDate = new Date(a.timestamp);
                return aDate.toDateString() === d.toDateString();
            });

            const totalCost = dayAnalyses.reduce((sum, a) => sum + (a.estimated_monthly_cost || 0), 0);
            
            mockCostData.push({
                date: new Date(d),
                cost: totalCost / 30, // Daily cost from monthly
                service: 'Estimated',
                region: 'all'
            });
        }

        this.processCostData(mockCostData.map(d => ({
            date: d.date.toISOString(),
            start_time: d.date.toISOString(),
            end_time: d.date.toISOString(),
            cost: d.cost,
            currency: 'USD',
            usage_amount: 0,
            usage_unit: 'hours',
            service: d.service,
            region: d.region,
            dimensions: {}
        })));
        } catch (error) {
            console.error('Error loading analysis-based costs:', error);
            this.processCostData([]);
        }
    }

    processCostData(costData) {
        if (!costData || costData.length === 0) {
            // Show empty state
            document.getElementById('metric-total-cost').textContent = '$0.00';
            document.getElementById('metric-daily-avg').textContent = '$0.00';
            document.getElementById('metric-resources').textContent = '0';
            
            // Clear charts
            if (this.charts.costTrend) {
                this.charts.costTrend.data.labels = [];
                this.charts.costTrend.data.datasets[0].data = [];
                this.charts.costTrend.update();
            }
            if (this.charts.costService) {
                this.charts.costService.data.labels = [];
                this.charts.costService.data.datasets[0].data = [];
                this.charts.costService.update();
            }
            if (this.charts.costRegion) {
                this.charts.costRegion.data.labels = [];
                this.charts.costRegion.data.datasets[0].data = [];
                this.charts.costRegion.update();
            }
            
            this.usageData = [];
            this.renderUsageTable();
            return;
        }

        // Group by date for trend chart
        const costByDate = {};
        const costByService = {};
        const costByRegion = {};

        costData.forEach(record => {
            const date = new Date(record.date).toLocaleDateString();
            costByDate[date] = (costByDate[date] || 0) + record.cost;

            const service = record.service || 'Unknown';
            costByService[service] = (costByService[service] || 0) + record.cost;

            const region = record.region || 'Unknown';
            costByRegion[region] = (costByRegion[region] || 0) + record.cost;
        });

        // Update cost trend chart
        if (this.charts.costTrend) {
            this.charts.costTrend.data.labels = Object.keys(costByDate);
            this.charts.costTrend.data.datasets[0].data = Object.values(costByDate);
            this.charts.costTrend.update();
        }

        // Update cost by service chart
        if (this.charts.costService) {
            this.charts.costService.data.labels = Object.keys(costByService);
            this.charts.costService.data.datasets[0].data = Object.values(costByService);
            this.charts.costService.update();
        }

        // Update cost by region chart
        if (this.charts.costRegion) {
            this.charts.costRegion.data.labels = Object.keys(costByRegion);
            this.charts.costRegion.data.datasets[0].data = Object.values(costByRegion);
            this.charts.costRegion.update();
        }

        // Update metrics
        const totalCost = costData.reduce((sum, r) => sum + r.cost, 0);
        const avgDailyCost = totalCost / Object.keys(costByDate).length;

        document.getElementById('metric-total-cost').textContent = '$' + totalCost.toFixed(2);
        document.getElementById('metric-daily-avg').textContent = '$' + avgDailyCost.toFixed(2);

        // Generate forecast
        this.generateForecast(Object.values(costByDate));

        // Store for table
        this.usageData = costData;
        this.renderUsageTable();
    }

    async loadUsageMetrics() {
        // Load resource usage metrics if available
        // This would require resource IDs, so we'll show basic info from cost data
        document.getElementById('metric-resources').textContent = this.usageData.length;
    }

    generateForecast(historicalData) {
        if (!historicalData || historicalData.length < 3) {
            return;
        }

        // Simple linear regression for forecast
        const n = historicalData.length;
        const sumX = (n * (n - 1)) / 2;
        const sumY = historicalData.reduce((a, b) => a + b, 0);
        const sumXY = historicalData.reduce((sum, y, x) => sum + x * y, 0);
        const sumX2 = (n * (n - 1) * (2 * n - 1)) / 6;

        const slope = (n * sumXY - sumX * sumY) / (n * sumX2 - sumX * sumX);
        const intercept = (sumY - slope * sumX) / n;

        // Generate forecast for next 30 days
        const forecastData = [];
        const forecastLabels = [];
        
        for (let i = 0; i < 30; i++) {
            const value = slope * (n + i) + intercept;
            forecastData.push(Math.max(0, value));
            const date = new Date();
            date.setDate(date.getDate() + i + 1);
            forecastLabels.push(date.toLocaleDateString());
        }

        // Update forecast chart
        if (this.charts.forecast) {
            const historicalLabels = [];
            for (let i = 0; i < historicalData.length; i++) {
                const date = new Date();
                date.setDate(date.getDate() - (historicalData.length - i));
                historicalLabels.push(date.toLocaleDateString());
            }

            this.charts.forecast.data.labels = [...historicalLabels, ...forecastLabels];
            this.charts.forecast.data.datasets[0].data = [...historicalData, ...Array(30).fill(null)];
            this.charts.forecast.data.datasets[1].data = [...Array(historicalData.length).fill(null), ...forecastData];
            this.charts.forecast.update();
        }

        // Update forecast stats
        const predictedCost = forecastData.reduce((a, b) => a + b, 0);
        document.getElementById('forecast-predicted').textContent = '$' + predictedCost.toFixed(2);
        
        const trend = slope > 0 ? '↑ Increasing' : slope < 0 ? '↓ Decreasing' : '→ Stable';
        document.getElementById('forecast-trend').textContent = trend;
        
        document.getElementById('forecast-confidence').textContent = 'Medium';
    }

    async loadRecommendations() {
        // Generate cost optimization recommendations
        const recommendations = [];

        // Analyze cost patterns
        if (this.usageData.length > 0) {
            const avgCost = this.usageData.reduce((sum, r) => sum + r.cost, 0) / this.usageData.length;
            
            recommendations.push({
                title: 'Review High-Cost Services',
                description: `Average daily cost is $${avgCost.toFixed(2)}. Consider reviewing services with costs above average.`,
                impact: 'Medium',
                effort: 'Low'
            });

            recommendations.push({
                title: 'Enable Reserved Instances',
                description: 'For predictable workloads, reserved instances can save up to 70% compared to on-demand pricing.',
                impact: 'High',
                effort: 'Medium'
            });

            recommendations.push({
                title: 'Implement Auto-Scaling',
                description: 'Configure auto-scaling to match resource capacity with actual demand.',
                impact: 'Medium',
                effort: 'Medium'
            });
        }

        this.renderRecommendations(recommendations);
    }

    renderRecommendations(recommendations) {
        const list = document.getElementById('recommendations-list');
        document.getElementById('recommendations-count').textContent = `${recommendations.length} recommendations`;

        if (recommendations.length === 0) {
            list.innerHTML = '<div class="no-data">No recommendations at this time</div>';
            return;
        }

        list.innerHTML = recommendations.map(rec => `
            <div class="recommendation-item">
                <div class="recommendation-header">
                    <h4>${rec.title}</h4>
                    <div class="recommendation-badges">
                        <span class="badge badge-${rec.impact.toLowerCase()}">${rec.impact} Impact</span>
                        <span class="badge badge-effort">${rec.effort} Effort</span>
                    </div>
                </div>
                <p>${rec.description}</p>
            </div>
        `).join('');
    }

    renderUsageTable() {
        const tbody = document.getElementById('usage-table-body');
        const start = (this.currentPage - 1) * this.itemsPerPage;
        const end = start + this.itemsPerPage;
        const pageData = this.usageData.slice(start, end);

        if (pageData.length === 0) {
            tbody.innerHTML = '<tr><td colspan="6" class="no-data">No usage data available</td></tr>';
            return;
        }

        tbody.innerHTML = pageData.map(record => `
            <tr>
                <td>${new Date(record.date).toLocaleDateString()}</td>
                <td>${record.service || 'N/A'}</td>
                <td>${record.region || 'N/A'}</td>
                <td>${record.usage_amount.toFixed(2)} ${record.usage_unit}</td>
                <td>$${record.cost.toFixed(2)}</td>
                <td>—</td>
            </tr>
        `).join('');

        // Update pagination
        const totalPages = Math.ceil(this.usageData.length / this.itemsPerPage);
        document.getElementById('usage-page-info').textContent = `Page ${this.currentPage} of ${totalPages}`;
        document.getElementById('usage-prev-page').disabled = this.currentPage === 1;
        document.getElementById('usage-next-page').disabled = this.currentPage === totalPages;
    }

    changeUsagePage(delta) {
        this.currentPage += delta;
        this.renderUsageTable();
    }

    filterUsageTable() {
        // Implement search filtering
        const searchTerm = document.getElementById('usage-table-search').value.toLowerCase();
        // Reset to page 1 and re-render
        this.currentPage = 1;
        this.renderUsageTable();
    }

    sortUsageTable() {
        const sortBy = document.getElementById('usage-table-sort').value;
        
        this.usageData.sort((a, b) => {
            switch (sortBy) {
                case 'cost-desc':
                    return b.cost - a.cost;
                case 'cost-asc':
                    return a.cost - b.cost;
                case 'date-desc':
                    return new Date(b.date) - new Date(a.date);
                case 'date-asc':
                    return new Date(a.date) - new Date(b.date);
                default:
                    return 0;
            }
        });

        this.currentPage = 1;
        this.renderUsageTable();
    }

    getDateRange() {
        const rangeSelect = document.getElementById('analytics-date-range');
        const days = parseInt(rangeSelect.value);

        if (rangeSelect.value === 'custom') {
            const start = new Date(document.getElementById('analytics-start-date').value);
            const end = new Date(document.getElementById('analytics-end-date').value);
            return { start, end };
        }

        const end = new Date();
        const start = new Date();
        start.setDate(end.getDate() - days);

        return { start, end };
    }

    async refreshAnalytics() {
        await this.loadAnalytics();
    }

    updateAnalyticsDashboard() {
        // Additional dashboard updates if needed
    }

    switchChartType(chartName, chartType) {
        const chart = this.charts[chartName];
        if (chart) {
            chart.config.type = chartType;
            chart.update();
        }
    }

    async exportAnalytics() {
        // Export analytics data to CSV
        let csv = 'Date,Service,Region,Usage Amount,Cost\n';
        this.usageData.forEach(record => {
            csv += `${new Date(record.date).toLocaleDateString()},${record.service},${record.region},${record.usage_amount},${record.cost}\n`;
        });

        const blob = new Blob([csv], { type: 'text/csv' });
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `finopsguard-analytics-${new Date().toISOString().split('T')[0]}.csv`;
        a.click();
        window.URL.revokeObjectURL(url);

        this.app.showToast('Analytics data exported successfully', 'success');
    }
}

