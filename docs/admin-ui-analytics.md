# Enhanced Admin UI - Advanced Analytics Dashboard

## Overview

The FinOpsGuard Admin UI now includes a comprehensive **Analytics Dashboard** with advanced cost visualization, usage analytics, and optimization recommendations powered by real-time data from cloud providers.

## Features

### 1. **Multi-Cloud Analytics**
- Support for AWS, GCP, and Azure
- Unified dashboard for all cloud providers
- Cloud-specific metrics and insights

### 2. **Interactive Charts & Visualizations**
- **Cost Trends**: Line and bar charts showing cost over time
- **Cost by Service**: Pie and doughnut charts for service breakdown
- **Resource Utilization**: Bar charts for CPU/memory usage
- **Cost by Region**: Geographic cost distribution
- **Cost Forecast**: Predictive analytics for future costs

### 3. **Key Metrics Dashboard**
- Total Cost (Period)
- Average Daily Cost
- Average CPU Utilization
- Active Resources Count
- Trend indicators with percentage changes

### 4. **Usage Integration Status**
- Real-time status check for cloud provider availability
- Visual indicators for enabled integrations
- Configuration guidance for disabled providers

### 5. **Detailed Usage Table**
- Sortable and searchable data grid
- Date, Service, Region, Usage Amount, Cost columns
- Pagination for large datasets
- Export functionality (CSV)

### 6. **Cost Forecasting**
- Linear regression-based predictions
- 30-day forecast visualization
- Confidence indicators
- Trend analysis (increasing/decreasing/stable)

### 7. **Optimization Recommendations**
- Automated cost-saving suggestions
- Impact and effort ratings
- Actionable recommendations
- Priority-based sorting

## Navigation

Access the Analytics dashboard from the main navigation bar:

```
Dashboard → Policies → Analyses → **Analytics** → Settings
```

## Dashboard Controls

### Time Range Selection
- Last 7 Days
- Last 30 Days (default)
- Last 90 Days
- Custom Range (date picker)

### Cloud Provider Filter
- All Providers
- AWS
- GCP
- Azure

### Actions
- **Refresh**: Reload analytics data
- **Export**: Download data as CSV

## Chart Interactions

### Chart Type Switching
Most charts support multiple visualization types:
- **Cost Trends**: Toggle between line and bar charts
- **Service Costs**: Switch between pie and doughnut charts
- Use the control buttons in the chart header

### Hover Details
- Hover over data points for detailed information
- Charts show tooltips with exact values
- Percentage breakdowns for pie/doughnut charts

## Usage Data Table

### Search & Filter
- **Search**: Find specific services or regions
- **Sort Options**:
  - Cost (High to Low)
  - Cost (Low to High)
  - Date (Newest)
  - Date (Oldest)

### Pagination
- Navigate through pages with Previous/Next buttons
- Current page indicator
- Configurable items per page (default: 10)

## Cost Forecast

The forecast feature uses historical data to predict future costs:

### How It Works
1. Analyzes historical cost patterns
2. Applies linear regression algorithm
3. Projects next 30 days of costs
4. Calculates confidence level

### Metrics Displayed
- **Predicted Cost**: Total forecasted cost for period
- **Confidence**: Data quality indicator (High/Medium/Low)
- **Trend**: Direction of cost movement (↑/↓/→)

## Optimization Recommendations

Automated recommendations based on usage patterns:

### Recommendation Types
1. **High-Cost Service Review**
   - Identifies services above average cost
   - Impact: Medium, Effort: Low

2. **Reserved Instances**
   - Suggests savings via reserved capacity
   - Impact: High, Effort: Medium

3. **Auto-Scaling**
   - Recommends dynamic resource allocation
   - Impact: Medium, Effort: Medium

### Badges
- **Impact**: High (red) / Medium (yellow) / Low (green)
- **Effort**: Indicates implementation complexity

## Data Export

### CSV Export
Exports the following data:
- Date
- Service Name
- Region
- Usage Amount
- Cost

### Export Process
1. Click "Export" button in analytics controls
2. CSV file downloads automatically
3. Filename format: `finopsguard-analytics-YYYY-MM-DD.csv`

## Integration Requirements

### Prerequisites
To see real data, configure usage integration:

1. **Enable Usage Integration**
   ```bash
   USAGE_INTEGRATION_ENABLED=true
   ```

