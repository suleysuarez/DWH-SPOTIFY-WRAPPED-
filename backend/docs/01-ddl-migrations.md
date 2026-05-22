# 01 — Diseño de la Base de Datos (Star Schema)

## Arquitectura General

El DWH utiliza un **star schema** en PostgreSQL bajo el schema `dwh`. La tabla de hechos central es `fact_listening_history`, rodeada de tres dimensiones: `dim_users`, `dim_artists` y `dim_tracks`. La tabla `etl_audit` registra cada ejecución del pipeline ETL.

```
                    ┌──────────────┐
                    │  dim_users   │
                    │  (user_id)   │
                    └──────┬───────┘
                           │
         ┌─────────────────▼──────────────────┐
         │        fact_listening_history        │
         │  user_id  │  track_id  │  artist_id │
         └────────┬──┴──────┬─────┴────────────┘
                  │         │
        ┌─────────▼──┐  ┌───▼──────────┐
        │ dim_artists │  │  dim_tracks  │
        │ (artist_id) │  │  (track_id)  │
        └─────────────┘  └──────────────┘
```

---

## Tablas del Schema `dwh`

### `dim_users`

Almacena el perfil y los tokens OAuth de cada usuario autenticado.

| Columna | Tipo | Descripción |
|---|---|---|
| `user_id` | SERIAL PK | Clave primaria interna |
| `spotify_id` | VARCHAR(100) UNIQUE | ID de Spotify (clave de negocio) |
| `display_name` | VARCHAR(255) | Nombre de usuario en Spotify |
| `email` | VARCHAR(255) | Email asociado |
| `country` | VARCHAR(10) | Código de país ISO 3166-1 alpha-2 |
| `followers` | INTEGER | Seguidores en Spotify |
| `product` | VARCHAR(20) | Plan: `free`, `premium`, `open` |
| `image_url` | TEXT | URL de la foto de perfil |
| `spotify_access_token` | TEXT | Token de acceso vigente |
| `spotify_refresh_token` | TEXT | Token para renovar el acceso |
| `token_expires_at` | TIMESTAMP | Expiración del access token |
| `loaded_at` | TIMESTAMP | Fecha/hora de última sincronización |

### `dim_artists`

Artistas más escuchados del usuario, poblados desde `/me/top/artists`.

| Columna | Tipo | Descripción |
|---|---|---|
| `artist_id` | SERIAL PK | Clave primaria interna |
| `spotify_id` | VARCHAR(100) UNIQUE | ID de artista en Spotify |
| `name` | VARCHAR(255) | Nombre del artista |
| `popularity` | INTEGER | Popularidad 0–100 |
| `followers_count` | INTEGER | Seguidores totales |
| `genres` | ARRAY(TEXT) | Géneros musicales asociados |
| `image_url` | TEXT | URL de foto del artista |
| `loaded_at` | TIMESTAMP | Fecha de carga |

> **Nota:** `genres` es un `ARRAY(String)` de PostgreSQL. SQLAlchemy requiere llamar `flag_modified(obj, "genres")` tras mutar la lista para detectar el cambio.

### `dim_tracks`

Canciones más escuchadas del usuario, pobladas desde `/me/top/tracks`.

| Columna | Tipo | Descripción |
|---|---|---|
| `track_id` | SERIAL PK | Clave primaria interna |
| `spotify_id` | VARCHAR(100) UNIQUE | ID de canción en Spotify |
| `name` | VARCHAR(255) | Nombre de la canción |
| `artist_id` | INTEGER FK | Referencia a `dim_artists.artist_id` |
| `album_name` | VARCHAR(255) | Nombre del álbum |
| `album_image_url` | TEXT | URL de portada del álbum |
| `duration_ms` | INTEGER | Duración en milisegundos |
| `popularity` | INTEGER | Popularidad 0–100 |
| `explicit` | BOOLEAN | Contenido explícito |
| `loaded_at` | TIMESTAMP | Fecha de carga |

### `fact_listening_history`

Tabla de hechos. Cada fila es una reproducción de una canción por un usuario.

| Columna | Tipo | Descripción |
|---|---|---|
| `id` | SERIAL PK | Clave primaria interna |
| `user_id` | INTEGER FK | Referencia a `dim_users.user_id` |
| `track_id` | INTEGER FK | Referencia a `dim_tracks.track_id` |
| `artist_id` | INTEGER FK | Referencia a `dim_artists.artist_id` |
| `played_at` | TIMESTAMP | Momento de la reproducción (UTC) |
| `hour_of_day` | INTEGER | Hora del día (0–23) |
| `day_of_week` | VARCHAR(10) | Día de la semana (Monday…Sunday) |
| `context_type` | VARCHAR(50) | Contexto: playlist, album, artist, unknown |

**Deduplicación:** antes de insertar se verifica que no exista `(user_id, track_id, played_at)`. No hay constraint UNIQUE en DB para esta combinación.

### `etl_audit`

Registra cada ejecución del pipeline ETL.

| Columna | Tipo | Descripción |
|---|---|---|
| `audit_id` | SERIAL PK | Clave primaria interna |
| `spotify_user_id` | VARCHAR(100) | spotify_id del usuario |
| `started_at` | TIMESTAMP | Inicio de la ejecución |
| `finished_at` | TIMESTAMP | Fin de la ejecución |
| `duration_ms` | INTEGER | Duración total en ms |
| `status` | VARCHAR(20) | `running`, `success`, `error` |
| `error_message` | TEXT | Detalle del error si aplica |
| `artists_new` | INTEGER | Artistas insertados |
| `tracks_new` | INTEGER | Canciones insertadas |
| `history_new` | INTEGER | Registros de historial insertados |
| `cursor_next_ms` | VARCHAR(50) | Cursor de Spotify para sincronización incremental |

---

## Schema Público (`public`)

### `pkce_sessions`

Sesiones PKCE temporales para el flujo OAuth. Se eliminan tras el callback exitoso.

| Columna | Tipo | Descripción |
|---|---|---|
| `state` | VARCHAR(128) PK | State CSRF generado al iniciar login |
| `verifier` | TEXT | Code verifier PKCE |
| `created_at` | TIMESTAMP | Momento de creación |

---

## Migraciones con Alembic

Las migraciones se almacenan en `backend/migrations/versions/`.

```bash
# Aplicar todas las migraciones pendientes
alembic upgrade head

# Crear nueva migración automática
alembic revision --autogenerate -m "descripcion del cambio"

# Revertir la última migración
alembic downgrade -1

# Ver historial
alembic history
```

**Migraciones aplicadas:**

| Revisión | Descripción |
|---|---|
| `001` | Creación inicial del star schema en `dwh` |
| `002` | Agrega columna `image_url` a `dim_users` |
