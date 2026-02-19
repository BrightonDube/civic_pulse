"""Add image_hash column to reports

Revision ID: 4c88f8126561
Revises: add_notifications_001
Create Date: 2026-02-19 09:13:15.424868

"""
from alembic import op
import sqlalchemy as sa


revision = '4c88f8126561'
down_revision = 'add_notifications_001'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add image_hash column to reports table for duplicate image detection
    op.add_column('reports', sa.Column('image_hash', sa.String(length=64), nullable=True))
    op.create_index(op.f('ix_reports_image_hash'), 'reports', ['image_hash'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_reports_image_hash'), table_name='reports')
    op.drop_column('reports', 'image_hash')
