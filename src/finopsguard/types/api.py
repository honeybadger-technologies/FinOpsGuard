"""
MCP request/response types
"""

from typing import Dict, List, Optional, Literal
from pydantic import BaseModel

from .models import CanonicalResourceModel, Recommendation, PolicyEvaluation, PricingConfidence


class CheckRequest(BaseModel):
    """Request for cost impact check"""
    iac_type: Literal['terraform', 'helm', 'k8s', 'pulumi']
    iac_payload: str  # base64 tarball or inline
    environment: Literal['dev', 'staging', 'prod']
    budget_rules: Optional[Dict[str, float]] = None
    options: Optional[Dict[str, object]] = None


class ResourceBreakdownItem(BaseModel):
    """Cost breakdown for a single resource"""
    resource_id: str
    monthly_cost: float
    notes: Optional[List[str]] = None


class CheckResponse(BaseModel):
    """Response from cost impact check"""
    estimated_monthly_cost: float
    estimated_first_week_cost: float
    breakdown_by_resource: List[ResourceBreakdownItem]
    risk_flags: List[str]
    recommendations: List[Recommendation]
    policy_eval: Optional[PolicyEvaluation] = None
    pricing_confidence: PricingConfidence
    duration_ms: int


class SuggestRequest(BaseModel):
    """Request for optimization suggestions"""
    iac_type: Optional[Literal['terraform', 'helm', 'k8s', 'pulumi']] = None
    resources: Optional[List[CanonicalResourceModel]] = None


class SuggestResponse(BaseModel):
    """Response with optimization suggestions"""
    suggestions: List[Recommendation]


class PolicyRequest(BaseModel):
    """Request for policy evaluation"""
    iac_type: Literal['terraform', 'helm', 'k8s', 'pulumi']
    iac_payload: str
    policy_id: str
    mode: Optional[Literal['advisory', 'blocking']] = None


class PolicyResponse(PolicyEvaluation):
    """Response from policy evaluation"""
    pass


class PriceQuery(BaseModel):
    """Query for price catalog"""
    cloud: Literal['aws', 'gcp', 'azure']
    region: Optional[str] = None
    instance_types: Optional[List[str]] = None


class PriceCatalogItem(BaseModel):
    """Price catalog item"""
    sku: str
    description: Optional[str] = None
    region: str
    unit: Literal['hour', 'month', 'gb-month', 'requests']
    price: float
    attributes: Optional[Dict[str, str]] = None


class PriceCatalogResponse(BaseModel):
    """Response with price catalog"""
    updated_at: str  # ISO timestamp
    pricing_confidence: PricingConfidence
    items: List[PriceCatalogItem]


class ListQuery(BaseModel):
    """Query for listing recent analyses"""
    limit: Optional[int] = None
    after: Optional[str] = None  # cursor


class AnalysisItem(BaseModel):
    """Analysis record item"""
    request_id: str
    started_at: str
    duration_ms: int
    summary: str


class ListResponse(BaseModel):
    """Response with list of analyses"""
    items: List[AnalysisItem]
    next_cursor: Optional[str] = None
