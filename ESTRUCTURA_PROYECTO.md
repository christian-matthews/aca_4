# 📁 Estructura del Proyecto - ACA 4.0

**Fecha:** 2025-11-13  
**Propósito:** Mapa completo del proyecto organizado

---

## 🌳 ÁRBOL DE DIRECTORIOS

```
aca_4/
│
├── 📄 CONTEXTO_PROYECTO.md           ← 🎯 DOCUMENTO CORE (usar al inicio de cada sesión)
├── 📄 ESTRUCTURA_PROYECTO.md         ← Este archivo
├── 📄 README.md                       ← README principal
├── 📄 requirements.txt                ← Dependencias Python
├── 📄 run.py                          ← Punto de entrada principal
├── 📄 start.sh                        ← Script de inicio
├── 📄 aca_bot.log                     ← Logs del sistema
│
├── 📂 app/                            ← Código principal de la aplicación
│   ├── __init__.py
│   ├── config.py                      ← ⚙️ Configuración (variables de entorno)
│   ├── main.py                        ← FastAPI app y startup
│   │
│   ├── 📂 bots/
│   │   ├── bot_manager.py             ← 🔧 Registro de handlers (CRÍTICO)
│   │   └── handlers/
│   │       ├── admin_handlers.py      ← Bot admin
│   │       ├── production_handlers.py ← Bot producción (enruta callbacks)
│   │       ├── file_upload_handler.py ← Subida de archivos
│   │       └── file_download_handler.py ← Descarga de archivos
│   │
│   ├── 📂 services/
│   │   ├── storage_service.py         ← 💾 Supabase Storage (CRÍTICO)
│   │   ├── ai_service.py              ← 🤖 OpenAI integration
│   │   ├── session_manager.py         ← Gestión de sesiones
│   │   └── conversation_logger.py     ← Logging de conversaciones
│   │
│   ├── 📂 database/
│   │   └── supabase.py                ← 🗄️ Cliente Supabase (CRÍTICO)
│   │
│   ├── 📂 security/
│   │   └── auth.py                    ← 🔐 Autenticación y autorización
│   │
│   ├── 📂 decorators/
│   │   └── conversation_logging.py    ← Decoradores de logging
│   │
│   ├── 📂 utils/
│   │   ├── file_types.py              ← 📋 Tipos de archivo (categorías/subtipos)
│   │   └── helpers.py                 ← Funciones auxiliares
│   │
│   └── 📂 api/
│       └── conversation_logs.py       ← API REST endpoints
│
├── 📂 database/
│   └── migrations/                    ← Migraciones SQL
│       ├── schema_completo.sql        ← Schema base
│       ├── 001_add_campos_archivos.sql ← Campos para archivos
│       ├── 002_create_sesiones_conversacion.sql ← Sesiones
│       ├── 003_create_usuarios_empresas.sql ← Multi-empresa
│       ├── 004_sistema_roles_permisos.sql ← Roles (opcional)
│       └── 005_create_reportes_mensuales.sql ← Reportes CFO
│
├── 📂 scripts_testing/                ← 🧪 Scripts de testing y utilidades
│   ├── README.md                      ← Documentación de scripts
│   ├── revisar_estructura_supabase.py
│   ├── verificar_sistema_completo.py
│   ├── verificar_archivos.py
│   ├── verificar_bd.py
│   ├── verificar_sesiones.py
│   ├── asignar_roles_usuarios.py
│   ├── asociar_empresa_usuario.py
│   ├── crear_empresa_factorit.py
│   ├── diagnosticar_comando_empresa.py
│   ├── ejecutar_migracion_roles.py
│   ├── revisar_cambios_supabase.py
│   ├── revisar_variables_bd.py
│   └── test_completo_sistema.py
│
├── 📂 docs/                           ← 📚 Documentación completa
│   ├── INDEX.md                       ← Índice de documentación
│   ├── NO_OLVIDAR.md                  ← ⚠️ Puntos críticos (LEER SIEMPRE)
│   ├── ESTADO_ACTUAL_SISTEMA.md       ← Estado completo del sistema
│   ├── REFERENCIA_RAPIDA.md           ← Guía rápida
│   ├── CAMBIOS_2025-11-13.md          ← Log de cambios de hoy
│   ├── LOGICA_DESCARGA_EMPRESA.md     ← Flujo de descarga detallado
│   ├── ESTRUCTURA_REAL_SUPABASE.md    ← Estructura de BD verificada
│   ├── PENDIENTES_ACTUALIZADOS.md     ← Tareas pendientes
│   └── [25+ documentos más...]        ← Ver INDEX.md para lista completa
│
└── 📂 venv/                           ← Entorno virtual Python
```

---

## 📌 ARCHIVOS CORE (Más importantes)

### **🎯 Para iniciar sesiones:**
1. **`CONTEXTO_PROYECTO.md`** - Pegar al inicio de cada chat
2. **`docs/NO_OLVIDAR.md`** - Puntos críticos
3. **`docs/INDEX.md`** - Navegación de documentación

### **⚙️ Configuración:**
4. **`app/config.py`** - Variables de entorno
5. **`run.py`** - Punto de entrada
6. **`requirements.txt`** - Dependencias

### **🔧 Lógica crítica:**
7. **`app/database/supabase.py`** - Cliente Supabase (usa SERVICE_KEY)
8. **`app/bots/bot_manager.py`** - Registro de handlers
9. **`app/services/storage_service.py`** - Gestión de Storage
10. **`app/utils/file_types.py`** - Categorías y subtipos

### **🤖 Handlers principales:**
11. **`app/bots/handlers/production_handlers.py`** - Enrutamiento
12. **`app/bots/handlers/file_upload_handler.py`** - Subida
13. **`app/bots/handlers/file_download_handler.py`** - Descarga
14. **`app/bots/handlers/admin_handlers.py`** - Administración

