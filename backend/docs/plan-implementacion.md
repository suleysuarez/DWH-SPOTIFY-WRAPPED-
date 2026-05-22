# Plan de Implementación — Mi Spotify Wrapped DWH

**Universidad de Pamplona · Bases de Datos II · 2026-I**  
**Profesor:** Juan Alejandro Carrillo Jaimes  
**Integrantes:** Suley Suárez · Jhonatan Vera  
**Generado con:** Manus AI · Mayo 2026

---

## Herramienta de IA y Prompt Utilizado

**Herramienta:** Manus AI  
**Técnica:** Prompting con rol + contexto estructurado + instrucciones explícitas de formato

El siguiente prompt fue enviado a Manus para generar este plan completo:

```
Actúa como un arquitecto de software senior, líder técnico y analista de requerimientos 
especializado en proyectos académicos de Data Warehouse, ETL, FastAPI, PostgreSQL, 
OAuth PKCE y Frontend React/Next.js. Necesito que generes documentación técnica COMPLETA, 
coherente y profesional para un proyecto universitario llamado "Mi Spotify Wrapped".

IMPORTANTE:
- NO omitas detalles.
- NO generes respuestas genéricas.
- Todo debe estar alineado técnicamente.
- Las tareas NO deben contradecirse.
- NO deben existir gaps de implementación.
- El análisis debe considerar dependencias reales entre backend, frontend, ETL, 
  autenticación y base de datos.
- Debes pensar como un líder técnico real preparando la ejecución del proyecto.
- Debes identificar riesgos, bloqueos y puntos críticos.

[CONTEXTO DEL PROYECTO]
El proyecto consiste en construir un sistema completo de Data Warehouse con Spotify usando:
FastAPI · PostgreSQL en Neon · ETL incremental · OAuth PKCE · JWT propio · React/TypeScript
· Alembic · SQLAlchemy · Dashboard analítico · Notebook EDA con pandas

Star Schema: dim_users, dim_artists, dim_tracks, fact_listening_history, etl_audit

Equipo:
- Desarrollador 1 (Suley): backend básico, frontend casi nulo
- Desarrollador 2 (Jhonatan): frontend básico, backend básico

[TU OBJETIVO]
Genera los siguientes documentos COMPLETOS:
1. Informe de criterios de aceptación (funcionales, no funcionales, seguridad, mínimos vs óptimos)
2. Análisis de requerimientos (explícitos, implícitos, dependencias, gaps)
3. Validación de buenas prácticas
4. Identificación de gaps de implementación (severidad, impacto, solución)
5. Plan de trabajo en 5 días (realista, por persona, con checkpoints diarios)
6. Matriz de responsabilidades RACI
7. Arquitectura y flujo técnico (OAuth PKCE, ETL incremental, JWT)
8. Recomendaciones finales

Instrucciones adicionales:
- elabora un informe de criterios de aceptacion para este proyecto
- analiza los requerimientos propuestos de forma y de fondo
- ten en cuenta las buenas practicas del proyecto definidas
- haz un plan de trabajo en 5 dias para 2 personas
- el conocimiento de backend del desarrollador 1 (suley) es basico, y su nivel de 
  frontend casi nulo
- el conocimiento del desarrollador 2 (jhonatan) en front es basico y en back es basico
- que las tareas no se contradigan entre si o queden incompletas
- que no haya gaps de implementacion
```

**Técnica de prompting aplicada:** Prompting con rol asignado + contexto técnico detallado + lista explícita de entregables + restricciones de calidad. Al definir el rol ("arquitecto senior"), las restricciones ("NO generes respuestas genéricas") y el formato de salida esperado, se obtuvo una respuesta técnicamente precisa y alineada con el proyecto real.

---

## 1. Criterios de Aceptación

### 1.1 Criterios Funcionales Clave

| ID | Criterio | Validación | Prioridad |
|---|---|---|---|
| CF-01 | ETL Pipeline completo (3 fases) | `POST /v1/etl/run` → `etl_audit.status='success'` | Alta |
| CF-02 | Carga incremental con cursor | Segunda ejecución: no duplica registros | Alta |
| CF-03 | Auditoría ETL completa | `etl_audit` con mín. 3 filas | Alta |
| CF-04 | OAuth PKCE funcional | Login → Spotify → JWT en localStorage | Alta |
| CF-05 | Endpoints protegidos | 200 con JWT, 401 sin token | Alta |
| CF-06 | Dashboard con 4 widgets | Datos reales visibles en `/dashboard` | Alta |
| CF-07 | Migraciones Alembic | `alembic upgrade head` en base vacía | Alta |

### 1.2 Criterios Mínimos vs Óptimos

| Aspecto | Mínimo (aprueba) | Óptimo (sobresaliente) |
|---|---|---|
| ETL | Corre y carga datos | Incremental con cursor + auditoría |
| Datos | 50 registros historial | 100+ registros para análisis rico |
| Dashboard | 4 widgets básicos | Datos en tiempo real, estado vacío elegante |
| Documentación | Screenshots presentes | Prompts exactos + técnica de prompting |
| Commits | Historial visible | Commits atómicos y descriptivos |

### 1.3 Criterios de Seguridad Obligatorios

