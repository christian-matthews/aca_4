# 🚀 ACA 4.0 - Sistema de Bots de Telegram con Supabase

Sistema simplificado enfocado en la gestión de chatbots de Telegram con almacenamiento en Supabase.

## ✨ Características Principales

### 🤖 **Bots de Telegram**
- **Bot Admin**: Gestión administrativa, creación de empresas y usuarios
- **Bot Producción**: Acceso para usuarios finales y consultas
- **Comando `/adduser`**: Agregar usuarios rápidamente con detección automática de nombres
- **Logging completo**: Registro de todas las conversaciones autorizadas y no autorizadas

### 📊 **Sistema de Logging Completo**
- Registro de todas las conversaciones de Telegram (autorizadas y no autorizadas)
- Detección automática de usuarios con/sin permisos
- API REST para consultar conversaciones
- Función SQL optimizada para logging (`log_conversacion_simple`)

### 🔒 **Sistema de Roles y Permisos** ✅ **IMPLEMENTADO**
- **3 niveles de roles**: `super_admin`, `gestor`, `usuario`
- **super_admin**: Todos los permisos (The Wingman, Christian Matthews)
- **gestor**: Puede asignar empresas, subir y descargar archivos
- **usuario**: Solo puede descargar archivos (NO puede subir)
- **Validaciones de seguridad**: Permisos verificados antes de cada operación
- **Multiempresa**: Un usuario puede tener diferentes roles en diferentes empresas

### 🏢 **Multiempresa** ✅ **IMPLEMENTADO**
- **Soporte completo**: Un usuario puede pertenecer a múltiples empresas
- **Tabla `usuarios_empresas`**: Relación muchos a muchos entre usuarios y empresas
- **Roles por empresa**: Cada usuario puede tener un rol diferente en cada empresa
- **Selección automática**: Si tiene 1 empresa, se asigna automáticamente
- **Menú de selección**: Si tiene múltiples empresas, muestra menú para elegir

### 📁 **Gestión de Archivos** ✅ **IMPLEMENTADO**
- **Subida de archivos**: Flujo conversacional completo con botones (empresa → categoría → subtipo → período)
- **Descarga de archivos**: Flujo estructurado con botones (sin lenguaje natural)
- **Menús en 2 columnas**: Todos los menús organizados en formato de 2 columnas
- **Selección múltiple**: Cuando hay múltiples archivos, permite descargar individual o todos
- **Clasificación jerárquica**: Legal (Estatutos, Poderes, CI, RUT) y Financiero (Reportes, Estados, F29, F22)
- **Sesiones conversacionales**: Gestión de estado para flujos multi-paso
- **Validaciones de seguridad**: Filtrado por empresa del usuario
- **Storage en Supabase**: Almacenamiento seguro con URLs firmadas (expiración 1 hora)
- **Comandos de control**: `/start` y `/cancelar` para limpiar sesiones activas
- **Sanitización de nombres**: Limpieza automática de caracteres especiales en nombres de archivo

### 🤖 **Asesor IA** ✅ **IMPLEMENTADO**
- **Contexto automático**: Lee reportes financieros del mes en curso/anterior y reportes CFO antes de responder
- **Respuestas inteligentes**: Utiliza OpenAI para analizar contexto y responder preguntas del usuario
- **Derivación a ayuda**: Si la IA no puede responder con confianza suficiente, deriva automáticamente al chat de ayuda
- **Historial conversacional**: Mantiene contexto de las últimas 5 interacciones para respuestas más coherentes
- **Nivel de confianza**: Evalúa la confiabilidad de cada respuesta y sugiere ayuda cuando es necesario

## 🚀 Instalación

### 1. Clonar y configurar entorno

```bash
# Crear entorno virtual
python3 -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate

# Instalar dependencias
pip install -r requirements.txt
```

### 2. Configurar variables de entorno

```bash
# Copiar archivo de ejemplo
cp .env.example .env

# Editar .env con tus credenciales
```

**Variables requeridas:**
```bash
# Telegram Bots
BOT_ADMIN_TOKEN=tu_token_de_bot_admin
BOT_PRODUCTION_TOKEN=tu_token_de_bot_produccion
ADMIN_CHAT_ID=tu_chat_id_admin

# Supabase
SUPABASE_URL=tu_url_de_supabase
SUPABASE_KEY=tu_key_de_supabase
SUPABASE_SERVICE_KEY=tu_service_key  # CRÍTICO para logging

# Storage
SUPABASE_STORAGE_BUCKET=ACA_4  # Nombre del bucket en Supabase

# OpenAI (Opcional - para Asesor IA y extracción de intención)
OPENAI_API_KEY=tu_openai_api_key  # Requerido para Asesor IA, opcional para descarga
```

