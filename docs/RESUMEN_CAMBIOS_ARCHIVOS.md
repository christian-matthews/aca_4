# 📋 Resumen Ejecutivo - Cambios para Gestión de Archivos

**Fecha:** 2025-01-11  
**Estado:** ⏳ PENDIENTE DE APROBACIÓN

---

## 🎯 OBJETIVO

Implementar subida y descarga de archivos con flujo conversacional que clasifica archivos por empresa, tipo y periodo.

---

## 📊 COMPARACIÓN: Estado Actual vs Requerido

### Tabla `archivos` - Campos Actuales vs Necesarios

| Campo Actual | Campo Necesario | Acción Requerida |
|-------------|----------------|------------------|
| `tipo_archivo` (VARCHAR) | `tipo` (factura, cartola, etc.) | ⚠️ **RENOMBRAR** `tipo_archivo` → `mime_type`<br>➕ **AGREGAR** `tipo` VARCHAR(50) |
| ❌ No existe | `periodo` (YYYY-MM) | ➕ **AGREGAR** `periodo` VARCHAR(7) |
| `nombre_archivo` | ✅ OK | ✅ Mantener |
| `empresa_id` | ✅ OK | ✅ Mantener |
| `chat_id` | ✅ OK | ✅ Mantener |
| `metadata` (JSONB) | ✅ OK | ✅ Mantener (puede guardar sesión) |

### Nueva Tabla Requerida

**`sesiones_conversacion`** - Para manejar flujos conversacionales
- `chat_id` (BIGINT)
- `estado` (VARCHAR) - 'idle', 'esperando_empresa', 'esperando_tipo', 'esperando_periodo'
- `intent` (VARCHAR) - 'subir_archivo', 'descargar_archivo'
- `data` (JSONB) - Datos temporales
- `archivo_temp_id` (UUID) - Archivo en proceso
- `expires_at` (TIMESTAMPTZ) - Expiración automática

---

## 🗄️ CAMBIOS EN BASE DE DATOS (5 cambios)

### 1. Modificar tabla `archivos`
```sql
-- Agregar campo 'periodo'
ALTER TABLE archivos ADD COLUMN periodo VARCHAR(7);

-- Agregar campo 'tipo' 
ALTER TABLE archivos ADD COLUMN tipo VARCHAR(50);

-- Renombrar 'tipo_archivo' a 'mime_type'
ALTER TABLE archivos RENAME COLUMN tipo_archivo TO mime_type;

-- Índices para búsquedas optimizadas
CREATE INDEX idx_archivos_empresa_tipo_periodo ON archivos(empresa_id, tipo, periodo);
```

### 2. Crear tabla `sesiones_conversacion`
```sql
CREATE TABLE sesiones_conversacion (
    id UUID PRIMARY KEY,
    chat_id BIGINT NOT NULL,
    estado VARCHAR(50) NOT NULL,
    intent VARCHAR(50),
    data JSONB DEFAULT '{}',
    archivo_temp_id UUID,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    expires_at TIMESTAMPTZ DEFAULT NOW() + INTERVAL '1 hour'
);
```

### 3. Crear función de limpieza
```sql
CREATE FUNCTION limpiar_sesiones_expiradas() RETURNS INTEGER;
```

### 4. Índices adicionales
- `idx_sesiones_chat_id` - Búsquedas por chat
- `idx_sesiones_expires_at` - Limpieza automática

### 5. Verificar bucket de Storage
- ✅ Bucket `archivos-bot` debe existir en Supabase
- ✅ Permisos configurados

---

## 💻 CAMBIOS EN CÓDIGO (8 archivos)

### Archivos NUEVOS a Crear (3)

1. **`app/services/session_manager.py`**
   - Clase `SessionManager`
   - Métodos: `get_session()`, `create_session()`, `update_session()`, `clear_session()`

2. **`app/services/file_handler.py`**
   - Clase `FileHandler`
   - Métodos: `get_user_empresas()`, `validate_periodo()`, `normalize_tipo()`, `search_files()`

3. **`app/bots/handlers/file_handlers.py`**
   - Clase `FileHandlers`
   - Métodos: `handle_file_upload()`, `handle_file_download_request()`, `handle_callback_file()`

### Archivos a MODIFICAR (5)

4. **`app/services/storage_service.py`**
   - Agregar parámetros `tipo` y `periodo` a `upload_file()`
   - Actualizar registro en BD con estos campos
   - Renombrar `tipo_archivo` → `mime_type` en código

5. **`app/database/supabase.py`**
   - Agregar métodos:
     - `get_user_empresas(chat_id)` - Obtener empresas del usuario
     - `search_archivos(empresa_id, tipo, periodo)` - Buscar archivos
     - `create_session()`, `get_session()`, `update_session()`, `clear_session()` - Gestión de sesiones

6. **`app/bots/bot_manager.py`**
   - Registrar handler para documentos: `MessageHandler(filters.Document.ALL, FileHandlers.handle_file_upload)`
   - Registrar callback handler para archivos

