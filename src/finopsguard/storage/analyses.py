"""
In-memory storage for analysis records
"""

from typing import List, Optional, Tuple
from ..types.api import AnalysisItem


class AnalysisRecord:
    """Analysis record for storage"""
    
    def __init__(self, request_id: str, started_at: str, duration_ms: int, summary: str):
        self.request_id = request_id
        self.started_at = started_at
        self.duration_ms = duration_ms
        self.summary = summary


# In-memory storage - simplified for MVP
_analyses: List[AnalysisRecord] = []


def add_analysis(record: AnalysisRecord) -> None:
    """Add a new analysis record"""
    _analyses.insert(0, record)
    if len(_analyses) > 1000:
        _analyses.pop()


def list_analyses(limit: int = 20, after: Optional[str] = None) -> Tuple[List[AnalysisItem], Optional[str]]:
    """List recent analyses with pagination"""
    start_idx = 0
    if after:
        idx = next((i for i, a in enumerate(_analyses) if a.started_at < after), len(_analyses))
        start_idx = idx if idx >= 0 else len(_analyses)
    
    items = _analyses[start_idx:start_idx + limit]
    next_cursor = _analyses[start_idx + limit - 1].started_at if start_idx + limit < len(_analyses) else None
    
    # Convert to API format
    api_items = [
        AnalysisItem(
            request_id=item.request_id,
            started_at=item.started_at,
            duration_ms=item.duration_ms,
            summary=item.summary
        )
        for item in items
    ]
    
    return api_items, next_cursor