### 3. Configurar Base de Datos

```bash
# Ejecutar migraciones SQL en Supabase (en orden):
# 1. Schema base
database/migrations/schema_completo.sql

# 2. Campos de archivos
database/migrations/001_add_campos_archivos.sql

# 3. Sesiones conversacionales
database/migrations/002_create_sesiones_conversacion.sql

# 4. Multiempresa
database/migrations/003_create_usuarios_empresas.sql

# 5. Sistema de roles y permisos
database/migrations/004_sistema_roles_permisos.sql
```

**Estructura de base de datos:**
- **9 tablas**: empresas, usuarios, conversaciones, usuarios_detalle, intentos_acceso_negado, security_logs, bot_analytics, archivos, sesiones_conversacion
- **1 tabla multiempresa**: usuarios_empresas (relación muchos a muchos)
- **2 funciones SQL**: `log_conversacion_simple()`, `limpiar_sesiones_expiradas()`, `migrar_empresas_existentes()`
- **2 vistas**: vista_conversaciones_recientes, vista_usuarios_sin_acceso
- **Índices optimizados** para búsquedas de archivos, sesiones y relaciones usuarios-empresas

### 4. Iniciar aplicación

```bash
# Opción 1: Usando script
python run.py

# Opción 2: Directamente
uvicorn app.main:app --reload
```

## 🌐 Endpoints API

### Endpoints Básicos
- `GET /` - Información del sistema
- `GET /health` - Health check completo
- `GET /status` - Estado detallado del sistema

### Control de Bots
- `POST /bots/start` - Iniciar bots manualmente
- `POST /bots/stop` - Detener bots manualmente
- `POST /bots/restart` - Reiniciar bots

### Conversaciones
- `GET /api/conversations/recent` - Conversaciones recientes
- `GET /api/conversations/unauthorized` - Usuarios no autorizados
- `GET /api/conversations/last` - Último chat
- `GET /api/conversations/user-history/{chat_id}` - Historial de usuario
- `GET /api/conversations/analytics` - Analíticas

## 📁 Estructura del Proyecto

```
aca_4/
├── app/
│   ├── __init__.py
│   ├── config.py                    # Configuración (Telegram + Supabase + OpenAI)
│   ├── main.py                      # FastAPI simplificado con funciones reutilizables
│   ├── bots/
│   │   ├── bot_manager.py          # Gestor de bots
│   │   └── handlers/
│   │       ├── admin_handlers.py    # Handlers del bot admin
│   │       ├── production_handlers.py  # Handlers del bot producción
│   │       ├── file_upload_handler.py  # ✅ Handler de subida de archivos
│   │       └── file_download_handler.py # ✅ Handler de descarga de archivos
│   ├── database/
│   │   └── supabase.py              # Cliente Supabase (incluye métodos para reportes financieros y CFO)
│   ├── security/
│   │   └── auth.py                 # Autenticación y validación
│   ├── services/
│   │   ├── conversation_logger.py  # Logging de conversaciones
│   │   ├── storage_service.py      # ✅ Servicio de almacenamiento
│   │   ├── session_manager.py      # ✅ Gestión de sesiones conversacionales
│   │   └── ai_service.py           # ✅ Integración con OpenAI (Asesor IA + extracción de intención)
│   ├── decorators/
│   │   └── conversation_logging.py # Decoradores de logging
│   ├── utils/
│   │   ├── helpers.py              # Funciones helper
│   │   └── file_types.py           # ✅ Tipos de archivo (estructura jerárquica)
│   └── api/
│       └── conversation_logs.py    # Endpoints de API
├── database/
│   └── migrations/
│       ├── schema_completo.sql     # Schema base
│       ├── 001_add_campos_archivos.sql  # ✅ Campos de archivos
│       └── 002_create_sesiones_conversacion.sql  # ✅ Sesiones
├── docs/
│   ├── CONCEPTO_HISTORIAL_OPENAI.md  # ✅ Documentación de IA
│   └── RESUMEN_IMPLEMENTACION_ARCHIVOS.md  # ✅ Resumen de implementación
├── requirements.txt
├── run.py
├── .env.example
└── README.md
```

## 🔧 Funciones Reutilizables en main.py

El `main.py` está estructurado con funciones reutilizables:

### Inicialización
- `validate_configuration()` - Validar variables de entorno
- `initialize_bots()` - Inicializar bots
- `start_bots()` - Iniciar bots
- `stop_bots()` - Detener bots
- `check_supabase_connection()` - Verificar Supabase

### Endpoints
- `/health` - Health check completo
- `/status` - Estado del sistema
- `/bots/start`, `/bots/stop`, `/bots/restart` - Control de bots

