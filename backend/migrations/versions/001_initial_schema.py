"""
001_initial_schema.py — Migración inicial del DWH.

Crea el schema `dwh` y todas las tablas del star schema de Spotify Wrapped:
    dwh.dim_users            → perfil y tokens OAuth del usuario.
    dwh.dim_artists          → catálogo de artistas (con genres ARRAY).
    dwh.dim_tracks           → catálogo de canciones.
    dwh.fact_listening_history → historial de escucha con UniqueConstraint(user_id, played_at).
    dwh.etl_audit            → log de ejecuciones del pipeline ETL.
    public.pkce_sessions     → sesiones PKCE temporales para OAuth.

Nota: esta migración es la única existente. Cambios posteriores en los modelos
(como image_url en dim_artists o album_image_url en dim_tracks) se aplicaron
mediante `Base.metadata.create_all` en desarrollo, no con Alembic.

Revision ID: 001
Revises: (ninguno — migración base)
Create Date: 2026-05-12
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create schema dwh and all tables."""
    
    # Crear schema dwh
    op.execute("CREATE SCHEMA IF NOT EXISTS dwh")
    
    # dim_users
    op.create_table(
        'dim_users',
        sa.Column('user_id', sa.Integer(), nullable=False, autoincrement=True),
        sa.Column('spotify_id', sa.String(100), nullable=False, unique=True, index=True),
        sa.Column('display_name', sa.String(255), nullable=True),
        sa.Column('email', sa.String(255), nullable=True),
        sa.Column('country', sa.String(10), nullable=True),
        sa.Column('followers', sa.Integer(), default=0),
        sa.Column('product', sa.String(20), default='free'),
        sa.Column('spotify_access_token', sa.Text(), nullable=False),
        sa.Column('spotify_refresh_token', sa.Text(), nullable=True),
        sa.Column('token_expires_at', sa.DateTime(), nullable=True),
        sa.Column('loaded_at', sa.DateTime(), server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('user_id'),
        schema='dwh',
    )
    
    # dim_artists
    op.create_table(
        'dim_artists',
        sa.Column('artist_id', sa.Integer(), nullable=False, autoincrement=True),
        sa.Column('spotify_id', sa.String(100), nullable=False, unique=True, index=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('popularity', sa.Integer(), nullable=True),
        sa.Column('followers_count', sa.Integer(), nullable=True),
        sa.Column('genres', sa.ARRAY(sa.String()), nullable=True),
        sa.Column('loaded_at', sa.DateTime(), server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('artist_id'),
        schema='dwh',
    )
    
    # dim_tracks
    op.create_table(
        'dim_tracks',
        sa.Column('track_id', sa.Integer(), nullable=False, autoincrement=True),
        sa.Column('spotify_id', sa.String(100), nullable=False, unique=True, index=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('artist_id', sa.Integer(), nullable=False),
        sa.Column('album_name', sa.String(255), nullable=True),
        sa.Column('duration_ms', sa.Integer(), nullable=True),
        sa.Column('popularity', sa.Integer(), nullable=True),
        sa.Column('explicit', sa.Boolean(), default=False),
        sa.Column('loaded_at', sa.DateTime(), server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('track_id'),
        sa.ForeignKeyConstraint(['artist_id'], ['dwh.dim_artists.artist_id']),
        schema='dwh',
    )
    
    # fact_listening_history
    op.create_table(
        'fact_listening_history',
        sa.Column('id', sa.Integer(), nullable=False, autoincrement=True),
        sa.Column('user_id', sa.Integer(), nullable=False, index=True),
        sa.Column('track_id', sa.Integer(), nullable=False),
        sa.Column('artist_id', sa.Integer(), nullable=False),
        sa.Column('played_at', sa.DateTime(), nullable=False, index=True),
        sa.Column('hour_of_day', sa.Integer(), nullable=True),
        sa.Column('day_of_week', sa.String(10), nullable=True),
        sa.Column('context_type', sa.String(50), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['user_id'], ['dwh.dim_users.user_id']),
        sa.ForeignKeyConstraint(['track_id'], ['dwh.dim_tracks.track_id']),
        sa.ForeignKeyConstraint(['artist_id'], ['dwh.dim_artists.artist_id']),
        sa.UniqueConstraint('user_id', 'played_at'),
        schema='dwh',
    )
    
    # etl_audit
    op.create_table(
        'etl_audit',
        sa.Column('audit_id', sa.Integer(), nullable=False, autoincrement=True),
        sa.Column('spotify_user_id', sa.String(100), nullable=False),
        sa.Column('started_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('finished_at', sa.DateTime(), nullable=True),
        sa.Column('duration_ms', sa.Integer(), nullable=True),
        sa.Column('status', sa.String(20), nullable=False),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('users_new', sa.Integer(), default=0),
        sa.Column('artists_new', sa.Integer(), default=0),
        sa.Column('artists_skipped', sa.Integer(), default=0),
        sa.Column('tracks_new', sa.Integer(), default=0),
        sa.Column('tracks_skipped', sa.Integer(), default=0),
        sa.Column('history_new', sa.Integer(), default=0),
        sa.Column('history_skipped', sa.Integer(), default=0),
        sa.Column('cursor_after_ms', sa.String(50), nullable=True),
        sa.Column('cursor_next_ms', sa.String(50), nullable=True),
        sa.Column('logs', sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint('audit_id'),
        schema='dwh',
    )
    
    # pkce_sessions (schema public)
    op.create_table(
        'pkce_sessions',
        sa.Column('state', sa.String(128), nullable=False, primary_key=True),
        sa.Column('verifier', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        schema='public',
    )


def downgrade() -> None:
    """Drop all tables and schema."""
    op.drop_table('pkce_sessions', schema='public')
    op.drop_table('etl_audit', schema='dwh')
    op.drop_table('fact_listening_history', schema='dwh')
    op.drop_table('dim_tracks', schema='dwh')
    op.drop_table('dim_artists', schema='dwh')
    op.drop_table('dim_users', schema='dwh')
    op.execute("DROP SCHEMA IF EXISTS dwh")
