# 05 — Consultas Analíticas del DWH

Todas las consultas se ejecutan sobre el schema `dwh` de PostgreSQL. Sustituir `<user_id>` por el `user_id` interno del usuario (entero, no el spotify_id).

---

## 1. Top 10 Artistas por Reproducciones

Artistas más escuchados del usuario ordenados por número de veces que aparecen en el historial.

```sql
SELECT
    a.name                              AS artista,
    COUNT(f.id)                         AS reproducciones,
    a.popularity,
    a.genres,
    a.image_url
FROM dwh.fact_listening_history f
JOIN dwh.dim_artists a ON a.artist_id = f.artist_id
WHERE f.user_id = <user_id>
GROUP BY a.artist_id, a.name, a.popularity, a.genres, a.image_url
ORDER BY reproducciones DESC
LIMIT 10;
```

---

## 2. Top 10 Canciones por Reproducciones

Canciones más escuchadas con nombre del artista y portada del álbum.

```sql
SELECT
    t.name                              AS cancion,
    a.name                              AS artista,
    COUNT(f.id)                         AS reproducciones,
    t.duration_ms,
    t.popularity,
    t.album_name,
    t.album_image_url
FROM dwh.fact_listening_history f
JOIN dwh.dim_tracks  t ON t.track_id  = f.track_id
JOIN dwh.dim_artists a ON a.artist_id = f.artist_id
WHERE f.user_id = <user_id>
GROUP BY t.track_id, t.name, a.name, t.duration_ms, t.popularity,
         t.album_name, t.album_image_url
ORDER BY reproducciones DESC
LIMIT 10;
```

---

## 3. Top Géneros Musicales

Géneros más frecuentes calculados expandiendo el array `genres` de `dim_artists`.

```sql
SELECT
    TRIM(genre)                         AS genero,
    COUNT(*)                            AS apariciones,
    ROUND(COUNT(*) * 100.0 /
        SUM(COUNT(*)) OVER (), 1)       AS porcentaje
FROM dwh.fact_listening_history f
JOIN dwh.dim_artists a ON a.artist_id = f.artist_id
CROSS JOIN UNNEST(a.genres) AS genre
WHERE f.user_id = <user_id>
  AND a.genres IS NOT NULL
GROUP BY TRIM(genre)
ORDER BY apariciones DESC
LIMIT 10;
```

---

## 4. Distribución de Escucha por Hora del Día

Cuántas reproducciones ocurrieron en cada hora del día (0–23).

```sql
SELECT
    f.hour_of_day                       AS hora,
    COUNT(f.id)                         AS reproducciones,
    TO_CHAR(f.hour_of_day, 'FM00') || ':00'  AS etiqueta
FROM dwh.fact_listening_history f
WHERE f.user_id = <user_id>
  AND f.hour_of_day IS NOT NULL
GROUP BY f.hour_of_day
ORDER BY f.hour_of_day;
```

---

## 5. Distribución de Escucha por Día de la Semana

Comparación de actividad entre días laborales y fin de semana.

```sql
SELECT
    f.day_of_week                       AS dia,
    COUNT(f.id)                         AS reproducciones,
    CASE
        WHEN f.day_of_week IN ('Saturday', 'Sunday') THEN 'Fin de semana'
        ELSE 'Día laboral'
    END                                 AS tipo_dia
FROM dwh.fact_listening_history f
WHERE f.user_id = <user_id>
  AND f.day_of_week IS NOT NULL
GROUP BY f.day_of_week
ORDER BY
    CASE f.day_of_week
        WHEN 'Monday'    THEN 1
        WHEN 'Tuesday'   THEN 2
        WHEN 'Wednesday' THEN 3
        WHEN 'Thursday'  THEN 4
        WHEN 'Friday'    THEN 5
        WHEN 'Saturday'  THEN 6
        WHEN 'Sunday'    THEN 7
    END;
```

---

## 6. Minutos Totales Escuchados

Total de minutos reproducidos por el usuario en el historial.

```sql
SELECT
    COUNT(f.id)                                  AS total_reproducciones,
    ROUND(SUM(t.duration_ms) / 60000.0, 1)      AS minutos_totales,
    ROUND(SUM(t.duration_ms) / 3600000.0, 2)    AS horas_totales
FROM dwh.fact_listening_history f
JOIN dwh.dim_tracks t ON t.track_id = f.track_id
WHERE f.user_id = <user_id>
  AND t.duration_ms IS NOT NULL;
```

---

## 7. Historial Diario de Reproducciones (Últimos 30 Días)

Evolución de la actividad de escucha día a día.

```sql
SELECT
    DATE(f.played_at)                   AS fecha,
    COUNT(f.id)                         AS reproducciones
FROM dwh.fact_listening_history f
WHERE f.user_id = <user_id>
  AND f.played_at >= NOW() - INTERVAL '30 days'
GROUP BY DATE(f.played_at)
ORDER BY fecha DESC;
```

---

## 8. Artistas Descubiertos Recientemente

Artistas que aparecen por primera vez en el historial en los últimos 7 días.

```sql
SELECT
    a.name                              AS artista,
    MIN(f.played_at)                    AS primera_vez,
    COUNT(f.id)                         AS reproducciones
FROM dwh.fact_listening_history f
JOIN dwh.dim_artists a ON a.artist_id = f.artist_id
WHERE f.user_id = <user_id>
GROUP BY a.artist_id, a.name
HAVING MIN(f.played_at) >= NOW() - INTERVAL '7 days'
ORDER BY primera_vez DESC;
```

---

## 9. Contexto de Reproducción (Playlist vs. Álbum vs. Artista)

Cómo el usuario descubre y escucha música.

```sql
SELECT
    COALESCE(f.context_type, 'unknown') AS contexto,
    COUNT(f.id)                         AS reproducciones,
    ROUND(COUNT(f.id) * 100.0 /
        SUM(COUNT(f.id)) OVER (), 1)    AS porcentaje
FROM dwh.fact_listening_history f
WHERE f.user_id = <user_id>
GROUP BY f.context_type
ORDER BY reproducciones DESC;
```

---

## 10. Resumen General del DWH

Vista global del estado del warehouse para el usuario.

```sql
SELECT
    (SELECT COUNT(*)    FROM dwh.dim_artists)                             AS total_artistas,
    (SELECT COUNT(*)    FROM dwh.dim_tracks)                              AS total_canciones,
    (SELECT COUNT(*)    FROM dwh.fact_listening_history
     WHERE user_id = <user_id>)                                           AS total_reproducciones,
    (SELECT COUNT(DISTINCT track_id) FROM dwh.fact_listening_history
     WHERE user_id = <user_id>)                                           AS canciones_unicas,
    (SELECT COUNT(DISTINCT artist_id) FROM dwh.fact_listening_history
     WHERE user_id = <user_id>)                                           AS artistas_unicos,
    (SELECT ROUND(SUM(t.duration_ms) / 60000.0, 1)
     FROM dwh.fact_listening_history f
     JOIN dwh.dim_tracks t ON t.track_id = f.track_id
     WHERE f.user_id = <user_id>
       AND t.duration_ms IS NOT NULL)                                     AS minutos_totales,
    (SELECT MAX(played_at) FROM dwh.fact_listening_history
     WHERE user_id = <user_id>)                                           AS ultima_reproduccion,
    (SELECT started_at FROM dwh.etl_audit
     WHERE spotify_user_id = (SELECT spotify_id FROM dwh.dim_users
                               WHERE user_id = <user_id>)
       AND status = 'success'
     ORDER BY started_at DESC LIMIT 1)                                    AS ultima_sincronizacion;
```
