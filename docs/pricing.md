# FinOpsGuard Pricing Guide

This guide covers pricing data sources and configuration in FinOpsGuard.

## Overview

FinOpsGuard supports both **static** and **real-time** pricing:

| Mode | Pros | Cons | Use Case |
|------|------|------|----------|
| **Static** | Fast, no API calls, no credentials needed | May be outdated | Development, testing |
| **Live** | Accurate, current prices | Slower, requires credentials, API limits | Production, accurate estimates |
| **Hybrid** | Best of both (live with static fallback) | More complex | Recommended for production |

### Architecture

```
Request for Pricing
        │
        ▼
┌───────────────────┐
│ Pricing Factory   │
└─────────┬─────────┘
          │
    ┌─────┴─────┐
    │ Try Live? │
    └─────┬─────┘
          │
    ┌─────┴─────┐
    ▼           ▼
  Yes          No
    │           │
    ▼           ▼
┌────────┐  ┌────────┐
│  Live  │  │ Static │
│Pricing │  │Pricing │
└───┬────┘  └───┬────┘
    │           │
    ▼           ▼
 Success?    Always
    │           Returns
┌───┴───┐       │
│ Cache │◄──────┘
└───┬───┘
    │
    ▼
 Return
```

---

## Quick Start

### Enable Real-time Pricing

```bash
# In .env
LIVE_PRICING_ENABLED=true
PRICING_FALLBACK_TO_STATIC=true

# Enable specific providers
AWS_PRICING_ENABLED=true
GCP_PRICING_ENABLED=true
AZURE_PRICING_ENABLED=true
```

### Test Configuration

```bash
# Check if live pricing is working
curl http://localhost:8080/mcp/cache/info

# Make a request (will use live pricing if available)
curl -X POST http://localhost:8080/mcp/getPriceCatalog \
  -d '{"cloud":"azure"}'
```

---

## AWS Pricing API

### Configuration

**Option 1: IAM Credentials**
```bash
AWS_PRICING_ENABLED=true
AWS_ACCESS_KEY_ID=AKIAIOSFODNN7EXAMPLE
AWS_SECRET_ACCESS_KEY=wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY
AWS_REGION=us-east-1
```

**Option 2: IAM Role (Kubernetes/ECS)**
```bash
AWS_PRICING_ENABLED=true
# Credentials from instance metadata
```

### Required Permissions

IAM policy for pricing access:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "pricing:GetProducts",
        "pricing:DescribeServices",
        "pricing:GetAttributeValues"
      ],
      "Resource": "*"
    }
  ]
}
```

### Supported Services

- ✅ EC2 (all instance types)
- ✅ RDS (all database engines)
- ⏳ EKS (future)
- ⏳ ElastiCache (future)
- ⏳ DynamoDB (future)

---

## GCP Cloud Billing API

### Configuration

**Option 1: API Key**
```bash
GCP_PRICING_ENABLED=true
GCP_PRICING_API_KEY=AIzaSyXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
```

**Option 2: Service Account**
```bash
GCP_PRICING_ENABLED=true
GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account.json
```

### Setup API Key

```bash
# Enable Cloud Billing API
gcloud services enable cloudbilling.googleapis.com

# Create API key
gcloud alpha services api-keys create \
  --display-name="FinOpsGuard Pricing" \
  --api-target=service=cloudbilling.googleapis.com

# Get API key
gcloud alpha services api-keys list
```

### Required Permissions

Service account needs:
- `cloudbilling.services.get`
- `cloudbilling.skus.list`

### Supported Services

- ✅ Compute Engine
- ⏳ Cloud SQL (future)
- ⏳ GKE (future)
- ⏳ Cloud Storage (future)

---

## Azure Retail Prices API

### Configuration

**Public API (No Authentication Required!):**
```bash
AZURE_PRICING_ENABLED=true
AZURE_REGION=eastus
```

Azure's Retail Prices API is publicly accessible - no credentials needed!

### API Details

- **Endpoint**: `https://prices.azure.com/api/retail/prices`
- **Authentication**: None required
- **Rate Limit**: 100 requests/minute
- **Documentation**: https://learn.microsoft.com/azure/cost-management-billing/

### Supported Services

- ✅ Virtual Machines
- ✅ SQL Database
- ⏳ AKS (future)
- ⏳ App Service (future)
- ⏳ Functions (future)

---

## Pricing Factory

The pricing factory automatically handles fallback logic:

```
1. Check live pricing enabled?
   └─ Yes: Try live API
      ├─ Success? Return live price (confidence: high)
      └─ Fail? Continue to step 2
   
2. Check fallback enabled?
   └─ Yes: Try static pricing
      ├─ Success? Return static price (confidence: medium)
      └─ Fail? Return default price (confidence: low)
```

