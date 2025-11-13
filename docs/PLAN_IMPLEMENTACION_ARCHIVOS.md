# 📋 Plan de Implementación - Gestión de Archivos ACA 4.0

**Fecha:** 2025-01-11  
**Objetivo:** Implementar subida y descarga de archivos con flujo conversacional  
**Estado:** 📝 PLAN - Pendiente de revisión

---

## 🔍 1. ANÁLISIS DEL ESTADO ACTUAL

### 1.1. Tabla `archivos` (Actual)
```sql
CREATE TABLE archivos (
    id UUID PRIMARY KEY,
    chat_id BIGINT NOT NULL,
    empresa_id UUID REFERENCES empresas(id),
    nombre_archivo VARCHAR(255) NOT NULL,
    nombre_original VARCHAR(255),
    tipo_archivo VARCHAR(100),
    extension VARCHAR(10),
    tamaño_bytes BIGINT,
    url_archivo TEXT NOT NULL,
    storage_provider VARCHAR(50) DEFAULT 'supabase',
    storage_path TEXT,
    descripcion TEXT,
    metadata JSONB DEFAULT '{}',
    activo BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
```

### 1.2. Lo que tenemos vs Lo que necesitamos

| Campo Actual | Campo Necesario | Estado | Acción |
|-------------|----------------|--------|--------|
| `tipo_archivo` | `tipo` (factura, cartola, etc.) | ⚠️ Diferente | **RENOMBRAR o AGREGAR** |
| ❌ | `periodo` (YYYY-MM) | ❌ Faltante | **AGREGAR** |
| `nombre_archivo` | ✅ OK | ✅ | - |
| `empresa_id` | ✅ OK | ✅ | - |
| `chat_id` | ✅ OK | ✅ | - |
| `metadata` | ✅ OK (puede guardar sesión) | ✅ | - |

### 1.3. Componentes Existentes

✅ **StorageService** (`app/services/storage_service.py`)
- Métodos: `upload_file()`, `download_file()`, `get_file_url()`, `delete_file()`
- **Estado:** Preparado pero no integrado con bots

✅ **Tabla archivos** en BD
- **Estado:** Existe pero falta `periodo` y `tipo` correcto

❌ **Manejo de sesiones conversacionales**
- **Estado:** No existe

❌ **Handlers para archivos en bots**
- **Estado:** No existe

---

## 🗄️ 2. CAMBIOS REQUERIDOS EN BASE DE DATOS

### 2.1. Modificar tabla `archivos`

**Archivo:** `database/migrations/add_campos_archivos.sql`

```sql
-- Agregar campo 'periodo' (YYYY-MM)
ALTER TABLE archivos 
ADD COLUMN IF NOT EXISTS periodo VARCHAR(7); -- Formato: YYYY-MM

-- Agregar campo 'tipo' (factura, cartola, contrato, etc.)
ALTER TABLE archivos 
ADD COLUMN IF NOT EXISTS tipo VARCHAR(50);

-- Renombrar 'tipo_archivo' a 'mime_type' para claridad
ALTER TABLE archivos 
RENAME COLUMN tipo_archivo TO mime_type;

-- Agregar índice para búsquedas por empresa + tipo + periodo
CREATE INDEX IF NOT EXISTS idx_archivos_empresa_tipo_periodo 
ON archivos(empresa_id, tipo, periodo) 
WHERE activo = true;

-- Agregar índice para búsquedas por chat_id
CREATE INDEX IF NOT EXISTS idx_archivos_chat_id 
ON archivos(chat_id) 
WHERE activo = true;
```

### 2.2. Crear tabla `sesiones_conversacion`

**Archivo:** `database/migrations/create_sesiones_conversacion.sql`

```sql
-- Tabla para manejar sesiones conversacionales
CREATE TABLE IF NOT EXISTS sesiones_conversacion (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    chat_id BIGINT NOT NULL,
    estado VARCHAR(50) NOT NULL, -- 'idle', 'esperando_empresa', 'esperando_tipo', 'esperando_periodo', 'finalizado'
    intent VARCHAR(50), -- 'subir_archivo', 'descargar_archivo'
    data JSONB DEFAULT '{}'::jsonb, -- Datos temporales de la sesión
    archivo_temp_id UUID, -- ID temporal del archivo si está en proceso de subida
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    expires_at TIMESTAMPTZ DEFAULT NOW() + INTERVAL '1 hour' -- Expiración automática
);

-- Índice para búsquedas rápidas por chat_id
CREATE INDEX IF NOT EXISTS idx_sesiones_chat_id 
ON sesiones_conversacion(chat_id) 
WHERE expires_at > NOW();

-- Índice para limpieza de sesiones expiradas
CREATE INDEX IF NOT EXISTS idx_sesiones_expires_at 
ON sesiones_conversacion(expires_at);
```

### 2.3. Función para limpiar sesiones expiradas

