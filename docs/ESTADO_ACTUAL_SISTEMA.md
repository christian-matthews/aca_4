# 📊 Estado Actual del Sistema - ACA 4.0

**Fecha actualización:** 2025-11-13  
**Versión:** 4.0.2  
**Estado:** ✅ **FUNCIONAL Y PROBADO**

---

## 🎯 RESUMEN EJECUTIVO

Sistema de gestión de archivos funcionando correctamente con:
- ✅ Subida y descarga de archivos
- ✅ Sistema multi-empresa
- ✅ Análisis de períodos con IA (con fallback manual)
- ✅ URLs firmadas de Supabase Storage
- ✅ Clasificación completa por categoría, subtipo y período
- ✅ Comando /adduser simplificado

---

## 🗄️ BASE DE DATOS

### **Tablas Principales:**

1. **empresas** - Empresas registradas
2. **usuarios** - Usuarios del sistema (con empresa_id legacy)
3. **usuarios_empresas** - Relación muchos a muchos (sistema multi-empresa)
4. **archivos** - Archivos subidos con clasificación completa
5. **sesiones_conversacion** - Sesiones activas de subida/descarga
6. **conversaciones** - Historial de conversaciones
7. **usuarios_detalle** - Información detallada de todos los usuarios
8. **intentos_acceso_negado** - Registro de intentos no autorizados
9. **reportes_mensuales** - Reportes mensuales CFO

### **Tabla archivos - Campos:**

```sql
- id (UUID)
- chat_id (BIGINT)
- empresa_id (UUID FK)
- nombre_archivo (VARCHAR) - Nombre sanitizado con timestamp
- nombre_original (VARCHAR) - Nombre original del archivo
- mime_type (VARCHAR) - Tipo MIME del archivo
- extension (VARCHAR)
- tamaño_bytes (BIGINT)
- url_archivo (TEXT)
- storage_provider (VARCHAR)
- storage_path (TEXT)
- descripcion (TEXT)
- metadata (JSONB)
- activo (BOOLEAN)
- periodo (VARCHAR(7)) - Formato YYYY-MM
- categoria (VARCHAR(50)) - 'legal' o 'financiero'
- tipo (VARCHAR(50))
- subtipo (VARCHAR(100))
- descripcion_personalizada (TEXT)
- usuario_subio_id (UUID FK)
- fecha_documento (DATE)
- created_at (TIMESTAMPTZ)
- updated_at (TIMESTAMPTZ)
```

---

## 🔑 CONFIGURACIÓN CRÍTICA

### **Cliente Supabase:**
```python
# ✅ CORRECTO: Usa SERVICE_KEY para bypasear RLS
create_client(Config.SUPABASE_URL, Config.SUPABASE_SERVICE_KEY)
```

### **Variables de entorno requeridas:**
- BOT_ADMIN_TOKEN
- BOT_PRODUCTION_TOKEN
- ADMIN_CHAT_ID
- SUPABASE_URL
- **SUPABASE_SERVICE_KEY** ← CRÍTICO para operaciones de backend
- SUPABASE_STORAGE_BUCKET
- OPENAI_API_KEY (opcional)

---

## 📤 FLUJO DE SUBIDA DE ARCHIVOS

### **Orden de preguntas:**
1. Identificar empresa (auto si tiene 1, preguntar si tiene múltiples)
2. Categoría (Legal/Financiero)
3. Subtipo (RUT, F29, Estatutos, etc.)
4. Descripción (solo si subtipo = "Otros")
5. Período (Mes actual/anterior/otro)
6. Subir archivo

### **Archivos involucrados:**
- `app/bots/handlers/file_upload_handler.py`
- `app/services/storage_service.py`
- `app/utils/file_types.py`

### **Callbacks:**
- `upload_categoria_*`
- `upload_subtipo_*`
- `upload_periodo_*`
- `upload_empresa_*`
- `upload_cancelar`

---

## 📥 FLUJO DE DESCARGA DE ARCHIVOS