### Usage in Code

```python
from finopsguard.adapters.pricing.pricing_factory import get_pricing_factory

factory = get_pricing_factory()

# Automatically tries live, falls back to static
price = factory.get_instance_price("aws", "t3.medium", "us-east-1")
print(f"Price: ${price['hourly_price']}/hour (confidence: {price['confidence']})")
```

---

## Caching Strategy

Real-time pricing is automatically cached:

### Cache TTLs

- **Static Pricing**: 24 hours (changes infrequently)
- **Live Pricing**: 6 hours (more dynamic, but still stable)
- **Failed Lookups**: 30 minutes (retry sooner)

### Cache Behavior

```python
# First request (cache miss)
price = get_instance_price("aws", "t3.medium")  # Calls AWS API (~200ms)

# Subsequent requests (cache hit)
price = get_instance_price("aws", "t3.medium")  # From cache (~2ms)

# After 6 hours
price = get_instance_price("aws", "t3.medium")  # Calls API again
```

### Manual Cache Control

```bash
# View cache statistics
curl http://localhost:8080/mcp/cache/info

# Flush pricing cache
curl -X POST http://localhost:8080/mcp/cache/flush
```

---

## Performance Comparison

### Response Times

| Scenario | Static | Live (Uncached) | Live (Cached) |
|----------|--------|-----------------|---------------|
| Single instance lookup | 1-2ms | 200-500ms | 2-5ms |
| Price catalog (50 items) | 10-20ms | 5-10s | 50-100ms |
| Cost analysis (10 resources) | 50-100ms | 1-2s | 100-200ms |

### Recommendations

- **Development**: Use static pricing
- **Staging**: Use hybrid (live with fallback)
- **Production**: Use hybrid with caching enabled

---

## Configuration Examples

### Development (Static Only)

```bash
# .env
LIVE_PRICING_ENABLED=false
# Uses built-in static pricing
```

### Production (Hybrid - Recommended)

```bash
# .env
LIVE_PRICING_ENABLED=true
PRICING_FALLBACK_TO_STATIC=true

# AWS
AWS_PRICING_ENABLED=true
AWS_ACCESS_KEY_ID=AKIA...
AWS_SECRET_ACCESS_KEY=...

# Azure (public API - no auth needed)
AZURE_PRICING_ENABLED=true

# GCP (requires API key)
GCP_PRICING_ENABLED=true
GCP_PRICING_API_KEY=AIza...

# Enable caching for performance
REDIS_ENABLED=true
```

### Production (Live Only - Advanced)

```bash
# .env
LIVE_PRICING_ENABLED=true
PRICING_FALLBACK_TO_STATIC=false  # Fail if live pricing unavailable

# All providers enabled
AWS_PRICING_ENABLED=true
GCP_PRICING_ENABLED=true
AZURE_PRICING_ENABLED=true

# Must have caching to handle API rate limits
REDIS_ENABLED=true
```

---

## API Rate Limits

### AWS Pricing API

- **Limit**: 20 requests/second
- **Burst**: 100 requests
- **Recommendation**: Enable caching, use IAM roles

### GCP Cloud Billing API

- **Limit**: 60 requests/minute
- **Quota**: 1,000 requests/day (default)
- **Recommendation**: Request quota increase, enable caching

### Azure Retail Prices API

- **Limit**: 100 requests/minute
- **Authentication**: Not required (public API)
- **Recommendation**: Enable caching for high-traffic scenarios

---

## Error Handling

### Fallback Behavior

```
Live Pricing API Call
        │
        ▼
  ┌──────────┐
  │ Success? │
  └─────┬────┘
        │
    ┌───┴───┐
   Yes     No
    │       │
    ▼       ▼
 Return  Try Static
  Live      │
    │   ┌───┴───┐
    │  Yes     No
    │   │       │
    │   ▼       ▼
    │ Return  Return
    │ Static  Default
    │   │       │
    └───┴───────┴──► Cache Result
```

### Example Error Scenarios

**AWS API returns 403:**
```
WARN: AWS Pricing API returned 403
INFO: Falling back to static AWS pricing
INFO: Using static pricing for aws t3.medium (confidence: medium)
```

**GCP API quota exceeded:**
```
ERROR: GCP Billing API quota exceeded
INFO: Falling back to static GCP pricing
INFO: Using static pricing for gcp e2-medium (confidence: medium)
```

**All methods fail:**
```
WARN: No pricing found for aws unknown.type
INFO: Using default fallback pricing (confidence: low)
```