```sql
-- Función para limpiar sesiones expiradas
CREATE OR REPLACE FUNCTION limpiar_sesiones_expiradas()
RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    DELETE FROM sesiones_conversacion 
    WHERE expires_at < NOW();
    
    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql;
```

---

## 💻 3. CAMBIOS REQUERIDOS EN CÓDIGO

### 3.1. Nuevos Archivos a Crear

#### 3.1.1. `app/services/session_manager.py`
**Propósito:** Gestionar sesiones conversacionales

```python
class SessionManager:
    - get_session(chat_id)
    - create_session(chat_id, intent, estado)
    - update_session(chat_id, data)
    - clear_session(chat_id)
    - cleanup_expired_sessions()
```

#### 3.1.2. `app/services/file_handler.py`
**Propósito:** Lógica de negocio para archivos

```python
class FileHandler:
    - get_user_empresas(chat_id) -> List[empresa]
    - validate_periodo(texto) -> YYYY-MM
    - normalize_tipo(texto) -> tipo_estandarizado
    - search_files(empresa_id, tipo, periodo) -> List[archivo]
```

#### 3.1.3. `app/bots/handlers/file_handlers.py`
**Propósito:** Handlers específicos para archivos

```python
class FileHandlers:
    - handle_file_upload(update, context)
    - handle_file_download_request(update, context)
    - handle_callback_file(update, context)
    - _process_upload_flow(update, context, session)
    - _process_download_flow(update, context, session)
```

### 3.2. Archivos a Modificar

#### 3.2.1. `app/services/storage_service.py`
**Cambios:**
- Agregar parámetros `tipo` y `periodo` a `upload_file()`
- Actualizar registro en BD con estos campos

```python
async def upload_file(
    self,
    file_bytes: bytes,
    filename: str,
    chat_id: int,
    empresa_id: Optional[str] = None,
    tipo: Optional[str] = None,  # NUEVO
    periodo: Optional[str] = None,  # NUEVO
    folder: str = "uploads"
) -> Optional[Dict[str, Any]]:
    # ... código existente ...
    archivo_data = {
        # ... campos existentes ...
        'tipo': tipo,  # NUEVO
        'periodo': periodo,  # NUEVO
        'mime_type': self._get_content_type(filename),  # RENOMBRADO
    }
```

#### 3.2.2. `app/bots/handlers/production_handlers.py`
**Cambios:**
- Agregar handler para documentos (MessageHandler con filters.Document)
- Integrar flujo de archivos en el menú principal
- Agregar botón "📁 Ver documentos" en menú

```python
# En _setup_production_handlers():
self.production_app.add_handler(
    MessageHandler(
        filters.Document.ALL, 
        FileHandlers.handle_file_upload
    )
)
```

#### 3.2.3. `app/database/supabase.py`
**Cambios:**
- Agregar métodos para sesiones
- Agregar métodos para búsqueda de archivos

```python
def get_user_empresas(self, chat_id: int) -> List[Dict]:
    """Obtener empresas asignadas a un usuario"""
    
def search_archivos(self, empresa_id: str, tipo: str = None, periodo: str = None) -> List[Dict]:
    """Buscar archivos por empresa, tipo y periodo"""
    
def create_session(self, chat_id: int, intent: str, estado: str, data: Dict = None) -> Dict:
    """Crear sesión conversacional"""
    
def get_session(self, chat_id: int) -> Optional[Dict]:
    """Obtener sesión activa"""
    
def update_session(self, chat_id: int, data: Dict) -> bool:
    """Actualizar sesión"""
    
def clear_session(self, chat_id: int) -> bool:
    """Limpiar sesión"""
```

---

## 🔄 4. FLUJOS DE IMPLEMENTACIÓN

### 4.1. Flujo de SUBIDA (Upload)

```
1. Usuario envía documento
   ↓
2. FileHandlers.handle_file_upload()
   ↓
3. Crear sesión: intent='subir_archivo', estado='esperando_empresa'
   ↓
4. Guardar archivo temporal en StorageService
   ↓
5. Consultar empresas del usuario
   ↓
6. Si 1 empresa → auto-asignar, ir a paso 7
   Si >1 empresa → mostrar botones, esperar selección
   ↓
7. estado='esperando_tipo'
   Mostrar botones: Factura, Cartola, Contrato, Documentación, Otro
   ↓
8. estado='esperando_periodo'
   Mostrar botones: Mes actual, Mes anterior, Otro mes
   ↓
9. Con todos los datos:
   - Subir archivo final a StorageService
   - Registrar en tabla archivos
   - Limpiar sesión
   - Confirmar al usuario
```

### 4.2. Flujo de BAJADA (Download)

```
1. Usuario envía mensaje o presiona "📁 Ver documentos"
   ↓
2. FileHandlers.handle_file_download_request()
   ↓
3. Intentar extraer: empresa, tipo, periodo (parser simple o IA)
   ↓
4. Validar empresa (debe estar asignada al usuario)
   ↓
5. Si falta empresa → estado='esperando_empresa', mostrar botones
   Si falta periodo → estado='esperando_periodo', mostrar botones
   Si falta tipo → estado='esperando_tipo', mostrar botones
   ↓
6. Con todos los datos validados:
   - Buscar archivos en BD
   - Generar URLs firmadas
   - Enviar lista al usuario
   - Limpiar sesión
```

