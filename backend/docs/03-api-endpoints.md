# 03 — Endpoints de la API REST

## Base URL

```
http://localhost:8000/v1
```

Documentación interactiva (Swagger UI): `http://localhost:8000/docs`

---

## Autenticación

Todos los endpoints protegidos requieren el header:

```
Authorization: Bearer <JWT>
```

El JWT se obtiene tras completar el flujo OAuth descrito en la sección Auth.

---

## Auth

### `GET /v1/auth/login`

Inicia el flujo OAuth 2.0 PKCE con Spotify. No requiere autenticación.

**Respuesta `200 OK`:**
```json
{
  "authorization_url": "https://accounts.spotify.com/authorize?client_id=...&code_challenge=...&scope=..."
}
```

**Flujo completo:**
1. El frontend llama a este endpoint y obtiene `authorization_url`.
2. Redirige al usuario a esa URL (Spotify consent screen).
3. Spotify redirige al callback del backend con `?code=X&state=Y`.
4. El backend intercambia el code por tokens y redirige al frontend con `?token=JWT`.
5. El frontend guarda el JWT en `localStorage["app_token"]`.

---

### `GET /v1/auth/callback`

Recibe el callback de Spotify. **No invocar manualmente.**

| Query param | Tipo | Descripción |
|---|---|---|
| `code` | string | Authorization code de Spotify |
| `state` | string | State CSRF para validar la sesión PKCE |

**Respuesta:** Redirección `302` a `{FRONTEND_URL}/callback?token=JWT`.

---

## Profile

### `GET /v1/profile/me` 🔒

Retorna el perfil del usuario autenticado desde `dwh.dim_users`.

**Respuesta `200 OK`:**
```json
{
  "spotify_id": "user123",
  "display_name": "Juan Pérez",
  "email": "juan@example.com",
  "country": "CO",
  "followers": 42,
  "product": "premium",
  "image_url": "https://i.scdn.co/image/ab67616d...",
  "user_id": 1,
  "loaded_at": "2026-05-15T12:00:00"
}
```

---

## Artists

### `GET /v1/artists/top` 🔒

Top 10 artistas más escuchados del usuario, ordenados por reproducciones en `fact_listening_history`. Si no hay historial, devuelve los artistas por popularidad.

**Respuesta `200 OK`:**
```json
{
  "artists": [
    {
      "id": "spotify_artist_id",
      "name": "Karol G",
      "popularity": 92,
      "genres": ["reggaeton", "latin pop"],
      "images": [{"url": "https://i.scdn.co/image/..."}],
      "external_urls": {"spotify": "https://open.spotify.com/artist/..."},
      "play_count": 48,
      "rank": 1
    }
  ],
  "total": 10
}
```

---

## Tracks

### `GET /v1/tracks/top` 🔒

Top 10 canciones más escuchadas, ordenadas por reproducciones. Si no hay historial, devuelve por popularidad.

**Respuesta `200 OK`:**
```json
{
  "tracks": [
    {
      "id": "spotify_track_id",
      "name": "BICHOTA",
      "artist_name": "Karol G",
      "album_name": "KG0516",
      "duration_ms": 210000,
      "popularity": 85,
      "preview_url": null,
      "external_urls": {"spotify": "https://open.spotify.com/track/..."},
      "album_image": "https://i.scdn.co/image/...",
      "play_count": 30,
      "rank": 1
    }
  ],
  "total": 10
}
```

---

## History

### `GET /v1/history/recently-played` 🔒

Últimas N reproducciones del usuario desde `fact_listening_history`.

| Query param | Tipo | Default | Descripción |
|---|---|---|---|
| `limit` | integer | 50 | Máximo de registros |

**Respuesta `200 OK`:**
```json
{
  "items": [
    {
      "id": 1,
      "user_id": 1,
      "track_id": 12,
      "artist_id": 5,
      "played_at": "2026-05-15T21:30:00",
      "hour_of_day": 21,
      "day_of_week": "Thursday",
      "context_type": "playlist"
    }
  ],
  "total": 50
}
```

