"""Add webhooks table

Revision ID: 003
Revises: 002
Create Date: 2025-01-27

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '003'
down_revision = '002'
branch_labels = None
depends_on = None


def upgrade():
    """Create webhooks and webhook_deliveries tables."""
    # Create webhooks table
    op.create_table(
        'webhooks',
        sa.Column('id', sa.String(length=255), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('url', sa.String(length=500), nullable=False),
        sa.Column('secret', sa.String(length=255), nullable=True),
        sa.Column('events', postgresql.JSON(astext_type=sa.Text()), nullable=False),
        sa.Column('enabled', sa.Boolean(), nullable=False, default=True),
        sa.Column('verify_ssl', sa.Boolean(), nullable=False, default=True),
        sa.Column('timeout_seconds', sa.Integer(), nullable=False, default=30),
        sa.Column('retry_attempts', sa.Integer(), nullable=False, default=3),
        sa.Column('retry_delay_seconds', sa.Integer(), nullable=False, default=5),
        sa.Column('headers', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('created_by', sa.String(length=255), nullable=True),
        sa.Column('updated_by', sa.String(length=255), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create webhook_deliveries table
    op.create_table(
        'webhook_deliveries',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('webhook_id', sa.String(length=255), nullable=False),
        sa.Column('event_id', sa.String(length=255), nullable=False),
        sa.Column('event_type', sa.String(length=100), nullable=False),
        sa.Column('payload', postgresql.JSON(astext_type=sa.Text()), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=False),
        sa.Column('response_status', sa.Integer(), nullable=True),
        sa.Column('response_body', sa.Text(), nullable=True),
        sa.Column('attempt_number', sa.Integer(), nullable=False, default=1),
        sa.Column('max_attempts', sa.Integer(), nullable=False, default=3),
        sa.Column('next_retry_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('delivered_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['webhook_id'], ['webhooks.id'], ondelete='CASCADE')
    )
    
    # Create indexes for webhooks table
    op.create_index(op.f('ix_webhooks_id'), 'webhooks', ['id'], unique=True)
    op.create_index(op.f('ix_webhooks_enabled'), 'webhooks', ['enabled'], unique=False)
    op.create_index(op.f('ix_webhooks_created_at'), 'webhooks', ['created_at'], unique=False)
    
    # Create indexes for webhook_deliveries table
    op.create_index(op.f('ix_webhook_deliveries_id'), 'webhook_deliveries', ['id'], unique=False)
    op.create_index(op.f('ix_webhook_deliveries_webhook_id'), 'webhook_deliveries', ['webhook_id'], unique=False)
    op.create_index(op.f('ix_webhook_deliveries_event_id'), 'webhook_deliveries', ['event_id'], unique=False)
    op.create_index(op.f('ix_webhook_deliveries_event_type'), 'webhook_deliveries', ['event_type'], unique=False)
    op.create_index(op.f('ix_webhook_deliveries_status'), 'webhook_deliveries', ['status'], unique=False)
    op.create_index(op.f('ix_webhook_deliveries_created_at'), 'webhook_deliveries', ['created_at'], unique=False)
    op.create_index(op.f('ix_webhook_deliveries_next_retry_at'), 'webhook_deliveries', ['next_retry_at'], unique=False)
    
    # Composite indexes for common queries
    op.create_index('idx_webhook_deliveries_webhook_status', 'webhook_deliveries', ['webhook_id', 'status'])
    op.create_index('idx_webhook_deliveries_event_type_created', 'webhook_deliveries', ['event_type', 'created_at'])


def downgrade():
    """Drop webhooks and webhook_deliveries tables."""
    # Drop indexes
    op.drop_index('idx_webhook_deliveries_event_type_created', table_name='webhook_deliveries')
    op.drop_index('idx_webhook_deliveries_webhook_status', table_name='webhook_deliveries')
    op.drop_index(op.f('ix_webhook_deliveries_next_retry_at'), table_name='webhook_deliveries')
    op.drop_index(op.f('ix_webhook_deliveries_created_at'), table_name='webhook_deliveries')
    op.drop_index(op.f('ix_webhook_deliveries_status'), table_name='webhook_deliveries')
    op.drop_index(op.f('ix_webhook_deliveries_event_type'), table_name='webhook_deliveries')
    op.drop_index(op.f('ix_webhook_deliveries_event_id'), table_name='webhook_deliveries')
    op.drop_index(op.f('ix_webhook_deliveries_webhook_id'), table_name='webhook_deliveries')
    op.drop_index(op.f('ix_webhook_deliveries_id'), table_name='webhook_deliveries')
    op.drop_index(op.f('ix_webhooks_created_at'), table_name='webhooks')
    op.drop_index(op.f('ix_webhooks_enabled'), table_name='webhooks')
    op.drop_index(op.f('ix_webhooks_id'), table_name='webhooks')
    
    # Drop tables
    op.drop_table('webhook_deliveries')
    op.drop_table('webhooks')
