"""SQLAlchemy database models for FinOpsGuard."""

from datetime import datetime
from typing import Optional
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, Text, JSON, Index
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func

Base = declarative_base()


class Policy(Base):
    """Policy database model."""
    
    __tablename__ = "policies"
    
    id = Column(String(255), primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    budget = Column(Float, nullable=True)
    expression_json = Column(JSON, nullable=True)  # PolicyExpression as JSON
    on_violation = Column(String(50), nullable=False, default='advisory')
    enabled = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    created_by = Column(String(255), nullable=True)
    updated_by = Column(String(255), nullable=True)
    
    # Indexes for performance
    __table_args__ = (
        Index('idx_policy_enabled', 'enabled'),
        Index('idx_policy_created_at', 'created_at'),
    )
    
    def __repr__(self):
        return f"<Policy(id='{self.id}', name='{self.name}', enabled={self.enabled})>"


class Analysis(Base):
    """Analysis history database model."""
    
    __tablename__ = "analyses"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    request_id = Column(String(255), unique=True, index=True, nullable=False)
    started_at = Column(DateTime(timezone=True), nullable=False)
    completed_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    duration_ms = Column(Integer, nullable=False)
    
    # Request data
    iac_type = Column(String(50), nullable=True)
    environment = Column(String(50), nullable=True)
    
    # Results
    estimated_monthly_cost = Column(Float, nullable=True)
    estimated_first_week_cost = Column(Float, nullable=True)
    resource_count = Column(Integer, nullable=True)
    
    # Policy evaluation
    policy_status = Column(String(50), nullable=True)  # pass, fail, block
    policy_id = Column(String(255), nullable=True)
    
    # Flags and metadata
    risk_flags = Column(JSON, nullable=True)  # List of risk flags
    recommendations_count = Column(Integer, nullable=True)
    
    # Full result (for detailed retrieval)
    result_json = Column(JSON, nullable=True)  # Full CheckResponse
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Indexes for performance
    __table_args__ = (
        Index('idx_analysis_started_at', 'started_at'),
        Index('idx_analysis_environment', 'environment'),
        Index('idx_analysis_policy_status', 'policy_status'),
        Index('idx_analysis_created_at', 'created_at'),
    )
    
    def __repr__(self):
        return f"<Analysis(id={self.id}, request_id='{self.request_id}', cost=${self.estimated_monthly_cost})>"


class CacheMetadata(Base):
    """Cache metadata for tracking and invalidation."""
    
    __tablename__ = "cache_metadata"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    cache_key = Column(String(255), unique=True, index=True, nullable=False)
    cache_type = Column(String(50), nullable=False)  # pricing, analysis, policy
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=True)
    hit_count = Column(Integer, default=0, nullable=False)
    last_accessed = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Indexes
    __table_args__ = (
        Index('idx_cache_type', 'cache_type'),
        Index('idx_cache_expires_at', 'expires_at'),
    )
    
    def __repr__(self):
        return f"<CacheMetadata(key='{self.cache_key}', type='{self.cache_type}')>"

