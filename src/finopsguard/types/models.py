"""
Canonical Resource Model and shared types
"""

from typing import Dict, List, Optional, Literal
from pydantic import BaseModel


class CanonicalResource(BaseModel):
    """Canonical representation of a cloud resource"""
    id: str
    type: str
    name: str
    region: str
    size: str
    count: int
    tags: Optional[Dict[str, str]] = None
    metadata: Optional[Dict[str, object]] = None


class CanonicalResourceModel(BaseModel):
    """Collection of canonical resources"""
    resources: List[CanonicalResource]


PricingConfidence = Literal['high', 'medium', 'low']


class Recommendation(BaseModel):
    """Cost optimization recommendation"""
    id: str
    type: Literal['right_size', 'spot', 'reserved', 'autoscale', 'other']
    description: str
    estimated_savings_monthly: Optional[float] = None


class PolicyEvaluation(BaseModel):
    """Policy evaluation result"""
    status: Literal['pass', 'fail']
    policy_id: Optional[str] = None
    reason: Optional[str] = None



