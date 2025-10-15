"""
Webhook API endpoints
"""

import logging
from typing import Optional

from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.responses import JSONResponse

from ..auth.middleware import require_auth
from ..auth.models import User
from ..webhooks.storage import WebhookStore
from ..webhooks.delivery import WebhookDeliveryService
from ..types.webhook import (
    WebhookCreateRequest, WebhookUpdateRequest, WebhookResponse,
    WebhookListResponse, WebhookDeliveryListResponse, WebhookTestRequest,
    WebhookTestResponse, WebhookEventType
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/webhooks", tags=["webhooks"])


def get_webhook_store() -> WebhookStore:
    """Dependency to get webhook store"""
    return WebhookStore()


def get_delivery_service() -> WebhookDeliveryService:
    """Dependency to get webhook delivery service"""
    return WebhookDeliveryService()


@router.post("/", response_model=WebhookResponse, status_code=status.HTTP_201_CREATED)
async def create_webhook(
    request: WebhookCreateRequest,
    webhook_store: WebhookStore = Depends(get_webhook_store),
    current_user: User = Depends(require_auth)
):
    """Create a new webhook"""
    try:
        webhook = webhook_store.create_webhook(request, created_by=current_user.username)
        logger.info(f"Created webhook {webhook.id} by user {current_user.username}")
        return webhook
    except Exception as e:
        logger.error(f"Failed to create webhook: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to create webhook: {str(e)}"
        )


@router.get("/", response_model=WebhookListResponse)
async def list_webhooks(
    enabled_only: bool = False,
    webhook_store: WebhookStore = Depends(get_webhook_store),
    current_user: User = Depends(require_auth)
):
    """List all webhooks"""
    try:
        webhooks = webhook_store.list_webhooks(enabled_only=enabled_only)
        return WebhookListResponse(webhooks=webhooks, total=len(webhooks))
    except Exception as e:
        logger.error(f"Failed to list webhooks: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list webhooks"
        )


@router.get("/{webhook_id}", response_model=WebhookResponse)
async def get_webhook(
    webhook_id: str,
    webhook_store: WebhookStore = Depends(get_webhook_store),
    current_user: User = Depends(require_auth)
):
    """Get a specific webhook"""
    webhook = webhook_store.get_webhook(webhook_id)
    if not webhook:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Webhook not found"
        )
    return webhook


@router.put("/{webhook_id}", response_model=WebhookResponse)
async def update_webhook(
    webhook_id: str,
    request: WebhookUpdateRequest,
    webhook_store: WebhookStore = Depends(get_webhook_store),
    current_user: User = Depends(require_auth)
):
    """Update a webhook"""
    try:
        webhook = webhook_store.update_webhook(webhook_id, request, updated_by=current_user.username)
        if not webhook:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Webhook not found"
            )
        logger.info(f"Updated webhook {webhook_id} by user {current_user.username}")
        return webhook
    except Exception as e:
        logger.error(f"Failed to update webhook {webhook_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to update webhook: {str(e)}"
        )


@router.delete("/{webhook_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_webhook(
    webhook_id: str,
    webhook_store: WebhookStore = Depends(get_webhook_store),
    current_user: User = Depends(require_auth)
):
    """Delete a webhook"""
    try:
        success = webhook_store.delete_webhook(webhook_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Webhook not found"
            )
        logger.info(f"Deleted webhook {webhook_id} by user {current_user.username}")
        return JSONResponse(status_code=status.HTTP_204_NO_CONTENT, content=None)
    except Exception as e:
        logger.error(f"Failed to delete webhook {webhook_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to delete webhook: {str(e)}"
        )


@router.get("/{webhook_id}/deliveries", response_model=WebhookDeliveryListResponse)
async def get_webhook_deliveries(
    webhook_id: str,
    limit: int = 50,
    status_filter: Optional[str] = None,
    webhook_store: WebhookStore = Depends(get_webhook_store),
    current_user: User = Depends(require_auth)
):
    """Get delivery history for a webhook"""
    try:
        # Verify webhook exists
        webhook = webhook_store.get_webhook(webhook_id)
        if not webhook:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Webhook not found"
            )
        
        # Get deliveries
        from ..types.webhook import WebhookStatus
        status_enum = None
        if status_filter:
            try:
                status_enum = WebhookStatus(status_filter)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid status filter: {status_filter}"
                )
        
        deliveries = webhook_store.get_deliveries_for_webhook(
            webhook_id=webhook_id,
            limit=limit,
            status=status_enum
        )
        
        return WebhookDeliveryListResponse(deliveries=deliveries, total=len(deliveries))
    except Exception as e:
        logger.error(f"Failed to get webhook deliveries: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get webhook deliveries"
        )