## 📊 Base de Datos

### Tablas Críticas
1. **empresas** - Información de empresas
2. **usuarios** - Usuarios autorizados (con campo `rol`: super_admin, gestor, usuario)
3. **conversaciones** - Log de conversaciones
4. **usuarios_detalle** - Detalles de usuarios
5. **intentos_acceso_negado** - Seguridad

### Tablas Opcionales
6. **security_logs** - Logs de seguridad
7. **bot_analytics** - Estadísticas

### Tablas de Gestión de Archivos ✅
8. **archivos** - Archivos con clasificación completa
   - Campos: `periodo`, `categoria`, `tipo`, `subtipo`, `descripcion_personalizada`
   - Índices optimizados para búsquedas
9. **sesiones_conversacion** - Gestión de sesiones conversacionales
   - Estados: `esperando_empresa`, `esperando_categoria`, `esperando_subtipo`, `esperando_periodo`
   - Expiración automática (1 hora)

### Tablas Multiempresa y Roles ✅
10. **usuarios_empresas** - Relación muchos a muchos entre usuarios y empresas
    - Campo `rol`: Rol del usuario en esa empresa específica (super_admin, gestor, usuario)
    - Permite diferentes roles en diferentes empresas
    - Migración automática de datos existentes

## 🛠️ Desarrollo

### Testing
```bash
# Verificar configuración
python -c "from app.config import Config; Config.validate()"

# Verificar conexión Supabase
python -c "from app.database.supabase import get_supabase_client; get_supabase_client()"

# Scripts de testing (ver scripts_testing/README.md)
python3 scripts_testing/verificar_sistema_completo.py
python3 scripts_testing/revisar_estructura_supabase.py
```

### Logs
Los logs se guardan en:
- Consola (stdout)
- Archivo `aca_bot.log` (si está configurado)

## 📁 Gestión de Archivos (Actualizado 2025-11-13)

### Subida de Archivos
El usuario puede subir archivos enviando un documento al bot. El sistema guía al usuario a través de un flujo conversacional:

1. **Identificación de empresa** (automática si tiene 1, pregunta si tiene múltiples)
2. **Selección de categoría** (Legal o Financiero)
3. **Selección de subtipo** (Estatutos, F29, Reporte mensual, etc.)
4. **Descripción personalizada** (si subtipo es "Otros")
5. **Período** (mes actual, anterior, o personalizado con IA)
6. **Confirmación y registro en Supabase Storage**

**Características:**
- ✅ Sanitización de nombres de archivo (tildes → ASCII)
- ✅ Timestamp único para evitar duplicados
- ✅ Análisis de períodos con IA (fallback manual disponible)
- ✅ Sistema multi-empresa completo

### Descarga de Archivos
El usuario puede solicitar archivos mediante el botón "📊 Información" en el menú principal:

**Menú Principal:**
- 📊 Información (descarga de archivos)
- 📈 Reporte CFO
- 🤖 Asesor IA
- ℹ️ Ayuda
- 🚪 Salir

**Flujo estructurado (Actualizado 2025-11-13):**
1. Usuario presiona "📊 Información"
2. Selecciona categoría (Legal o Financiero) - **2 columnas**
3. Selecciona subtipo según categoría - **2 columnas**
4. Selecciona período (mes actual, anterior u otro con IA)
5. **Selecciona empresa (SOLO si tiene múltiples)** ← AL FINAL
6. Sistema busca archivos y muestra resultados:
   - Si 1 archivo → Muestra directamente con link de descarga
   - Si múltiples → Menú de selección (2 columnas)
7. Genera URLs firmadas (válidas 1 hora)

**Características:**
- ✅ Menús siempre en 2 columnas
- ✅ Pregunta de empresa AL FINAL (solo si tiene múltiples)
- ✅ URLs firmadas con múltiples fallbacks
- ✅ Mensajes incluyen: Categoría, Tipo, Período y Empresa
- ✅ Botones para buscar otro período si no hay resultados
- ✅ URLs firmadas con expiración de 1 hora
- ✅ No pregunta empresa si usuario tiene solo 1
- ✅ Comandos `/start` y `/cancelar` para limpiar sesiones
- ✅ Regeneración automática de URLs si expiran

### Tipos de Archivo

**Legal:**
- Estatutos empresa
- Poderes
- CI
- RUT
- Otros (con descripción)

**Financiero:**
- Reporte mensual
- Estados financieros
- Carpeta tributaria
- F29
- F22
- Otros (con descripción)

### Asesor IA
El bot incluye un asistente inteligente que puede responder preguntas sobre información financiera y reportes:

