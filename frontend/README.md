# Frontend — React 19 + TypeScript + Vite

**Autoras/es:** Suley Suárez y Jhonatan Vera — Universidad de Pamplona 2026-I

Interfaz de usuario del Data Warehouse personal de Spotify. Diseño Glassmorphism Premium Dark (#121212 fondo, #1DB954 acento verde Spotify).

---

## Estructura

```
frontend/src/
├── App.tsx                     # Rutas Wouter + ThemeProvider + ErrorBoundary
├── main.tsx                    # Punto de entrada React
├── index.css                   # Estilos globales (glass-card, skeleton-shimmer, etc.)
├── const.ts                    # Re-exportaciones de shared/const (legado Manus)
│
├── pages/
│   ├── Login.tsx               # Pantalla de login — redirige a /v1/auth/login
│   ├── Callback.tsx            # Procesa JWT de ?token= y guarda en localStorage
│   ├── Dashboard.tsx           # 5 llamadas paralelas, layout 3 columnas
│   ├── Profile.tsx             # Perfil de usuario (datos del DWH)
│   ├── Etl.tsx                 # Panel ETL: RunEtlPanel + DwhStatusTable + EtlHistoryTable
│   ├── NotFound.tsx            # 404
│   └── Home.tsx                # ⚠️ LEGACY — no registrada en App.tsx (scaffold Manus)
│
├── components/
│   ├── layout/
│   │   ├── AppLayout.tsx       # Shell: Navbar sticky + <main> container
│   │   └── Navbar.tsx          # Barra de navegación con indicador de ruta activa
│   ├── dashboard/
│   │   ├── QuickStatsCards.tsx # 5 KPIs: tracks, artistas, géneros, última sync, estado ETL
│   │   ├── TopArtistsCard.tsx  # Top 10 artistas con ranking y play_count
│   │   ├── TopTracksCard.tsx   # Top 10 canciones con duración y álbum
│   │   ├── PeakHourCard.tsx    # AreaChart Recharts + fetch propio de distribución 24h
│   │   └── GenresChart.tsx     # BarChart horizontal top 5 géneros
│   ├── etl/
│   │   ├── RunEtlPanel.tsx     # Terminal de logs con animación + botón Sincronizar
│   │   ├── DwhStatusTable.tsx  # Estado de tablas del DWH (record_count, last_sync)
│   │   └── EtlHistoryTable.tsx # Historial paginado (5 iniciales, +10 por página)
│   └── ui/
│       ├── EmptyState.tsx      # ← custom: DWH vacío con link a /etl
│       ├── ErrorState.tsx      # ← custom: error API con botón Reintentar
│       ├── SkeletonCard.tsx    # ← custom: Skeleton, SkeletonCard, SkeletonList
│       └── [~50 archivos]      # shadcn/ui generados (button, card, tooltip, etc.)
│
├── lib/
│   ├── api.ts                  # Cliente HTTP: Bearer token, 401→logout, endpoints tipados
│   ├── auth.ts                 # JWT en localStorage["app_token"]: save/get/remove/validate
│   └── utils.ts                # cn() = clsx + tailwind-merge
│
├── hooks/
│   ├── useApi.ts               # Hook genérico: loading/error/data/refetch
│   ├── useComposition.ts       # IME input handler (sin uso actual)
│   ├── useMobile.tsx           # Detecta viewport < 768px con MediaQueryList
│   └── usePersistFn.ts         # Referencia estable a función (alternativa a useCallback)
│
├── types/
│   ├── artist.ts               # Artist, TopArtistsResponse
│   ├── track.ts                # Track, TopTracksResponse, formatDuration()
│   ├── history.ts              # PeakHour, GenreData, GenresResponse, QuickStats
│   ├── etl.ts                  # DwhTable, EtlRun, EtlStatusResponse, EtlRunResponse, EtlLogLine
│   └── user.ts                 # SpotifyUser, UserProfile
│
├── router/
│   └── ProtectedRoute.tsx      # Verifica isTokenValid() — redirige a /login si falló
│
└── contexts/
    └── ThemeContext.tsx         # ThemeProvider (fijado a "dark" en App.tsx)
```

---

## Rutas

| Ruta | Componente | Auth |
|---|---|---|
| `/login` | Login | No |
| `/callback` | Callback | No |
| `/dashboard` | Dashboard | JWT |
| `/profile` | Profile | JWT |
| `/etl` | Etl | JWT |
| `/` | → `/dashboard` | — |

---

## Variables de Entorno

Crear `frontend/.env.local` (o `.env` en raíz del monorepo):

```env
VITE_API_URL=http://localhost:8000
```

> **Nota:** `PeakHourCard.tsx` y `EtlHistoryTable.tsx` usan `VITE_API_BASE_URL` en su fetch directo — si ambas variables difieren, configurar ambas o unificar.

---

## Comandos

```bash
# Desde raíz del monorepo
pnpm install
pnpm dev          # Vite HMR en puerto 3000
pnpm check        # TypeScript type-check
pnpm build        # Build → dist/public/
```

---

## Notas de Diseño

- **Glassmorphism:** Los componentes usan `style={{...}}` inline extensamente para el diseño dark (pre-existente, no un error de lint).
- **shadcn/ui:** Los ~50 archivos en `components/ui/` son templates generados por la CLI de shadcn — no editar manualmente.
- **Recharts:** Usado en PeakHourCard (AreaChart) y GenresChart (BarChart).
- **Wouter:** Router ligero (no React Router). `useLocation()` retorna la ruta actual.