---

## Monitoring

### Pricing Metrics

```promql
# Live pricing API calls
finops_pricing_api_calls_total{provider="aws",status="success"}
finops_pricing_api_calls_total{provider="aws",status="failure"}

# Pricing API latency
finops_pricing_api_duration_seconds{provider="aws"}

# Confidence distribution
finops_pricing_confidence{level="high"}
finops_pricing_confidence{level="medium"}
finops_pricing_confidence{level="low"}

# Cache hit rate for pricing
finops_cache_hits_total{cache_type="pricing"} /
(finops_cache_hits_total{cache_type="pricing"} + finops_cache_misses_total{cache_type="pricing"})
```

### Alerts

```yaml
# Alert on high API failure rate
- alert: PricingAPIFailureRateHigh
  expr: |
    rate(finops_pricing_api_calls_total{status="failure"}[5m]) /
    rate(finops_pricing_api_calls_total[5m]) > 0.5
  for: 5m
  annotations:
    summary: "High pricing API failure rate"

# Alert on low confidence pricing
- alert: LowConfidencePricingHigh
  expr: finops_pricing_confidence{level="low"} > 100
  for: 10m
  annotations:
    summary: "Many low confidence pricing lookups"
```

---

## Best Practices

### 1. Use Hybrid Mode

```bash
# Recommended configuration
LIVE_PRICING_ENABLED=true
PRICING_FALLBACK_TO_STATIC=true
```

**Benefits:**
- Most accurate pricing when APIs are available
- Graceful degradation when APIs fail
- No downtime due to pricing issues

### 2. Enable Caching

```bash
REDIS_ENABLED=true
```

**Benefits:**
- Reduces API calls by 90%+
- Avoids rate limits
- Faster response times
- Lower costs

### 3. Monitor Pricing Confidence

```python
# Check pricing confidence in results
if result['pricing_confidence'] == 'low':
    logger.warning("Using fallback pricing - may not be accurate")
```

### 4. Set Appropriate TTLs

```python
# Adjust cache TTL based on your needs
PRICING_CACHE_TTL_HOURS=6  # Default

# More frequent updates
PRICING_CACHE_TTL_HOURS=1

# Less frequent (save API calls)
PRICING_CACHE_TTL_HOURS=24
```

### 5. Handle Regional Pricing

```python
# Always specify region for accurate pricing
payload = {
    "iac_type": "terraform",
    "iac_payload": base64_encoded,
    "region": "us-west-2"  # Pricing varies by region
}
```

---

## Troubleshooting

### Live Pricing Not Working

**Check configuration:**
```bash
# Verify environment variables
echo $LIVE_PRICING_ENABLED
echo $AWS_PRICING_ENABLED
echo $GCP_PRICING_ENABLED
echo $AZURE_PRICING_ENABLED
```

**Test API connectivity:**
```bash
# AWS
aws pricing describe-services --region us-east-1

# GCP
curl "https://cloudbilling.googleapis.com/v1/services/6F81-5844-456A/skus?key=$GCP_PRICING_API_KEY"

# Azure (public - no auth)
curl "https://prices.azure.com/api/retail/prices?api-version=2021-10-01-preview"
```

**Check logs:**
```bash
docker logs finopsguard | grep -i pricing
```

### API Rate Limits

**Symptoms:**
- Slow responses
- Pricing API errors in logs
- Fallback to static pricing

**Solutions:**
```bash
# Enable caching
REDIS_ENABLED=true

# Increase cache TTL
PRICING_CACHE_TTL_HOURS=12

# Reduce concurrent requests
# (configure in load balancer)
```

### Credential Issues

**AWS:**
```bash
# Test credentials
aws sts get-caller-identity

# Check IAM permissions
aws iam simulate-principal-policy \
  --policy-source-arn arn:aws:iam::ACCOUNT:role/ROLE \
  --action-names pricing:GetProducts
```

**GCP:**
```bash
# Test API key
curl "https://cloudbilling.googleapis.com/v1/services?key=$GCP_PRICING_API_KEY"

# Test service account
gcloud auth application-default print-access-token
```

---

## Cost Optimization

### API Call Costs

| Provider | Cost per 1000 Calls | Free Tier |
|----------|---------------------|-----------|
| AWS Pricing API | $0.00 | Unlimited |
| GCP Cloud Billing | $0.00 | 1,000/day default |
| Azure Retail Prices | $0.00 | 100/minute |

**All pricing APIs are free**, but consider:
- Network egress costs
- Rate limit quotas
- API latency impact

### Reduce API Calls

