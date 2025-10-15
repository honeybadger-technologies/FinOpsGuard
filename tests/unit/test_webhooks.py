"""
Unit tests for webhook functionality
"""

import pytest
import asyncio
import json
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime, timedelta, timezone

from finopsguard.types.webhook import (
    WebhookCreateRequest, WebhookUpdateRequest, WebhookEvent, WebhookEventType,
    WebhookStatus, WebhookPayload
)
from finopsguard.webhooks.storage import WebhookStore
from finopsguard.webhooks.delivery import WebhookDeliveryService
from finopsguard.webhooks.events import WebhookEventService


class TestWebhookStorage:
    """Test webhook storage functionality"""
    
    @pytest.fixture
    def webhook_store(self):
        with patch('finopsguard.webhooks.storage.get_db_session') as mock_session:
            store = WebhookStore()
            store.db_session = mock_session.return_value
            return store
    
    @pytest.fixture
    def sample_webhook_request(self):
        return WebhookCreateRequest(
            name="Test Webhook",
            description="Test webhook for unit tests",
            url="https://example.com/webhook",
            secret="test-secret",
            events=[WebhookEventType.COST_ANOMALY, WebhookEventType.BUDGET_EXCEEDED],
            enabled=True,
            verify_ssl=True,
            timeout_seconds=30,
            retry_attempts=3,
            retry_delay_seconds=5,
            headers={"X-Custom": "value"}
        )
    
    def test_webhook_create_request_validation(self):
        """Test webhook creation request validation"""
        # Valid request
        request = WebhookCreateRequest(
            name="Test",
            url="https://example.com/webhook",
            events=[WebhookEventType.COST_ANOMALY]
        )
        assert request.name == "Test"
        assert request.url == "https://example.com/webhook"
        assert request.events == [WebhookEventType.COST_ANOMALY]
        
        # Invalid URL
        with pytest.raises(ValueError):
            WebhookCreateRequest(
                name="Test",
                url="invalid-url",
                events=[WebhookEventType.COST_ANOMALY]
            )
        
        # Reserved header
        with pytest.raises(ValueError):
            WebhookCreateRequest(
                name="Test",
                url="https://example.com/webhook",
                events=[WebhookEventType.COST_ANOMALY],
                headers={"Content-Type": "application/json"}
            )
    
    def test_webhook_update_request_validation(self):
        """Test webhook update request validation"""
        # Valid update
        request = WebhookUpdateRequest(
            name="Updated Name",
            url="https://updated.example.com/webhook"
        )
        assert request.name == "Updated Name"
        assert request.url == "https://updated.example.com/webhook"
        
        # Invalid URL
        with pytest.raises(ValueError):
            WebhookUpdateRequest(url="invalid-url")
    
    def test_create_webhook(self, webhook_store, sample_webhook_request):
        """Test webhook creation"""
        mock_webhook = Mock()
        mock_webhook.id = "test-webhook-id"
        mock_webhook.name = "Test Webhook"
        mock_webhook.created_at = datetime.now(timezone.utc)
        mock_webhook.updated_at = datetime.now(timezone.utc)
        
        webhook_store.db_session.add.return_value = None
        webhook_store.db_session.commit.return_value = None
        
        # Mock the query result
        webhook_store._webhook_to_response = Mock(return_value=Mock())
        
        result = webhook_store.create_webhook(sample_webhook_request, "test-user")
        
        assert webhook_store.db_session.add.called
        assert webhook_store.db_session.commit.called
    
    def test_get_webhook(self, webhook_store):
        """Test webhook retrieval"""
        mock_webhook = Mock()
        mock_webhook.id = "test-webhook-id"
        mock_webhook.events = ["cost_anomaly"]
        
        webhook_store.db_session.query.return_value.filter.return_value.first.return_value = mock_webhook
        
        webhook_store._webhook_to_response = Mock(return_value=Mock())
        
        result = webhook_store.get_webhook("test-webhook-id")
        
        assert result is not None
    
    def test_list_webhooks(self, webhook_store):
        """Test webhook listing"""
        mock_webhooks = [Mock(), Mock()]
        webhook_store.db_session.query.return_value.filter.return_value.order_by.return_value.all.return_value = mock_webhooks
        
        webhook_store._webhook_to_response = Mock(return_value=Mock())
        
        result = webhook_store.list_webhooks(enabled_only=True)
        
        assert len(result) == 2
    
    def test_delete_webhook(self, webhook_store):
        """Test webhook deletion"""
        mock_webhook = Mock()
        webhook_store.db_session.query.return_value.filter.return_value.first.return_value = mock_webhook
        webhook_store.db_session.delete.return_value = None
        webhook_store.db_session.commit.return_value = None
        
        result = webhook_store.delete_webhook("test-webhook-id")
        
        assert result is True
        assert webhook_store.db_session.delete.called
        assert webhook_store.db_session.commit.called


