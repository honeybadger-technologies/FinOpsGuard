# Webhook Notifications for Cost Anomalies

FinOpsGuard provides comprehensive webhook functionality to notify external systems about cost anomalies, policy violations, and other important events.

## Overview

Webhooks allow you to receive real-time notifications when:
- Cost anomalies are detected
- Budget limits are exceeded
- Policy violations occur
- High-cost resources are identified
- Cost spikes are detected
- Analyses complete
- Policies are created, updated, or deleted

## Webhook Configuration

### Creating a Webhook

Create a webhook using the API:

```bash
curl -X POST "http://localhost:8080/webhooks/" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -d '{
    "name": "Cost Anomaly Alerts",
    "description": "Notifications for cost anomalies and budget violations",
    "url": "https://your-system.com/webhooks/finopsguard",
    "secret": "your-webhook-secret",
    "events": [
      "cost_anomaly",
      "budget_exceeded",
      "policy_violation",
      "high_cost_resource",
      "cost_spike"
    ],
    "enabled": true,
    "verify_ssl": true,
    "timeout_seconds": 30,
    "retry_attempts": 3,
    "retry_delay_seconds": 5,
    "headers": {
      "X-Custom-Header": "value"
    }
  }'
```

### Webhook Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `name` | string | Yes | Human-readable name for the webhook |
| `description` | string | No | Optional description |
| `url` | string | Yes | Target URL for webhook delivery |
| `secret` | string | No | Secret for HMAC signature verification |
| `events` | array | Yes | List of event types to subscribe to |
| `enabled` | boolean | No | Whether the webhook is active (default: true) |
| `verify_ssl` | boolean | No | Whether to verify SSL certificates (default: true) |
| `timeout_seconds` | integer | No | HTTP timeout in seconds (default: 30) |
| `retry_attempts` | integer | No | Number of retry attempts (default: 3) |
| `retry_delay_seconds` | integer | No | Delay between retries (default: 5) |
| `headers` | object | No | Custom headers to include in requests |

## Event Types

### Cost Anomaly Events

#### `cost_anomaly`
Triggered when unusual cost patterns are detected.

```json
{
  "id": "event-uuid",
  "type": "cost_anomaly",
  "timestamp": "2025-01-27T10:30:00Z",
  "data": {
    "environment": "production",
    "analysis": {
      "estimated_monthly_cost": 15000.0,
      "estimated_first_week_cost": 3750.0,
      "breakdown_by_resource": [...],
      "risk_flags": [...],
      "recommendations": [...],
      "policy_eval": {...}
    },
    "anomaly": {
      "type": "cost_spike",
      "severity": "high",
      "description": "Monthly cost increased by 150%"
    }
  }
}
```

#### `budget_exceeded`
Triggered when estimated costs exceed budget limits.

```json
{
  "id": "event-uuid",
  "type": "budget_exceeded",
  "timestamp": "2025-01-27T10:30:00Z",
  "data": {
    "environment": "production",
    "budget_limit": 10000.0,
    "actual_cost": 15000.0,
    "overage": 5000.0,
    "overage_percentage": 50.0,
    "analysis": {...}
  }
}
```

#### `policy_violation`
Triggered when infrastructure violates defined policies.

```json
{
  "id": "event-uuid",
  "type": "policy_violation",
  "timestamp": "2025-01-27T10:30:00Z",
  "data": {
    "environment": "production",
    "violation_type": "blocking",
    "violations": [
      {
        "policy_id": "no-gpu-in-dev",
        "policy_name": "No GPU in Development",
        "reason": "GPU instance detected in development environment",
        "violation_details": {...}
      }
    ],
    "analysis": {...}
  }
}
```

#### `high_cost_resource`
Triggered when individual resources have high costs.

```json
{
  "id": "event-uuid",
  "type": "high_cost_resource",
  "timestamp": "2025-01-27T10:30:00Z",
  "data": {
    "environment": "production",
    "resource": {
      "resource_id": "aws-ec2-instance-1",
      "monthly_cost": 1500.0,
      "type": "aws_instance",
      "region": "us-west-2"
    },
    "cost_threshold": 1000.0,
    "monthly_cost": 1500.0,
    "analysis": {...}
  }
}
```

#### `cost_spike`
Triggered when costs spike significantly compared to previous analyses.

```json
{
  "id": "event-uuid",
  "type": "cost_spike",
  "timestamp": "2025-01-27T10:30:00Z",
  "data": {
    "environment": "production",
    "current_cost": 15000.0,
    "previous_cost": 10000.0,
    "spike_percentage": 50.0,
    "cost_increase": 5000.0,
    "analysis": {...}
  }
}
```

### Analysis Events

#### `analysis_completed`
Triggered when cost analysis completes.

```json
{
  "id": "event-uuid",
  "type": "analysis_completed",
  "timestamp": "2025-01-27T10:30:00Z",
  "data": {
    "environment": "production",
    "duration_ms": 2500,
    "analysis": {...}
  }
}
```

### Policy Management Events

#### `policy_created`
Triggered when a new policy is created.

```json
{
  "id": "event-uuid",
  "type": "policy_created",
  "timestamp": "2025-01-27T10:30:00Z",
  "data": {
    "policy": {
      "id": "new-policy-id",
      "name": "Budget Limit Policy",
      "description": "Enforce monthly budget limits",
      "budget": 10000.0,
      "enabled": true
    },
    "created_by": "admin"
  }
}
```

