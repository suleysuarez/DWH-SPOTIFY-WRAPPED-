"""
filename: 003_add_missing_columns.py
author: Suley Suárez y Jhonatan Vera
date: 2026-05-15
version: 1.0
description: Agrega columnas que el ORM requiere pero que la migración 001 omitió:
             image_url en dim_artists, album_image_url en dim_tracks.
             Además fija el server_default de explicit a FALSE para evitar NULLs.

Revision ID: 003
Revises: 002
Create Date: 2026-05-15
"""

from alembic import op
import sqlalchemy as sa


revision = '003'
down_revision = '002'
branch_labels = None
depends_on = None


def upgrade() -> None:
    conn = op.get_bind()

    # imagen del artista — solo si no existe (create_all pudo haberla creado)
    col_exists = conn.execute(sa.text(
        "SELECT 1 FROM information_schema.columns "
        "WHERE table_schema='dwh' AND table_name='dim_artists' AND column_name='image_url'"
    )).fetchone()
    if not col_exists:
        op.add_column(
            'dim_artists',
            sa.Column('image_url', sa.Text(), nullable=True),
            schema='dwh',
        )

    # portada del álbum — solo si no existe
    col_exists = conn.execute(sa.text(
        "SELECT 1 FROM information_schema.columns "
        "WHERE table_schema='dwh' AND table_name='dim_tracks' AND column_name='album_image_url'"
    )).fetchone()
    if not col_exists:
        op.add_column(
            'dim_tracks',
            sa.Column('album_image_url', sa.Text(), nullable=True),
            schema='dwh',
        )

    # fijar server_default en explicit para evitar NULLs futuros
    op.alter_column(
        'dim_tracks',
        'explicit',
        server_default=sa.text('false'),
        schema='dwh',
    )

    # rellenar NULLs existentes en explicit y popularity
    op.execute("UPDATE dwh.dim_tracks SET explicit = false WHERE explicit IS NULL")
    op.execute("UPDATE dwh.dim_tracks SET popularity = 0 WHERE popularity IS NULL")


def downgrade() -> None:
    op.alter_column('dim_tracks', 'explicit', server_default=None, schema='dwh')
    op.drop_column('dim_tracks', 'album_image_url', schema='dwh')
    op.drop_column('dim_artists', 'image_url', schema='dwh')
