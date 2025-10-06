"""
Unit tests for getPriceCatalog functionality
"""

import pytest
from finopsguard.api.handlers import get_price_catalog
from finopsguard.types.api import PriceQuery


@pytest.mark.asyncio
async def test_get_price_catalog_aws():
    """Test getting AWS price catalog"""
    request = PriceQuery(
        cloud="aws",
        region="us-east-1"
    )
    
    response = await get_price_catalog(request)
    
    assert response.pricing_confidence in ['high', 'medium', 'low']
    assert response.updated_at is not None
    assert isinstance(response.items, list)


@pytest.mark.asyncio
async def test_get_price_catalog_with_instance_types():
    """Test getting AWS price catalog with specific instance types"""
    request = PriceQuery(
        cloud="aws",
        region="us-east-1",
        instance_types=["t3.micro", "t3.medium"]
    )
    
    response = await get_price_catalog(request)
    
    assert response.pricing_confidence in ['high', 'medium', 'low']
    assert response.updated_at is not None
    assert isinstance(response.items, list)