7. **`app/bots/handlers/production_handlers.py`**
   - Agregar botón "📁 Ver documentos" en menú principal
   - Agregar handler para callback `ver_documentos`
   - Integrar con `FileHandlers.handle_file_download_request()`

8. **`app/bots/handlers/production_handlers.py`** (adicional)
   - Agregar comando `/cancelar` para resetear sesión activa

---

## 🔄 FLUJOS A IMPLEMENTAR

### Flujo 1: SUBIDA DE ARCHIVOS
```
Usuario envía documento
  ↓
Detectar archivo → Crear sesión
  ↓
Consultar empresas del usuario
  ↓
Si 1 empresa → auto-asignar
Si >1 empresa → mostrar botones
  ↓
Preguntar tipo (Factura, Cartola, Contrato, etc.)
  ↓
Preguntar periodo (Mes actual, anterior, otro)
  ↓
Subir a Storage + Registrar en BD
  ↓
Confirmar al usuario
```

### Flujo 2: DESCARGA DE ARCHIVOS
```
Usuario: "cartolas de mayo"
  ↓
Parser extrae: empresa?, tipo?, periodo?
  ↓
Validar empresa (debe estar asignada)
  ↓
Si falta algo → preguntar con botones
  ↓
Buscar archivos en BD
  ↓
Generar URLs firmadas
  ↓
Enviar lista al usuario
```

---

## ⚠️ DECISIONES TÉCNICAS IMPORTANTES

### 1. Tipos de Archivo Estándar
```python
TIPOS = {
    'factura': '🧾 Factura',
    'cartola': '💳 Cartola', 
    'contrato': '📑 Contrato',
    'documentacion': '📦 Documentación',
    'otro': '🗃️ Otro'
}
```

### 2. Formato de Periodo
- **Estándar:** `YYYY-MM` (ej: `2025-01`)
- **Validación:** Regex `^\d{4}-\d{2}$`
- **Normalización:** "mayo 2025" → `2025-05`

### 3. Expiración de Sesiones
- **Tiempo:** 1 hora desde última actualización
- **Limpieza:** Automática al consultar

### 4. Multiempresa
- Si usuario tiene **1 empresa** → auto-asignar
- Si usuario tiene **>1 empresa** → mostrar botones
- Si usuario tiene **0 empresas** → error

---

## 📝 CHECKLIST DE IMPLEMENTACIÓN

### FASE 1: Base de Datos
- [ ] Ejecutar migración para agregar `periodo` a `archivos`
- [ ] Ejecutar migración para agregar `tipo` a `archivos`
- [ ] Renombrar `tipo_archivo` → `mime_type`
- [ ] Crear tabla `sesiones_conversacion`
- [ ] Crear función `limpiar_sesiones_expiradas()`
- [ ] Crear índices necesarios
- [ ] Verificar bucket de Storage en Supabase

### FASE 2: Servicios Base
- [ ] Crear `session_manager.py`
- [ ] Crear `file_handler.py`
- [ ] Modificar `storage_service.py` (agregar tipo y periodo)
- [ ] Agregar métodos en `supabase.py`:
  - [ ] `get_user_empresas()`
  - [ ] `search_archivos()`
  - [ ] `create_session()`
  - [ ] `get_session()`
  - [ ] `update_session()`
  - [ ] `clear_session()`

### FASE 3: Handlers
- [ ] Crear `file_handlers.py`
- [ ] Implementar `handle_file_upload()`
- [ ] Implementar `handle_file_download_request()`
- [ ] Implementar `handle_callback_file()`
- [ ] Implementar flujos conversacionales

### FASE 4: Integración
- [ ] Registrar handlers en `bot_manager.py`
- [ ] Agregar botón "📁 Ver documentos" en menú
- [ ] Agregar comando `/cancelar`
- [ ] Integrar con `production_handlers.py`

### FASE 5: Testing
- [ ] Probar subida completa
- [ ] Probar descarga completa
- [ ] Probar multiempresa
- [ ] Probar cancelación
- [ ] Validar seguridad

---

## 🎯 IMPACTO ESTIMADO

### Archivos Afectados
- **Nuevos:** 3 archivos
- **Modificados:** 5 archivos
- **Total:** 8 archivos

### Líneas de Código Estimadas
- **Nuevas:** ~800-1000 líneas
- **Modificadas:** ~100-150 líneas

### Tiempo Estimado
- **Desarrollo:** 2-3 días
- **Testing:** 1 día
- **Total:** 3-4 días

---

## ✅ CRITERIOS DE APROBACIÓN

Antes de comenzar, confirmar:

1. ✅ Estructura de BD aprobada
2. ✅ Flujos conversacionales aprobados
3. ✅ Tipos de archivo estándar definidos
4. ✅ Formato de periodo definido
5. ✅ Bucket de Storage configurado
6. ✅ Plan de testing definido

---

**📌 PRÓXIMO PASO:** Revisar este plan y aprobar antes de comenzar implementación.


