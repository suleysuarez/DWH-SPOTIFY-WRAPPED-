"""add is_full_run to etl_audit

Revision ID: cbc58ae29def
Revises: 003
Create Date: 2026-05-21 23:07:01.102011

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'cbc58ae29def'
down_revision = '003'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('etl_audit', sa.Column('is_full_run', sa.Boolean(), nullable=False, server_default='false'), schema='dwh')


def downgrade() -> None:
    op.drop_column('etl_audit', 'is_full_run', schema='dwh')
