# 🚀 CONTEXTO DEL PROYECTO - ACA 4.0

**Propósito:** Documento core para iniciar sesiones de chat  
**Última actualización:** 2024-12-05  
**Versión:** 4.1.1  
**Estado:** ✅ FUNCIONAL CON ASESOR IA, TICKETS Y OPENAI ASSISTANTS

---

## 📌 QUÉ ES ESTE PROYECTO

Sistema de bots de Telegram para gestión empresarial financiero-contable con:
- 2 bots: Admin (gestión) y Producción (usuarios finales)
- Almacenamiento en Supabase (PostgreSQL + Storage)
- Sistema multi-empresa (un usuario puede tener múltiples empresas)
- **Asesor IA con OpenAI Assistants** (búsqueda en PDFs)
- **Sistema de tickets** con ID único para seguimiento
- **Subida automática de reportes a OpenAI**

---

## ⚠️ PUNTOS CRÍTICOS - NO MODIFICAR SIN REVISAR

### **1. Cliente Supabase**
```python
# ✅ DEBE usar SERVICE_KEY (no SUPABASE_KEY)
create_client(Config.SUPABASE_URL, Config.SUPABASE_SERVICE_KEY)
```

### **2. Sistema Multi-Empresa**
```python
# ✅ SIEMPRE usar este método:
empresas = supabase.get_user_empresas(chat_id)
```

### **3. OpenAI Assistants**
```python
# ✅ Un Assistant por empresa (aislamiento de datos)
# ✅ PDFs en Vector Store por empresa
# ✅ La IA NO inventa datos - usa NO_TENGO_INFO
```

### **4. Subida automática a OpenAI**
```python
# ✅ Solo reportes: reporte_mensual, estados_financieros
# ✅ Solo archivos PDF
# ✅ Otros tipos solo van a Supabase
```

### **5. Menús en 2 columnas**
```python
# ✅ TODOS los menús deben usar 2 columnas
# ✅ Usar organizar_botones_en_columnas(botones, columnas=2)
```

---

## 📂 ESTRUCTURA DEL PROYECTO

```
aca_4/
├── app/
│   ├── bots/handlers/
│   │   ├── admin_handlers.py          ← Bot admin
│   │   ├── production_handlers.py     ← Bot producción
│   │   ├── file_upload_handler.py     ← Subida (+ OpenAI auto)
│   │   ├── file_download_handler.py   ← Descarga
│   │   └── advisor_handler.py         ← Asesor IA + Tickets
│   ├── services/
│   │   ├── storage_service.py         ← Supabase Storage
│   │   ├── ai_service.py              ← OpenAI Chat Completions
│   │   ├── openai_assistant_service.py ← Assistants API
│   │   └── session_manager.py         ← Gestión de sesiones
│   ├── security/
│   │   ├── auth.py                    ← Autenticación
│   │   └── company_guard.py           ← Validación empresa
│   ├── database/
│   │   └── supabase.py                ← Cliente Supabase
│   └── config.py                      ← Variables de entorno
├── database/migrations/
│   └── 006_openai_assistants.sql      ← Migración OpenAI
└── docs/
```

---

## 🗄️ BASE DE DATOS SUPABASE

### **Tablas Principales:**
- `empresas` - Con `openai_assistant_id`
- `usuarios` - Usuarios del sistema
- `usuarios_empresas` - Relación multi-empresa
- `archivos` - Con `openai_file_id` para PDFs en OpenAI
- `sesiones_conversacion` - Sesiones activas

### **Campos para OpenAI:**
```sql
empresas.openai_assistant_id  -- ID del Assistant
archivos.openai_file_id       -- ID del archivo en OpenAI
```

---

## 🎯 FLUJOS PRINCIPALES

### **Subida de archivos:**
```
Archivo → Empresa → Categoría → Subtipo → Período → ✅
         ↓
    Si es reporte PDF → Sube también a OpenAI
         ↓
    Muestra botón "Volver al menú"
```

