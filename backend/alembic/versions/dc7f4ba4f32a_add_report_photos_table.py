"""add_report_photos_table

Revision ID: dc7f4ba4f32a
Revises: 53aac29d198a
Create Date: 2026-02-18 02:01:51.669233

"""
from alembic import op
import sqlalchemy as sa


revision = 'dc7f4ba4f32a'
down_revision = '53aac29d198a'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create report_photos table
    op.create_table(
        'report_photos',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('report_id', sa.String(length=36), nullable=False),
        sa.Column('photo_url', sa.String(), nullable=False),
        sa.Column('is_before_photo', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('upload_order', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.ForeignKeyConstraint(['report_id'], ['reports.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes
    op.create_index('ix_report_photos_report_id', 'report_photos', ['report_id'])
    op.create_index('ix_report_photos_upload_order', 'report_photos', ['report_id', 'upload_order'])


def downgrade() -> None:
    # Drop indexes
    op.drop_index('ix_report_photos_upload_order', table_name='report_photos')
    op.drop_index('ix_report_photos_report_id', table_name='report_photos')
    
    # Drop table
    op.drop_table('report_photos')
