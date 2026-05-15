# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

A full-stack personal data warehouse that syncs Spotify listening history and visualizes analytics. Built as an academic project for Universidad de Pamplona (2026-I).

**Stack:**
- Frontend: React 19 + TypeScript + Vite + Tailwind CSS 4 + shadcn/ui + Wouter
- Backend: FastAPI + SQLAlchemy 2.0 + PostgreSQL + Alembic
- Auth: OAuth 2.0 PKCE (Spotify) + JWT (HS256, 8h expiry)
- Design: Glassmorphism Premium Dark (#121212 bg, Spotify green #1DB954 accents)

## Development Commands

### Backend
```bash
cd backend
# Install (one-time)
python -m venv venv
venv\Scripts\activate      # Windows
pip install -r requirements.txt

# Run dev server
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Database migrations
alembic upgrade head
alembic revision --autogenerate -m "Description"
alembic downgrade -1

# Lint/format
black app/
flake8 app/
```

### Frontend
```bash
# Install (one-time, uses pnpm)
pnpm install

# Dev server (port 3000)
pnpm dev

# Type check
pnpm check

# Build (Vite client → dist/public/ + esbuild server → dist/index.js)
pnpm build

# Production server
node dist/index.js
```

### Run tests
```bash
cd backend && pytest tests/
pnpm test   # frontend (vitest)
```

## Environment Variables

**`backend/.env`:**
```
DATABASE_URL=postgresql://user:pass@host:5432/dbname
SPOTIFY_CLIENT_ID=...
SPOTIFY_CLIENT_SECRET=...
SPOTIFY_REDIRECT_URI=http://localhost:8000/v1/auth/callback
JWT_SECRET=...           # Generate: python -c "import secrets; print(secrets.token_hex(32))"
FRONTEND_URL=http://localhost:3000
ALLOW_HOSTS=http://localhost:3000
```

**`frontend/.env.local` (or `.env`):**
```
VITE_API_URL=http://localhost:8000
```

## Architecture

### Backend Structure (`backend/app/`)
- `main.py` — FastAPI app, CORS config, startup table creation, mounts `/v1` router
- `core/config.py` — pydantic-settings; reads `.env`; `get_allow_hosts()` returns CORS list
- `core/database.py` — SQLAlchemy engine (pool tuned for Neon), `get_db()` session dependency
- `models/models.py` — All ORM models in schema `dwh` (see Database section)
- `v1/routers/` — One file per resource (auth, artists, tracks, history, etl, profile)
- `v1/services/auth_service.py` — PKCE generation, JWT create/verify
- `v1/services/spotify_client.py` — Spotify API HTTP client (user, top artists/tracks, recently_played)
- `v1/services/etl_service.py` — Full ETL orchestration (extract → transform → load → audit)
- `v1/schemas/` — Pydantic request/response models per resource

### Frontend Structure (`frontend/src/`)
- `App.tsx` — Wouter routes (public: /login, /callback; protected: /dashboard, /profile, /etl)
- `router/ProtectedRoute.tsx` — JWT validity guard, redirects to /login
- `lib/api.ts` — Axios-based client that injects `Authorization: Bearer <token>` from localStorage
- `lib/auth.ts` — JWT token read/write/clear from localStorage
- `hooks/useApi.ts` — Generic data-fetching hook with loading/error states
- `pages/` — Login, Callback (parses JWT from URL, saves to localStorage), Dashboard, Profile, Etl
- `components/dashboard/` — QuickStatsCards, TopArtistsCard, TopTracksCard, PeakHourCard, GenresChart
- `components/etl/` — RunEtlPanel, DwhStatusTable, EtlHistoryTable
- `components/ui/` — 50+ shadcn/ui components; custom: SkeletonCard, EmptyState, ErrorState

### Database Schema (`dwh` PostgreSQL schema — star schema)
| Table | Type | Key Columns |
|---|---|---|
| `dim_users` | Dimension | spotify_id, display_name, spotify_access_token, token_expires_at |
| `dim_artists` | Dimension | spotify_id, name, popularity, genres (ARRAY) |
| `dim_tracks` | Dimension | spotify_id, name, artist_id (FK), duration_ms, explicit |
| `fact_listening_history` | Fact | user_id (FK), track_id (FK), artist_id (FK), played_at, hour_of_day, day_of_week |
| `etl_audit` | Audit | status (running/success/failed), duration_ms, counts per entity |

Unique constraint on `fact_listening_history(user_id, played_at)` prevents duplicates.

### API Endpoints (all under `/v1`)
| Method | Path | Auth | Description |
|---|---|---|---|
| GET | `/auth/login` | No | Returns Spotify OAuth URL |
| GET | `/auth/callback` | No | Exchanges code for JWT |
| GET | `/artists/top` | JWT | Top 5 artists from DWH |
| GET | `/tracks/top` | JWT | Top 5 tracks from DWH |
| GET | `/history/peak-hour` | JWT | Peak listening hour |
| GET | `/history/genres` | JWT | Top 5 genres |
| GET | `/history/stats` | JWT | Quick stats (counts, last sync) |
| GET | `/profile/me` | JWT | Current user profile |
| POST | `/etl/run` | JWT | Trigger full ETL pipeline |
| GET | `/etl/status` | JWT | ETL history + audit log |

### ETL Pipeline (3 phases)
1. **Extract** — Calls Spotify API for user, top 50 artists, top 50 tracks, recently played (cursor-paginated)
2. **Transform** — Maps Spotify API fields to DWH schema, computes `hour_of_day`, `day_of_week`
3. **Load** — Upserts by `spotify_id`; skips duplicates; maintains FK relationships; writes to `etl_audit`

Incremental sync: uses `cursor_next_ms` from last successful audit to avoid reprocessing old history.

### OAuth Flow
1. Frontend → GET `/v1/auth/login` → receives `authorization_url`
2. Redirect to Spotify consent screen
3. Spotify → GET `/v1/auth/callback?code=X&state=Y` (backend) → returns JWT
4. Frontend at `/callback?token=JWT` saves to localStorage → redirects to `/dashboard`

## Key Conventions
- All backend endpoints are versioned under `/v1`
- JWT is stored in `localStorage` (key defined in `shared/const.ts`)
- Frontend components show `SkeletonCard` while loading, `EmptyState` when DWH has no data, `ErrorState` on failure
- The `dwh` PostgreSQL schema must exist before running migrations; Alembic's `env.py` handles schema creation
- Database connection pool is tuned for Neon free tier (5 connections, max 10 total)
- Spotify required scopes: `user-read-private user-read-email user-top-read user-read-recently-played`
