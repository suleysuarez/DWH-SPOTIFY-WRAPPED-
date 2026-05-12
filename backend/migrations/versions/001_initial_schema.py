"""Initial schema creation

Revision ID: 001
Revises: 
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
    """Create all tables."""
    
    # dim_users
    op.create_table(
        'dim_users',
        sa.Column('user_id', sa.Integer(), nullable=False, autoincrement=True),
        sa.Column('spotify_id', sa.String(50), nullable=False, unique=True, index=True),
        sa.Column('display_name', sa.String(255), nullable=True),
        sa.Column('email', sa.String(255), nullable=True),
        sa.Column('country', sa.String(10), nullable=True),
        sa.Column('followers', sa.Integer(), default=0),
        sa.Column('product', sa.String(20), default='free'),
        sa.Column('images_url', sa.String(500), nullable=True),
        sa.Column('spotify_access_token', sa.Text(), nullable=False),
        sa.Column('spotify_refresh_token', sa.Text(), nullable=True),
        sa.Column('token_expires_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.PrimaryKeyConstraint('user_id'),
    )
    
    # dim_artists
    op.create_table(
        'dim_artists',
        sa.Column('artist_id', sa.Integer(), nullable=False, autoincrement=True),
        sa.Column('spotify_id', sa.String(50), nullable=False, unique=True, index=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('genres', sa.String(500), nullable=True),
        sa.Column('popularity', sa.Integer(), nullable=True),
        sa.Column('images_url', sa.String(500), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('artist_id'),
    )
    
    # dim_tracks
    op.create_table(
        'dim_tracks',
        sa.Column('track_id', sa.Integer(), nullable=False, autoincrement=True),
        sa.Column('spotify_id', sa.String(50), nullable=False, unique=True, index=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('artist_id', sa.Integer(), nullable=False),
        sa.Column('album_name', sa.String(255), nullable=True),
        sa.Column('album_image_url', sa.String(500), nullable=True),
        sa.Column('duration_ms', sa.Integer(), nullable=True),
        sa.Column('explicit', sa.Boolean(), default=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('track_id'),
        sa.ForeignKeyConstraint(['artist_id'], ['dim_artists.artist_id']),
    )
    
    # fact_listening_history
    op.create_table(
        'fact_listening_history',
        sa.Column('history_id', sa.Integer(), nullable=False, autoincrement=True),
        sa.Column('user_id', sa.Integer(), nullable=False, index=True),
        sa.Column('track_id', sa.Integer(), nullable=False),
        sa.Column('artist_id', sa.Integer(), nullable=False),
        sa.Column('played_at', sa.DateTime(), nullable=False, index=True),
        sa.Column('context_type', sa.String(50), nullable=True),
        sa.Column('context_name', sa.String(255), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('history_id'),
        sa.ForeignKeyConstraint(['user_id'], ['dim_users.user_id']),
        sa.ForeignKeyConstraint(['track_id'], ['dim_tracks.track_id']),
        sa.ForeignKeyConstraint(['artist_id'], ['dim_artists.artist_id']),
    )
    
    # etl_audit
    op.create_table(
        'etl_audit',
        sa.Column('etl_id', sa.Integer(), nullable=False, autoincrement=True),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('status', sa.String(20), default='pending'),
        sa.Column('started_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('ended_at', sa.DateTime(), nullable=True),
        sa.Column('duration_ms', sa.Integer(), nullable=True),
        sa.Column('records_extracted', sa.Integer(), default=0),
        sa.Column('records_loaded', sa.Integer(), default=0),
        sa.Column('records_skipped', sa.Integer(), default=0),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('cursor_next_ms', sa.String(50), nullable=True),
        sa.Column('logs', sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint('etl_id'),
        sa.ForeignKeyConstraint(['user_id'], ['dim_users.user_id']),
    )
    
    # pkce_sessions
    op.create_table(
        'pkce_sessions',
        sa.Column('session_id', sa.Integer(), nullable=False, autoincrement=True),
        sa.Column('state', sa.String(100), nullable=False, unique=True, index=True),
        sa.Column('code_verifier', sa.String(128), nullable=False),
        sa.Column('code_challenge', sa.String(128), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('expires_at', sa.DateTime(), nullable=False),
        sa.Column('used', sa.Boolean(), default=False),
        sa.PrimaryKeyConstraint('session_id'),
    )


def downgrade() -> None:
    """Drop all tables."""
    op.drop_table('pkce_sessions')
    op.drop_table('etl_audit')
    op.drop_table('fact_listening_history')
    op.drop_table('dim_tracks')
    op.drop_table('dim_artists')
    op.drop_table('dim_users')
