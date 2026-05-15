# Migraciones — Alembic

**Autoras/es:** Suley Suárez y Jhonatan Vera — Universidad de Pamplona 2026-I

Gestión de esquema de base de datos con Alembic para el DWH de Spotify.

---

## Configuración

El archivo `env.py` lee `DATABASE_URL` desde las variables de entorno (o `backend/.env`) e inyecta la URL en Alembic en tiempo de ejecución. También crea el schema `dwh` de PostgreSQL si no existe antes de aplicar migraciones.

`alembic.ini` define la ruta de migraciones (`migrations/versions/`) y el formato del timestamp de revision (`%Y%m%d_%H%M`).

---

## Comandos

```bash
# Desde backend/
alembic upgrade head           # Aplicar todas las migraciones pendientes
alembic downgrade -1           # Revertir la última migración
alembic current                # Ver revisión actual en la BD
alembic history --verbose      # Ver todas las revisiones
alembic revision --autogenerate -m "descripcion"  # Crear nueva migración desde ORM
```

---

## Versiones

### `001_initial_schema` — Migración inicial

Crea las tablas del star schema en el schema `dwh`:

| Tabla | Tipo |
|---|---|
| `dim_users` | Dimensión de usuarios Spotify |
| `dim_artists` | Dimensión de artistas |
| `dim_tracks` | Dimensión de canciones |
| `fact_listening_history` | Tabla de hechos (reproduccciones) |
| `etl_audit` | Registro de ejecuciones del pipeline |
| `pkce_sessions` | Sesiones PKCE en schema `public` |

> **Nota:** Algunas columnas añadidas posteriormente (ej. `album_image_url` en `dim_tracks`) se crean mediante `Base.metadata.create_all()` al inicio de la app (`main.py`) y no tienen migración Alembic asociada. Para evitar inconsistencias, ejecutar `alembic upgrade head` **y** arrancar la app al menos una vez después de cada cambio de schema.

---

## Prerrequisitos

El schema `dwh` debe existir antes de correr migraciones. `env.py` lo crea automáticamente con `CREATE SCHEMA IF NOT EXISTS dwh`, pero si se conecta con un usuario sin permisos de creación de schemas, debe crearse manualmente:

```sql
CREATE SCHEMA IF NOT EXISTS dwh;
```
