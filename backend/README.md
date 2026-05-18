# Backend — FastAPI + SQLAlchemy + PostgreSQL

**Autoras/es:** Suley Suárez y Jhonatan Vera — Universidad de Pamplona 2026-I

API REST del Data Warehouse personal de Spotify. Maneja el flujo OAuth PKCE, el pipeline ETL y todas las consultas analíticas.

---

## Estructura

```
backend/
├── app/
│   ├── main.py                  # App FastAPI, CORS, monta router /v1
│   ├── core/
│   │   ├── config.py            # pydantic-settings — lee .env
│   │   ├── database.py          # Motor SQLAlchemy, dependencia get_db()
│   │   └── security.py          # ⚠️ LEGACY — no usado en flujo activo
│   ├── models/
│   │   └── models.py            # Todos los ORM: dim_*, fact_*, etl_audit, pkce_sessions
│   ├── v1/                      # Código activo
│   │   ├── api.py               # APIRouter raíz /v1
│   │   ├── routers/
│   │   │   ├── auth.py          # OAuth PKCE: /login, /callback
│   │   │   ├── artists.py       # /artists/top
│   │   │   ├── tracks.py        # /tracks/top
│   │   │   ├── history.py       # /history/peak-hour, /genres, /stats, /recently-played
│   │   │   ├── profile.py       # /profile/me
│   │   │   └── etl.py           # /etl/run, /etl/status, /etl/history
│   │   ├── services/
│   │   │   ├── auth_service.py  # PKCE helpers + JWT (HS256, 8h)
│   │   │   ├── spotify_client.py # HTTP client para la API de Spotify
│   │   │   └── etl_service.py   # Orquestación ETL: extract → transform → load
│   │   └── schemas/
│   │       ├── artists.py       # ArtistResponse, ArtistsResponse
│   │       ├── tracks.py        # TrackResponse, TracksResponse
│   │       ├── history.py       # PeakHour, GenreData, QuickStats
│   │       ├── profile.py       # UserProfileResponse
│   │       └── auth.py          # TokenResponse
│   ├── routers/                 # ⚠️ LEGACY — NO montado en main.py
│   ├── schemas/                 # ⚠️ LEGACY
│   └── services/                # ⚠️ LEGACY
└── migrations/
    ├── env.py                   # Alembic env: DATABASE_URL + schema dwh
    └── versions/
        └── 001_initial_schema.py
```

---

## Schema de Base de Datos (PostgreSQL schema `dwh`)

```
dim_users ──────────────────────────────────────────────────────────┐
  id (PK), spotify_id (UQ), display_name, email, country,           │
  spotify_access_token, spotify_refresh_token, token_expires_at     │
                                                                     │
dim_artists ─────────────────────────────────────────────────────┐  │
  id (PK), spotify_id (UQ), name, popularity, genres (ARRAY)     │  │
                                                                  │  │
dim_tracks ──────────────────────────────────────────────────┐   │  │
  id (PK), spotify_id (UQ), name, artist_id (FK→dim_artists), │   │  │
  duration_ms, explicit, album_image_url                      │   │  │
                                                              │   │  │
fact_listening_history                                        │   │  │
  id (PK), user_id (FK)──────────────────────────────────────┘───┘  │
  track_id (FK)────────────────────────────────────────────────────┘
  artist_id (FK→dim_artists), played_at, hour_of_day, day_of_week
  UNIQUE(user_id, played_at)

etl_audit
  id (PK), user_id (FK→dim_users), started_at, finished_at,
  duration_ms, status (running/success/error), error_message,
  artists_new, tracks_new, history_new, history_skipped,
  cursor_next_ms (para sync incremental)

pkce_sessions (schema public)
  state (PK), code_verifier, created_at
```

---

## Variables de Entorno (`backend/.env`)

```env
DATABASE_URL=postgresql://user:pass@host:5432/dbname
SPOTIFY_CLIENT_ID=...
SPOTIFY_CLIENT_SECRET=...
SPOTIFY_REDIRECT_URI=http://localhost:8000/v1/auth/callback
JWT_SECRET=...           # python -c "import secrets; print(secrets.token_hex(32))"
FRONTEND_URL=http://localhost:3000
ALLOW_HOSTS=http://localhost:3000
```

---

## Comandos

```bash
# Servidor de desarrollo
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Migraciones
alembic upgrade head
alembic revision --autogenerate -m "descripcion"
alembic downgrade -1

# Lint
black app/
flake8 app/

# Tests
pytest tests/
```

---

## Notas de Implementación

- **Pool de conexiones:** ajustado para Neon free tier (5 conexiones, max 10, pool_recycle=300).
- **get_current_user:** copiado en cada router (no hay dependencia compartida).
- **genres en DimArtists:** columna ARRAY — requiere `flag_modified(artist, "genres")` antes de commit al actualizar.
- **ETL incremental:** usa `cursor_next_ms` del último `etl_audit` exitoso para no reprocesar historial.
- **Scopes OAuth requeridos:** `user-read-private user-read-email user-top-read user-read-recently-played`