@router.get("/{webhook_id}/stats")
async def get_webhook_stats(
    webhook_id: str,
    webhook_store: WebhookStore = Depends(get_webhook_store),
    current_user: User = Depends(require_auth)
):
    """Get delivery statistics for a webhook"""
    try:
        # Verify webhook exists
        webhook = webhook_store.get_webhook(webhook_id)
        if not webhook:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Webhook not found"
            )
        
        stats = webhook_store.get_delivery_stats(webhook_id)
        return {"webhook_id": webhook_id, "stats": stats}
    except Exception as e:
        logger.error(f"Failed to get webhook stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get webhook stats"
        )


@router.post("/{webhook_id}/test", response_model=WebhookTestResponse)
async def test_webhook(
    webhook_id: str,
    request: WebhookTestRequest,
    webhook_store: WebhookStore = Depends(get_webhook_store),
    delivery_service: WebhookDeliveryService = Depends(get_delivery_service),
    current_user: User = Depends(require_auth)
):
    """Test a webhook with a sample event"""
    try:
        # Verify webhook exists
        webhook = webhook_store.get_webhook(webhook_id)
        if not webhook:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Webhook not found"
            )
        
        # Create test event
        from ..types.webhook import WebhookEvent
        import uuid
        from datetime import datetime
        
        test_data = request.custom_data or {
            "test": True,
            "message": "This is a test webhook event from FinOpsGuard",
            "timestamp": datetime.utcnow().isoformat()
        }
        
        event = WebhookEvent(
            id=str(uuid.uuid4()),
            type=request.event_type,
            timestamp=datetime.utcnow(),
            data=test_data
        )
        
        # Get webhook model for delivery
        from ..database.models import Webhook as WebhookModel
        from ..database.connection import get_db_session
        
        db_session = get_db_session()
        webhook_model = db_session.query(WebhookModel).filter(WebhookModel.id == webhook_id).first()
        
        if not webhook_model:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Webhook not found"
            )
        
        # Attempt delivery
        success = await delivery_service.deliver_event(webhook_model, event)
        
        # Get the delivery record to return response details
        deliveries = webhook_store.get_deliveries_for_webhook(webhook_id, limit=1)
        delivery = deliveries[0] if deliveries else None
        
        return WebhookTestResponse(
            success=success,
            delivery_id=delivery.id if delivery else None,
            response_status=delivery.response_status if delivery else None,
            response_body=delivery.response_body if delivery else None,
            error_message=delivery.error_message if delivery and not success else None
        )
        
    except Exception as e:
        logger.error(f"Failed to test webhook {webhook_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to test webhook: {str(e)}"
        )


@router.post("/retry-pending")
async def retry_pending_deliveries(
    batch_size: int = 10,
    delivery_service: WebhookDeliveryService = Depends(get_delivery_service),
    current_user: User = Depends(require_auth)
):
    """Manually trigger retry of pending webhook deliveries"""
    try:
        success_count = await delivery_service.retry_pending_deliveries(batch_size)
        return {"message": f"Retried {success_count} pending deliveries"}
    except Exception as e:
        logger.error(f"Failed to retry pending deliveries: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retry pending deliveries"
        )


@router.get("/events/types")
async def get_webhook_event_types(
    current_user: User = Depends(require_auth)
):
    """Get list of available webhook event types"""
    event_types = [
        {
            "type": event_type.value,
            "name": event_type.value.replace("_", " ").title(),
            "description": _get_event_type_description(event_type)
        }
        for event_type in WebhookEventType
    ]
    return {"event_types": event_types}


def _get_event_type_description(event_type: WebhookEventType) -> str:
    """Get human-readable description for event type"""
    descriptions = {
        WebhookEventType.COST_ANOMALY: "Triggered when unusual cost patterns are detected",
        WebhookEventType.BUDGET_EXCEEDED: "Triggered when estimated costs exceed budget limits",
        WebhookEventType.POLICY_VIOLATION: "Triggered when infrastructure violates defined policies",
        WebhookEventType.HIGH_COST_RESOURCE: "Triggered when individual resources have high costs",
        WebhookEventType.COST_SPIKE: "Triggered when costs spike significantly compared to previous analyses",
        WebhookEventType.ANALYSIS_COMPLETED: "Triggered when cost analysis completes",
        WebhookEventType.POLICY_CREATED: "Triggered when a new policy is created",
        WebhookEventType.POLICY_UPDATED: "Triggered when an existing policy is updated",
        WebhookEventType.POLICY_DELETED: "Triggered when a policy is deleted"
    }
    return descriptions.get(event_type, "Webhook event")