**Funcionamiento:**
1. Usuario presiona "🤖 Asesor IA" en el menú principal
2. El sistema carga automáticamente:
   - Reportes financieros del mes en curso o anterior
   - Reportes CFO disponibles
3. Usuario hace una pregunta en lenguaje natural
4. La IA analiza el contexto y responde con:
   - Respuesta basada en los reportes disponibles
   - Nivel de confianza de la respuesta
   - Fuentes utilizadas
5. Si la confianza es baja (< 30%), el sistema ofrece derivar al chat de ayuda

**Características:**
- ✅ Contexto automático de reportes financieros y CFO
- ✅ Historial conversacional (últimas 5 interacciones)
- ✅ Evaluación de confianza en respuestas
- ✅ Derivación automática a ayuda cuando es necesario
- ✅ Fuentes citadas en cada respuesta
- ✅ Comando `/cancelar` para salir de la sesión

## 📝 Notas

- **FastAPI mínimo**: Solo endpoints esenciales, sin dashboard web
- **Gestión de archivos**: ✅ Completamente implementado
- **Flujo estructurado**: Descarga mediante botones (sin lenguaje natural)
- **Menús en 2 columnas**: Todos los menús organizados uniformemente
- **Selección múltiple**: Soporte para descargar archivos individuales o todos
- **Asesor IA**: ✅ Implementado con contexto automático de reportes
- **OpenAI requerido**: Necesario para Asesor IA, opcional para descarga
- **SQL completo**: Schema con todas las tablas necesarias + migraciones
- **Funciones reutilizables**: Código modular y mantenible
- **Seguridad**: Validaciones de empresa y permisos en todas las operaciones
- **Sistema de roles**: 3 niveles (super_admin, gestor, usuario) con validaciones de permisos
- **Multiempresa**: Soporte completo para usuarios con múltiples empresas
- **URLs firmadas**: Acceso seguro con expiración automática
- **Comandos de control**: `/start` limpia sesiones, `/cancelar` cancela operaciones
- **Botones deshabilitados**: Pendientes, CxC & CxP, Agendar (no disponibles en menú principal)
- **Service Key**: Uso de SUPABASE_SERVICE_KEY para operaciones de Storage y DB (bypass RLS)

## 🆘 Soporte

- **Documentación API**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health
- **Issues**: Crear issue en el repositorio

## 📚 Documentación Adicional

- **Concepto de Historial e IA**: `docs/CONCEPTO_HISTORIAL_OPENAI.md`
- **Resumen de Implementación**: `docs/RESUMEN_IMPLEMENTACION_ARCHIVOS.md`
- **Cambios Recientes**: `docs/CAMBIOS_RECIENTES.md` ⭐ **NUEVO**
- **Plan de Implementación**: `docs/PLAN_IMPLEMENTACION_ARCHIVOS.md`
- **Multiempresa y Seguridad**: `docs/EXPLICACION_MULTIEMPRESA_SEGURIDAD.md`
- **Sistema de Roles y Permisos**: `docs/SISTEMA_ROLES_PERMISOS.md` ⭐ **NUEVO**
- **Archivos a Actualizar Multiempresa**: `docs/ARCHIVOS_ACTUALIZAR_MULTIEMPRESA.md`
- **Resumen Actualizaciones Multiempresa**: `docs/RESUMEN_ACTUALIZACIONES_MULTIEMPRESA.md`

## 🎯 Estado del Proyecto

### ✅ Completado
- Sistema de bots (Admin y Producción)
- Logging completo de conversaciones
- **Gestión de archivos (subida y descarga)**
- **Flujo estructurado con botones (sin lenguaje natural)**
- **Menús en 2 columnas**
- **Selección múltiple de archivos**
- **URLs firmadas con expiración**
- **Comandos `/start` y `/cancelar`**
- **Asesor IA con contexto automático**
- **Derivación a ayuda cuando la IA no puede responder**
- **Botón "Reporte CFO" en menú principal**
- **Sistema de roles y permisos (3 niveles)**
- **Multiempresa (usuarios con múltiples empresas)**
- **Validaciones de seguridad y permisos**
- API REST para consultas
- Sanitización de nombres de archivo
- Uso de Service Key para Storage y DB

### 🔄 En Desarrollo
- Reporte CFO (funcionalidad completa)
- Testing end-to-end
- Mejoras en prompts de IA
- Métricas y analytics

### 🚫 Deshabilitado (no disponible en menú)
- Pendientes
- CxC & CxP
- Agendar

---

**ACA 4.0** - Sistema de Bots de Telegram con Supabase  
Versión: 4.0.1  
Enfoque: Bots + Supabase + Logging + Gestión de Archivos + Asesor IA + Roles y Permisos + Multiempresa  
Última actualización: 2025-11-12