### **Orden de preguntas (ACTUALIZADO 2025-11-13):**
1. Categoría (Legal/Financiero)
2. Subtipo (RUT, F29, Estatutos, etc.)
3. Período (Mes actual/anterior/otro)
4. **Empresa (SOLO si tiene múltiples empresas)** ← AL FINAL
5. Buscar y mostrar archivos

### **Archivos involucrados:**
- `app/bots/handlers/file_download_handler.py`
- `app/services/storage_service.py`
- `app/utils/file_types.py`

### **Callbacks:**
- `download_categoria_*`
- `download_subtipo_*`
- `download_periodo_*`
- `download_empresa_*` ← Solo si tiene múltiples empresas
- `download_cancelar`
- `download_buscar_otro_periodo`
- `download_volver_menu`

---

## 🤖 COMANDO /adduser SIMPLIFICADO

### **Formato:**
```
/adduser CHAT_ID NOMBRE ROL RUT_EMPRESA
```

### **Ejemplo:**
```
/adduser 123456789 Juan Perez user 76142021-6
```

### **Parámetros:**
- **CHAT_ID:** ID del chat de Telegram (número)
- **NOMBRE:** Nombre del usuario (puede contener espacios)
- **ROL:** `super_admin`, `gestor`, o `user`
- **RUT_EMPRESA:** RUT de la empresa con guión (busca empresa por RUT)

### **Roles:**
- `super_admin` - Todos los permisos
- `gestor` - Puede subir y bajar archivos
- `user` - Solo puede bajar archivos

### **Lo que hace:**
1. Busca empresa por RUT (en vez de UUID)
2. Crea o actualiza usuario en tabla `usuarios`
3. Asocia usuario a empresa en tabla `usuarios_empresas`
4. Asigna el rol especificado

---

## 🔄 SISTEMA MULTI-EMPRESA

### **Implementación:**

**Tabla usuarios_empresas:**
```sql
- id (UUID)
- usuario_id (UUID FK a usuarios)
- empresa_id (UUID FK a empresas)
- rol (VARCHAR) - Rol específico en esa empresa
- activo (BOOLEAN)
```

**Método correcto para obtener empresas:**
```python
# ✅ CORRECTO
empresas = supabase.get_user_empresas(chat_id)
# Retorna TODAS las empresas del usuario desde usuarios_empresas

# ❌ INCORRECTO (legacy)
empresa_id = user.get('empresa_id')
# Solo retorna 1 empresa del campo legacy
```

**Archivos con método correcto:**
- ✅ `app/bots/handlers/file_upload_handler.py` - Línea 115-123
- ✅ `app/bots/handlers/file_download_handler.py` - Línea 111-118
- ✅ `app/database/supabase.py` - Método `get_user_empresas()`

---

## 📁 GESTIÓN DE NOMBRES DE ARCHIVO

### **Sanitización:**
```python
# Proceso:
1. Normalizar Unicode (tildes, ñ → ASCII)
2. Reemplazar espacios por guiones bajos
3. Eliminar caracteres especiales
4. Agregar timestamp único

# Ejemplo:
"Evaluación desempeño.pdf" → "Evaluacion_desempeno_20251113_094500.pdf"
```

### **Por qué es necesario:**
- Evita errores `InvalidKey` en Supabase Storage
- Evita errores `Duplicate` al subir mismo archivo múltiples veces
- Mantiene trazabilidad con nombre original en BD

---

## 🔗 GENERACIÓN DE URLs

### **Método:**
```python
# 1. Intentar URL firmada (expira en 1 hora)
signed_response = storage.create_signed_url(path, expires_in=3600)

# Puede retornar:
# - Dict: {'signedURL': 'url...'}
# - String: 'url...'

# 2. Fallback: URL pública
public_url = storage.get_public_url(path)

# 3. Último fallback: URL almacenada en BD
url_archivo
```

### **Formato de respuesta de create_signed_url:**
- Puede ser `dict` con key `signedURL`, `signedUrl` o `url`
- Puede ser `string` directamente
- El código maneja ambos casos

