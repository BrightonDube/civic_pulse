"""create_users_table

Revision ID: 0fed0e439052
Revises: 
Create Date: 2026-02-15 12:05:16.887272

"""
from alembic import op
import sqlalchemy as sa


revision = '0fed0e439052'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'users',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('email', sa.String(), nullable=False),
        sa.Column('password_hash', sa.String(), nullable=False),
        sa.Column('phone', sa.String(), nullable=False),
        sa.Column('role', sa.String(), nullable=False, server_default='user'),
        sa.Column('email_verified', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('leaderboard_opt_out', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('report_count', sa.Integer(), nullable=False, server_default='0'),
    )
    
    # Create unique constraint on email
    op.create_unique_constraint('uq_users_email', 'users', ['email'])
    
    # Create index on email for faster lookups
    op.create_index('ix_users_email', 'users', ['email'])


def downgrade() -> None:
    op.drop_index('ix_users_email', table_name='users')
    op.drop_constraint('uq_users_email', 'users', type_='unique')
    op.drop_table('users')
