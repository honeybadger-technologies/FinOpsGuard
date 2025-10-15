"""
Webhook storage and management
"""

import uuid
import logging
from typing import List, Optional, Dict, Any
from datetime import datetime

from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from ..database.connection import get_db_session
from ..database.models import Webhook, WebhookDelivery
from ..types.webhook import (
    WebhookCreateRequest, WebhookUpdateRequest, WebhookResponse,
    WebhookDeliveryResponse, WebhookStatus, WebhookEventType
)

logger = logging.getLogger(__name__)


class WebhookStore:
    """Webhook storage and management service"""
    
    def __init__(self):
        self.db_session = get_db_session()
    
    def create_webhook(self, request: WebhookCreateRequest, created_by: Optional[str] = None) -> WebhookResponse:
        """Create a new webhook"""
        webhook_id = request.id or str(uuid.uuid4())
        
        # Convert events to list of strings
        events_list = [event.value for event in request.events]
        
        webhook = Webhook(
            id=webhook_id,
            name=request.name,
            description=request.description,
            url=request.url,
            secret=request.secret,
            events=events_list,
            enabled=request.enabled,
            verify_ssl=request.verify_ssl,
            timeout_seconds=request.timeout_seconds,
            retry_attempts=request.retry_attempts,
            retry_delay_seconds=request.retry_delay_seconds,
            headers=request.headers,
            created_by=created_by,
            updated_by=created_by
        )
        
        try:
            self.db_session.add(webhook)
            self.db_session.commit()
            logger.info(f"Created webhook {webhook_id}")
            return self._webhook_to_response(webhook)
        except Exception as e:
            self.db_session.rollback()
            logger.error(f"Failed to create webhook: {e}")
            raise
    
    def get_webhook(self, webhook_id: str) -> Optional[WebhookResponse]:
        """Get a webhook by ID"""
        webhook = self.db_session.query(Webhook).filter(Webhook.id == webhook_id).first()
        if webhook:
            return self._webhook_to_response(webhook)
        return None
    
    def list_webhooks(self, enabled_only: bool = False) -> List[WebhookResponse]:
        """List all webhooks"""
        query = self.db_session.query(Webhook)
        if enabled_only:
            query = query.filter(Webhook.enabled == True)
        
        webhooks = query.order_by(Webhook.created_at.desc()).all()
        return [self._webhook_to_response(webhook) for webhook in webhooks]
    
    def update_webhook(self, webhook_id: str, request: WebhookUpdateRequest, updated_by: Optional[str] = None) -> Optional[WebhookResponse]:
        """Update an existing webhook"""
        webhook = self.db_session.query(Webhook).filter(Webhook.id == webhook_id).first()
        if not webhook:
            return None
        
        # Update fields if provided
        if request.name is not None:
            webhook.name = request.name
        if request.description is not None:
            webhook.description = request.description
        if request.url is not None:
            webhook.url = request.url
        if request.secret is not None:
            webhook.secret = request.secret
        if request.events is not None:
            webhook.events = [event.value for event in request.events]
        if request.enabled is not None:
            webhook.enabled = request.enabled
        if request.verify_ssl is not None:
            webhook.verify_ssl = request.verify_ssl
        if request.timeout_seconds is not None:
            webhook.timeout_seconds = request.timeout_seconds
        if request.retry_attempts is not None:
            webhook.retry_attempts = request.retry_attempts
        if request.retry_delay_seconds is not None:
            webhook.retry_delay_seconds = request.retry_delay_seconds
        if request.headers is not None:
            webhook.headers = request.headers
        
        webhook.updated_by = updated_by
        
        try:
            self.db_session.commit()
            logger.info(f"Updated webhook {webhook_id}")
            return self._webhook_to_response(webhook)
        except Exception as e:
            self.db_session.rollback()
            logger.error(f"Failed to update webhook {webhook_id}: {e}")
            raise
    
    def delete_webhook(self, webhook_id: str) -> bool:
        """Delete a webhook"""
        webhook = self.db_session.query(Webhook).filter(Webhook.id == webhook_id).first()
        if not webhook:
            return False
        
        try:
            self.db_session.delete(webhook)
            self.db_session.commit()
            logger.info(f"Deleted webhook {webhook_id}")
            return True
        except Exception as e:
            self.db_session.rollback()
            logger.error(f"Failed to delete webhook {webhook_id}: {e}")
            raise
    
    def get_webhooks_for_event(self, event_type: WebhookEventType) -> List[Webhook]:
        """Get all enabled webhooks that subscribe to a specific event type"""
        webhooks = self.db_session.query(Webhook).filter(
            and_(
                Webhook.enabled == True,
                Webhook.events.contains([event_type.value])
            )
        ).all()
        return webhooks
    
    def create_delivery(self, webhook_id: str, event_id: str, event_type: str, 
                       payload: Dict[str, Any], max_attempts: int) -> WebhookDelivery:
        """Create a new webhook delivery record"""
        delivery = WebhookDelivery(
            webhook_id=webhook_id,
            event_id=event_id,
            event_type=event_type,
            payload=payload,
            status=WebhookStatus.PENDING.value,
            max_attempts=max_attempts
        )
        
        try:
            self.db_session.add(delivery)
            self.db_session.commit()
            return delivery
        except Exception as e:
            self.db_session.rollback()
            logger.error(f"Failed to create delivery for webhook {webhook_id}: {e}")
            raise
    
    def update_delivery_status(self, delivery_id: int, status: WebhookStatus, 
                              response_status: Optional[int] = None,
                              response_body: Optional[str] = None,
                              error_message: Optional[str] = None,
                              next_retry_at: Optional[datetime] = None,
                              delivered_at: Optional[datetime] = None) -> bool:
        """Update delivery status"""
        delivery = self.db_session.query(WebhookDelivery).filter(WebhookDelivery.id == delivery_id).first()
        if not delivery:
            return False
        
        delivery.status = status.value
        if response_status is not None:
            delivery.response_status = response_status
        if response_body is not None:
            delivery.response_body = response_body
        if error_message is not None:
            delivery.error_message = error_message
        if next_retry_at is not None:
            delivery.next_retry_at = next_retry_at
        if delivered_at is not None:
            delivery.delivered_at = delivered_at
        
        try:
            self.db_session.commit()
            return True
        except Exception as e:
            self.db_session.rollback()
            logger.error(f"Failed to update delivery {delivery_id}: {e}")
            raise
    
    def increment_delivery_attempt(self, delivery_id: int) -> bool:
        """Increment the attempt number for a delivery"""
        delivery = self.db_session.query(WebhookDelivery).filter(WebhookDelivery.id == delivery_id).first()
        if not delivery:
            return False
        
        delivery.attempt_number += 1
        
        try:
            self.db_session.commit()
            return True
        except Exception as e:
            self.db_session.rollback()
            logger.error(f"Failed to increment delivery attempt {delivery_id}: {e}")
            raise
    
    def get_pending_deliveries(self, limit: int = 100) -> List[WebhookDelivery]:
        """Get deliveries that are pending retry"""
        now = datetime.utcnow()
        deliveries = self.db_session.query(WebhookDelivery).filter(
            and_(
                or_(
                    WebhookDelivery.status == WebhookStatus.PENDING.value,
                    WebhookDelivery.status == WebhookStatus.RETRYING.value
                ),
                or_(
                    WebhookDelivery.next_retry_at.is_(None),
                    WebhookDelivery.next_retry_at <= now
                ),
                WebhookDelivery.attempt_number < WebhookDelivery.max_attempts
            )
        ).order_by(WebhookDelivery.created_at.asc()).limit(limit).all()
        
        return deliveries
    
    def get_deliveries_for_webhook(self, webhook_id: str, limit: int = 50, 
                                  status: Optional[WebhookStatus] = None) -> List[WebhookDeliveryResponse]:
        """Get delivery history for a webhook"""
        query = self.db_session.query(WebhookDelivery).filter(WebhookDelivery.webhook_id == webhook_id)
        
        if status:
            query = query.filter(WebhookDelivery.status == status.value)
        
        deliveries = query.order_by(WebhookDelivery.created_at.desc()).limit(limit).all()
        return [self._delivery_to_response(delivery) for delivery in deliveries]
    
    def get_delivery_stats(self, webhook_id: str) -> Dict[str, Any]:
        """Get delivery statistics for a webhook"""
        from sqlalchemy import func
        stats = self.db_session.query(
            WebhookDelivery.status,
            func.count(WebhookDelivery.id).label('count')
        ).filter(WebhookDelivery.webhook_id == webhook_id).group_by(WebhookDelivery.status).all()
        
        return {stat.status: stat.count for stat in stats}
    
    def _webhook_to_response(self, webhook: Webhook) -> WebhookResponse:
        """Convert database webhook to response model"""
        return WebhookResponse(
            id=webhook.id,
            name=webhook.name,
            description=webhook.description,
            url=webhook.url,
            events=[WebhookEventType(event) for event in webhook.events],
            enabled=webhook.enabled,
            verify_ssl=webhook.verify_ssl,
            timeout_seconds=webhook.timeout_seconds,
            retry_attempts=webhook.retry_attempts,
            retry_delay_seconds=webhook.retry_delay_seconds,
            headers=webhook.headers,
            created_at=webhook.created_at,
            updated_at=webhook.updated_at,
            created_by=webhook.created_by,
            updated_by=webhook.updated_by
        )
    
    def _delivery_to_response(self, delivery: WebhookDelivery) -> WebhookDeliveryResponse:
        """Convert database delivery to response model"""
        return WebhookDeliveryResponse(
            id=delivery.id,
            webhook_id=delivery.webhook_id,
            event_id=delivery.event_id,
            event_type=delivery.event_type,
            status=WebhookStatus(delivery.status),
            response_status=delivery.response_status,
            response_body=delivery.response_body,
            attempt_number=delivery.attempt_number,
            max_attempts=delivery.max_attempts,
            next_retry_at=delivery.next_retry_at,
            delivered_at=delivery.delivered_at,
            created_at=delivery.created_at,
            error_message=delivery.error_message
        )
