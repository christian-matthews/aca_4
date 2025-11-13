# 🔍 Análisis del Código SQL de Migración

**Fecha:** 2025-01-11  
**Estado:** ✅ REVISADO Y VALIDADO

---

## 📊 ESTADO ACTUAL DE TABLA `archivos`

### Campos Existentes (16 campos):
- ✅ `id` (UUID)
- ✅ `chat_id` (BIGINT)
- ✅ `empresa_id` (UUID)
- ✅ `nombre_archivo` (VARCHAR)
- ✅ `nombre_original` (VARCHAR)
- ✅ `tipo_archivo` (VARCHAR) ⚠️ **Necesita renombrarse a `mime_type`**
- ✅ `extension` (VARCHAR)
- ✅ `tamaño_bytes` (BIGINT)
- ✅ `url_archivo` (TEXT)
- ✅ `storage_provider` (VARCHAR)
- ✅ `storage_path` (TEXT)
- ✅ `descripcion` (TEXT)
- ✅ `metadata` (JSONB)
- ✅ `activo` (BOOLEAN)
- ✅ `created_at` (TIMESTAMPTZ)
- ✅ `updated_at` (TIMESTAMPTZ)

### Campos Faltantes (8 campos):
- ❌ `periodo` (VARCHAR(7))
- ❌ `categoria` (VARCHAR(50))
- ❌ `tipo` (VARCHAR(50))
- ❌ `subtipo` (VARCHAR(100))
- ❌ `descripcion_personalizada` (TEXT)
- ❌ `mime_type` (VARCHAR(100)) - Actualmente se llama `tipo_archivo`
- ❌ `usuario_subio_id` (UUID) - Opcional
- ❌ `fecha_documento` (DATE) - Opcional

---

## ✅ REVISIÓN DEL CÓDIGO SQL

### 1. Agregar Campos Nuevos

```sql
ALTER TABLE archivos ADD COLUMN IF NOT EXISTS periodo VARCHAR(7);
ALTER TABLE archivos ADD COLUMN IF NOT EXISTS categoria VARCHAR(50);
ALTER TABLE archivos ADD COLUMN IF NOT EXISTS tipo VARCHAR(50);
ALTER TABLE archivos ADD COLUMN IF NOT EXISTS subtipo VARCHAR(100);
ALTER TABLE archivos ADD COLUMN IF NOT EXISTS descripcion_personalizada TEXT;
```

**✅ CORRECTO:**
- Usa `IF NOT EXISTS` - No fallará si el campo ya existe
- Tipos de datos correctos
- Compatible con estructura actual

### 2. Renombrar `tipo_archivo` → `mime_type`

```sql
DO $$ 
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'archivos' AND column_name = 'tipo_archivo'
    ) THEN
        ALTER TABLE archivos RENAME COLUMN tipo_archivo TO mime_type;
    END IF;
END $$;
```

**✅ CORRECTO:**
- Verifica que la columna existe antes de renombrar
- No fallará si ya fue renombrada
- Usa bloque DO para lógica condicional

**⚠️ NOTA:** Este bloque DO es seguro y no afectará datos existentes.

### 3. Agregar Campos Opcionales

```sql
ALTER TABLE archivos ADD COLUMN IF NOT EXISTS usuario_subio_id UUID REFERENCES usuarios(id) ON DELETE SET NULL;
ALTER TABLE archivos ADD COLUMN IF NOT EXISTS fecha_documento DATE;
```

**✅ CORRECTO:**
- `usuario_subio_id` tiene foreign key a `usuarios(id)` ✅
- `ON DELETE SET NULL` - Si se elimina usuario, no elimina archivo
- Ambos son opcionales (NULL permitido)

### 4. Crear Índices

```sql
CREATE INDEX IF NOT EXISTS idx_archivos_empresa_categoria_tipo_periodo 
ON archivos(empresa_id, categoria, tipo, subtipo, periodo) 
WHERE activo = true;
```

**✅ CORRECTO:**
- Índice compuesto para búsquedas optimizadas
- `WHERE activo = true` - Solo indexa archivos activos (más eficiente)
- `IF NOT EXISTS` - No fallará si ya existe

