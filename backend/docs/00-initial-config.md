# 00 — Configuración Inicial del Proyecto

## Descripción General

**Mi Spotify Wrapped DWH** es un Data Warehouse personal que sincroniza el historial de escucha de Spotify y expone analíticas mediante una API REST. Proyecto académico Universidad de Pamplona — 2026-I.

| Componente | Tecnología |
|---|---|
| Backend | FastAPI 0.110 + SQLAlchemy 2.0 |
| Base de datos | PostgreSQL (Neon serverless) |
| Migraciones | Alembic |
| Frontend | React 19 + TypeScript + Vite |
| Autenticación | OAuth 2.0 PKCE (Spotify) + JWT HS256 |

---

## Requisitos Previos

- Python 3.11+
- Node.js 20+ / pnpm 9+
- Cuenta de Spotify y aplicación registrada en [Spotify Developer Dashboard](https://developer.spotify.com/dashboard)
- Base de datos PostgreSQL (local o Neon)

---

## 1. Clonar el Repositorio

```bash
git clone <url-del-repositorio>
cd mi-spotify-wrapped-dwh
```

---

## 2. Configuración del Backend

### 2.1 Crear entorno virtual

```bash
cd backend
python -m venv venv

# Windows
venv\Scripts\activate

# Linux / macOS
source venv/bin/activate
```

### 2.2 Instalar dependencias

```bash
pip install -r requirements.txt
```

### 2.3 Variables de entorno

Crear el archivo `backend/.env` basándose en `.env.example`:

```env
DATABASE_URL=postgresql://usuario:contraseña@host:5432/nombre_db
SPOTIFY_CLIENT_ID=<id_de_la_app_spotify>
SPOTIFY_CLIENT_SECRET=<secreto_de_la_app_spotify>
SPOTIFY_REDIRECT_URI=http://localhost:8000/v1/auth/callback
JWT_SECRET=<cadena_aleatoria_minimo_32_chars>
FRONTEND_URL=http://localhost:3000
ALLOW_HOSTS=http://localhost:3000,http://127.0.0.1:3000
LOG_LEVEL=INFO
```

Generar `JWT_SECRET`:

```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

### 2.4 Configurar Spotify Developer App

En el Spotify Developer Dashboard:
- **Redirect URIs**: agregar `http://localhost:8000/v1/auth/callback`
- **Scopes requeridos**: `user-read-private user-read-email user-top-read user-read-recently-played`

### 2.5 Crear el schema en PostgreSQL

```sql
CREATE SCHEMA IF NOT EXISTS dwh;
```

### 2.6 Ejecutar migraciones

```bash
alembic upgrade head
```

### 2.7 Iniciar el servidor

```bash
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

La documentación interactiva queda disponible en `http://localhost:8000/docs`.

---

## 3. Configuración del Frontend

### 3.1 Instalar dependencias

```bash
# Desde la raíz del proyecto
pnpm install
```

### 3.2 Variables de entorno

Crear `frontend/.env.local`:

```env
VITE_API_URL=http://127.0.0.1:8000
VITE_API_BASE_URL=http://127.0.0.1:8000
```

### 3.3 Iniciar el servidor de desarrollo

```bash
pnpm dev
```

La aplicación queda disponible en `http://localhost:3000`.

---

## 4. Verificar la Instalación

```bash
# Salud del backend
curl http://localhost:8000/health

# Respuesta esperada
{"status": "healthy"}
```

---

## 5. Ejecutar Tests

```bash
cd backend
python -m pytest tests/ -v
```