| ID | Criterio | Validación |
|---|---|---|
| CS-01 | JWT con expiración (8h) | Sin token → 401; token expirado → 401 |
| CS-02 | PKCE correcto | `code_verifier` en DB, `code_challenge = BASE64URL(SHA256(verifier))` |
| CS-03 | State PKCE de uso único | Reusar mismo state → debe fallar |
| CS-04 | CORS restringido | Solo `FRONTEND_URL`, no wildcard `*` |
| CS-05 | Tokens nunca en localStorage | `access_token` y `refresh_token` solo en `dim_users` |

---

## 2. Análisis de Requerimientos

### 2.1 Requerimientos Implícitos Críticos

Estos requerimientos no están escritos en el enunciado pero son obligatorios para que el sistema funcione:

| ID | Requerimiento | Por qué es crítico |
|---|---|---|
| RI-01 | Refresh de token Spotify antes del ETL | Sin renovación, el ETL falla 1h después del login |
| RI-02 | FK lookup de `artist_id` en `dim_tracks` | Sin lookup previo → FK violation al cargar tracks |
| RI-03 | Orden de carga ETL | `dim_users → dim_artists → dim_tracks → fact_*` |
| RI-04 | `context_type` puede ser `None` | `recently-played` retorna `context: null` — mapear a `'unknown'` |
| RI-05 | `played_at` con formato ISO + `Z` | Reemplazar `Z` por `+00:00` antes de `datetime.fromisoformat()` |
| RI-06 | CORS configurado | Sin CORS el frontend no puede llamar al backend |

### 2.2 Gaps de Implementación Identificados

| ID | Gap | Severidad | Solución |
|---|---|---|---|
| G-01 | FK lookup `artist_id` en `load_tracks` | Alta | `SELECT artist_id FROM dim_artists WHERE spotify_id = %s` antes de INSERT |
| G-02 | Sub-endpoints `/history/peak-hour` y `/history/genres` | Alta | Crear en `history.py` con queries analíticas sobre `fact_listening_history` |
| G-03 | Refresh de token antes del ETL | Alta | Verificar `token_expires_at < NOW() + 5min` antes de llamar a Spotify |
| G-04 | `played_at` con `Z` al final | Media | `.replace('Z', '+00:00')` en transform |
| G-05 | `context_type` puede ser `None` | Media | `context_type = (item.get('context') or {}).get('type', 'unknown')` |
| G-06 | Cursor de primera ejecución | Alta | Si `cursor_after_ms` es `NULL`, no pasar parámetro `after` a Spotify |

---

## 3. Plan de Trabajo — 5 Días

### Día 1 — Fundación (Base de datos + Auth)
- **Suley:** Repo + `.gitignore` + Neon + Alembic migraciones + `main.py` + OAuth PKCE backend
- **Jhonatan:** Proyecto React/Vite + `/login` + `/callback` + `lib/auth.ts` + `lib/api.ts`
- **Checkpoint:** Flujo completo login → JWT funcionando

### Día 2 — ETL Core + Endpoints + Primera carga
- **Suley:** `extract_*` + `transform_*` + `load_*` + auditoría + primera ejecución real
- **Jhonatan:** Tipos TypeScript + `/profile` + `/dashboard` (TopArtists + TopTracks)
- **Checkpoint:** ETL completo + primera fila en `etl_audit` + dashboard con datos

### Día 3 — ETL Incremental + Dashboard completo
- **Suley:** Cursor incremental + sub-endpoints analíticos + `/etl/status` + refresh token
- **Jhonatan:** `PeakHourCard` + `GenresChart` + `/etl` page con log + polish visual
- **Checkpoint:** Sistema end-to-end + 2 ejecuciones en `etl_audit`

### Día 4 — EDA Notebook + Preguntas técnicas + Documentación
- **Ambos:** EDA notebook con 6 secciones + preguntas técnicas individuales + docs completos
- **Checkpoint:** Notebook ejecutable + docs con prompts + preguntas individuales

### Día 5 — Pulido, Testing y Entrega
- **Suley:** Verificar migraciones en base limpia + Postman screenshots + README
- **Jhonatan:** Testing E2E + screenshots frontend + documentación diseño IA
- **Checkpoint:** Entrega antes de las 23:59

---

## 4. Matriz RACI Resumida

| Módulo | Suley | Jhonatan |
|---|---|---|
| Migraciones Alembic | **R** | C |
| OAuth PKCE Backend | **R** | C |
| ETL Pipeline completo | **R** | I |
| ETL Incremental + cursor | **R** | I |
| Frontend /login + /callback | C | **R** |
| Frontend /dashboard (4 widgets) | C | **R** |
| Frontend /etl + log | C | **R** |
| EDA Notebook | **R** | **R** |
| Preguntas técnicas individuales | **R** | **R** |
| Documentación con prompts | **R** | **R** |

---

## 5. Riesgos Críticos

| Riesgo | Probabilidad | Impacto | Mitigación |
|---|---|---|---|
| `.env` commiteado accidentalmente | Media | Muy Alta — cero en todo | `.gitignore` desde el primer commit |
| FK violation al cargar `dim_tracks` | Alta | Alta | FK lookup previo en `load_tracks` |
| OAuth PKCE mal implementado | Media | Muy Alta — bloquea todo | Testear el flujo completo el Día 1 |
| Menos de 100 registros en `fact_*` | Media | Alta — EDA pobre | Ejecutar ETL múltiples días |
| Respuestas técnicas copiadas | Media | Alta — cero puntos | Responder individualmente sin coordinación |
