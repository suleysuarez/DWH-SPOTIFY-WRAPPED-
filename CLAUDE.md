# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Description

Full-stack personal data warehouse that syncs Spotify listening history and visualizes analytics. Academic project at Universidad de Pamplona (2026-I).

**Stack:**
- Frontend: React 19 + TypeScript + Vite + Tailwind CSS 4 + shadcn/ui + Wouter
- Backend: FastAPI + SQLAlchemy 2.0 + PostgreSQL + Alembic
- Auth: OAuth 2.0 PKCE (Spotify) + JWT (HS256, 8h expiry)
- Design: Glassmorphism Premium Dark (background #121212, Spotify green accent #1DB954)

## Development Commands

### Backend
```bash
cd backend
# First-time setup
python -m venv venv
venv\Scripts\activate      # Windows
pip install -r requirements.txt

# Dev server
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
# First-time setup (uses pnpm)
pnpm install

# Dev server (port 3000)
pnpm dev

# Type checking
pnpm check

# Build (Vite client → dist/public/ + esbuild server → dist/index.js)
pnpm build
```

### Tests
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
ALLOW_HOSTS=http://localhost:3000,http://127.0.0.1:3000   # comma-separated list
LOG_LEVEL=INFO
```

**`frontend/.env.local`:**
```
VITE_API_URL=http://127.0.0.1:8000
```

> **Note:** `PeakHourCard.tsx` reads `VITE_API_BASE_URL` directly (not `VITE_API_URL`) and falls back to `http://127.0.0.1:8000`. All other components use `lib/api.ts` which reads `VITE_API_URL`.

## Architecture

### Backend (`backend/app/`)
- `main.py` — FastAPI app, CORS middleware, `Base.metadata.create_all` on startup, mounts `/v1` router
- `core/config.py` — pydantic-settings; reads `.env`; `get_allow_hosts()` splits `ALLOW_HOSTS` by comma
- `core/database.py` — SQLAlchemy engine (pool tuned for Neon free tier), `get_db()` dependency
- `models/models.py` — All ORM models in `dwh` schema (except `PkceSessions` which is in `public`)
- `v1/api.py` — Aggregates all v1 routers under `/v1` prefix
- `v1/routers/` — One file per resource: `auth`, `artists`, `tracks`, `history`, `etl`, `profile`
- `v1/services/auth_service.py` — PKCE pair generation, JWT create/verify
- `v1/services/spotify_client.py` — HTTP client for Spotify API (current user, top artists/tracks, recently played)
- `v1/services/etl_service.py` — ETL orchestration: static methods grouped as Extract / Transform / Load
- `v1/schemas/` — Pydantic request/response models per resource

> **Legacy code:** `backend/app/routers/` and `backend/app/services/` contain old router/service files that are **not wired** to the active app. All active code is under `backend/app/v1/`.

> **Auth dependency duplication:** Each router file independently defines its own `get_current_user()` async function (copy-paste pattern). There is no shared dependency.

### Frontend (`frontend/src/`)
- `App.tsx` — Wouter routes: public (`/login`, `/callback`), protected (`/dashboard`, `/profile`, `/etl`)
- `router/ProtectedRoute.tsx` — JWT validity guard via `isTokenValid()`, redirects to `/login`
- `lib/api.ts` — Fetch wrapper with Bearer token injection, 401 auto-logout, typed endpoint helpers
- `lib/auth.ts` — JWT stored in `localStorage` under key `"app_token"`; `isTokenValid()` decodes payload client-side to check `exp`
- `hooks/useApi.ts` — Generic fetching hook with loading/error states
- `pages/Callback.tsx` — Parses `?token=JWT` from URL, saves to localStorage, redirects to `/dashboard`
- `components/dashboard/` — `QuickStatsCards`, `TopArtistsCard`, `TopTracksCard`, `PeakHourCard`, `GenresChart`
- `components/etl/` — `RunEtlPanel`, `DwhStatusTable`, `EtlHistoryTable`
- `components/ui/` — shadcn/ui components + custom: `SkeletonCard`, `EmptyState`, `ErrorState`

> **`shared/const.ts`** exports `COOKIE_NAME = "app_session_id"` and `ONE_YEAR_MS` — these are **not used** by the current auth flow; JWT key is hardcoded as `"app_token"` in `lib/auth.ts`.

### Database Schema (PostgreSQL `dwh` star schema)
| Table | Type | Key Columns |
|---|---|---|
| `dim_users` | Dimension | `spotify_id`, `display_name`, `spotify_access_token`, `spotify_refresh_token`, `token_expires_at` |
| `dim_artists` | Dimension | `spotify_id`, `name`, `popularity`, `genres` (ARRAY), `image_url` |
| `dim_tracks` | Dimension | `spotify_id`, `name`, `artist_id` (FK), `album_image_url`, `duration_ms`, `explicit` |
| `fact_listening_history` | Fact | `user_id` (FK), `track_id` (FK), `artist_id` (FK), `played_at`, `hour_of_day`, `day_of_week`, `context_type` |
| `etl_audit` | Audit | `status` (`running`/`success`/`error`), `duration_ms`, counters per entity, `cursor_after_ms`, `cursor_next_ms` |
| `pkce_sessions` | Auth (schema: `public`) | `state` (PK), `verifier`, `created_at` |

Deduplication in `fact_listening_history` is done by querying `(user_id, track_id, played_at)` before insert — there is no DB-level unique constraint on this combination.

### API Endpoints (all under `/v1`)
| Method | Route | Auth | Description |
|---|---|---|---|
| GET | `/auth/login` | No | Returns Spotify OAuth URL |
| GET | `/auth/callback` | No | Exchanges code for JWT, redirects frontend |
| GET | `/artists/top` | JWT | Top 5 artists from DWH |
| GET | `/tracks/top` | JWT | Top 5 tracks from DWH |
| GET | `/history/recently-played` | JWT | Last N plays (default 50) |
| GET | `/history/stats` | JWT | Quick stats (counts, last sync, top track, total minutes) |
| GET | `/history/genres` | JWT | Top 10 genres with counts and percentages |
| GET | `/history/peak-hour` | JWT | Single peak hour `{hour, play_count, label}` |
| GET | `/history/peak-hour/distribution` | JWT | Play counts for all 24 hours |
| GET | `/profile/me` | JWT | Current user profile |
| POST | `/etl/run` | JWT | Trigger full ETL pipeline, returns logs |
| GET | `/etl/status` | JWT | DWH table counts + last 5 ETL runs |
| GET | `/etl/history` | JWT | Paginated ETL run history (params: `status`, `limit`, `offset`) |

### ETL Pipeline (3 phases)
1. **Extract** — Calls Spotify API: current user, top 50 artists, top 50 tracks, recently played (cursor pagination)
2. **Transform** — Maps Spotify API fields to DWH schema, computes `hour_of_day` and `day_of_week` from `played_at`
3. **Load** — Insert-or-update by `spotify_id`; if a track's artist is missing, a minimal `DimArtists` record is created; writes `EtlAudit`

Incremental sync: uses `cursor_next_ms` from the last successful audit as the `after` parameter for `recently_played` to avoid reprocessing old history.

### OAuth Flow
1. Frontend → GET `/v1/auth/login` → receives `authorization_url`
2. Redirect to Spotify consent screen
3. Spotify → GET `/v1/auth/callback?code=X&state=Y` (backend) → issues JWT, redirects to `{FRONTEND_URL}/callback?token=JWT`
4. Frontend at `/callback` saves JWT to `localStorage["app_token"]` → redirects to `/dashboard`

## Key Conventions
- All backend endpoints versioned under `/v1`
- JWT stored in `localStorage["app_token"]`; `isTokenValid()` checks expiry client-side without verification
- Frontend components render `SkeletonCard` while loading, `EmptyState` when DWH has no data, `ErrorState` on failures
- The `dwh` PostgreSQL schema must exist before running migrations; Alembic's `env.py` manages schema creation
- Connection pool tuned for Neon free tier: 5 connections, max 10
- Required Spotify scopes: `user-read-private user-read-email user-top-read user-read-recently-played`
- `genres` in `dim_artists` is a PostgreSQL `ARRAY(String)`; SQLAlchemy requires `flag_modified(obj, "genres")` after mutation for change detection
