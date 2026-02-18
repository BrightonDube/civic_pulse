"""add_comments_table

Revision ID: 53aac29d198a
Revises: 0fed0e439052
Create Date: 2026-02-18 01:31:52.425243

Requirements: 14.1, 14.2, 14.3
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID


revision = '53aac29d198a'
down_revision = '0fed0e439052'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create comments table for report discussions."""
    op.create_table(
        'comments',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('report_id', sa.String(36), nullable=False),
        sa.Column('user_id', sa.String(36), nullable=False),
        sa.Column('parent_comment_id', sa.String(36), nullable=True),
        sa.Column('text', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['report_id'], ['reports.id'], name='fk_comments_report_id'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], name='fk_comments_user_id'),
        sa.ForeignKeyConstraint(['parent_comment_id'], ['comments.id'], name='fk_comments_parent_comment_id'),
    )
    
    # Create indexes for performance
    op.create_index('ix_comments_report_id', 'comments', ['report_id'])
    op.create_index('ix_comments_created_at', 'comments', ['created_at'])
    op.create_index('ix_comments_parent_id', 'comments', ['parent_comment_id'])


def downgrade() -> None:
    """Drop comments table."""
    op.drop_index('ix_comments_parent_id', table_name='comments')
    op.drop_index('ix_comments_created_at', table_name='comments')
    op.drop_index('ix_comments_report_id', table_name='comments')
    op.drop_table('comments')
