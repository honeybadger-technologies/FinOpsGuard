"""
Storage for analysis records (hybrid: in-memory + PostgreSQL)
"""

import logging
from typing import List, Optional, Tuple
from ..types.api import AnalysisItem

logger = logging.getLogger(__name__)


class AnalysisRecord:
    """Analysis record for storage"""
    
    def __init__(self, request_id: str, started_at: str, duration_ms: int, summary: str):
        self.request_id = request_id
        self.started_at = started_at
        self.duration_ms = duration_ms
        self.summary = summary


# In-memory storage - fallback for when database is not available
_analyses: List[AnalysisRecord] = []

# Database store instance
_db_store = None


def _get_db_store():
    """Get database store instance (lazy initialization)."""
    global _db_store
    if _db_store is None:
        try:
            from ..database import get_analysis_store, is_db_available
            if is_db_available():
                _db_store = get_analysis_store()
                logger.info("Analysis storage using PostgreSQL")
        except Exception as e:
            logger.warning(f"PostgreSQL not available, using in-memory storage: {e}")
            _db_store = False  # Mark as failed to avoid repeated attempts
    return _db_store if _db_store is not False else None


def add_analysis(record: AnalysisRecord, result_data: dict = None) -> None:
    """
    Add a new analysis record.
    
    Args:
        record: AnalysisRecord object
        result_data: Full analysis result (optional, stored in database if available)
    """
    # Always add to in-memory store (for fast recent access)
    _analyses.insert(0, record)
    if len(_analyses) > 1000:
        _analyses.pop()
    
    # Also add to database if available
    db_store = _get_db_store()
    if db_store:
        db_store.add_analysis(record, result_data)


def list_analyses(limit: int = 20, after: Optional[str] = None) -> Tuple[List[AnalysisItem], Optional[str]]:
    """
    List recent analyses with pagination.
    
    Args:
        limit: Maximum number of results
        after: Cursor for pagination
        
    Returns:
        Tuple of (list of AnalysisItem, next_cursor)
    """
    # Try database first
    db_store = _get_db_store()
    if db_store:
        try:
            db_records, next_cursor = db_store.list_analyses(limit, after)
            if db_records:
                # Convert to API format
                api_items = [
                    AnalysisItem(
                        request_id=item.request_id,
                        started_at=item.started_at,
                        duration_ms=item.duration_ms,
                        summary=item.summary
                    )
                    for item in db_records
                ]
                return api_items, next_cursor
        except Exception as e:
            logger.error(f"Error listing analyses from database: {e}, falling back to in-memory")
    
    # Fall back to in-memory storage
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
