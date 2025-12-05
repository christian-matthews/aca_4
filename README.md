# 🚀 ACA 4.0 - Sistema de Bots de Telegram

Sistema de chatbots de Telegram para gestión empresarial financiero-contable con Supabase y OpenAI.

## ✨ Características Principales

### 🤖 **Bots de Telegram**
- **Bot Admin**: Gestión de empresas y usuarios
- **Bot Producción**: Acceso para usuarios finales

### 🔒 **Sistema de Roles**
- `super_admin`, `gestor`, `usuario`
- Permisos por empresa

### 🏢 **Multiempresa**
- Un usuario puede tener múltiples empresas
- Menús en 2 columnas para selección

### 📁 **Gestión de Archivos**
- Subida con clasificación (categoría → subtipo → período)
- Descarga con búsqueda estructurada
- Storage en Supabase con URLs firmadas

### 🤖 **Asesor IA** (OpenAI Assistants)
- Búsqueda inteligente en PDFs
- Vector Store por empresa (aislamiento)
- **NO inventa datos** - Solo información verificable
- Responde "NO_TENGO_INFO" si no encuentra

### 📤 **Subida Automática a OpenAI**
- `reporte_mensual` (PDF) → OpenAI ✅
- `estados_financieros` (PDF) → OpenAI ✅
- Otros tipos → Solo Supabase

### 🎫 **Sistema de Tickets**
- ID único: `TKT-YYYYMMDD-XXXX`
- Automático cuando IA no puede responder
- Manual: "crear ticket", "necesito ayuda"
- Envío via bot producción al admin

### 📱 **Menús Estandarizados**
- Todos los menús en **2 columnas**
- Botón "Volver" después de subir archivo

---

## 🚀 Instalación

```bash
# 1. Clonar y crear entorno
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 2. Configurar .env
cp .env.example .env
# Editar con tus credenciales

# 3. Ejecutar migraciones SQL en Supabase
# Ver database/migrations/

# 4. Iniciar
python run_production.py
```

---

## 📊 Variables de Entorno

```bash
# Telegram
BOT_ADMIN_TOKEN=xxx
BOT_PRODUCTION_TOKEN=xxx
ADMIN_CHAT_ID=xxx

# Supabase
SUPABASE_URL=xxx
SUPABASE_KEY=xxx
SUPABASE_SERVICE_KEY=xxx
SUPABASE_STORAGE_BUCKET=ACA_4

# OpenAI (REQUERIDO para Asesor IA)
OPENAI_API_KEY=xxx
```

---

## 📁 Estructura

```
aca_4/
├── app/
│   ├── bots/handlers/
│   │   ├── advisor_handler.py      ← Asesor IA + Tickets
│   │   ├── file_upload_handler.py  ← Subida + OpenAI auto
│   │   └── file_download_handler.py
│   ├── services/
│   │   ├── openai_assistant_service.py  ← Assistants API
│   │   └── storage_service.py
│   └── security/
│       └── company_guard.py
├── database/migrations/
│   └── 006_openai_assistants.sql
└── scripts_testing/
    └── migrar_pdfs_openai.py
```

---

## 🔧 Comandos Útiles

```bash
# Iniciar
python3 run_production.py

# Detener
pkill -9 -f python

# Migrar PDFs existentes a OpenAI
python3 scripts_testing/migrar_pdfs_openai.py

# Ver logs
tail -f aca_bot.log
```

---

## 🎯 Flujos Principales

### Subida de Archivos
```
Documento → Empresa → Categoría → Subtipo → Período
    ↓
Si es reporte PDF → Sube a OpenAI automáticamente
    ↓
✅ "Disponible para consultas con Asesor IA"
    ↓
[🔙 Volver al menú]
```

### Asesor IA
```
🤖 Asesor IA → Selecciona empresa → Pregunta
    ↓
Busca en PDFs (OpenAI Assistants)
    ↓
Si encuentra → Responde con fuentes
Si NO encuentra → "NO_TENGO_INFO" + [🎫 Crear ticket]
```

### Tickets
```
"crear ticket" / IA no puede responder
    ↓
Genera ID: TKT-20241205-A1B2
    ↓
Envía al admin via bot producción
    ↓
Usuario recibe confirmación con ID
```

---

## ✅ Estado del Proyecto

### Completado
- ✅ Sistema de bots (Admin + Producción)
- ✅ Gestión de archivos (subida/descarga)
- ✅ Sistema multi-empresa
- ✅ Asesor IA con OpenAI Assistants
- ✅ Sistema de tickets con ID único
- ✅ Subida automática de reportes a OpenAI
- ✅ Menús en 2 columnas
- ✅ Botón "Volver" post-subida

### Pendiente
- ⏳ Dashboard de tickets
- ⏳ Métricas y analytics

---

**ACA 4.0** - Sistema de Bots de Telegram  
Versión: 4.1.1  
Última actualización: 2024-12-05