---

## 📝 5. LISTA DE TAREAS DETALLADA

### FASE 1: Base de Datos ✅
- [ ] Crear migración para agregar `periodo` a tabla `archivos`
- [ ] Crear migración para agregar `tipo` a tabla `archivos`
- [ ] Renombrar `tipo_archivo` a `mime_type`
- [ ] Crear índices para búsquedas optimizadas
- [ ] Crear tabla `sesiones_conversacion`
- [ ] Crear función `limpiar_sesiones_expiradas()`
- [ ] Ejecutar migraciones en Supabase

### FASE 2: Servicios Base ✅
- [ ] Crear `app/services/session_manager.py`
- [ ] Crear `app/services/file_handler.py`
- [ ] Modificar `app/services/storage_service.py` (agregar tipo y periodo)
- [ ] Agregar métodos en `app/database/supabase.py`:
  - `get_user_empresas()`
  - `search_archivos()`
  - `create_session()`
  - `get_session()`
  - `update_session()`
  - `clear_session()`

### FASE 3: Handlers de Archivos ✅
- [ ] Crear `app/bots/handlers/file_handlers.py`
- [ ] Implementar `handle_file_upload()`
- [ ] Implementar `handle_file_download_request()`
- [ ] Implementar `handle_callback_file()`
- [ ] Implementar flujos conversacionales completos

### FASE 4: Integración con Bot ✅
- [ ] Registrar handlers en `bot_manager.py`
- [ ] Agregar botón "📁 Ver documentos" en menú principal
- [ ] Integrar con `production_handlers.py`
- [ ] Agregar comando `/cancelar` para resetear sesión

### FASE 5: Testing y Validación ✅
- [ ] Probar flujo completo de subida
- [ ] Probar flujo completo de descarga
- [ ] Probar multiempresa
- [ ] Probar cancelación de sesión
- [ ] Probar limpieza de sesiones expiradas
- [ ] Validar permisos y seguridad

---

## ⚠️ 6. CONSIDERACIONES Y DECISIONES

### 6.1. Tipos de Archivo Estándar
```python
TIPOS_ARCHIVO = {
    'factura': '🧾 Factura',
    'cartola': '💳 Cartola',
    'contrato': '📑 Contrato',
    'documentacion': '📦 Documentación',
    'otro': '🗃️ Otro'
}
```

### 6.2. Formato de Periodo
- **Estándar:** `YYYY-MM` (ej: `2025-01`)
- **Validación:** Regex `^\d{4}-\d{2}$`
- **Normalización:** Convertir "mayo 2025" → `2025-05`

### 6.3. Expiración de Sesiones
- **Tiempo:** 1 hora desde última actualización
- **Limpieza:** Automática al consultar sesión
- **Job:** Opcional - cron job para limpiar masivamente

### 6.4. Seguridad
- ✅ Validar que usuario tenga acceso a la empresa
- ✅ Validar que archivo pertenezca a empresa del usuario
- ✅ URLs firmadas con expiración (Supabase Storage)
- ✅ No permitir acceso a archivos de otras empresas

### 6.5. Multiempresa
- Si usuario tiene 1 empresa → auto-asignar
- Si usuario tiene >1 empresa → mostrar botones
- Si usuario tiene 0 empresas → mensaje de error

---

## 🎯 7. ORDEN DE IMPLEMENTACIÓN RECOMENDADO

1. **Base de Datos** (FASE 1)
   - Migraciones son independientes
   - Se pueden ejecutar sin afectar código existente

2. **Servicios Base** (FASE 2)
   - Crear servicios sin integración
   - Probar unitariamente

3. **Handlers** (FASE 3)
   - Implementar lógica de negocio
   - Probar flujos conversacionales

4. **Integración** (FASE 4)
   - Conectar con bot existente
   - Integrar en menú

5. **Testing** (FASE 5)
   - Pruebas end-to-end
   - Validación completa

---

## 📊 8. MÉTRICAS DE ÉXITO

- ✅ Usuario puede subir archivo con clasificación completa
- ✅ Usuario puede buscar y descargar archivos por empresa/tipo/periodo
- ✅ Sesiones se limpian automáticamente
- ✅ Multiempresa funciona correctamente
- ✅ Sin errores en producción
- ✅ Performance aceptable (<2s por operación)

---

## 🔗 9. DEPENDENCIAS

- ✅ Supabase Storage configurado
- ✅ Bucket `archivos-bot` creado
- ✅ Permisos de Storage configurados
- ✅ Tabla `archivos` existente
- ✅ Tabla `empresas` existente
- ✅ Tabla `usuarios` existente

---

**📌 NOTA:** Este plan debe ser revisado y aprobado antes de comenzar la implementación.