---

## 📂 ORGANIZACIÓN POR FUNCIÓN

### **Sistema de Bots:**
```
app/bots/
├── bot_manager.py              ← Registro y configuración de handlers
└── handlers/
    ├── production_handlers.py  ← Enrutamiento de callbacks
    ├── admin_handlers.py       ← Bot de administración
    ├── file_upload_handler.py  ← Flujo de subida
    └── file_download_handler.py ← Flujo de descarga
```

### **Servicios:**
```
app/services/
├── storage_service.py          ← Supabase Storage (sanitización, timestamps)
├── ai_service.py               ← OpenAI (análisis de períodos)
├── session_manager.py          ← Gestión de sesiones
└── conversation_logger.py      ← Logging
```

### **Base de Datos:**
```
app/database/
└── supabase.py                 ← Cliente (SERVICE_KEY, multi-empresa)

database/migrations/
├── schema_completo.sql         ← Schema base
├── 001_add_campos_archivos.sql ← +8 campos a archivos
├── 002_create_sesiones_conversacion.sql
├── 003_create_usuarios_empresas.sql ← Multi-empresa
├── 004_sistema_roles_permisos.sql
└── 005_create_reportes_mensuales.sql
```

### **Testing y Utilidades:**
```
scripts_testing/
├── README.md                   ← Documentación de scripts
├── verificar_*.py              ← Scripts de verificación
├── revisar_*.py                ← Scripts de revisión
├── asignar_*.py                ← Scripts de administración
└── test_*.py                   ← Scripts de testing
```

### **Documentación:**
```
docs/
├── INDEX.md                    ← Índice completo
├── NO_OLVIDAR.md              ← ⚠️ Puntos críticos
├── ESTADO_ACTUAL_SISTEMA.md   ← Estado completo
├── REFERENCIA_RAPIDA.md       ← Guía rápida
├── CAMBIOS_2025-11-13.md      ← Log de cambios
└── [22+ documentos más...]    ← Ver INDEX.md
```

---

## 🔍 DÓNDE ESTÁ CADA COSA

### **¿Dónde se maneja...?**

**Callbacks de botones:**
- Enrutamiento → `production_handlers.py` handle_callback()
- Descarga → `file_download_handler.py` handle_download_callback()
- Subida → `file_upload_handler.py` handle_upload_callback()

**Texto del usuario:**
- Handler unificado → `bot_manager.py` unified_text_handler()
- Delegación por intent de sesión

**Gestión de archivos:**
- Upload a Storage → `storage_service.py` upload_file()
- Download de Storage → `storage_service.py` download_file()
- URLs firmadas → `storage_service.py` get_file_url()

**Base de datos:**
- Cliente → `supabase.py`
- Queries → Métodos en `supabase.py`
- Multi-empresa → `supabase.py` get_user_empresas()

**Tipos de archivo:**
- Categorías y subtipos → `file_types.py` TIPOS_ARCHIVO
- Validaciones → `file_types.py` validar_categoria(), validar_subtipo()
- Botones → `file_types.py` get_botones_categorias(), get_botones_subtipos()

**Sesiones:**
- CRUD → `session_manager.py`
- Estados posibles → `docs/PROCESO_GESTION_ARCHIVOS.md`

---

## 🎨 PATRONES DE CÓDIGO

### **Detectar Message vs CallbackQuery:**
```python
is_callback = hasattr(message_or_query, 'edit_message_text')

if is_callback:
    await message_or_query.edit_message_text(text)
else:
    await message_or_query.reply_text(text)
```

### **Obtener empresas del usuario:**
```python
empresas = supabase.get_user_empresas(chat_id)  # Retorna lista
```

### **Organizar menú en 2 columnas:**
```python
from app.utils.file_types import organizar_botones_en_columnas

keyboard = organizar_botones_en_columnas(botones, columnas=2)
```

### **Sanitizar nombre de archivo:**
```python
safe_filename = self._sanitize_filename(filename)
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
unique_filename = f"{name}_{timestamp}.{ext}"
```

---

## 🚨 ERRORES COMUNES Y SOLUCIONES

### **"RLS policy violation"**
→ Cliente usa SUPABASE_KEY en vez de SUPABASE_SERVICE_KEY

### **"Usuario tiene 1 empresa" pero debería tener 2**
→ Método usa `user.get('empresa_id')` en vez de `get_user_empresas()`

### **"No pregunta por empresa"**
→ Es correcto si usuario tiene solo 1 empresa

### **"Callback no se maneja"**
→ Falta enrutamiento en `production_handlers.py`

### **"Texto no se procesa"**
→ Handler general intercepta antes que handler de sesión

---

## 📊 ESTADO ACTUAL (2025-11-13)

**✅ Funcionando:**
- Subida de archivos
- Descarga de archivos
- Sistema multi-empresa
- Análisis de períodos con IA
- Comando /adduser simplificado
- Menús en 2 columnas
- Comandos de control

**⚠️ En verificación:**
- URLs firmadas (logs agregados para debugging)

**⏳ Pendiente:**
- Validaciones de permisos en handlers
- Testing end-to-end completo

---

## 🔗 NAVEGACIÓN RÁPIDA

**Inicio de sesión:** `CONTEXTO_PROYECTO.md`  
**Puntos críticos:** `docs/NO_OLVIDAR.md`  
**Estado actual:** `docs/ESTADO_ACTUAL_SISTEMA.md`  
**Comandos rápidos:** `docs/REFERENCIA_RAPIDA.md`  
**Scripts testing:** `scripts_testing/README.md`  
**Índice completo:** `docs/INDEX.md`

---

**Última actualización:** 2025-11-13