---

### `GET /v1/history/stats` 🔒

Estadísticas rápidas del historial del usuario.

**Respuesta `200 OK`:**
```json
{
  "total_tracks": 120,
  "total_artists": 45,
  "total_plays": 850,
  "total_minutes": 3120.5,
  "last_sync": "2026-05-15T10:30:00+00:00",
  "etl_status": "success",
  "top_track": "BICHOTA",
  "top_track_artist": "Karol G",
  "top_track_plays": 30
}
```

---

### `GET /v1/history/genres` 🔒

Top 10 géneros musicales del usuario con conteo y porcentaje.

**Respuesta `200 OK`:**
```json
{
  "genres": [
    {"genre": "reggaeton", "count": 320, "percentage": 38.2},
    {"genre": "latin pop", "count": 180, "percentage": 21.5}
  ],
  "total_plays": 850
}
```

---

### `GET /v1/history/peak-hour` 🔒

Hora del día con mayor número de reproducciones.

**Respuesta `200 OK`:**
```json
{"hour": 21, "play_count": 95, "label": "21:00 - 22:00"}
```

---

### `GET /v1/history/peak-hour/distribution` 🔒

Distribución de reproducciones por cada una de las 24 horas.

**Respuesta `200 OK`:**
```json
{
  "hours": [
    {"hour": 0, "play_count": 5, "label": "00:00"},
    {"hour": 1, "play_count": 2, "label": "01:00"},
    ...
    {"hour": 23, "play_count": 12, "label": "23:00"}
  ]
}
```

---

## ETL

### `POST /v1/etl/run` 🔒

Ejecuta el pipeline ETL completo. Devuelve el log de la ejecución.

**Respuesta `200 OK` (éxito):**
```json
{
  "status": "success",
  "message": "ETL completado exitosamente",
  "logs": [
    "Extrayendo datos de Spotify...",
    "Extraido: 50 artistas, 50 canciones, 48 historial",
    "Transformando datos...",
    "Cargando datos en DWH...",
    "Cargado: 12 artistas nuevos, 8 canciones nuevas, 48 historial nuevo"
  ]
}
```

**Respuesta `200 OK` (error):**
```json
{
  "status": "error",
  "message": "401 Client Error: Unauthorized",
  "logs": ["Extrayendo datos de Spotify...", "Error: 401 Client Error: Unauthorized"]
}
```

---

### `GET /v1/etl/status` 🔒

Estado del DWH (conteos por tabla) y últimas 5 ejecuciones ETL.

**Respuesta `200 OK`:**
```json
{
  "tables": [
    {"table_name": "dim_artists", "record_count": 87, "status": "loaded"},
    {"table_name": "dim_tracks", "record_count": 124, "status": "loaded"},
    {"table_name": "fact_listening_history", "record_count": 850, "status": "loaded"}
  ],
  "recent_runs": [
    {
      "id": 5,
      "started_at": "2026-05-15T10:30:00+00:00",
      "duration_seconds": 8,
      "records_extracted": 68,
      "records_loaded": 68,
      "status": "success",
      "error_message": null
    }
  ]
}
```

---

### `GET /v1/etl/history` 🔒

Historial paginado de ejecuciones ETL.

| Query param | Tipo | Default | Descripción |
|---|---|---|---|
| `limit` | integer | 20 | Registros por página (1-100) |
| `offset` | integer | 0 | Registro de inicio |
| `status` | string | — | Filtro: `success`, `error`, `running` |

**Respuesta `200 OK`:**
```json
{
  "runs": [...],
  "total": 12,
  "limit": 20,
  "offset": 0,
  "has_more": false
}
```

---

## Códigos de Error

| Código | Significado |
|---|---|
| `401` | Token JWT inválido, expirado o ausente |
| `400` | State PKCE inválido en el callback |
| `403` | Header Authorization ausente |
| `500` | Error interno del servidor |
