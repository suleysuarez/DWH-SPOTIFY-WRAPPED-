# Guía de Prueba Local — Mi Spotify Wrapped DWH

## Paso 1: Preparar Spotify Developer

1. Ir a https://developer.spotify.com/dashboard
2. Iniciar sesión (crear cuenta si no tienes)
3. Crear una nueva aplicación:
   - Nombre: "Mi Spotify Wrapped Local"
   - Aceptar términos
4. Copiar:
   - **Client ID**
   - **Client Secret**
5. Ir a "Edit Settings"
6. Agregar Redirect URI: `http://localhost:8000/v1/auth/callback`
7. Guardar

## Paso 2: Preparar Base de Datos

### Opción A: PostgreSQL Local (Recomendado para desarrollo)

```bash
# Instalar PostgreSQL (macOS con Homebrew)
brew install postgresql@15

# Iniciar servicio
brew services start postgresql@15

# Crear base de datos
createdb dwh

# Verificar conexión
psql dwh -c "SELECT 1"
```

**DATABASE_URL:**
```
postgresql://localhost/dwh
```

### Opción B: Neon Cloud (Recomendado para producción)

1. Ir a https://neon.tech
2. Crear cuenta gratuita
3. Crear proyecto
4. Copiar Connection String (con `sslmode=require`)

**DATABASE_URL:**
```
postgresql://user:password@host.neon.tech/dbname?sslmode=require
```

## Paso 3: Configurar Backend

```bash
# Navegar a carpeta backend
cd mi-spotify-wrapped-dwh/backend

# Crear entorno virtual
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Instalar dependencias
pip install -r requirements.txt

# Crear archivo .env
cat > .env << 'EOF'
DATABASE_URL=postgresql://localhost/dwh
SPOTIFY_CLIENT_ID=tu_client_id_aqui
SPOTIFY_CLIENT_SECRET=tu_client_secret_aqui
SPOTIFY_REDIRECT_URI=http://localhost:8000/v1/auth/callback
JWT_SECRET=tu_secret_key_aqui_cambiar_en_produccion
JWT_ALGORITHM=HS256
JWT_EXPIRATION_HOURS=8
FRONTEND_URL=http://localhost:3000
LOG_LEVEL=INFO
EOF
```

### Generar JWT_SECRET

```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

Copiar el resultado y pegarlo en `.env` como `JWT_SECRET`.

### Crear Tablas (Migraciones)

```bash
# Desde carpeta backend
cd backend

# Ejecutar migraciones
python -m alembic upgrade head

# Verificar tablas creadas
psql dwh -c "\dt"
```

Deberías ver:
```
            List of relations
 Schema |        Name         | Type  | Owner
--------+---------------------+-------+-------
 public | dim_artists         | table | user
 public | dim_tracks          | table | user
 public | dim_users           | table | user
 public | etl_audit           | table | user
 public | fact_listening_history | table | user
 public | pkce_sessions       | table | user
```

### Iniciar Backend

```bash
# Desde carpeta backend
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**Resultado esperado:**
```
INFO:     Uvicorn running on http://0.0.0.0:8000
INFO:     Application startup complete
```

**Verificar:**
- Abrir http://localhost:8000/health
- Deberías ver: `{"status":"healthy"}`

## Paso 4: Configurar Frontend

```bash
# En otra terminal, navegar a carpeta frontend
cd mi-spotify-wrapped-dwh/client

# Instalar dependencias
npm install

# Crear .env.local
cat > .env.local << 'EOF'
VITE_API_URL=http://localhost:8000
EOF

# Iniciar frontend
npm run dev
```

**Resultado esperado:**
```
  VITE v7.1.9  ready in 500 ms

  ➜  Local:   http://localhost:3000/
```

## Paso 5: Probar Flujo Completo

### 1. Abrir Login

```
http://localhost:3000/login
```

Deberías ver:
- Logo de Spotify (verde)
- Título "Mi Spotify Wrapped"
- Botón "Conectar con Spotify"

### 2. Hacer Clic en "Conectar con Spotify"

- Se abrirá página de Spotify
- Inicia sesión con tu cuenta
- Autoriza acceso

### 3. Callback Automático

- Serás redirigido a `/dashboard`
- Se guardará JWT en `localStorage`

### 4. Ver Dashboard

Deberías ver:
- 4 KPI cards (Total Canciones, Artistas, Última Sync, Estado ETL)
- Top Artistas (vacío si no has ejecutado ETL)
- Top Canciones (vacío si no has ejecutado ETL)
- Hora Pico (vacío si no has ejecutado ETL)
- Géneros (vacío si no has ejecutado ETL)

### 5. Ejecutar ETL

1. Ir a `/etl`
2. Hacer clic en "Sincronizar Ahora"
3. Ver logs en tiempo real:
   ```
   Iniciando proceso ETL...
   Extrayendo datos de Spotify...
   Extraído: 50 artistas, 50 canciones, 50 historial
   Transformando datos...
   Datos transformados exitosamente
   Cargando datos en DWH...
   Cargado: 45 artistas, 50 canciones, 50 historial
   ETL completado exitosamente.
   ```