class TestWebhookDelivery:
    """Test webhook delivery functionality"""
    
    @pytest.fixture
    def delivery_service(self):
        with patch('finopsguard.webhooks.delivery.get_db_session') as mock_session:
            with patch('finopsguard.webhooks.delivery.WebhookStore') as mock_store_class:
                service = WebhookDeliveryService()
                service.db_session = mock_session.return_value
                service.webhook_store = mock_store_class.return_value
                return service
    
    @pytest.fixture
    def mock_webhook(self):
        webhook = Mock()
        webhook.id = "test-webhook-id"
        webhook.url = "https://example.com/webhook"
        webhook.secret = "test-secret"
        webhook.timeout_seconds = 30
        webhook.verify_ssl = True
        webhook.headers = {"X-Custom": "value"}
        webhook.retry_attempts = 3
        webhook.retry_delay_seconds = 5
        return webhook
    
    @pytest.fixture
    def sample_event(self):
        return WebhookEvent(
            id="test-event-id",
            type=WebhookEventType.COST_ANOMALY,
            timestamp=datetime.now(timezone.utc),
            data={"test": "data"}
        )
    
    @patch('httpx.AsyncClient')
    async def test_successful_delivery(self, mock_client, delivery_service, mock_webhook, sample_event):
        """Test successful webhook delivery"""
        # Mock HTTP response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = "OK"
        
        # Mock async client
        mock_client_instance = AsyncMock()
        mock_client_instance.post.return_value = mock_response
        mock_client.return_value.__aenter__.return_value = mock_client_instance
        
        # Mock store methods
        mock_delivery = Mock()
        mock_delivery.id = 1
        mock_delivery.event_id = "test-event-id"
        mock_delivery.event_type = "cost_anomaly"
        mock_delivery.payload = {"data": {"test": "data"}, "metadata": None}
        mock_delivery.attempt_number = 1
        mock_delivery.max_attempts = 3
        delivery_service.webhook_store.create_delivery.return_value = mock_delivery
        delivery_service.webhook_store.update_delivery_status.return_value = True
        delivery_service.webhook_store.increment_delivery_attempt.return_value = True
        
        result = await delivery_service.deliver_event(mock_webhook, sample_event)
        
        assert result is True
        assert delivery_service.webhook_store.create_delivery.called
        assert delivery_service.webhook_store.update_delivery_status.called
    
    @patch('httpx.AsyncClient')
    async def test_failed_delivery_with_retry(self, mock_client, delivery_service, mock_webhook, sample_event):
        """Test failed delivery with retry"""
        # Mock HTTP response with error
        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.text = "Internal Server Error"
        
        # Mock async client
        mock_client_instance = AsyncMock()
        mock_client_instance.post.return_value = mock_response
        mock_client.return_value.__aenter__.return_value = mock_client_instance
        
        # Mock store methods
        mock_delivery = Mock()
        mock_delivery.id = 1
        mock_delivery.attempt_number = 1
        mock_delivery.max_attempts = 3
        delivery_service.webhook_store.create_delivery.return_value = mock_delivery
        delivery_service.webhook_store.update_delivery_status.return_value = True
        
        result = await delivery_service.deliver_event(mock_webhook, sample_event)
        
        assert result is False
        assert delivery_service.webhook_store.update_delivery_status.called
    
    @patch('httpx.AsyncClient')
    async def test_delivery_timeout(self, mock_client, delivery_service, mock_webhook, sample_event):
        """Test delivery timeout"""
        import httpx
        
        # Mock timeout exception
        mock_client_instance = AsyncMock()
        mock_client_instance.post.side_effect = httpx.TimeoutException("Request timeout")
        mock_client.return_value.__aenter__.return_value = mock_client_instance
        
        # Mock store methods
        mock_delivery = Mock()
        mock_delivery.id = 1
        mock_delivery.attempt_number = 1
        mock_delivery.max_attempts = 3
        delivery_service.webhook_store.create_delivery.return_value = mock_delivery
        delivery_service.webhook_store.update_delivery_status.return_value = True
        
        result = await delivery_service.deliver_event(mock_webhook, sample_event)
        
        assert result is False
        assert delivery_service.webhook_store.update_delivery_status.called
    
    def test_signature_generation(self, delivery_service):
        """Test HMAC signature generation"""
        secret = "test-secret"
        payload = '{"test": "data"}'
        
        signature = delivery_service._generate_signature(secret, payload)
        
        assert signature is not None
        assert len(signature) == 64  # SHA256 hex digest length


