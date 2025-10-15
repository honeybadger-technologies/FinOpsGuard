"""
Webhook delivery service with retry logic
"""

import asyncio
import hashlib
import hmac
import json
import logging
import time
from typing import Dict, Any, Optional
from datetime import datetime, timedelta, timezone

import httpx
from sqlalchemy.orm import Session

from .storage import WebhookStore
from ..database.connection import get_db_session
from ..database.models import Webhook, WebhookDelivery
from ..types.webhook import WebhookEvent, WebhookPayload, WebhookStatus

logger = logging.getLogger(__name__)


class WebhookDeliveryService:
    """Service for delivering webhook events with retry logic"""
    
    def __init__(self):
        self.webhook_store = WebhookStore()
        self.db_session = get_db_session()
    
    async def deliver_event(self, webhook: Webhook, event: WebhookEvent) -> bool:
        """Deliver a webhook event"""
        try:
            # Create delivery record
            delivery = self.webhook_store.create_delivery(
                webhook_id=webhook.id,
                event_id=event.id,
                event_type=event.type.value,
                payload=event.model_dump(),
                max_attempts=webhook.retry_attempts
            )
            
            # Attempt delivery
            success = await self._attempt_delivery(webhook, delivery)
            
            if success:
                self.webhook_store.update_delivery_status(
                    delivery_id=delivery.id,
                    status=WebhookStatus.DELIVERED,
                    delivered_at=datetime.now(timezone.utc)
                )
                logger.info(f"Successfully delivered webhook {webhook.id} for event {event.id}")
                return True
            else:
                # Schedule retry if attempts remaining
                if delivery.attempt_number < delivery.max_attempts:
                    next_retry = datetime.now(timezone.utc) + timedelta(seconds=webhook.retry_delay_seconds)
                    self.webhook_store.update_delivery_status(
                        delivery_id=delivery.id,
                        status=WebhookStatus.RETRYING,
                        next_retry_at=next_retry
                    )
                    logger.warning(f"Failed to deliver webhook {webhook.id}, will retry at {next_retry}")
                else:
                    self.webhook_store.update_delivery_status(
                        delivery_id=delivery.id,
                        status=WebhookStatus.FAILED
                    )
                    logger.error(f"Failed to deliver webhook {webhook.id} after {delivery.max_attempts} attempts")
                
                return False
                
        except Exception as e:
            logger.error(f"Error delivering webhook {webhook.id}: {e}")
            return False
    
    async def _attempt_delivery(self, webhook: Webhook, delivery: WebhookDelivery) -> bool:
        """Attempt to deliver a webhook"""
        try:
            # Prepare payload
            payload = WebhookPayload(
                id=delivery.event_id,
                type=delivery.event_type,
                timestamp=datetime.now(timezone.utc),
                data=delivery.payload['data'],
                metadata=delivery.payload.get('metadata')
            )
            
            # Create headers
            headers = {
                'Content-Type': 'application/json',
                'User-Agent': 'FinOpsGuard-Webhook/1.0',
                'X-Webhook-Event': delivery.event_type,
                'X-Webhook-Delivery': str(delivery.id),
                'X-Webhook-Attempt': str(delivery.attempt_number)
            }
            
            # Add custom headers
            if webhook.headers:
                headers.update(webhook.headers)
            
            # Add signature if secret is configured
            if webhook.secret:
                signature = self._generate_signature(webhook.secret, payload.model_dump_json())
                headers['X-Webhook-Signature'] = f'sha256={signature}'
            
            # Make HTTP request
            async with httpx.AsyncClient(
                timeout=webhook.timeout_seconds,
                verify=webhook.verify_ssl
            ) as client:
                response = await client.post(
                    webhook.url,
                    json=payload.model_dump(),
                    headers=headers
                )
                
                # Update delivery record with response
                self.webhook_store.update_delivery_status(
                    delivery_id=delivery.id,
                    status=WebhookStatus.DELIVERED if response.status_code < 400 else WebhookStatus.FAILED,
                    response_status=response.status_code,
                    response_body=response.text[:1000]  # Limit response body size
                )
                
                # Increment attempt number
                self.webhook_store.increment_delivery_attempt(delivery.id)
                
                # Check if successful
                success = 200 <= response.status_code < 300
                
                if not success:
                    error_msg = f"HTTP {response.status_code}: {response.text[:200]}"
                    self.webhook_store.update_delivery_status(
                        delivery_id=delivery.id,
                        error_message=error_msg
                    )
                
                return success
                
        except httpx.TimeoutException:
            error_msg = f"Request timeout after {webhook.timeout_seconds} seconds"
            self.webhook_store.update_delivery_status(
                delivery_id=delivery.id,
                error_message=error_msg
            )
            logger.warning(f"Webhook delivery timeout for {webhook.id}")
            return False
            
        except httpx.RequestError as e:
            error_msg = f"Request error: {str(e)}"
            self.webhook_store.update_delivery_status(
                delivery_id=delivery.id,
                error_message=error_msg
            )
            logger.warning(f"Webhook delivery error for {webhook.id}: {e}")
            return False
            
        except Exception as e:
            error_msg = f"Unexpected error: {str(e)}"
            self.webhook_store.update_delivery_status(
                delivery_id=delivery.id,
                error_message=error_msg
            )
            logger.error(f"Unexpected error delivering webhook {webhook.id}: {e}")
            return False
    
    def _generate_signature(self, secret: str, payload: str) -> str:
        """Generate HMAC signature for webhook payload"""
        return hmac.new(
            secret.encode('utf-8'),
            payload.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
    
    async def retry_pending_deliveries(self, batch_size: int = 10) -> int:
        """Retry pending webhook deliveries"""
        pending_deliveries = self.webhook_store.get_pending_deliveries(limit=batch_size)
        
        if not pending_deliveries:
            return 0
        
        logger.info(f"Retrying {len(pending_deliveries)} pending webhook deliveries")
        
        success_count = 0
        for delivery in pending_deliveries:
            try:
                # Get webhook configuration
                webhook = self.db_session.query(Webhook).filter(Webhook.id == delivery.webhook_id).first()
                if not webhook or not webhook.enabled:
                    # Mark as failed if webhook is disabled
                    self.webhook_store.update_delivery_status(
                        delivery_id=delivery.id,
                        status=WebhookStatus.FAILED,
                        error_message="Webhook is disabled"
                    )
                    continue
                
                # Create event from delivery payload
                event = WebhookEvent(
                    id=delivery.event_id,
                    type=delivery.event_type,
                    timestamp=datetime.fromisoformat(delivery.payload['timestamp']),
                    data=delivery.payload['data'],
                    metadata=delivery.payload.get('metadata')
                )
                
                # Attempt delivery
                success = await self.deliver_event(webhook, event)
                if success:
                    success_count += 1
                
                # Small delay between retries to avoid overwhelming the target
                await asyncio.sleep(0.1)
                
            except Exception as e:
                logger.error(f"Error retrying delivery {delivery.id}: {e}")
                # Mark as failed after too many errors
                if delivery.attempt_number >= delivery.max_attempts:
                    self.webhook_store.update_delivery_status(
                        delivery_id=delivery.id,
                        status=WebhookStatus.FAILED,
                        error_message=f"Max retries exceeded: {str(e)}"
                    )
        
        logger.info(f"Completed retry batch: {success_count}/{len(pending_deliveries)} successful")
        return success_count
    
    async def cleanup_old_deliveries(self, days_to_keep: int = 30) -> int:
        """Clean up old webhook delivery records"""
        cutoff_date = datetime.utcnow() - timedelta(days=days_to_keep)
        
        try:
            # Delete old delivered/failed deliveries
            result = self.db_session.query(WebhookDelivery).filter(
                WebhookDelivery.created_at < cutoff_date
            ).delete()
            
            self.db_session.commit()
            logger.info(f"Cleaned up {result} old webhook deliveries")
            return result
            
        except Exception as e:
            self.db_session.rollback()
            logger.error(f"Error cleaning up old deliveries: {e}")
            raise