### 6. Volver a Dashboard

1. Ir a `/dashboard`
2. Deberías ver datos reales:
   - Top 5 artistas con reproducciones
   - Top 5 canciones con duración
   - Hora pico (ej: 14:00 — 18:00)
   - Géneros dominantes

### 7. Ver Perfil

1. Ir a `/profile`
2. Deberías ver:
   - Avatar de Spotify
   - Nombre, email, país
   - Seguidores
   - Plan (Free/Premium)

## Troubleshooting

### Error: "CORS error" o "Failed to fetch"

**Problema:** Frontend no puede conectar con backend

**Solución:**
```bash
# Verificar que backend está corriendo en puerto 8000
curl http://localhost:8000/health

# Verificar FRONTEND_URL en .env del backend
cat backend/.env | grep FRONTEND_URL
# Debe ser: FRONTEND_URL=http://localhost:3000
```

### Error: "Connection refused" a PostgreSQL

**Problema:** Base de datos no está corriendo

**Solución:**
```bash
# Verificar PostgreSQL está corriendo
psql -U postgres -c "SELECT 1"

# Si no está corriendo, iniciar
brew services start postgresql@15  # macOS
# o en Linux:
sudo systemctl start postgresql
```

### Error: "Token expirado" después de 8 horas

**Problema:** JWT expira automáticamente

**Solución:** Hacer login nuevamente

### Error: "Artista no encontrado" en ETL

**Problema:** Orden de carga incorrecta

**Solución:** Ejecutar ETL nuevamente. Verificar logs en `/v1/etl/status`

### Error: "Spotify API error"

**Problema:** Credenciales inválidas o token expirado

**Solución:**
```bash
# Verificar SPOTIFY_CLIENT_ID y SPOTIFY_CLIENT_SECRET en .env
cat backend/.env | grep SPOTIFY

# Regenerar token: hacer logout y login nuevamente
```

## Verificar en DevTools

### 1. Verificar JWT en localStorage

```javascript
// Abrir DevTools (F12)
// Console tab
localStorage.getItem('token')
// Deberías ver un token largo como:
// "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

### 2. Verificar Requests a API

```
DevTools → Network tab
Hacer clic en "Sincronizar Ahora"
Deberías ver:
- POST /v1/etl/run (200 OK)
- Response con logs y status
```

### 3. Verificar Base de Datos

```bash
# Conectar a BD
psql dwh

# Ver registros cargados
SELECT COUNT(*) FROM dim_artists;
SELECT COUNT(*) FROM dim_tracks;
SELECT COUNT(*) FROM fact_listening_history;

# Ver ejecuciones ETL
SELECT * FROM etl_audit ORDER BY etl_id DESC LIMIT 1;
```

## Comandos Útiles

### Backend

```bash
# Reinstalar dependencias
pip install -r requirements.txt --force-reinstall

# Recrear base de datos
dropdb dwh
createdb dwh
python -m alembic upgrade head

# Ver logs del backend
tail -f backend.log

# Detener backend
Ctrl+C
```

### Frontend

```bash
# Limpiar cache y reinstalar
rm -rf node_modules package-lock.json
npm install

# Detener frontend
Ctrl+C

# Ver logs del frontend
npm run dev 2>&1 | tee frontend.log
```

### PostgreSQL

```bash
# Conectar a BD
psql dwh

# Ver todas las tablas
\dt

# Ver estructura de tabla
\d dim_users

# Contar registros
SELECT COUNT(*) FROM dim_artists;

# Salir
\q
```

## Checklist de Prueba

- [ ] Backend corriendo en puerto 8000
- [ ] Frontend corriendo en puerto 3000
- [ ] PostgreSQL corriendo
- [ ] JWT_SECRET generado y en .env
- [ ] SPOTIFY_CLIENT_ID y SPOTIFY_CLIENT_SECRET en .env
- [ ] SPOTIFY_REDIRECT_URI registrado en Spotify Developer
- [ ] Tablas creadas en BD (alembic upgrade head)
- [ ] Login funciona y redirige a /dashboard
- [ ] JWT guardado en localStorage
- [ ] ETL ejecuta sin errores
- [ ] Dashboard muestra datos reales
- [ ] Perfil muestra avatar y datos
- [ ] Logs en tiempo real en /etl

## Siguiente Paso

Una vez todo funciona localmente:

1. **Desplegar Backend** en Render, Railway o Heroku
2. **Desplegar Frontend** en Manus (Publish button)
3. **Actualizar FRONTEND_URL** en backend con URL de producción
4. **Registrar Redirect URI** en Spotify con URL de producción

---

**¿Problemas?** Revisar logs:
- Backend: `backend.log` o consola
- Frontend: DevTools Console (F12)
- BD: `psql dwh -c "SELECT * FROM etl_audit ORDER BY etl_id DESC LIMIT 1"`