class TestWebhookEvents:
    """Test webhook event functionality"""
    
    @pytest.fixture
    def event_service(self):
        with patch('finopsguard.webhooks.events.WebhookStore'):
            with patch('finopsguard.webhooks.events.WebhookDeliveryService'):
                return WebhookEventService()
    
    @pytest.fixture
    def sample_analysis_data(self):
        return {
            'estimated_monthly_cost': 15000.0,
            'estimated_first_week_cost': 3750.0,
            'breakdown_by_resource': [
                {'resource_id': 'aws-instance-1', 'monthly_cost': 500.0},
                {'resource_id': 'aws-instance-2', 'monthly_cost': 1500.0}
            ],
            'risk_flags': ['high_cost'],
            'recommendations': [],
            'policy_eval': {
                'overall_status': 'pass',
                'blocking_violations': [],
                'advisory_violations': []
            },
            'duration_ms': 2500,
            'environment': 'production'
        }
    
    @patch('finopsguard.webhooks.events.WebhookEventService._send_event_to_webhooks')
    async def test_send_cost_anomaly_event(self, mock_send, event_service, sample_analysis_data):
        """Test cost anomaly event sending"""
        anomaly_details = {
            'type': 'cost_spike',
            'severity': 'high',
            'description': 'Monthly cost increased by 150%'
        }
        
        await event_service.send_cost_anomaly_event(
            analysis_data=sample_analysis_data,
            anomaly_details=anomaly_details,
            environment='production'
        )
        
        assert mock_send.called
        call_args = mock_send.call_args[0][0]
        assert call_args.type == WebhookEventType.COST_ANOMALY
        assert call_args.data['environment'] == 'production'
        assert call_args.data['anomaly']['type'] == 'cost_spike'
    
    @patch('finopsguard.webhooks.events.WebhookEventService._send_event_to_webhooks')
    async def test_send_budget_exceeded_event(self, mock_send, event_service, sample_analysis_data):
        """Test budget exceeded event sending"""
        await event_service.send_budget_exceeded_event(
            budget_limit=10000.0,
            actual_cost=15000.0,
            analysis_data=sample_analysis_data,
            environment='production'
        )
        
        assert mock_send.called
        call_args = mock_send.call_args[0][0]
        assert call_args.type == WebhookEventType.BUDGET_EXCEEDED
        assert call_args.data['budget_limit'] == 10000.0
        assert call_args.data['actual_cost'] == 15000.0
        assert call_args.data['overage'] == 5000.0
        assert call_args.data['overage_percentage'] == 50.0
    
    @patch('finopsguard.webhooks.events.WebhookEventService._send_event_to_webhooks')
    async def test_send_policy_violation_event(self, mock_send, event_service, sample_analysis_data):
        """Test policy violation event sending"""
        violations = [
            {
                'policy_id': 'no-gpu-in-dev',
                'policy_name': 'No GPU in Development',
                'reason': 'GPU instance detected in development environment',
                'violation_details': {}
            }
        ]
        
        await event_service.send_policy_violation_event(
            policy_violations=violations,
            analysis_data=sample_analysis_data,
            environment='production',
            violation_type='blocking'
        )
        
        assert mock_send.called
        call_args = mock_send.call_args[0][0]
        assert call_args.type == WebhookEventType.POLICY_VIOLATION
        assert call_args.data['violation_type'] == 'blocking'
        assert len(call_args.data['violations']) == 1
        assert call_args.data['violations'][0]['policy_id'] == 'no-gpu-in-dev'
    
    @patch('finopsguard.webhooks.events.WebhookEventService._send_event_to_webhooks')
    async def test_detect_cost_anomalies_budget_exceeded(self, mock_send, event_service, sample_analysis_data):
        """Test cost anomaly detection for budget exceeded"""
        sample_analysis_data['budget_limit'] = 10000.0  # Less than estimated cost
        
        await event_service.detect_cost_anomalies(
            current_analysis=sample_analysis_data,
            previous_analyses=[],
            environment='production'
        )
        
        # Should send budget exceeded event
        assert mock_send.called
        calls = mock_send.call_args_list
        budget_calls = [call for call in calls if call[0][0].type == WebhookEventType.BUDGET_EXCEEDED]
        assert len(budget_calls) > 0
    
    @patch('finopsguard.webhooks.events.WebhookEventService._send_event_to_webhooks')
    async def test_detect_cost_anomalies_high_cost_resource(self, mock_send, event_service, sample_analysis_data):
        """Test cost anomaly detection for high cost resources"""
        # Add a high-cost resource
        sample_analysis_data['breakdown_by_resource'] = [
            {'resource_id': 'expensive-instance', 'monthly_cost': 1500.0}
        ]
        
        await event_service.detect_cost_anomalies(
            current_analysis=sample_analysis_data,
            previous_analyses=[],
            environment='production'
        )
        
        # Should send high cost resource event
        assert mock_send.called
        # Check that high cost resource event was sent
        calls = mock_send.call_args_list
        high_cost_calls = [call for call in calls if call[0][0].type == WebhookEventType.HIGH_COST_RESOURCE]
        assert len(high_cost_calls) > 0
    
    @patch('finopsguard.webhooks.events.WebhookEventService._send_event_to_webhooks')
    async def test_detect_cost_anomalies_cost_spike(self, mock_send, event_service, sample_analysis_data):
        """Test cost anomaly detection for cost spikes"""
        previous_analyses = [
            {'estimated_monthly_cost': 8000.0}  # 87.5% increase to 15000
        ]
        
        await event_service.detect_cost_anomalies(
            current_analysis=sample_analysis_data,  # 15000.0 cost
            previous_analyses=previous_analyses,
            environment='production'
        )
        
        # Should send cost spike event (87.5% increase)
        assert mock_send.called
        calls = mock_send.call_args_list
        spike_calls = [call for call in calls if call[0][0].type == WebhookEventType.COST_SPIKE]
        assert len(spike_calls) > 0


