"""
002_add_image_url_to_dim_users.py — Agrega image_url a dwh.dim_users.

Almacena la URL de la foto de perfil del usuario de Spotify
(tomada de images[0].url durante el login/ETL).

Revision ID: 002
Revises: 001
Create Date: 2026-05-15
"""

from alembic import op
import sqlalchemy as sa


revision = '002'
down_revision = '001'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        'dim_users',
        sa.Column('image_url', sa.Text(), nullable=True),
        schema='dwh',
    )


def downgrade() -> None:
    op.drop_column('dim_users', 'image_url', schema='dwh')
