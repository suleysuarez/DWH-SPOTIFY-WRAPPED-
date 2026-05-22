# Reflexión sobre el Diseño del DWH

**Proyecto:** Mi Spotify Wrapped DWH  
**Universidad de Pamplona · Bases de Datos II · 2026-I**  
**Integrantes:** Suley Suárez · Jhonatan Vera

---

## Pregunta 1 — ¿Por qué star schema y no snowflake?

Elegimos **star schema** porque la naturaleza del problema no justifica la normalización adicional que introduce el snowflake.

En un snowflake schema, las dimensiones se descomponen en subdimensiones normalizadas. Por ejemplo, `dim_artists` tendría una tabla separada `dim_genres` enlazada por clave foránea, y `dim_tracks` tendría una tabla `dim_albums` separada. Eso agrega JOINs a cada consulta analítica sin que el volumen de datos lo requiera.

**Razones concretas para elegir star schema en este proyecto:**

| Criterio | Star Schema | Snowflake |
|---|---|---|
| Volumen de datos | Cientos de filas por tabla | Millones+ de filas |
| Complejidad de queries | JOINs simples (3 dimensiones) | JOINs en cascada |
| Rendimiento de lectura | Óptimo — una sola pasada por dimensión | Más lento — múltiples JOINs |
| Mantenimiento | Simple — una tabla por entidad | Mayor superficie de cambio |
| Casos de uso OLAP | Agregaciones directas sobre fact | Requiere navegación jerárquica |

El DWH de este proyecto tiene en su estado actual ~266 artistas, ~596 canciones y ~628 reproducciones. A esta escala, la desnormalización del star schema no genera redundancia significativa en disco, pero sí simplifica enormemente las consultas analíticas del EDA (como el `UNNEST` de géneros o los JOINs en el notebook).

Si el proyecto escalara a millones de usuarios con miles de géneros distintos y álbumes reutilizados entre artistas, tendría sentido migrar a snowflake para evitar la anomalía de actualización de géneros duplicados. Por ahora, el star schema es la elección correcta.

---

## Pregunta 2 — ¿Por qué `genres` como `TEXT[]` y no una tabla normalizada?

El campo `genres` en `dim_artists` se almacena como un **array de PostgreSQL (`ARRAY(TEXT)`)** en lugar de una tabla `dim_genres` separada con una tabla de relación `artist_genre`.

**El trade-off que evaluamos:**

**Opción A — Tabla normalizada (snowflake):**
```sql
dim_genres        (genre_id, name)
artist_genre      (artist_id, genre_id)   -- tabla puente M:N
```
- Consulta de géneros requiere 2 JOINs adicionales
- Permite queries como "todos los artistas del género X" con índice
- Correcto desde perspectiva de 3FN

**Opción B — `TEXT[]` en `dim_artists` (elegida):**
```sql
dim_artists.genres   TEXT[]   -- ej: ['reggaeton', 'latin pop', 'trap latino']
```
- Un `CROSS JOIN UNNEST(a.genres)` es suficiente para todas las consultas analíticas
- Los géneros en Spotify/Last.fm son etiquetas de texto libre, no entidades con identidad propia (no tienen ID, no tienen atributos adicionales)
- Evita una tabla puente para datos que solo se leen, nunca se actualizan individualmente
- PostgreSQL tiene soporte nativo para arrays con índices GIN que aceleran búsquedas de contenido

**Decisión:** Los géneros son atributos descriptivos del artista, no entidades independientes con ciclo de vida propio. No existe un catálogo oficial de géneros de Spotify — son cadenas de texto que Last.fm asigna libremente. Normalizar algo que no tiene identidad estable genera complejidad sin beneficio real. El `TEXT[]` con `UNNEST` en SQL cubre el 100% de los casos de uso analíticos del proyecto.

> **Nota técnica:** SQLAlchemy requiere llamar `flag_modified(artist, "genres")` después de mutar la lista en Python para que el ORM detecte el cambio. Esto se debe a que SQLAlchemy no detecta mutaciones in-place de listas Python mapeadas a columnas de tipo array.

---

## Pregunta 3 — ¿Por qué `played_at` solo no puede ser la clave primaria de `fact_listening_history`?

La tabla `fact_listening_history` tiene como clave primaria un `SERIAL id` autoincremental. La pregunta natural es: ¿por qué no usar `played_at` directamente como PK, si cada reproducción ocurre en un instante único?

**El problema: colisiones temporales reales**

Spotify registra `played_at` con precisión de milisegundos, pero **dos usuarios distintos pueden escuchar canciones exactamente al mismo timestamp**. Incluso para un mismo usuario, la API de Spotify puede devolver registros con `played_at` idéntico en casos donde el cliente de Spotify registró la reproducción en el mismo instante (por ejemplo, al presionar "siguiente" rápidamente o al sincronizar múltiples dispositivos).

**Por qué `(user_id, played_at)` tampoco es suficiente:**

Un mismo usuario podría reproducir dos canciones distintas con el mismo `played_at` reportado por Spotify (falla de precisión del cliente, salto rápido entre canciones). Esto no es teórico — lo observamos en los datos: el endpoint `/me/player/recently-played` devuelve ocasionalmente registros con timestamps solapados.

**La combinación correcta para deduplicación:**

```sql
(user_id, track_id, played_at)
```

Esta es la combinación que usa el pipeline para detectar duplicados antes de insertar:

```python
existing = db.query(FactListeningHistory).filter_by(
    user_id=user_id,
    track_id=track_id,
    played_at=played_at
).first()
if not existing:
    db.add(new_record)
```

**¿Por qué no es un UNIQUE constraint en la DB?**

Se optó por deduplicación programática en la capa ETL en lugar de un constraint de base de datos por dos razones:
1. El constraint generaría un error de integridad que abortaría toda la transacción si Spotify devuelve un duplicado — la deduplicación en Python permite continuar con los demás registros.
2. Existe el caso teórico de que un usuario escuche la misma canción dos veces en el mismo segundo (reproducción en loop), que sería un falso duplicado bajo ese constraint pero una reproducción legítima.

El `id SERIAL` como PK es la elección correcta: es inmutable, sin semántica de negocio, y permite que la lógica de deduplicación sea responsabilidad explícita del ETL y no del motor de base de datos.
