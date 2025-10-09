"""Initial database schema for FinOpsGuard.

Revision ID: 001
Revises: 
Create Date: 2025-10-09 13:00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '001'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create initial tables."""
    
    # Create policies table
    op.create_table(
        'policies',
        sa.Column('id', sa.String(255), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('budget', sa.Float(), nullable=True),
        sa.Column('expression_json', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('on_violation', sa.String(50), nullable=False, server_default='advisory'),
        sa.Column('enabled', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('created_by', sa.String(255), nullable=True),
        sa.Column('updated_by', sa.String(255), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes for policies
    op.create_index('idx_policy_enabled', 'policies', ['enabled'])
    op.create_index('idx_policy_created_at', 'policies', ['created_at'])
    
    # Create analyses table
    op.create_table(
        'analyses',
        sa.Column('id', sa.Integer(), nullable=False, autoincrement=True),
        sa.Column('request_id', sa.String(255), nullable=False),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('completed_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('duration_ms', sa.Integer(), nullable=False),
        sa.Column('iac_type', sa.String(50), nullable=True),
        sa.Column('environment', sa.String(50), nullable=True),
        sa.Column('estimated_monthly_cost', sa.Float(), nullable=True),
        sa.Column('estimated_first_week_cost', sa.Float(), nullable=True),
        sa.Column('resource_count', sa.Integer(), nullable=True),
        sa.Column('policy_status', sa.String(50), nullable=True),
        sa.Column('policy_id', sa.String(255), nullable=True),
        sa.Column('risk_flags', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('recommendations_count', sa.Integer(), nullable=True),
        sa.Column('result_json', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes for analyses
    op.create_index('idx_analysis_request_id', 'analyses', ['request_id'], unique=True)
    op.create_index('idx_analysis_started_at', 'analyses', ['started_at'])
    op.create_index('idx_analysis_environment', 'analyses', ['environment'])
    op.create_index('idx_analysis_policy_status', 'analyses', ['policy_status'])
    op.create_index('idx_analysis_created_at', 'analyses', ['created_at'])
    
    # Create cache_metadata table
    op.create_table(
        'cache_metadata',
        sa.Column('id', sa.Integer(), nullable=False, autoincrement=True),
        sa.Column('cache_key', sa.String(255), nullable=False),
        sa.Column('cache_type', sa.String(50), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('hit_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('last_accessed', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes for cache_metadata
    op.create_index('idx_cache_key', 'cache_metadata', ['cache_key'], unique=True)
    op.create_index('idx_cache_type', 'cache_metadata', ['cache_type'])
    op.create_index('idx_cache_expires_at', 'cache_metadata', ['expires_at'])


def downgrade() -> None:
    """Drop all tables."""
    op.drop_index('idx_cache_expires_at', table_name='cache_metadata')
    op.drop_index('idx_cache_type', table_name='cache_metadata')
    op.drop_index('idx_cache_key', table_name='cache_metadata')
    op.drop_table('cache_metadata')
    
    op.drop_index('idx_analysis_created_at', table_name='analyses')
    op.drop_index('idx_analysis_policy_status', table_name='analyses')
    op.drop_index('idx_analysis_environment', table_name='analyses')
    op.drop_index('idx_analysis_started_at', table_name='analyses')
    op.drop_index('idx_analysis_request_id', table_name='analyses')
    op.drop_table('analyses')
    
    op.drop_index('idx_policy_created_at', table_name='policies')
    op.drop_index('idx_policy_enabled', table_name='policies')
    op.drop_table('policies')