**1. Enable caching:**
```bash
REDIS_ENABLED=true
```

**2. Increase cache TTL:**
```bash
PRICING_CACHE_TTL_HOURS=12  # or 24
```

**3. Use static pricing for development:**
```bash
# Development environment
LIVE_PRICING_ENABLED=false
```

**4. Batch requests:**
```python
# Get price catalog once, use for multiple analyses
catalog = get_price_catalog("aws")
# Reuse catalog data
```

---

## Advanced Configuration

### Regional Pricing

```bash
# Set default regions
AWS_REGION=us-east-1
GCP_REGION=us-central1
AZURE_REGION=eastus

# Pricing will automatically use region from Terraform:
# provider "aws" { region = "eu-west-1" }
```

### Custom Pricing Data

```python
# Override pricing for specific resources
from finopsguard.adapters.pricing.pricing_factory import get_pricing_factory

factory = get_pricing_factory()

# Add custom pricing logic
def get_custom_price(resource_type, size):
    if resource_type == "special_instance":
        return {"hourly_price": 0.50, "confidence": "high"}
    return factory.get_instance_price("aws", size)
```

### Spot/Reserved Pricing

Currently, FinOpsGuard uses on-demand pricing. For spot/reserved:

```python
# Future enhancement
payload = {
    "pricing_model": "spot",  # or "reserved_1year", "reserved_3year"
    # ...
}
```

---

## Migration from Static to Live

### Step 1: Test in Development

```bash
# Enable live pricing
LIVE_PRICING_ENABLED=true
PRICING_FALLBACK_TO_STATIC=true

# Test with sample Terraform
curl -X POST http://localhost:8080/mcp/checkCostImpact ...

# Check logs for pricing source
docker logs finopsguard | grep "Using live pricing"
```

### Step 2: Enable Caching

```bash
# Start Redis
docker-compose --profile caching up -d

# Enable Redis caching
REDIS_ENABLED=true
```

### Step 3: Monitor Performance

```bash
# Check cache hit rate
curl http://localhost:8080/mcp/cache/info | jq '.keyspace_hits, .keyspace_misses'

# Monitor API latency
curl http://localhost:8080/metrics | grep pricing_api_duration
```

### Step 4: Deploy to Production

```bash
# Configure credentials
export AWS_ACCESS_KEY_ID=...
export GCP_PRICING_API_KEY=...

# Enable all providers
AWS_PRICING_ENABLED=true
GCP_PRICING_ENABLED=true
AZURE_PRICING_ENABLED=true

# Deploy
docker-compose up -d
```

---

## Pricing Confidence Levels

### High Confidence
- **Source**: Live API or verified static data
- **Accuracy**: ±1-2%
- **Use**: Production cost estimates

### Medium Confidence
- **Source**: Static pricing (may be outdated)
- **Accuracy**: ±5-10%
- **Use**: Development, approximate estimates

### Low Confidence
- **Source**: Default fallback values
- **Accuracy**: ±50%+
- **Use**: Unknown resource types, placeholder

### Interpreting Confidence

```python
result = check_cost_impact(payload)

if result['pricing_confidence'] == 'low':
    print("⚠️  Warning: Pricing estimates are approximate")
    print("Consider enabling live pricing for accuracy")

elif result['pricing_confidence'] == 'medium':
    print("ℹ️  Using static pricing - may not reflect current rates")

else:  # high
    print("✅ Using current live pricing")
```

---

## FAQ

**Q: Do I need credentials for all providers?**

A: No. Azure Retail Prices API is public. AWS and GCP require credentials only if you enable their live pricing.

**Q: What happens if live pricing fails?**

A: FinOpsGuard automatically falls back to static pricing (if enabled), ensuring cost analysis always completes.

**Q: How often are static prices updated?**

A: Static pricing is updated with each FinOpsGuard release (typically monthly). Enable live pricing for current rates.

**Q: Can I use live pricing for some clouds and static for others?**

A: Yes! Enable per-provider:
```bash
AWS_PRICING_ENABLED=true    # Live AWS
GCP_PRICING_ENABLED=false   # Static GCP
AZURE_PRICING_ENABLED=true  # Live Azure
```

**Q: Will live pricing slow down my CI/CD?**

A: Not significantly with caching enabled. First request is slower (~500ms), subsequent requests are fast (~5ms).

**Q: Are pricing API calls free?**

A: Yes, all three cloud providers offer free pricing APIs. Monitor for rate limits.

---

## See Also

- [Deployment Guide](./deployment.md)
- [Authentication Guide](./authentication.md)
- [Database Guide](./database.md)
- [Integration Examples](./integrations.md)


