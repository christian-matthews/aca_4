# 📋 Archivos a Actualizar para Multiempresa con Seguridad

## 🔒 Principios de Seguridad

1. **Validación de acceso**: Usuario solo puede acceder a empresas a las que pertenece
2. **Filtrado automático**: Todas las consultas deben filtrar por empresas del usuario
3. **Validación en operaciones**: Verificar acceso antes de subir/descargar/modificar

---

## 📁 Archivos Críticos a Actualizar

### 1. **app/database/supabase.py** ⚠️ CRÍTICO
**Cambios necesarios:**
- ✅ Agregar método `get_user_empresas(chat_id)` - Consultar tabla `usuarios_empresas`
- ✅ Agregar método `user_has_access_to_empresa(chat_id, empresa_id)` - Validar acceso
- ⚠️ Actualizar métodos que filtran por `empresa_id` para validar acceso:
  - `get_reportes_financieros()` - Validar que empresa_id pertenece al usuario
  - `get_reportes_cfo()` - Validar que empresa_id pertenece al usuario
  - `get_empresa_data()` - Validar acceso antes de retornar datos

**Seguridad:**
- Todos los métodos que reciben `empresa_id` deben validar que el usuario tiene acceso

---

### 2. **app/security/auth.py** ⚠️ CRÍTICO
**Cambios necesarios:**
- ✅ Actualizar `validate_user()` para retornar lista de empresas
- ✅ Agregar método `user_has_access_to_empresa(chat_id, empresa_id)` - Validar acceso específico
- ✅ Agregar método `get_user_empresas(chat_id)` - Obtener todas las empresas del usuario

**Seguridad:**
- Validar que usuario tiene al menos una empresa activa
- Retornar lista de empresas en lugar de una sola

---

### 3. **app/bots/handlers/file_upload_handler.py** ⚠️ CRÍTICO
**Cambios necesarios:**
- ✅ Actualizar `_get_user_empresas()` - Consultar tabla `usuarios_empresas`
- ✅ Validar acceso antes de subir archivo (verificar que empresa_id pertenece al usuario)
- ✅ En callback `upload_empresa_*` - Validar que empresa_id pertenece al usuario

**Seguridad:**
- **CRÍTICO**: Validar que `empresa_id` en sesión pertenece al usuario antes de subir
- No permitir subir archivos a empresas no asociadas

---

### 4. **app/bots/handlers/file_download_handler.py** ⚠️ CRÍTICO
**Cambios necesarios:**
- ✅ Actualizar `_get_user_empresas()` - Consultar tabla `usuarios_empresas`
- ✅ Validar acceso antes de descargar archivo
- ✅ Filtrar búsquedas por empresas del usuario (usar `IN` con lista de empresa_ids)
- ✅ En callback `download_empresa_*` - Validar que empresa_id pertenece al usuario

**Seguridad:**
- **CRÍTICO**: Validar que archivo pertenece a empresa del usuario antes de descargar
- **CRÍTICO**: Filtrar búsquedas solo por empresas del usuario (no todas las empresas)

---

### 5. **app/bots/handlers/production_handlers.py** ⚠️ IMPORTANTE
**Cambios necesarios:**
- ✅ Actualizar para usar lista de empresas en lugar de una sola
- ✅ Validar acceso en operaciones que usan `user_data['empresa_id']`
- ⚠️ Métodos afectados:
  - `_handle_mes_reporte()` - Validar acceso a empresa
  - `_handle_pendientes()` - Filtrar por empresas del usuario
  - `_handle_cxc_cxp()` - Filtrar por empresas del usuario
  - `_handle_asesor_ia()` - Validar acceso a empresa

**Seguridad:**
- Validar que empresa_id pertenece al usuario antes de mostrar datos

---

### 6. **app/services/conversation_logger.py** ⚠️ IMPORTANTE
**Cambios necesarios:**
- ✅ Actualizar para obtener todas las empresas del usuario
- ✅ Manejar caso de múltiples empresas en logging

**Seguridad:**
- Registrar conversación con empresa_id correcto (validar acceso)

---

### 7. **app/services/storage_service.py** ⚠️ IMPORTANTE
**Cambios necesarios:**
- ✅ Validar acceso a empresa antes de subir archivo
- ✅ Validar acceso a empresa antes de obtener URL de archivo

**Seguridad:**
- No permitir subir/descargar archivos de empresas no asociadas

---

## 🔒 Validaciones de Seguridad Requeridas

### 1. Al SUBIR archivo:
```python
# ✅ Validar acceso antes de subir
if not security.user_has_access_to_empresa(chat_id, empresa_id):
    return "❌ No tienes acceso a esta empresa"
```

### 2. Al DESCARGAR archivo:
```python
# ✅ Validar que archivo pertenece a empresa del usuario
archivo = get_archivo(file_id)
if not security.user_has_access_to_empresa(chat_id, archivo['empresa_id']):
    return "❌ No tienes acceso a este archivo"
```

### 3. En BÚSQUEDAS:
```python
# ✅ Filtrar SOLO por empresas del usuario
empresas_usuario = get_user_empresas(chat_id)
empresa_ids = [e['id'] for e in empresas_usuario]
archivos = supabase.table('archivos')\
    .select('*')\
    .in_('empresa_id', empresa_ids)\  # ← FILTRO CRÍTICO
    .execute()
```

---

## 📊 Orden de Actualización Recomendado

1. **app/database/supabase.py** - Métodos base
2. **app/security/auth.py** - Validaciones de seguridad
3. **app/bots/handlers/file_upload_handler.py** - Subida de archivos
4. **app/bots/handlers/file_download_handler.py** - Descarga de archivos
5. **app/bots/handlers/production_handlers.py** - Otros handlers
6. **app/services/conversation_logger.py** - Logging
7. **app/services/storage_service.py** - Storage

---

## ✅ Checklist de Seguridad

- [ ] Todos los métodos que reciben `empresa_id` validan acceso
- [ ] Todas las búsquedas filtran por empresas del usuario
- [ ] Validación antes de subir archivo
- [ ] Validación antes de descargar archivo
- [ ] Validación en callbacks de selección de empresa
- [ ] Logging actualizado para multiempresa
- [ ] Storage service valida acceso

---

**Última actualización:** 2025-11-12








