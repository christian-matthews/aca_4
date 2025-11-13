# 🚀 CONTEXTO DEL PROYECTO - ACA 4.0

**Propósito:** Documento core para iniciar sesiones de chat  
**Última actualización:** 2025-11-13  
**Versión:** 4.0.2  
**Estado:** ✅ FUNCIONAL Y PROBADO

---

## 📌 QUÉ ES ESTE PROYECTO

Sistema de bots de Telegram para gestión de archivos empresariales con:
- 2 bots: Admin (gestión) y Producción (usuarios finales)
- Almacenamiento en Supabase (PostgreSQL + Storage)
- Sistema multi-empresa (un usuario puede tener múltiples empresas)
- Clasificación de archivos por categoría, subtipo y período
- Análisis de períodos con IA (OpenAI, con fallback manual)

---

## ⚠️ PUNTOS CRÍTICOS - NO MODIFICAR SIN REVISAR

### **1. Cliente Supabase**
```python
# ✅ DEBE usar SERVICE_KEY (no SUPABASE_KEY)
# Archivo: app/database/supabase.py línea 19
create_client(Config.SUPABASE_URL, Config.SUPABASE_SERVICE_KEY)
```

### **2. Sistema Multi-Empresa**
```python
# ✅ SIEMPRE usar este método:
empresas = supabase.get_user_empresas(chat_id)

# ❌ NUNCA usar:
empresa_id = user.get('empresa_id')  # Solo retorna 1 empresa (legacy)
```

### **3. Orden de Preguntas en Descarga**
```
✅ CORRECTO: Categoría → Subtipo → Período → Empresa (al final, solo si tiene múltiples)
❌ INCORRECTO: Empresa → Categoría → Subtipo → Período
```

### **4. Handler de Texto**
```python
# ✅ UN SOLO handler unificado que delega según intent
# Archivo: app/bots/bot_manager.py líneas 66-89
```

### **5. Nombres de Archivo**
```python
# ✅ SIEMPRE sanitizar y agregar timestamp
# Archivo: app/services/storage_service.py
"Evaluación.pdf" → "Evaluacion_20251113_100935.pdf"
```

---

## 📂 ESTRUCTURA DEL PROYECTO

```
aca_4/
├── app/
│   ├── bots/handlers/
│   │   ├── admin_handlers.py          ← Bot admin
│   │   ├── production_handlers.py     ← Bot producción (enruta callbacks)
│   │   ├── file_upload_handler.py     ← Subida de archivos
│   │   └── file_download_handler.py   ← Descarga de archivos
│   ├── services/
│   │   ├── storage_service.py         ← Supabase Storage (CRÍTICO)
│   │   ├── ai_service.py              ← OpenAI integration
│   │   ├── session_manager.py         ← Gestión de sesiones
│   │   └── conversation_logger.py     ← Logging
│   ├── database/
│   │   └── supabase.py                ← Cliente Supabase (CRÍTICO)
│   ├── utils/
│   │   └── file_types.py              ← Tipos y categorías de archivos
│   └── config.py                      ← Variables de entorno
├── database/migrations/               ← Migraciones SQL
└── docs/                              ← Documentación
```

---

## 🗄️ BASE DE DATOS SUPABASE

### **Tablas Principales:**
- `empresas` - Empresas del sistema
- `usuarios` - Usuarios (con empresa_id legacy)
- **`usuarios_empresas`** ← Multi-empresa (muchos a muchos)
- **`archivos`** ← Archivos subidos (23 campos)
- `sesiones_conversacion` - Sesiones activas
- `conversaciones` - Historial
- `reportes_mensuales` - Reportes CFO

### **Tabla archivos - Campos importantes:**
```sql
- empresa_id (UUID)
- categoria ('legal' o 'financiero')
- subtipo ('estatutos_empresa', 'f29', 'reporte_mensual', etc.)
- periodo (VARCHAR(7)) - Formato YYYY-MM
- mime_type (VARCHAR) ← NO "tipo_archivo"
- nombre_archivo (VARCHAR) ← Con timestamp único
- nombre_original (VARCHAR) ← Nombre original del usuario
- storage_path (TEXT)
```

---

## 🎯 FLUJOS PRINCIPALES

### **Subida:**
```
Archivo → Empresa (si múltiples) → Categoría → Subtipo → Descripción (si Otros) → Período → ✅
```

### **Descarga:**
```
"📊 Información" → Categoría → Subtipo → Período → Empresa (si múltiples, AL FINAL) → Resultados
```

### **Agregar Usuario:**
```
/adduser CHAT_ID NOMBRE ROL RUT_EMPRESA
Ejemplo: /adduser 123456789 "Juan Perez" user 76142021-6
```

---

## 📋 CATEGORÍAS Y SUBTIPOS

### **Legal (⚖️):**
- estatutos_empresa, poderes, ci, rut, otros

### **Financiero (💰):**
- reporte_mensual, estados_financieros, carpeta_tributaria, f29, f22, otros

**Archivo:** `app/utils/file_types.py`

---

## 👥 USUARIOS DE PRUEBA

