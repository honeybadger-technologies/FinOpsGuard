"""PostgreSQL-backed analysis history storage."""

import json
import logging
from typing import List, Optional, Tuple
from datetime import datetime

from sqlalchemy.orm import Session
from sqlalchemy import desc

from .connection import get_db_session, is_db_available
from .models import Analysis as DBAnalysis
from ..storage.analyses import AnalysisRecord

logger = logging.getLogger(__name__)


class PostgreSQLAnalysisStore:
    """PostgreSQL-backed analysis history storage."""
    
    def __init__(self):
        """Initialize PostgreSQL analysis store."""
        self.db_available = is_db_available()
        if not self.db_available:
            logger.info("PostgreSQL not available - analyses will use in-memory storage")
    
    def add_analysis(self, record: AnalysisRecord, result_data: dict = None) -> bool:
        """
        Add analysis record to database.
        
        Args:
            record: AnalysisRecord object
            result_data: Full analysis result (optional, for detailed storage)
            
        Returns:
            True if added successfully
        """
        if not self.db_available:
            return False
        
        try:
            with get_db_session() as db:
                if db is None:
                    return False
                
                # Parse summary for details
                summary_parts = record.summary.split() if record.summary else []
                monthly_cost = None
                resource_count = None
                
                for part in summary_parts:
                    if part.startswith('monthly='):
                        try:
                            monthly_cost = float(part.split('=')[1])
                        except:
                            pass
                    elif part.startswith('resources='):
                        try:
                            resource_count = int(part.split('=')[1])
                        except:
                            pass
                
                # Extract data from result if provided
                if result_data:
                    monthly_cost = result_data.get('estimated_monthly_cost', monthly_cost)
                    resource_count = len(result_data.get('breakdown_by_resource', []))
                    policy_eval = result_data.get('policy_eval', {})
                else:
                    policy_eval = {}
                
                db_analysis = DBAnalysis(
                    request_id=record.request_id,
                    started_at=datetime.fromisoformat(record.started_at) if isinstance(record.started_at, str) else record.started_at,
                    duration_ms=record.duration_ms,
                    estimated_monthly_cost=monthly_cost,
                    estimated_first_week_cost=result_data.get('estimated_first_week_cost') if result_data else None,
                    resource_count=resource_count,
                    policy_status=policy_eval.get('status'),
                    policy_id=policy_eval.get('policy_id'),
                    risk_flags=result_data.get('risk_flags', []) if result_data else [],
                    recommendations_count=len(result_data.get('recommendations', [])) if result_data else 0,
                    result_json=result_data
                )
                
                db.add(db_analysis)
                db.commit()
                logger.debug(f"Added analysis {record.request_id}")
                return True
        except Exception as e:
            logger.error(f"Error adding analysis: {e}")
            return False
    
    def list_analyses(
        self,
        limit: int = 20,
        after: Optional[str] = None,
        environment: Optional[str] = None
    ) -> Tuple[List[AnalysisRecord], Optional[str]]:
        """
        List recent analyses.
        
        Args:
            limit: Maximum number of results
            after: Cursor for pagination (request_id)
            environment: Filter by environment
            
        Returns:
            Tuple of (list of AnalysisRecord, next_cursor)
        """
        if not self.db_available:
            return ([], None)
        
        try:
            with get_db_session() as db:
                if db is None:
                    return ([], None)
                
                query = db.query(DBAnalysis)
                
                # Filter by environment if specified
                if environment:
                    query = query.filter(DBAnalysis.environment == environment)
                
                # Pagination
                if after:
                    cursor_analysis = db.query(DBAnalysis).filter(DBAnalysis.request_id == after).first()
                    if cursor_analysis:
                        query = query.filter(DBAnalysis.id < cursor_analysis.id)
                
                # Order and limit
                query = query.order_by(desc(DBAnalysis.created_at))
                db_analyses = query.limit(limit + 1).all()
                
                # Check if there are more results
                has_more = len(db_analyses) > limit
                if has_more:
                    db_analyses = db_analyses[:limit]
                    next_cursor = db_analyses[-1].request_id
                else:
                    next_cursor = None
                
                # Convert to AnalysisRecord
                records = [self._db_to_record(a) for a in db_analyses]
                
                return (records, next_cursor)
        except Exception as e:
            logger.error(f"Error listing analyses: {e}")
            return ([], None)
    
    def get_analysis(self, request_id: str) -> Optional[dict]:
        """
        Get full analysis result by request ID.
        
        Args:
            request_id: Request ID
            
        Returns:
            Full analysis result or None
        """
        if not self.db_available:
            return None
        
        try:
            with get_db_session() as db:
                if db is None:
                    return None
                
                db_analysis = db.query(DBAnalysis).filter(
                    DBAnalysis.request_id == request_id
                ).first()
                
                if not db_analysis or not db_analysis.result_json:
                    return None
                
                return db_analysis.result_json
        except Exception as e:
            logger.error(f"Error getting analysis {request_id}: {e}")
            return None
    
    def delete_old_analyses(self, days: int = 30) -> int:
        """
        Delete analyses older than specified days.
        
        Args:
            days: Age threshold in days
            
        Returns:
            Number of analyses deleted
        """
        if not self.db_available:
            return 0
        
        try:
            from datetime import timedelta
            
            with get_db_session() as db:
                if db is None:
                    return 0
                
                cutoff_date = datetime.now() - timedelta(days=days)
                count = db.query(DBAnalysis).filter(
                    DBAnalysis.created_at < cutoff_date
                ).delete()
                
                db.commit()
                logger.info(f"Deleted {count} old analyses (older than {days} days)")
                return count
        except Exception as e:
            logger.error(f"Error deleting old analyses: {e}")
            return 0
    
    def get_statistics(self) -> dict:
        """
        Get analysis statistics.
        
        Returns:
            Dict with statistics
        """
        if not self.db_available:
            return {"total": 0, "enabled": False}
        
        try:
            with get_db_session() as db:
                if db is None:
                    return {"total": 0, "enabled": False}
                
                from sqlalchemy import func
                
                total = db.query(func.count(DBAnalysis.id)).scalar()
                avg_cost = db.query(func.avg(DBAnalysis.estimated_monthly_cost)).scalar()
                blocked_count = db.query(func.count(DBAnalysis.id)).filter(
                    DBAnalysis.policy_status == 'block'
                ).scalar()
                
                return {
                    "enabled": True,
                    "total_analyses": total,
                    "average_monthly_cost": float(avg_cost) if avg_cost else 0.0,
                    "blocked_count": blocked_count,
                }
        except Exception as e:
            logger.error(f"Error getting statistics: {e}")
            return {"total": 0, "enabled": False, "error": str(e)}
    
    def _db_to_record(self, db_analysis: DBAnalysis) -> AnalysisRecord:
        """
        Convert database analysis to AnalysisRecord.
        
        Args:
            db_analysis: Database analysis
            
        Returns:
            AnalysisRecord object
        """
        summary = f"monthly={db_analysis.estimated_monthly_cost:.2f} resources={db_analysis.resource_count or 0}"
        
        return AnalysisRecord(
            request_id=db_analysis.request_id,
            started_at=db_analysis.started_at.isoformat() if isinstance(db_analysis.started_at, datetime) else db_analysis.started_at,
            duration_ms=db_analysis.duration_ms,
            summary=summary
        )


# Global instance
_analysis_store_instance: Optional[PostgreSQLAnalysisStore] = None


def get_analysis_store() -> PostgreSQLAnalysisStore:
    """
    Get global analysis store instance.
    
    Returns:
        PostgreSQLAnalysisStore instance
    """
    global _analysis_store_instance
    if _analysis_store_instance is None:
        _analysis_store_instance = PostgreSQLAnalysisStore()
    return _analysis_store_instance

