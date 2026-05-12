# Mi Spotify Wrapped — Personal Data Warehouse

Aplicación full-stack para sincronizar, analizar y visualizar tu historial de Spotify en un Data Warehouse personal.

**Stack:**
- **Frontend:** React 19 + TypeScript + Tailwind CSS 4 + Wouter (routing)
- **Backend:** FastAPI + SQLAlchemy + PostgreSQL
- **Auth:** OAuth 2.0 PKCE + JWT
- **ETL:** Pipeline incremental con Spotify API

---

## Instalación Local

### Requisitos Previos

- Node.js 22+
- Python 3.10+
- PostgreSQL 14+ (o Neon cloud)
- Cuenta de Spotify (gratuita o premium)
- Aplicación registrada en [Spotify Developer Dashboard](https://developer.spotify.com/dashboard)

### 1. Clonar el Repositorio

```bash
git clone <repo-url>
cd mi-spotify-wrapped-dwh
```

### 2. Configurar Backend

#### 2.1 Crear Entorno Virtual

```bash
cd backend
python -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate
```

#### 2.2 Instalar Dependencias

```bash
pip install -r requirements.txt
```

#### 2.3 Configurar Variables de Entorno

Copiar `.env.example` a `.env` y llenar con tus valores:

```bash
cp .env.example .env
```

Editar `.env`:

```env
# PostgreSQL (Neon)
DATABASE_URL=postgresql://user:password@host/dbname?sslmode=require

# Spotify OAuth (obtener de https://developer.spotify.com/dashboard)
SPOTIFY_CLIENT_ID=your_client_id
SPOTIFY_CLIENT_SECRET=your_client_secret
SPOTIFY_REDIRECT_URI=http://localhost:8000/v1/auth/callback

# JWT (generar con: python -c "import secrets; print(secrets.token_urlsafe(32))")
JWT_SECRET=your_secret_key_here

# Frontend
FRONTEND_URL=http://localhost:3000
```

#### 2.4 Crear Base de Datos

Si usas PostgreSQL local:

```bash
createdb dwh
```

Si usas Neon, copiar la URL de conexión a `DATABASE_URL`.

#### 2.5 Ejecutar Migraciones (Alembic)

```bash
cd backend
alembic upgrade head
```

#### 2.6 Iniciar Backend

```bash
cd backend
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Backend disponible en: `http://localhost:8000`

### 3. Configurar Frontend

#### 3.1 Instalar Dependencias

```bash
cd client
npm install
```

#### 3.2 Configurar Variables de Entorno

El frontend usa variables de entorno inyectadas por Manus. Localmente, crear `.env.local`:

```env
VITE_API_URL=http://localhost:8000
```

#### 3.3 Iniciar Frontend

```bash
npm run dev
```

Frontend disponible en: `http://localhost:3000`

---

## Flujo de Uso

### 1. Login con Spotify

1. Abrir `http://localhost:3000/login`
2. Hacer clic en "Conectar con Spotify"
3. Autorizar acceso a tu historial de Spotify
4. Serás redirigido a `/dashboard`

### 2. Ejecutar ETL

1. Ir a `/etl`
2. Hacer clic en "Sincronizar Ahora"
3. Esperar a que se carguen los datos (primero: ~20-30s)
4. Ver logs en tiempo real en el panel terminal

### 3. Explorar Dashboard

1. Ir a `/dashboard`
2. Ver:
   - Top 5 artistas
   - Top 5 canciones
   - Hora pico de escucha
   - Géneros dominantes
   - Estadísticas rápidas (total tracks, artistas, última sync)

### 4. Ver Perfil

1. Ir a `/profile`
2. Ver datos de tu cuenta Spotify (avatar, email, país, seguidores, plan)

---

## Estructura del Proyecto

```
mi-spotify-wrapped-dwh/
├── backend/
│   ├── app/
│   │   ├── core/
│   │   │   ├── config.py          # Configuración (BaseSettings)
│   │   │   ├── database.py        # SQLAlchemy engine
│   │   │   └── security.py        # JWT, PKCE, tokens
│   │   ├── models/
│   │   │   └── models.py          # Tablas SQLAlchemy (dim_*, fact_*, etl_audit, pkce_sessions)
│   │   ├── schemas/
│   │   │   └── schemas.py         # Pydantic models (Request/Response)
│   │   ├── services/
│   │   │   ├── spotify_service.py # Cliente Spotify API
│   │   │   └── etl_service.py     # Pipeline ETL (extract, transform, load)
│   │   ├── routers/
│   │   │   ├── auth.py            # /v1/auth/login, /v1/auth/callback
│   │   │   ├── data.py            # /v1/artists/top, /v1/tracks/top, /v1/history/*, /v1/profile/me
│   │   │   └── etl.py             # /v1/etl/status, /v1/etl/run
│   │   └── main.py                # FastAPI app
│   ├── migrations/                # Alembic migrations
│   ├── requirements.txt
│   ├── .env.example
│   └── alembic.ini
├── client/
│   ├── src/
│   │   ├── pages/
│   │   │   ├── Login.tsx
│   │   │   ├── Callback.tsx
│   │   │   ├── Dashboard.tsx
│   │   │   ├── Profile.tsx
│   │   │   ├── Etl.tsx
│   │   │   └── NotFound.tsx
│   │   ├── components/
│   │   │   ├── layout/
│   │   │   │   ├── Navbar.tsx
│   │   │   │   └── AppLayout.tsx
│   │   │   ├── dashboard/
│   │   │   │   ├── TopArtistsCard.tsx
│   │   │   │   ├── TopTracksCard.tsx
│   │   │   │   ├── PeakHourCard.tsx
│   │   │   │   ├── GenresChart.tsx
│   │   │   │   └── QuickStatsCards.tsx
│   │   │   ├── etl/
│   │   │   │   ├── DwhStatusTable.tsx
│   │   │   │   ├── EtlHistoryTable.tsx
│   │   │   │   └── RunEtlPanel.tsx
│   │   │   └── ui/
│   │   ├── lib/
│   │   │   ├── api.ts             # Cliente API con JWT
│   │   │   ├── auth.ts            # Funciones de autenticación
│   │   │   └── utils.ts
│   │   ├── hooks/
│   │   │   └── useApi.ts          # Hook para llamadas a API
│   │   ├── types/
│   │   │   ├── user.ts
│   │   │   ├── artist.ts
│   │   │   ├── track.ts
│   │   │   ├── history.ts
│   │   │   └── etl.ts
│   │   ├── router/
│   │   │   └── ProtectedRoute.tsx # Rutas protegidas
│   │   ├── App.tsx
│   │   ├── main.tsx
│   │   └── index.css
│   ├── package.json
│   └── tsconfig.json
└── README.md
```

---

## Endpoints API

### Autenticación

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| GET | `/v1/auth/login` | Inicia flujo OAuth PKCE, retorna URL de Spotify |
| POST | `/v1/auth/callback` | Recibe code y state, retorna JWT |

### Datos (Requieren JWT)

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| GET | `/v1/artists/top` | Top 5 artistas del usuario |
| GET | `/v1/tracks/top` | Top 5 canciones del usuario |
| GET | `/v1/history/peak-hour` | Hora pico de escucha |
| GET | `/v1/history/genres` | Top 5 géneros |
| GET | `/v1/history/stats` | Estadísticas rápidas |
| GET | `/v1/profile/me` | Perfil del usuario |

### ETL (Requieren JWT)

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| GET | `/v1/etl/status` | Estado del DWH y historial de ejecuciones |
| POST | `/v1/etl/run` | Ejecuta ETL completo |

---

## Seguridad

### JWT

- **Expiración:** 8 horas
- **Algoritmo:** HS256
- **Almacenamiento:** localStorage (frontend)

### PKCE

- **code_verifier:** Generado en frontend, nunca enviado a Spotify
- **code_challenge:** SHA256(code_verifier) en Base64URL
- **state:** UUID único, verificado en callback

### CORS

- Solo permite requests desde `FRONTEND_URL`
- Wildcard (*) deshabilitado

### Tokens Spotify

- **access_token:** Almacenado en BD (encriptado en producción)
- **refresh_token:** Almacenado en BD, renovado automáticamente antes del ETL

---

## Troubleshooting

### "CORS error" al conectar frontend con backend

**Solución:** Verificar que `FRONTEND_URL` en `.env` del backend coincida con la URL del frontend.

```env
FRONTEND_URL=http://localhost:3000
```

### "Connection refused" a PostgreSQL

**Solución:** Verificar que PostgreSQL está corriendo y `DATABASE_URL` es correcto.

```bash
# Verificar conexión
psql $DATABASE_URL -c "SELECT 1"
```

### "Token expirado" después de 8 horas

**Solución:** El JWT expira automáticamente. El usuario debe hacer login nuevamente.

### ETL falla con "Artista no encontrado"

**Solución:** Ejecutar ETL nuevamente. Puede haber un problema de orden de carga. Verificar logs en `/v1/etl/status`.

---

## Desarrollo

### Agregar Migraciones (Alembic)

```bash
cd backend
alembic revision --autogenerate -m "Descripción del cambio"
alembic upgrade head
```

### Ejecutar Tests

```bash
cd backend
pytest tests/
```

### Lint y Format

```bash
# Frontend
cd client
npm run format

# Backend
cd backend
black app/
flake8 app/
```

---

## Deployment

### Frontend (Manus)

1. Guardar checkpoint en Management UI
2. Hacer clic en "Publish"
3. Configurar dominio personalizado en Settings > Domains

### Backend (Render, Railway, Heroku)

1. Crear aplicación en plataforma
2. Configurar variables de entorno (DATABASE_URL, SPOTIFY_*, JWT_SECRET, etc.)
3. Ejecutar migraciones: `alembic upgrade head`
4. Desplegar

---

## Licencia

Proyecto académico - Universidad de Pamplona 2026-I

**Desarrolladores:** Suley & Jhonatan

**Profesor:** Juan Alejandro Carrillo Jaimes

---

## Contacto

Para preguntas o issues, contactar a los desarrolladores o abrir un issue en GitHub.