---

## 🎨 FORMATO DE MENÚS

### **Todos los menús en 2 COLUMNAS:**

Función helper:
```python
from app.utils.file_types import organizar_botones_en_columnas

botones = [btn1, btn2, btn3, btn4]
keyboard = organizar_botones_en_columnas(botones, columnas=2)
# Resultado:
# [[btn1, btn2],
#  [btn3, btn4]]
```

**Menús estandarizados:**
- ✅ Categorías (Legal/Financiero)
- ✅ Subtipos (según categoría)
- ✅ Empresas (si tiene múltiples)
- ✅ Selección múltiple de archivos

---

## 🔍 ORDEN DE HANDLERS DE TEXTO

### **Handler Unificado:**

El bot usa un handler unificado que delega según el `intent` de la sesión:

```python
if session:
    intent = session.get('intent')
    if intent == 'descargar_archivo':
        await FileDownloadHandler.handle_text_during_download(...)
    elif intent == 'subir_archivo':
        await FileUploadHandler.handle_text_during_upload(...)
else:
    await ProductionHandlers.handle_message(...)
```

**Por qué es necesario:**
- Evita que handlers de descarga intercepten mensajes de subida
- Evita que handlers de subida intercepten mensajes de descarga
- Mantiene el flujo correcto según la sesión activa

---

## 🧪 ANÁLISIS DE PERÍODOS CON IA

### **Cuando usuario selecciona "Otro mes":**

```python
# Estado de sesión: esperando_periodo_texto_ia

# 1. Intentar con OpenAI (si está disponible)
periodo_result = await ai_service.extract_periodo_from_text(mensaje)

# 2. Fallback manual si no hay OpenAI
periodo_result = ai_service._parse_periodo_manual(mensaje)

# Maneja:
- "mayo 2024" → "2024-05"
- "febrero del año pasado" → "2024-02"
- "el mes pasado" → "2025-10"
- "2024-05" → "2024-05"
```

### **Confianza:**
- Si confianza >= 0.75: Usa período directamente
- Si confianza < 0.75: Pide confirmación al usuario

---

## 📝 MENSAJES DE RESULTADO

### **Cuando SE encuentra archivo:**
```
✅ Archivo encontrado

📂 Categoría: ⚖️ Legales
📄 Tipo: Estatutos empresa
📅 Período: 2025-11
🏢 Empresa: Empresa de Prueba ACA

📎 Descarga: [nombre_archivo.pdf](URL_firmada)
```

### **Cuando NO se encuentra archivo:**
```
❌ No se encontraron archivos

📂 Categoría: ⚖️ Legales
📄 Tipo: Estatutos empresa
📅 Período: 2025-11
🏢 Empresa: Empresa de Prueba ACA

¿Quieres buscar en otro período?

[Botones]
• ✅ Sí, buscar otro período
• 🔙 Volver al menú
```

---

## ⚙️ COMANDOS DE CONTROL

### **Comandos que cancelan procesos en curso:**

**`/start`:**
- Cancela cualquier sesión activa (subida o descarga)
- Muestra menú principal

**Botón "Salir":**
- Cancela cualquier sesión activa
- Muestra mensaje de despedida

**Botón "Cancelar" (en cualquier flujo):**
- Cancela sesión actual
- Vuelve al menú principal

---

## 🐛 PROBLEMAS RESUELTOS (2025-11-13)

### **1. RLS bloqueaba operaciones:**
- ✅ Cambiado cliente a usar `SUPABASE_SERVICE_KEY`

### **2. Callbacks de descarga no se manejaban:**
- ✅ Agregado enrutamiento en `ProductionHandlers.handle_callback`

### **3. Callbacks de subida no se manejaban:**
- ✅ Agregado enrutamiento en `ProductionHandlers.handle_callback`

### **4. Entrada de texto no funcionaba:**
- ✅ Creado handler unificado que delega según intent

### **5. Nombres con tildes causaban error:**
- ✅ Mejorado método `_sanitize_filename()`

