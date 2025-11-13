# 🚀 Guía de Despliegue en Render

## 📋 Pasos para Desplegar ACA 4.0 en Render

### Paso 1: Crear cuenta en Render

1. Ve a [render.com](https://render.com)
2. Haz clic en **"Get Started"** o **"Sign Up"**
3. Elige **"Sign up with GitHub"** (recomendado) o crea cuenta con email
4. Autoriza Render para acceder a tus repositorios de GitHub

### Paso 2: Crear nuevo Web Service

1. En el Dashboard de Render, haz clic en **"New +"** → **"Web Service"**
2. Selecciona **"Connect a repository"**
3. Busca y selecciona: `christian-matthews/aca_4`
4. Haz clic en **"Connect"**

### Paso 3: Configurar el Servicio

#### Configuración Básica

- **Name**: `aca-4-bot` (o el nombre que prefieras)
- **Region**: Elige la región más cercana (ej: `Oregon (US West)`)
- **Branch**: `main`
- **Root Directory**: (dejar vacío - usa la raíz del proyecto)

#### Build & Deploy

- **Environment**: `Python 3`
- **Build Command**: 
  ```bash
  pip install -r requirements.txt
  ```
- **Start Command**: 
  ```bash
  python run_production.py
  ```

#### Plan

- **Free**: Para empezar (puede tener limitaciones)
- **Starter ($7/mes)**: Recomendado para producción
- **Standard ($25/mes)**: Para mayor rendimiento

### Paso 4: Configurar Variables de Entorno

Haz clic en **"Environment"** y agrega las siguientes variables:

#### 🔴 Variables REQUERIDAS (Críticas)

```bash
# Telegram Bots
BOT_ADMIN_TOKEN=tu_token_de_bot_admin
BOT_PRODUCTION_TOKEN=tu_token_de_bot_produccion
ADMIN_CHAT_ID=tu_chat_id_admin

# Supabase
SUPABASE_URL=https://tu-proyecto.supabase.co
SUPABASE_KEY=tu_anon_key
SUPABASE_SERVICE_KEY=tu_service_key

# Storage
SUPABASE_STORAGE_BUCKET=ACA_4
```

#### 🟡 Variables OPCIONALES

```bash
# OpenAI (requerido para Asesor IA)
OPENAI_API_KEY=tu_openai_api_key

# Configuración
ENVIRONMENT=production
DEBUG=false
MAX_FILE_SIZE_MB=50
```

**⚠️ IMPORTANTE:**
- **NO** agregues `PORT` - Render lo asigna automáticamente
- **NO** agregues `ENVIRONMENT=production` y `DEBUG=false` si usas `render.yaml` (ya están configuradas)
- Copia los valores de tu archivo `.env` local

### Paso 5: Configurar Health Check

En la sección **"Health Check Path"**:
- **Path**: `/health`
- Render verificará automáticamente que el servicio esté funcionando

### Paso 6: Desplegar

1. Haz clic en **"Create Web Service"**
2. Render comenzará a:
   - Clonar el repositorio
   - Instalar dependencias (`pip install -r requirements.txt`)
   - Ejecutar el servicio (`python run_production.py`)
3. Espera 2-5 minutos para el primer despliegue
4. Verás los logs en tiempo real

### Paso 7: Verificar el Despliegue

Una vez completado el despliegue:

1. **Verificar Health Check**:
   - Render te dará una URL como: `https://aca-4-bot.onrender.com`
   - Ve a: `https://aca-4-bot.onrender.com/health`
   - Deberías ver: `{"status":"healthy",...}`

2. **Verificar Bots**:
   - Los bots de Telegram deberían estar funcionando
   - Prueba enviando un mensaje al bot de producción

3. **Ver Logs**:
   - En Render Dashboard → Tu servicio → **"Logs"**
   - Deberías ver: `✅ Bots iniciados y escuchando mensajes`

## 🔧 Configuración Avanzada

### Usar render.yaml (Opcional)

Si prefieres usar el archivo `render.yaml` que ya está en el repositorio:

1. En Render Dashboard → Tu servicio → **"Settings"**
2. Scroll hasta **"Infrastructure as Code"**
3. Selecciona **"Use render.yaml"**
4. Render leerá automáticamente `render.yaml` del repositorio

**Ventajas:**
- Configuración versionada en Git
- Fácil de replicar
- Menos clics en la interfaz

### Auto-Deploy

Por defecto, Render despliega automáticamente cuando:
- Haces push a la rama `main`
- Haces merge de un Pull Request

Para desactivar:
- Settings → **"Auto-Deploy"** → Desactivar

### Custom Domain (Opcional)

1. Settings → **"Custom Domains"**
2. Agrega tu dominio
3. Sigue las instrucciones de DNS

## 🐛 Troubleshooting

### Error: "Build failed"

**Causa común**: Dependencias no instaladas
**Solución**: Verifica que `requirements.txt` esté completo

### Error: "Service crashed"

**Causa común**: Variables de entorno faltantes
**Solución**: 
1. Ve a **"Environment"**
2. Verifica que todas las variables REQUERIDAS estén configuradas
3. Revisa los logs para ver qué variable falta

### Error: "Bots no funcionan"

**Causa común**: Tokens incorrectos o variables mal configuradas
**Solución**:
1. Verifica que `BOT_ADMIN_TOKEN` y `BOT_PRODUCTION_TOKEN` sean correctos
2. Verifica que `SUPABASE_SERVICE_KEY` tenga permisos suficientes
3. Revisa los logs para ver errores específicos

### Error: "Port already in use"

**Causa común**: Conflicto de puerto
**Solución**: 
- Render asigna el puerto automáticamente via `PORT`
- Asegúrate de que `run_production.py` use `os.getenv("PORT")`

### Logs útiles

Para ver logs en tiempo real:
```bash
# En Render Dashboard
Tu servicio → Logs → "Live"
```

Para ver logs históricos:
```bash
# En Render Dashboard
Tu servicio → Logs → "Historical"
```

## 📊 Monitoreo

### Health Check

Render verifica automáticamente `/health` cada minuto.

Si el health check falla:
- Render intentará reiniciar el servicio
- Recibirás una notificación por email

### Métricas

En el Dashboard puedes ver:
- **CPU Usage**
- **Memory Usage**
- **Request Count**
- **Response Time**

## 🔄 Actualizar el Código

Para actualizar el código en producción:

1. Haz cambios en tu repositorio local
2. Haz commit y push a GitHub:
   ```bash
   git add .
   git commit -m "Descripción del cambio"
   git push
   ```
3. Render detectará el cambio automáticamente
4. Desplegará la nueva versión (2-5 minutos)

## 💰 Costos

### Plan Free
- ✅ 750 horas/mes gratis
- ⚠️ El servicio se "duerme" después de 15 minutos de inactividad
- ⚠️ Primera petición después de dormir puede tardar 30-60 segundos

### Plan Starter ($7/mes)
- ✅ Siempre activo (no se duerme)
- ✅ Mejor rendimiento
- ✅ Recomendado para producción

### Plan Standard ($25/mes)
- ✅ Mayor rendimiento
- ✅ Para aplicaciones con mucho tráfico

## 📝 Checklist Pre-Despliegue

Antes de desplegar, verifica:

- [ ] Todas las variables de entorno están configuradas
- [ ] Los tokens de Telegram son válidos
- [ ] Las credenciales de Supabase son correctas
- [ ] El bucket de Storage existe en Supabase
- [ ] `render.yaml` está en el repositorio (opcional)
- [ ] `run_production.py` está en el repositorio
- [ ] `requirements.txt` está completo
- [ ] El código está en la rama `main` de GitHub

## 🆘 Soporte

Si tienes problemas:

1. **Revisa los logs** en Render Dashboard
2. **Verifica las variables de entorno**
3. **Prueba localmente** primero con `python run_production.py`
4. **Consulta la documentación**: [render.com/docs](https://render.com/docs)

## 🎯 Próximos Pasos

Después de desplegar:

1. ✅ Verifica que el health check funcione
2. ✅ Prueba los bots de Telegram
3. ✅ Verifica que los archivos se suban/descarguen correctamente
4. ✅ Configura notificaciones de errores (opcional)
5. ✅ Considera configurar un dominio personalizado

---

**¡Listo para desplegar!** 🚀

Si tienes dudas durante el proceso, revisa los logs o consulta esta guía.

