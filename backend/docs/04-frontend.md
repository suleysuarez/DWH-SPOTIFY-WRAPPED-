# 04 — Frontend (React + TypeScript)

## Stack Tecnológico

| Herramienta | Versión | Rol |
|---|---|---|
| React | 19 | UI library |
| TypeScript | 5 | Tipado estático |
| Vite | 5 | Bundler y dev server |
| Tailwind CSS | 4 | Estilos utilitarios |
| shadcn/ui | — | Componentes UI base |
| Wouter | 3 | Enrutamiento cliente |

**Puerto de desarrollo:** `http://localhost:3000`

---

## Arquitectura de Carpetas

```
frontend/src/
├── App.tsx                    # Rutas principales (Wouter)
├── main.tsx                   # Entry point React
├── lib/
│   ├── api.ts                 # Fetch wrapper con inyección de JWT
│   └── auth.ts                # Gestión del token en localStorage
├── hooks/
│   └── useApi.ts              # Hook genérico de fetching
├── router/
│   └── ProtectedRoute.tsx     # Guard de rutas protegidas
├── pages/
│   ├── Login.tsx              # Página de inicio de sesión
│   ├── Callback.tsx           # Recibe JWT de la redirección OAuth
│   ├── Dashboard.tsx          # Panel principal de analíticas
│   ├── Profile.tsx            # Perfil del usuario
│   ├── Etl.tsx                # Panel de control del ETL
│   └── NotFound.tsx           # 404
├── components/
│   ├── layout/
│   │   └── Navbar.tsx         # Barra de navegación lateral
│   ├── dashboard/
│   │   ├── QuickStatsCards.tsx
│   │   ├── TopArtistsCard.tsx
│   │   ├── TopTracksCard.tsx
│   │   ├── GenresChart.tsx
│   │   └── PeakHourCard.tsx
│   ├── etl/
│   │   ├── RunEtlPanel.tsx
│   │   ├── DwhStatusTable.tsx
│   │   └── EtlHistoryTable.tsx
│   └── ui/
│       ├── SkeletonCard.tsx   # Placeholder de carga
│       ├── EmptyState.tsx     # Estado sin datos
│       └── ErrorState.tsx     # Estado de error
└── types/
    ├── user.ts
    ├── artist.ts
    └── track.ts
```

---

## Flujo de Autenticación

```
1. Usuario visita /login
        │
        ▼
2. Login.tsx → GET /v1/auth/login → { authorization_url }
        │
        ▼
3. window.location.href = authorization_url  (Spotify)
        │
        ▼
4. Usuario aprueba en Spotify
        │
        ▼
5. Spotify → GET /v1/auth/callback?code=X&state=Y  (backend)
        │
        ▼
6. Backend intercambia code → JWT → redirect /callback?token=JWT
        │
        ▼
7. Callback.tsx → localStorage["app_token"] = JWT → navigate("/dashboard")
        │
        ▼
8. ProtectedRoute verifica isTokenValid() en cada ruta protegida
```

### Gestión del Token

- **Storage:** `localStorage["app_token"]`
- **Inyección:** `lib/api.ts` agrega `Authorization: Bearer <token>` a cada request
- **Validación:** `lib/auth.ts → isTokenValid()` decodifica el payload JWT client-side y verifica `exp`
- **Logout:** `localStorage.removeItem("app_token")` + redirect a `/login`
- **Auto-logout:** si cualquier request retorna `401`, se borra el token y se redirige al login

---

## Rutas

| Ruta | Componente | Protegida |
|---|---|---|
| `/login` | `Login.tsx` | No |
| `/callback` | `Callback.tsx` | No |
| `/dashboard` | `Dashboard.tsx` | Sí |
| `/profile` | `Profile.tsx` | Sí |
| `/etl` | `Etl.tsx` | Sí |
| `*` | `NotFound.tsx` | No |

---

## Variables de Entorno

| Variable | Descripción |
|---|---|
| `VITE_API_URL` | URL base del backend (usada por `lib/api.ts`) |
| `VITE_API_BASE_URL` | URL base alternativa (usada por `PeakHourCard.tsx`) |

---

## Componentes del Dashboard

### `QuickStatsCards`

Muestra 4 tarjetas de estadísticas rápidas obtenidas de `GET /v1/history/stats`:
- Total de canciones únicas
- Total de artistas únicos
- Total de reproducciones
- Total de minutos escuchados

### `TopArtistsCard`

Top 5 artistas con foto, nombre, géneros y reproducciones. Datos de `GET /v1/artists/top`.

### `TopTracksCard`

Top 5 canciones con portada del álbum, nombre, artista y reproducciones. Datos de `GET /v1/tracks/top`.

### `GenresChart`

Gráfico de barras con los top 10 géneros. Datos de `GET /v1/history/genres`.

### `PeakHourCard`

Muestra la hora pico de escucha y la distribución por hora. Datos de:
- `GET /v1/history/peak-hour`
- `GET /v1/history/peak-hour/distribution`

---

## Estados de UI

Todos los componentes siguen el patrón:

```
Loading → SkeletonCard (placeholder animado)
Empty   → EmptyState ("No hay datos. Ejecuta el ETL.")
Error   → ErrorState (mensaje de error + botón reintentar)
Data    → Contenido real
```

---

## Design System

- **Fondo:** `#121212` (negro Spotify)
- **Acento:** `#1DB954` (verde Spotify)
- **Tipografía:** DM Sans (Google Fonts — aproximación gratuita de Spotify Circular)
- **Estilo:** Glassmorphism con `backdrop-filter: blur` y `background: rgba(255,255,255,0.05)`
- **Componentes base:** shadcn/ui con tema dark personalizado

---

## Comandos

```bash
# Instalar dependencias
pnpm install

# Servidor de desarrollo
pnpm dev

# Verificación de tipos
pnpm check

# Build de producción
pnpm build
```
