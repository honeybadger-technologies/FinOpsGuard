"""
Webhook types and models
"""

from typing import Dict, List, Optional, Any, Literal
from datetime import datetime
from pydantic import BaseModel, Field, field_validator
from enum import Enum


class WebhookEventType(str, Enum):
    """Supported webhook event types"""
    COST_ANOMALY = "cost_anomaly"
    BUDGET_EXCEEDED = "budget_exceeded"
    POLICY_VIOLATION = "policy_violation"
    HIGH_COST_RESOURCE = "high_cost_resource"
    COST_SPIKE = "cost_spike"
    ANALYSIS_COMPLETED = "analysis_completed"
    POLICY_CREATED = "policy_created"
    POLICY_UPDATED = "policy_updated"
    POLICY_DELETED = "policy_deleted"


class WebhookStatus(str, Enum):
    """Webhook delivery status"""
    PENDING = "pending"
    DELIVERED = "delivered"
    FAILED = "failed"
    RETRYING = "retrying"


class WebhookCreateRequest(BaseModel):
    """Request to create a webhook"""
    id: Optional[str] = None
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    url: str = Field(..., min_length=1, max_length=500)
    secret: Optional[str] = Field(None, max_length=255)
    events: List[WebhookEventType] = Field(..., min_length=1)
    enabled: bool = True
    verify_ssl: bool = True
    timeout_seconds: int = Field(30, ge=1, le=300)
    retry_attempts: int = Field(3, ge=1, le=10)
    retry_delay_seconds: int = Field(5, ge=1, le=3600)
    headers: Optional[Dict[str, str]] = None

    @field_validator('url')
    @classmethod
    def validate_url(cls, v):
        if not v.startswith(('http://', 'https://')):
            raise ValueError('URL must start with http:// or https://')
        return v

    @field_validator('headers')
    @classmethod
    def validate_headers(cls, v):
        if v:
            # Validate header names are not reserved
            reserved_headers = {'content-type', 'content-length', 'authorization', 'user-agent'}
            for header_name in v.keys():
                if header_name.lower() in reserved_headers:
                    raise ValueError(f'Header "{header_name}" is reserved and cannot be used')
        return v


class WebhookUpdateRequest(BaseModel):
    """Request to update a webhook"""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    url: Optional[str] = Field(None, min_length=1, max_length=500)
    secret: Optional[str] = Field(None, max_length=255)
    events: Optional[List[WebhookEventType]] = Field(None, min_length=1)
    enabled: Optional[bool] = None
    verify_ssl: Optional[bool] = None
    timeout_seconds: Optional[int] = Field(None, ge=1, le=300)
    retry_attempts: Optional[int] = Field(None, ge=1, le=10)
    retry_delay_seconds: Optional[int] = Field(None, ge=1, le=3600)
    headers: Optional[Dict[str, str]] = None

    @field_validator('url')
    @classmethod
    def validate_url(cls, v):
        if v is not None and not v.startswith(('http://', 'https://')):
            raise ValueError('URL must start with http:// or https://')
        return v

    @field_validator('headers')
    @classmethod
    def validate_headers(cls, v):
        if v:
            # Validate header names are not reserved
            reserved_headers = {'content-type', 'content-length', 'authorization', 'user-agent'}
            for header_name in v.keys():
                if header_name.lower() in reserved_headers:
                    raise ValueError(f'Header "{header_name}" is reserved and cannot be used')
        return v


class WebhookResponse(BaseModel):
    """Webhook configuration response"""
    id: str
    name: str
    description: Optional[str]
    url: str
    events: List[WebhookEventType]
    enabled: bool
    verify_ssl: bool
    timeout_seconds: int
    retry_attempts: int
    retry_delay_seconds: int
    headers: Optional[Dict[str, str]]
    created_at: datetime
    updated_at: datetime
    created_by: Optional[str]
    updated_by: Optional[str]


class WebhookListResponse(BaseModel):
    """Response with list of webhooks"""
    webhooks: List[WebhookResponse]
    total: int


class WebhookDeliveryResponse(BaseModel):
    """Webhook delivery attempt response"""
    id: int
    webhook_id: str
    event_id: str
    event_type: str
    status: WebhookStatus
    response_status: Optional[int]
    response_body: Optional[str]
    attempt_number: int
    max_attempts: int
    next_retry_at: Optional[datetime]
    delivered_at: Optional[datetime]
    created_at: datetime
    error_message: Optional[str]


class WebhookDeliveryListResponse(BaseModel):
    """Response with list of webhook deliveries"""
    deliveries: List[WebhookDeliveryResponse]
    total: int


class WebhookEvent(BaseModel):
    """Webhook event payload"""
    id: str
    type: WebhookEventType
    timestamp: datetime
    data: Dict[str, Any]
    metadata: Optional[Dict[str, Any]] = None


class WebhookPayload(BaseModel):
    """Standard webhook payload format"""
    id: str
    type: WebhookEventType
    timestamp: datetime
    data: Dict[str, Any]
    metadata: Optional[Dict[str, Any]] = None


class WebhookTestRequest(BaseModel):
    """Request to test a webhook"""
    webhook_id: str
    event_type: Optional[WebhookEventType] = WebhookEventType.COST_ANOMALY
    custom_data: Optional[Dict[str, Any]] = None


class WebhookTestResponse(BaseModel):
    """Response from webhook test"""
    success: bool
    delivery_id: Optional[int] = None
    response_status: Optional[int] = None
    response_body: Optional[str] = None
    error_message: Optional[str] = None
