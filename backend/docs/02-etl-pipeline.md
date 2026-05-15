# 02 — Pipeline ETL

## Descripción General

El pipeline ETL (Extract → Transform → Load) sincroniza los datos de la cuenta de Spotify del usuario hacia el Data Warehouse. Se ejecuta bajo demanda mediante `POST /v1/etl/run` y soporta sincronización incremental gracias al cursor de paginación de Spotify.

```
Spotify API
    │
    │  GET /me
    │  GET /me/top/artists
    │  GET /me/top/tracks
    │  GET /me/player/recently-played?after=<cursor>
    │
    ▼
┌─────────────┐     ┌───────────────┐     ┌──────────────┐
│   EXTRACT   │────▶│   TRANSFORM   │────▶│     LOAD     │
│ (API calls) │     │ (normalizar)  │     │  (upsert DB) │
└─────────────┘     └───────────────┘     └──────────────┘
                                                │
                                          etl_audit (log)
```

---

## Fase 1 — Extract

Implementada en `EtlService` (métodos `extract_*`). Llama a la Spotify Web API usando el `access_token` almacenado en `dim_users`.

| Método | Endpoint Spotify | Datos obtenidos |
|---|---|---|
| `extract_user` | `GET /me` | Perfil del usuario |
| `extract_top_artists` | `GET /me/top/artists?limit=50` | Top 50 artistas |
| `extract_top_tracks` | `GET /me/top/tracks?limit=50` | Top 50 canciones |
| `extract_recently_played` | `GET /me/player/recently-played?limit=50&after=<cursor>` | Historial reciente |

### Sincronización Incremental

Para evitar reprocesar historial antiguo, el ETL usa el cursor de Spotify:

1. Consulta el último `EtlAudit` con `status = "success"` del usuario.
2. Usa su campo `cursor_next_ms` como parámetro `after` en `recently_played`.
3. Al finalizar exitosamente, guarda el nuevo cursor en `etl_audit.cursor_next_ms`.

En el **primer ETL** no hay cursor previo, por lo que se traen las últimas 50 reproducciones.

---

## Fase 2 — Transform

Implementada en `EtlService` (métodos `transform_*`). Normaliza los datos crudos de la API al esquema del DWH. No hace I/O; es lógica pura.

### `transform_user`

```
user_data["id"]               → spotify_id
user_data["display_name"]     → display_name
user_data["email"]            → email
user_data["country"]          → country
user_data["followers"]["total"] → followers
user_data["product"]          → product
user_data["images"][0]["url"] → image_url
```

### `transform_artists`

Por cada artista:
```
artist["id"]                         → spotify_id
artist["name"]                       → name
artist["popularity"]                 → popularity
artist["followers"]["total"]         → followers_count
artist["genres"]                     → genres (ARRAY)
artist["images"][0]["url"]           → image_url (primera imagen = mayor resolución)
```

### `transform_tracks`

Por cada canción:
```
track["id"]                          → spotify_id
track["name"]                        → name
track["artists"][0]["id"]            → spotify_artist_id
track["artists"][0]["name"]          → artist_name
track["album"]["name"]               → album_name
track["album"]["images"][0]["url"]   → album_image_url
track["duration_ms"]                 → duration_ms
track["popularity"]                  → popularity
track["explicit"]                    → explicit
```

### `transform_history`

Por cada item de reproducción:
```
item["track"]["id"]                  → spotify_track_id
item["track"]["artists"][0]["id"]    → spotify_artist_id
item["played_at"]  (ISO 8601 UTC)    → played_at (datetime)
played_at.hour                       → hour_of_day (0-23)
played_at.strftime("%A")             → day_of_week ("Monday"…"Sunday")
item["context"]["type"]              → context_type ("playlist", "album", etc.)
```

---

## Fase 3 — Load

Implementada en `EtlService` (métodos `load_*`). Realiza upserts en el DWH dentro de una transacción SQLAlchemy.

### `load_user`

- Si el `spotify_id` ya existe: actualiza todos los campos y el `access_token`.
- Si no existe: inserta un nuevo `DimUsers`.

### `load_artists`

Por cada artista:
- Si no existe: `INSERT` en `dim_artists`.
- Si ya existe: actualiza `genres`, `popularity`, `followers_count` e `image_url`.

### `load_tracks`

Por cada canción:
- Si no existe: busca el artista en `dim_artists`. Si tampoco existe, crea un `DimArtists` mínimo con `db.flush()`. Luego inserta el `DimTracks`.
- Si ya existe: repara `artist_id` si era `NULL`.

### `load_history`

Por cada reproducción:
1. Busca el `DimTracks` por `spotify_track_id`. Si no existe, omite el registro.
2. Verifica duplicado por `(user_id, track_id, played_at)`. Si ya existe, omite.
3. Si es nuevo: inserta `FactListeningHistory`.

---

## Auditoría

Cada ejecución de `POST /v1/etl/run` crea un `EtlAudit`:

1. Al inicio: `status = "running"`.
2. Al finalizar con éxito: `status = "success"` + contadores + cursor.
3. Si hay error: `status = "error"` + `error_message`.

Los últimos 5 audits son visibles en `GET /v1/etl/status`. El historial completo paginado en `GET /v1/etl/history`.

---

## Diagrama de Secuencia (ETL Run)

```
Frontend          Backend (etl.py)       EtlService        Spotify API       PostgreSQL
   │                     │                    │                  │                │
   │  POST /etl/run      │                    │                  │                │
   │────────────────────▶│                    │                  │                │
   │                     │ INSERT etl_audit   │                  │                │
   │                     │ (status=running)   │                  │                │
   │                     │────────────────────────────────────────────────────────▶│
   │                     │                    │  GET /me         │                │
   │                     │                    │─────────────────▶│                │
   │                     │                    │◀─────────────────│                │
   │                     │                    │  GET /me/top/... │                │
   │                     │                    │─────────────────▶│                │
   │                     │                    │◀─────────────────│                │
   │                     │                    │  transform_*()   │                │
   │                     │                    │──(puro)──────────│                │
   │                     │                    │  load_*()        │                │
   │                     │                    │──────────────────────────────────▶│
   │                     │ UPDATE etl_audit   │                  │                │
   │                     │ (status=success)   │                  │                │
   │                     │────────────────────────────────────────────────────────▶│
   │  200 {status, logs} │                    │                  │                │
   │◀────────────────────│                    │                  │                │
```