### **6. Archivos duplicados causaban error 409:**
- ✅ Agregado timestamp único a nombres de archivo

### **7. Sistema multi-empresa no funcionaba:**
- ✅ Corregido `_get_user_empresas()` en ambos handlers

### **8. Pregunta de empresa al inicio:**
- ✅ Movida pregunta al FINAL (después de categoría, subtipo y período)

### **9. Error al confirmar subida:**
- ✅ Corregido manejo de Message vs CallbackQuery

### **10. Campo "Empresa" no aparecía en mensajes:**
- ✅ Agregado en todos los mensajes de resultados

---

## 📋 ARCHIVOS MODIFICADOS HOY

### **Handlers:**
1. `app/bots/handlers/production_handlers.py`
   - Conectado menú Información con FileDownloadHandler
   - Agregado enrutamiento de callbacks upload_* y download_*
   - /start y Salir cancelan sesiones activas

2. `app/bots/handlers/file_download_handler.py`
   - Sistema multi-empresa correcto
   - Pregunta empresa al FINAL
   - Mensajes con campo Empresa
   - Botones en 2 columnas

3. `app/bots/handlers/file_upload_handler.py`
   - Sistema multi-empresa correcto
   - Manejo correcto de Message vs CallbackQuery
   - Botones en 2 columnas

4. `app/bots/handlers/admin_handlers.py`
   - Comando /adduser simplificado
   - Acepta RUT en lugar de UUID

### **Servicios:**
5. `app/services/storage_service.py`
   - Parámetros completos en upload_file()
   - Sanitización mejorada de nombres
   - Timestamp único en nombres
   - Manejo robusto de URLs firmadas

6. `app/services/ai_service.py`
   - Método extract_periodo_from_text()
   - Fallback manual _parse_periodo_manual()
   - Detección de "año pasado"

7. `app/database/supabase.py`
   - Usa SUPABASE_SERVICE_KEY (bypasea RLS)

### **Bot Manager:**
8. `app/bots/bot_manager.py`
   - Handler unificado de texto
   - Delegación según intent de sesión

---

## 🚀 CÓMO USAR EL SISTEMA

### **Subir archivos:**
1. Enviar archivo al bot
2. Seleccionar empresa (si tiene múltiples)
3. Seleccionar categoría
4. Seleccionar subtipo
5. Si es "Otros": escribir descripción
6. Seleccionar período
7. ✅ Archivo subido

### **Descargar archivos:**
1. Presionar "📊 Información"
2. Seleccionar categoría
3. Seleccionar subtipo
4. Seleccionar período
5. Seleccionar empresa (si tiene múltiples) ← AL FINAL
6. Ver/descargar archivos

### **Agregar usuarios:**
```bash
/adduser 123456789 "Juan Perez" user 76142021-6
```

---

## ✅ VERIFICACIÓN FUNCIONAL

### **Pruebas realizadas:**
- ✅ Subida de archivos con tildes en nombre
- ✅ Descarga con usuario multi-empresa
- ✅ Análisis de períodos con IA fallback
- ✅ Comando /adduser con RUT
- ✅ Menús en 2 columnas
- ✅ Cancelación de procesos con /start y Salir

### **Usuarios de prueba:**
1. **The Wingman** (7580149783)
   - Rol: super_admin
   - Empresas: 2 (Empresa de Prueba ACA, Factor IT)

2. **Christian Matthews** (866310278)
   - Rol: super_admin
   - Empresas: 2

---

## 📚 DOCUMENTACIÓN ACTUALIZADA

- ✅ ESTADO_ACTUAL_SISTEMA.md (este archivo)
- ✅ LOGICA_DESCARGA_EMPRESA.md
- ✅ ESTRUCTURA_REAL_SUPABASE.md
- ✅ RESUMEN_CORRECCIONES_CODIGO.md
- ✅ COMPARACION_MENU_INFORMACION.md
- ✅ CORRECCION_MENU_INFORMACION.md

---

**Última actualización:** 2025-11-13 10:15