2. **Configure Cloud Provider Credentials**
   - **AWS**: AWS_USAGE_ENABLED=true + credentials
   - **GCP**: GCP_USAGE_ENABLED=true + project ID
   - **Azure**: AZURE_USAGE_ENABLED=true + subscription ID

3. **Verify Connection**
   - Check status banner at top of Analytics page
   - Green = Available, Yellow = Configured but not available, Red = Not configured

### Without Integration
If usage integration is not enabled:
- Analytics dashboard still loads
- Shows estimated data from cost analyses
- Status banner displays configuration instructions

## API Endpoints

The analytics dashboard uses these endpoints:

### Usage Integration Status
```http
GET /usage/availability
```
Returns availability for AWS, GCP, Azure

### Cost Data
```http
POST /usage/cost
Content-Type: application/json

{
  "cloud_provider": "aws",
  "start_time": "2024-01-01T00:00:00Z",
  "end_time": "2024-01-31T23:59:59Z",
  "granularity": "DAILY",
  "group_by": ["service", "region"]
}
```

### Analytics Aggregation
```http
GET /usage/analytics/{cloud_provider}?days=30
```
Returns aggregated analytics data

### Clear Cache
```http
DELETE /usage/cache
```
Clears cached usage data

## Responsive Design

The analytics dashboard is fully responsive:

### Desktop (>1024px)
- 2-column chart grid
- Full-width tables
- Side-by-side forecast layout

### Tablet (768px - 1024px)
- Single-column chart grid
- Optimized metric cards
- Stacked forecast layout

### Mobile (<768px)
- Vertical layouts
- Compact tables
- Touch-friendly controls

## Performance

### Caching Strategy
- Usage data cached for 1 hour (configurable)
- Charts render client-side for fast updates
- Lazy loading for expensive queries

### Loading States
- Skeleton screens during data fetch
- Progress indicators for long operations
- Error messages with retry options

## Troubleshooting

### No Data Showing
1. **Check Usage Integration Status**
   - Look at status banner
   - Verify credentials are configured

2. **Verify Date Range**
   - Ensure selected range has data
   - Try wider date range

3. **Check Cloud Provider**
   - Confirm provider is enabled
   - Verify API permissions

### Charts Not Loading
1. **Check Browser Console**
   - Look for JavaScript errors
   - Verify Chart.js loaded

2. **Clear Browser Cache**
   - Hard refresh (Ctrl+Shift+R / Cmd+Shift+R)
   - Clear site data

3. **Check Network**
   - Verify API endpoints reachable
   - Check CORS settings

### Slow Performance
1. **Reduce Date Range**
   - Use shorter time periods
   - Aggregate by week instead of day

2. **Clear Usage Cache**
   - Use "Clear Cache" API endpoint
   - Restart application

3. **Check Cloud API Limits**
   - Verify not hitting rate limits
   - Monitor API usage quotas

## Best Practices

### 1. Regular Monitoring
- Check analytics dashboard daily
- Set up alerts for unusual patterns
- Review recommendations weekly

### 2. Data Freshness
- Clear cache when needed
- Use appropriate time ranges
- Consider data lag (24-72 hours for some providers)

### 3. Cost Optimization
- Act on high-impact recommendations
- Track savings from optimizations
- Compare forecasts with actuals

### 4. Multi-Cloud Management
- Use "All Providers" view for overview
- Compare costs across clouds
- Identify cost-efficient regions

## Advanced Features

### Custom Date Ranges
Select "Custom Range" to specify exact dates:
1. Choose start date
2. Choose end date
3. Click "Refresh"

### Chart Customization
Future enhancements may include:
- Custom chart colors
- Export charts as images
- Configurable chart types
- Additional metrics

## Security Considerations

### Data Privacy
- Usage data stays in your environment
- No data sent to external services
- Cloud credentials managed securely

### Access Control
- Analytics requires authenticated access
- Respects existing RBAC policies
- Audit logs for data access

## See Also

- [Usage Integration Guide](usage-integration.md)
- [Authentication Setup](authentication.md)
- [Deployment Guide](deployment.md)
- [API Documentation](api/openapi.yaml)

## Support

For issues or questions:
1. Check troubleshooting section
2. Review usage integration docs
3. Verify cloud provider configuration
4. Check application logs

---

**Last Updated**: October 2025
**Version**: 0.3.0
**Status**: Production Ready ✅