### **The Wingman:**
- Chat ID: 7580149783
- Rol: super_admin
- **Empresas: 2** (Empresa de Prueba ACA, Factor IT)

### **Christian Matthews:**
- Chat ID: 866310278
- Rol: super_admin
- **Empresas: 2**

---

## 🔧 COMANDOS ÚTILES

### **Iniciar/Detener:**
```bash
# Iniciar
python3 run.py

# Detener
lsof -ti:8000 | xargs kill -9
pkill -f "python.*run.py"
```

### **Ver logs en tiempo real:**
```bash
tail -f aca_bot.log | grep -E "(🔍|📋|❌|ERROR)"
```

### **Scripts de testing:**
```bash
# Ver estructura de Supabase
python3 scripts_testing/revisar_estructura_supabase.py

# Verificar sistema completo
python3 scripts_testing/verificar_sistema_completo.py

# Ver todos los scripts disponibles
ls scripts_testing/
```
**Documentación:** `scripts_testing/README.md`

---

## 📚 DOCUMENTACIÓN CLAVE

**LEER PRIMERO:**
1. **docs/NO_OLVIDAR.md** ⚠️ Puntos críticos
2. **docs/ESTADO_ACTUAL_SISTEMA.md** - Estado completo
3. **docs/REFERENCIA_RAPIDA.md** - Comandos rápidos

**Para debugging:**
4. **docs/CAMBIOS_2025-11-13.md** - Problemas resueltos hoy
5. **docs/LOGICA_DESCARGA_EMPRESA.md** - Flujo de empresas

**Índice completo:**
6. **docs/INDEX.md** - Índice de toda la documentación

---

## ⚡ CAMBIOS RECIENTES (2025-11-13)

### **14 problemas resueltos:**
1. ✅ RLS bloqueando operaciones → Usar SERVICE_KEY
2. ✅ Sistema multi-empresa no funcionaba → Corregido método
3. ✅ Callbacks no se enrutaban → Agregado enrutamiento
4. ✅ Handlers de texto se interceptaban → Handler unificado
5. ✅ Nombres con tildes → Sanitización mejorada
6. ✅ Archivos duplicados → Timestamp único
7. ✅ Pregunta empresa al inicio → Movida al final
8. ✅ Errores de indentación → Corregidos todos
9. ✅ Import redundante security → Eliminado
10. ✅ Comando /adduser complejo → Simplificado con RUT
11. ✅ Campo Empresa no aparecía → Agregado en mensajes
12. ✅ URLs no se mostraban → Manejo robusto
13. ✅ Error al confirmar subida → Detectar Message vs CallbackQuery
14. ✅ Menús no estandarizados → Todos en 2 columnas

---

## 🚨 AL INICIO DE CADA SESIÓN

### **Verificar:**
1. ✅ Leer **docs/NO_OLVIDAR.md**
2. ✅ Leer **docs/ESTADO_ACTUAL_SISTEMA.md**
3. ✅ Revisar últimos cambios en **docs/CAMBIOS_*.md**
4. ✅ NO asumir comportamientos sin verificar código actual
5. ✅ NO modificar puntos críticos sin revisar documentación

### **Antes de hacer cambios:**
1. ✅ Revisar checklist en **docs/NO_OLVIDAR.md**
2. ✅ Verificar que el cambio no rompe puntos críticos
3. ✅ Actualizar documentación después del cambio

---

## 📊 ESTADO ACTUAL

**Funcionalidades:**
- ✅ Subida de archivos: FUNCIONAL
- ✅ Descarga de archivos: FUNCIONAL
- ✅ Sistema multi-empresa: FUNCIONAL
- ✅ Análisis períodos con IA: FUNCIONAL (con fallback)
- ✅ Comando /adduser: FUNCIONAL
- ⏳ Validaciones de permisos: PENDIENTE
- ⏳ URLs firmadas: FUNCIONAL (pendiente verificar formato exacto)

**Problemas conocidos:**
- Ninguno crítico actualmente
- Logs agregados para debugging de URLs

**Última prueba:**
- Fecha: 2025-11-13 10:15
- Usuario: The Wingman
- Resultado: Sistema funcionando correctamente

---

## 🔗 ENLACES ÚTILES

- **Supabase Dashboard:** [https://gggfxcgiabwubfedzffp.supabase.co](https://gggfxcgiabwubfedzffp.supabase.co)
- **API Health:** http://localhost:8000/health
- **API Docs:** http://localhost:8000/docs

---

## 💡 NOTAS IMPORTANTES

1. **El sistema está FUNCIONAL** - No reescribir código que funciona
2. **Service Key es OBLIGATORIO** - No cambiar a anon key
3. **Empresa se pregunta AL FINAL** - Es por diseño, no error
4. **Handler unificado de texto** - No separar en múltiples handlers
5. **Documentación está ACTUALIZADA** - Confiar en docs/NO_OLVIDAR.md

---

**📌 Pega este documento al inicio de cada nueva sesión de chat para mantener contexto**

---

**Última actualización:** 2025-11-13 10:25

