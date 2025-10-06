"""
Unit tests for listRecentAnalyses functionality
"""

import pytest
from finopsguard.api.handlers import list_recent_analyses
from finopsguard.types.api import ListQuery


@pytest.mark.asyncio
async def test_list_recent_analyses():
    """Test listing recent analyses"""
    request = ListQuery(limit=10)
    
    response = await list_recent_analyses(request)
    
    assert isinstance(response.items, list)
    assert response.next_cursor is None or isinstance(response.next_cursor, str)


@pytest.mark.asyncio
async def test_list_recent_analyses_with_limit():
    """Test listing recent analyses with custom limit"""
    request = ListQuery(limit=5)
    
    response = await list_recent_analyses(request)
    
    assert isinstance(response.items, list)
    assert len(response.items) <= 5