#### `policy_updated`
Triggered when an existing policy is updated.

```json
{
  "id": "event-uuid",
  "type": "policy_updated",
  "timestamp": "2025-01-27T10:30:00Z",
  "data": {
    "policy": {...},
    "updated_by": "admin",
    "changes": {
      "old_policy": {...},
      "new_policy": {...}
    }
  }
}
```

#### `policy_deleted`
Triggered when a policy is deleted.

```json
{
  "id": "event-uuid",
  "type": "policy_deleted",
  "timestamp": "2025-01-27T10:30:00Z",
  "data": {
    "policy_id": "deleted-policy-id",
    "policy_name": "Old Policy",
    "deleted_by": "admin"
  }
}
```

## Webhook Security

### HMAC Signature Verification

If you provide a secret when creating a webhook, FinOpsGuard will include an HMAC signature in the `X-Webhook-Signature` header:

```
X-Webhook-Signature: sha256=abc123...
```

The signature is calculated using HMAC-SHA256 with your secret and the JSON payload.

Example verification in Python:

```python
import hmac
import hashlib

def verify_webhook_signature(payload, signature, secret):
    expected_signature = hmac.new(
        secret.encode('utf-8'),
        payload.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()
    
    provided_signature = signature.replace('sha256=', '')
    return hmac.compare_digest(expected_signature, provided_signature)
```

### SSL Verification

By default, webhook deliveries verify SSL certificates. You can disable this for testing by setting `verify_ssl: false`, but this is not recommended for production.

## Delivery and Retry Logic

### Delivery Process

1. Webhook event is created
2. All subscribed webhooks are identified
3. HTTP POST request is sent to each webhook URL
4. Response is recorded in the delivery history

### Retry Logic

- Failed deliveries are automatically retried
- Retry attempts are configurable (default: 3 attempts)
- Retry delay is configurable (default: 5 seconds)
- Exponential backoff is applied between retries
- Failed deliveries are marked as failed after max attempts

### Delivery Status

- `pending`: Initial delivery attempt
- `delivered`: Successfully delivered (HTTP 2xx response)
- `failed`: Failed after max retry attempts
- `retrying`: Scheduled for retry

## API Endpoints

### Webhook Management

- `GET /webhooks/` - List all webhooks
- `POST /webhooks/` - Create a new webhook
- `GET /webhooks/{id}` - Get webhook details
- `PUT /webhooks/{id}` - Update webhook
- `DELETE /webhooks/{id}` - Delete webhook

### Delivery Management

- `GET /webhooks/{id}/deliveries` - Get delivery history
- `GET /webhooks/{id}/stats` - Get delivery statistics
- `POST /webhooks/{id}/test` - Test webhook delivery

### Background Tasks

- `POST /webhooks/retry-pending` - Manually trigger retry of pending deliveries

## Monitoring and Troubleshooting

### Delivery History

View delivery history for each webhook to monitor success rates and troubleshoot issues:

```bash
curl -H "Authorization: Bearer YOUR_API_KEY" \
  "http://localhost:8080/webhooks/webhook-id/deliveries"
```

### Delivery Statistics

Get delivery statistics for monitoring:

```bash
curl -H "Authorization: Bearer YOUR_API_KEY" \
  "http://localhost:8080/webhooks/webhook-id/stats"
```

### Testing Webhooks

Test webhook delivery with sample data:

```bash
curl -X POST \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -d '{
    "event_type": "cost_anomaly",
    "custom_data": {
      "test": true,
      "message": "Test webhook delivery"
    }
  }' \
  "http://localhost:8080/webhooks/webhook-id/test"
```

## Best Practices

1. **Use HTTPS**: Always use HTTPS URLs for webhook endpoints
2. **Verify Signatures**: Always verify HMAC signatures for security
3. **Handle Duplicates**: Implement idempotency to handle duplicate events
4. **Process Asynchronously**: Process webhook events asynchronously to avoid timeouts
5. **Monitor Delivery**: Monitor delivery success rates and investigate failures
6. **Rate Limiting**: Implement rate limiting to handle high-volume events
7. **Error Handling**: Implement proper error handling and logging

## Integration Examples

### Slack Integration

```python
from flask import Flask, request
import json

app = Flask(__name__)

@app.route('/webhooks/finopsguard', methods=['POST'])
def handle_webhook():
    payload = request.json
    
    if payload['type'] == 'budget_exceeded':
        message = f"🚨 Budget exceeded! "
        message += f"Cost: ${payload['data']['actual_cost']:.2f}, "
        message += f"Budget: ${payload['data']['budget_limit']:.2f}"
        
        # Send to Slack
        send_slack_message(message)
    
    return {'status': 'success'}, 200
```

### PagerDuty Integration

```python
def handle_webhook(payload):
    if payload['type'] in ['budget_exceeded', 'cost_spike']:
        # Create PagerDuty incident
        create_pagerduty_incident(
            title=f"Cost Anomaly: {payload['type']}",
            description=payload['data'].get('reason', 'Cost anomaly detected'),
            severity='high'
        )
```

## Configuration Management

Webhook configurations are stored in the database and persist across restarts. The webhook delivery service runs as a background task and automatically handles retries and cleanup.