### **Descarga de archivos:**
```
"📊 Información" → Categoría → Subtipo → Período → Empresa → Resultados
```

### **Asesor IA:**
```
"🤖 Asesor IA" → Selección empresa → Pregunta →
→ Busca en PDFs (OpenAI Assistants) → Responde con fuentes
→ Si no encuentra → Ofrece crear ticket
```

### **Crear Ticket:**
```
"crear ticket" o "necesito ayuda" →
→ Genera ID (TKT-YYYYMMDD-XXXX) →
→ Envía al admin via bot producción →
→ Usuario recibe confirmación con ID
```

---

## 🤖 ASESOR IA - DETALLES

### **Arquitectura:**
- 1 Assistant OpenAI por empresa
- Vector Store con PDFs indexados
- File Search para búsqueda semántica

### **Reglas de la IA:**
- ❌ PROHIBIDO inventar datos
- ❌ PROHIBIDO estimar sin fuentes
- ✅ Solo información de documentos
- ✅ Responde "NO_TENGO_INFO" si no encuentra
- ✅ Cita fuentes siempre

### **Subida automática a OpenAI:**
| Tipo | Supabase | OpenAI |
|------|----------|--------|
| reporte_mensual (PDF) | ✅ | ✅ Auto |
| estados_financieros (PDF) | ✅ | ✅ Auto |
| F29, F22, carpeta_tributaria | ✅ | ❌ |
| Legal (estatutos, CI, RUT) | ✅ | ❌ |

---

## 🎫 SISTEMA DE TICKETS

### **Cuándo se crea:**
1. IA responde "NO_TENGO_INFO"
2. Usuario escribe: "crear ticket", "necesito ayuda", "escalar"
3. Acciones prohibidas detectadas

### **Formato ID:** `TKT-YYYYMMDD-XXXX`

### **Se envía via bot producción al ADMIN_CHAT_ID**

---

## 📊 VARIABLES DE ENTORNO

```bash
# Telegram
BOT_ADMIN_TOKEN=xxx
BOT_PRODUCTION_TOKEN=xxx
ADMIN_CHAT_ID=7580149783

# Supabase
SUPABASE_URL=xxx
SUPABASE_KEY=xxx
SUPABASE_SERVICE_KEY=xxx
SUPABASE_STORAGE_BUCKET=ACA_4

# OpenAI (REQUERIDO para Asesor IA)
OPENAI_API_KEY=xxx
```

---

## 🔧 COMANDOS ÚTILES

```bash
# Iniciar
python3 run_production.py

# Detener
pkill -9 -f python

# Migrar PDFs existentes a OpenAI
python3 scripts_testing/migrar_pdfs_openai.py

# Ver logs
tail -f aca_bot.log | grep -E "(🔍|❌|🎫|Ticket)"
```

---

## ✅ FUNCIONALIDADES IMPLEMENTADAS

- ✅ Subida de archivos con clasificación
- ✅ Descarga de archivos con búsqueda
- ✅ Sistema multi-empresa
- ✅ **Asesor IA con OpenAI Assistants**
- ✅ **Sistema de tickets con ID único**
- ✅ **Subida automática de reportes PDF a OpenAI**
- ✅ **Menús en 2 columnas (todos)**
- ✅ **Botón "Volver" después de subir archivo**
- ✅ URLs firmadas con expiración
- ✅ Sistema de roles y permisos

---

## 💡 NOTAS IMPORTANTES

1. **Asesor IA usa OpenAI Assistants** - No Chat Completions
2. **Reportes PDF se suben a OpenAI automáticamente**
3. **Tickets se envían via bot producción**
4. **Todos los menús en 2 columnas**
5. **La IA NO inventa** - Responde NO_TENGO_INFO

---

**📌 Pega este documento al inicio de cada nueva sesión de chat**

---

**Última actualización:** 2024-12-05 00:10
