"""add trigger_source to etl_audit

Indica quién lanzó cada ejecución del ETL: "manual" o "scheduled".
Las ejecuciones anteriores quedan en NULL.

Revision ID: 005
Revises: cbc58ae29def
Create Date: 2026-11-26
"""
from alembic import op
import sqlalchemy as sa

revision = "005"
down_revision = "cbc58ae29def"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("etl_audit", sa.Column("trigger_source", sa.String(20), nullable=True), schema="dwh")


def downgrade() -> None:
    op.drop_column("etl_audit", "trigger_source", schema="dwh")
