# Mi Spotify Wrapped — Personal Data Warehouse

Aplicación full-stack para sincronizar, analizar y visualizar el historial de Spotify en un Data Warehouse personal.

**Proyecto académico — Universidad de Pamplona 2026-I**
Autoras/es: Suley Suárez y Jhonatan Vera | Profesor: Juan Alejandro Carrillo Jaimes

---

## Stack

| Capa | Tecnologías |
|---|---|
| Frontend | React 19 + TypeScript + Vite + Tailwind CSS 4 + Wouter |
| Backend | FastAPI + SQLAlchemy 2.0 + Alembic + PostgreSQL |
| Auth | OAuth 2.0 PKCE (Spotify) + JWT HS256 (8h) |
| ETL | Pipeline incremental: Extract → Transform → Load |
| UI | Glassmorphism Premium Dark (#121212 + #1DB954) |

---

## Arquitectura General

```
┌─────────────────────┐        ┌──────────────────────────┐
│  React (Wouter)     │ JWT    │  FastAPI (puerto 8000)   │
│  puerto 3000        │◄──────►│  /v1/auth, /v1/artists,  │
│                     │        │  /v1/tracks, /v1/history, │
│  /dashboard         │        │  /v1/profile, /v1/etl     │
│  /profile           │        └──────────┬───────────────┘
│  /etl               │                   │ SQLAlchemy
└─────────────────────┘                   ▼
                                ┌──────────────────────┐
          Spotify API           │  PostgreSQL (Neon)   │
          ◄─────────────────────│  schema dwh:         │
          OAuth PKCE + REST     │  dim_users           │
                                │  dim_artists         │
                                │  dim_tracks          │
                                │  fact_listening_hist │
                                │  etl_audit           │
                                └──────────────────────┘
```

**Flujo OAuth:**
1. Frontend → `GET /v1/auth/login` → recibe `authorization_url`
2. Redirección a Spotify (el backend genera `code_verifier` y `code_challenge`)
3. Spotify → `GET /v1/auth/callback?code=X&state=Y` → backend crea JWT
4. Frontend en `/callback?token=JWT` guarda en `localStorage["app_token"]` → `/dashboard`

---

## Instalación Local

### Requisitos

- Node.js 22+ y pnpm
- Python 3.10+
- PostgreSQL 14+ (o cuenta en [Neon](https://neon.tech))
- Aplicación registrada en [Spotify Developer Dashboard](https://developer.spotify.com/dashboard)

### 1. Configurar Backend

```bash
cd backend
python -m venv venv
venv\Scripts\activate          # Windows
# source venv/bin/activate     # Linux/Mac
pip install -r requirements.txt
```

Crear `backend/.env`:

```env
DATABASE_URL=postgresql://user:pass@host:5432/dbname
SPOTIFY_CLIENT_ID=...
SPOTIFY_CLIENT_SECRET=...
SPOTIFY_REDIRECT_URI=http://localhost:8000/v1/auth/callback
JWT_SECRET=...           # python -c "import secrets; print(secrets.token_hex(32))"
FRONTEND_URL=http://localhost:3000
ALLOW_HOSTS=http://localhost:3000
```

Ejecutar migraciones e iniciar:

```bash
alembic upgrade head
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 2. Configurar Frontend

```bash
# Desde la raíz del proyecto
pnpm install
```

Crear `frontend/.env.local` (o `.env`):

```env
VITE_API_URL=http://localhost:8000
```

Iniciar:

```bash
pnpm dev   # puerto 3000
```

---

## Flujo de Uso

1. **Login:** Ir a `/login` → "Conectar con Spotify" → autorizar acceso → redirigido a `/dashboard`
2. **ETL:** Ir a `/etl` → "Sincronizar Ahora" → esperar logs (~20-30s la primera vez)
3. **Dashboard:** Ver top artistas/canciones, hora pico, géneros, estadísticas rápidas
4. **Perfil:** Ver datos de la cuenta Spotify (avatar, email, país, seguidores)

---

## Endpoints API (bajo `/v1`)

| Método | Ruta | Auth | Descripción |
|---|---|---|---|
| GET | `/auth/login` | No | URL de autorización OAuth |
| GET | `/auth/callback` | No | Intercambia code por JWT |
| GET | `/artists/top` | JWT | Top 10 artistas del DWH |
| GET | `/tracks/top` | JWT | Top 10 canciones del DWH |
| GET | `/history/peak-hour` | JWT | Hora pico de escucha |
| GET | `/history/peak-hour/distribution` | JWT | Distribución por las 24 horas |
| GET | `/history/genres` | JWT | Top géneros musicales |
| GET | `/history/stats` | JWT | Stats rápidas (conteos, última sync) |
| GET | `/history/recently-played` | JWT | Reproducciones recientes |
| GET | `/profile/me` | JWT | Perfil del usuario (desde DWH) |
| POST | `/etl/run` | JWT | Disparar pipeline ETL completo |
| GET | `/etl/status` | JWT | Estado del DWH + auditoría |
| GET | `/etl/history` | JWT | Historial paginado de ejecuciones |

---

## Seguridad

- **JWT:** HS256, 8h de expiración, almacenado en `localStorage["app_token"]`
- **PKCE:** `code_verifier` y `code_challenge` generados en el backend, PKCESessions en BD
- **CORS:** Controlado con `ALLOW_HOSTS` (sin wildcard)
- **Scopes Spotify:** `user-read-private user-read-email user-top-read user-read-recently-played`

---

## Troubleshooting

**CORS error:** Verificar que `ALLOW_HOSTS` en `.env` coincida exactamente con el origen del frontend.

**"No such table" en el backend:** Ejecutar `alembic upgrade head` y asegurarse que el schema `dwh` exista en PostgreSQL.

**ETL falla:** Revisar logs en `/etl`. El access token de Spotify expira — hacer login nuevamente para obtener uno nuevo.

**JWT expirado:** El token dura 8h. Hacer logout y volver a autenticarse con Spotify.

---

## Estructura del Proyecto

```
mi-spotify-wrapped-dwh/
├── backend/              # FastAPI + SQLAlchemy + Alembic
│   ├── app/
│   │   ├── core/         # config.py, database.py, security.py (legacy)
│   │   ├── models/       # models.py — todos los ORM del schema dwh
│   │   ├── v1/           # Código activo
│   │   │   ├── routers/  # auth, artists, tracks, history, profile, etl
│   │   │   ├── services/ # auth_service, spotify_client, etl_service
│   │   │   └── schemas/  # Pydantic request/response
│   │   ├── routers/      # ⚠️ LEGACY — no montado en main.py
│   │   ├── schemas/      # ⚠️ LEGACY
│   │   ├── services/     # ⚠️ LEGACY
│   │   └── main.py
│   └── migrations/       # Alembic versions
├── frontend/             # React + Vite
│   └── src/
│       ├── pages/        # Login, Callback, Dashboard, Profile, Etl, NotFound
│       ├── components/   # dashboard/, etl/, layout/, ui/
│       ├── lib/          # api.ts, auth.ts, utils.ts
│       ├── hooks/        # useApi, useComposition, useMobile, usePersistFn
│       ├── types/        # artist, track, history, etl, user
│       ├── router/       # ProtectedRoute
│       ├── contexts/     # ThemeContext
│       └── App.tsx, main.tsx
├── server/               # Express — sirve build Vite en producción
├── shared/               # Constantes compartidas (legado Manus)
└── vite.config.ts        # Root Vite: root=frontend/, aliases @/@shared
```