**⚠️ NOTA:** Este índice incluye campos que aún no existen, pero PostgreSQL permite crear el índice aunque algunos campos sean NULL inicialmente.

---

## 🔍 VALIDACIONES ADICIONALES

### Verificar Foreign Keys

**Campo `usuario_subio_id`:**
```sql
REFERENCES usuarios(id) ON DELETE SET NULL
```

**✅ CORRECTO:**
- La tabla `usuarios` existe ✅
- El campo `id` en `usuarios` es UUID ✅
- `ON DELETE SET NULL` es seguro ✅

### Verificar Tipos de Datos

| Campo | Tipo SQL | Compatible con Python | ✅ |
|-------|----------|----------------------|-----|
| `periodo` | VARCHAR(7) | str | ✅ |
| `categoria` | VARCHAR(50) | str | ✅ |
| `tipo` | VARCHAR(50) | str | ✅ |
| `subtipo` | VARCHAR(100) | str | ✅ |
| `descripcion_personalizada` | TEXT | str | ✅ |
| `usuario_subio_id` | UUID | str/uuid | ✅ |
| `fecha_documento` | DATE | date | ✅ |

**✅ Todos los tipos son compatibles**

---

## ⚠️ POSIBLES PROBLEMAS Y SOLUCIONES

### Problema 1: Índice con campos NULL

**Situación:** El índice incluye campos que serán NULL inicialmente (para archivos existentes).

**Solución:** ✅ PostgreSQL permite índices con NULL. Los archivos existentes tendrán NULL en estos campos, pero el índice funcionará correctamente para nuevos registros.

### Problema 2: Renombrar columna con datos

**Situación:** La columna `tipo_archivo` tiene datos existentes.

**Solución:** ✅ `RENAME COLUMN` es seguro y no afecta los datos, solo cambia el nombre.

### Problema 3: Foreign Key a usuarios

**Situación:** `usuario_subio_id` referencia a `usuarios(id)`.

**Verificación:** ✅ La tabla `usuarios` existe y tiene campo `id` UUID.

---

## ✅ CONCLUSIÓN

**El código SQL es:**
- ✅ **Seguro** - No elimina ni modifica datos existentes
- ✅ **Compatible** - Funciona con la estructura actual
- ✅ **Reversible** - Los campos se pueden eliminar si es necesario
- ✅ **Optimizado** - Índices para búsquedas rápidas
- ✅ **Documentado** - Comentarios en columnas

**Puede ejecutarse sin problemas en Supabase.**

---

## 📝 ORDEN DE EJECUCIÓN RECOMENDADO

1. **Primero:** Ejecutar todo el script completo
2. **Verificar:** Que todos los campos se crearon
3. **Confirmar:** Que `tipo_archivo` se renombró a `mime_type`
4. **Validar:** Que los índices se crearon

---

## 🔄 ROLLBACK (Si es necesario)

Si necesitas revertir los cambios:

```sql
-- Eliminar campos nuevos
ALTER TABLE archivos DROP COLUMN IF EXISTS periodo;
ALTER TABLE archivos DROP COLUMN IF EXISTS categoria;
ALTER TABLE archivos DROP COLUMN IF EXISTS tipo;
ALTER TABLE archivos DROP COLUMN IF EXISTS subtipo;
ALTER TABLE archivos DROP COLUMN IF EXISTS descripcion_personalizada;
ALTER TABLE archivos DROP COLUMN IF EXISTS usuario_subio_id;
ALTER TABLE archivos DROP COLUMN IF EXISTS fecha_documento;

-- Renombrar de vuelta
ALTER TABLE archivos RENAME COLUMN mime_type TO tipo_archivo;

-- Eliminar índices
DROP INDEX IF EXISTS idx_archivos_empresa_categoria_tipo_periodo;
DROP INDEX IF EXISTS idx_archivos_periodo;
DROP INDEX IF EXISTS idx_archivos_categoria_subtipo;
```

---

**✅ El código está listo para ejecutar en Supabase.**