class TestWebhookIntegration:
    """Test webhook integration with policy engine"""
    
    @pytest.fixture
    def mock_policy_engine(self):
        from finopsguard.types.policy import PolicyEvaluationResult
        
        result = PolicyEvaluationResult(
            overall_status="pass",
            blocking_violations=[],
            advisory_violations=[],
            passed_policies=["policy1"],
            evaluation_context={}
        )
        return result
    
    @patch('finopsguard.api.handlers.policy_engine')
    @patch('finopsguard.api.handlers.analysis_cache')
    @patch('finopsguard.webhooks.events.WebhookEventService')
    async def test_webhook_integration_in_cost_check(self, mock_webhook_service, mock_cache, mock_engine):
        """Test webhook integration in cost check handler"""
        from finopsguard.api.handlers import check_cost_impact
        from finopsguard.types.api import CheckRequest
        from finopsguard.types.policy import PolicyEvaluationResult
        
        # Mock policy evaluation result
        mock_result = PolicyEvaluationResult(
            overall_status="pass",
            blocking_violations=[],
            advisory_violations=[],
            passed_policies=["policy1"],
            evaluation_context={}
        )
        mock_engine.evaluate_policies.return_value = mock_result
        
        # Mock cache
        mock_cache.get_full_analysis.return_value = None
        mock_cache.get_parsed_terraform.return_value = None
        
        # Mock webhook service
        mock_webhook_instance = AsyncMock()
        mock_webhook_service.return_value = mock_webhook_instance
        
        # Create request
        request = CheckRequest(
            iac_type="terraform",
            iac_payload="dGVzdA==",  # base64 encoded "test"
            environment="prod",
            budget_rules={"monthly_budget": 10000.0}
        )
        
        # Mock simulation
        with patch('finopsguard.api.handlers.simulate_cost') as mock_sim:
            from finopsguard.types.api import CheckResponse
            mock_response = CheckResponse(
                estimated_monthly_cost=15000.0,
                estimated_first_week_cost=3750.0,
                breakdown_by_resource=[],
                risk_flags=[],
                recommendations=[],
                pricing_confidence="high",
                duration_ms=1000
            )
            mock_sim.return_value = mock_response
            
            # Mock terraform parsing
            with patch('finopsguard.api.handlers.parse_terraform_to_crmodel') as mock_parse:
                from finopsguard.types.models import CanonicalResourceModel
                mock_parse.return_value = CanonicalResourceModel(resources=[])
                
                result = await check_cost_impact(request)
                
                # Verify webhook service was called
                assert mock_webhook_instance.detect_cost_anomalies.called
                
        # Verify the call arguments
        call_args = mock_webhook_instance.detect_cost_anomalies.call_args
        analysis_data = call_args[1]['current_analysis']
        assert analysis_data['estimated_monthly_cost'] == 15000.0
        assert analysis_data['environment'] == 'prod'
        assert analysis_data['budget_limit'] == 10000.0


if __name__ == "__main__":
    pytest.main([__file__])
