# 📋 Plan Revisado - Gestión de Archivos ACA 4.0

**Fecha:** 2025-01-11  
**Estado:** ✅ REVISADO Y APROBADO

---

## 🗄️ 1. ESTRUCTURA DE BASE DE DATOS - CAMPOS ADICIONALES

### 1.1. Campos Esenciales (Confirmados)
- ✅ `periodo` (VARCHAR(7)) - Formato YYYY-MM
- ✅ `tipo` (VARCHAR(50)) - Tipo de archivo (legal/financiero + subtipo)

### 1.2. Campos Adicionales Recomendados

Basado en el análisis, estos campos adicionales serían útiles:

| Campo | Tipo | Propósito | ¿Requerido? |
|-------|------|-----------|-------------|
| `subtipo` | VARCHAR(100) | Subtipo específico (Estatutos, F29, etc.) | ✅ **SÍ** - Para la estructura jerárquica |
| `descripcion_personalizada` | TEXT | Descripción cuando tipo es "Otros" | ✅ **SÍ** - Para identificar archivos "Otros" |
| `categoria` | VARCHAR(50) | Categoría principal (legal/financiero) | ✅ **SÍ** - Para agrupar y filtrar |
| `usuario_subio_id` | UUID | ID del usuario que subió (referencia a usuarios) | ⚠️ Opcional - Para auditoría |
| `fecha_documento` | DATE | Fecha del documento (si es diferente al periodo) | ⚠️ Opcional - Para documentos con fecha específica |
| `tags` | JSONB | Etiquetas adicionales para búsqueda | ⚠️ Opcional - Para búsquedas avanzadas |

**Recomendación:** Implementar los 3 primeros (subtipo, descripcion_personalizada, categoria) como esenciales.

---

## 📁 2. ESTRUCTURA DE TIPOS DE ARCHIVO (JERÁRQUICA)

### 2.1. Categorías Principales

```python
TIPOS_ARCHIVO = {
    'legal': {
        'nombre': '⚖️ Legales',
        'subtipos': {
            'estatutos_empresa': 'Estatutos empresa',
            'poderes': 'Poderes',
            'ci': 'CI',
            'rut': 'RUT',
            'otros': 'Otros'
        }
    },
    'financiero': {
        'nombre': '💰 Financieros',
        'subtipos': {
            'reporte_mensual': 'Reporte mensual',
            'estados_financieros': 'Estados financieros',
            'carpeta_tributaria': 'Carpeta tributaria',
            'f29': 'F29',
            'f22': 'F22',
            'otros': 'Otros'
        }
    }
}
```

### 2.2. Flujo de Selección

**Paso 1:** Seleccionar categoría (Legal o Financiero)
```
Bot: "¿Qué categoría de archivo es?"
[⚖️ Legales] [💰 Financieros]
```

**Paso 2:** Seleccionar subtipo
```
Si eligió "Legales":
[Estatutos empresa] [Poderes] [CI] [RUT] [Otros]

Si eligió "Financieros":
[Reporte mensual] [Estados financieros] [Carpeta tributaria] [F29] [F22] [Otros]
```

**Paso 3:** Si eligió "Otros"
```
Bot: "Describe brevemente el archivo para identificarlo"
Usuario: "Contrato de arriendo"
→ Se guarda en campo `descripcion_personalizada`
```

### 2.3. Almacenamiento en BD

```sql
-- Ejemplo de registro:
categoria = 'legal'
tipo = 'legal'  -- Categoría principal
subtipo = 'otros'  -- Subtipo seleccionado
descripcion_personalizada = 'Contrato de arriendo'  -- Solo si subtipo = 'otros'
```

---

## 🏢 3. MULTIEMPRESA - EXPLICACIÓN

### 3.1. ¿Qué es Multiempresa?

**Situación actual:** 
- Cada usuario en la tabla `usuarios` tiene un solo `empresa_id`
- Un usuario solo puede pertenecer a UNA empresa

**Escenario Multiempresa:**
- Un usuario podría trabajar para MÚLTIPLES empresas
- Ejemplo: Un contador que maneja 3 empresas diferentes

### 3.2. ¿Cómo afecta al flujo de archivos?

**Si usuario tiene 1 empresa:**
```
Usuario sube archivo
  ↓
Sistema detecta: 1 empresa asignada
  ↓
AUTO-ASIGNAR empresa (sin preguntar)
  ↓
Preguntar solo: tipo y periodo
```

**Si usuario tiene >1 empresa:**
```
Usuario sube archivo
  ↓
Sistema detecta: 3 empresas asignadas
  ↓
Preguntar: "¿De qué empresa es este archivo?"
  ↓
Mostrar botones: [Empresa A] [Empresa B] [Empresa C]
  ↓
Usuario selecciona
  ↓
Continuar con tipo y periodo
```

### 3.3. Implementación Actual

**Estado actual del sistema:**
- La tabla `usuarios` solo permite 1 `empresa_id` por usuario
- **Para soportar multiempresa real**, necesitaríamos:
  - Opción 1: Tabla intermedia `usuarios_empresas` (muchos a muchos)
  - Opción 2: Campo `empresas_ids` JSONB en usuarios

**Para este proyecto:**
- Por ahora, asumimos 1 empresa por usuario
- El código debe estar preparado para cuando se implemente multiempresa
- El flujo pregunta empresa solo si detecta múltiples (futuro)

---

## 🔒 4. SEGURIDAD - EXPLICACIÓN

### 4.1. ¿Qué es Seguridad en este contexto?

**Problema a resolver:**
- Un usuario NO debe poder ver/descargar archivos de empresas a las que NO pertenece
- Un usuario NO debe poder subir archivos a empresas que NO le corresponden

### 4.2. Validaciones Necesarias

#### 4.2.1. Al SUBIR archivo:
```python
# Validación 1: Usuario debe estar autorizado
if not security.validate_user(chat_id)['valid']:
    return "❌ No tienes acceso"

# Validación 2: Empresa debe pertenecer al usuario
user = supabase.get_user_by_chat_id(chat_id)
if empresa_id != user['empresa_id']:
    return "❌ No tienes acceso a esta empresa"
```

#### 4.2.2. Al DESCARGAR archivo:
```python
# Validación 1: Usuario debe estar autorizado
if not security.validate_user(chat_id)['valid']:
    return "❌ No tienes acceso"

# Validación 2: Archivo debe pertenecer a empresa del usuario
archivo = supabase.table('archivos').select('*').eq('id', file_id).execute()
user = supabase.get_user_by_chat_id(chat_id)

if archivo['empresa_id'] != user['empresa_id']:
    return "❌ No tienes acceso a este archivo"
```

#### 4.2.3. En búsquedas:
```python
# SIEMPRE filtrar por empresa_id del usuario
user = supabase.get_user_by_chat_id(chat_id)
archivos = supabase.table('archivos')\
    .select('*')\
    .eq('empresa_id', user['empresa_id'])\  # ← CRÍTICO
    .eq('tipo', tipo)\
    .eq('periodo', periodo)\
    .execute()
```

### 4.3. URLs Firmadas

**Supabase Storage** genera URLs firmadas con expiración:
- URL válida por tiempo limitado (ej: 1 hora)
- No se puede acceder sin la URL firmada
- Previene acceso no autorizado

---

## 📝 5. CAMBIOS FINALES EN BASE DE DATOS

### 5.1. Modificar tabla `archivos`

```sql
-- Campos esenciales
ALTER TABLE archivos ADD COLUMN IF NOT EXISTS periodo VARCHAR(7);
ALTER TABLE archivos ADD COLUMN IF NOT EXISTS categoria VARCHAR(50); -- 'legal' o 'financiero'
ALTER TABLE archivos ADD COLUMN IF NOT EXISTS tipo VARCHAR(50); -- Categoría principal
ALTER TABLE archivos ADD COLUMN IF NOT EXISTS subtipo VARCHAR(100); -- Subtipo específico
ALTER TABLE archivos ADD COLUMN IF NOT EXISTS descripcion_personalizada TEXT; -- Para "Otros"

-- Renombrar campo existente
ALTER TABLE archivos RENAME COLUMN tipo_archivo TO mime_type;

-- Campos opcionales (para futuro)
ALTER TABLE archivos ADD COLUMN IF NOT EXISTS usuario_subio_id UUID REFERENCES usuarios(id);
ALTER TABLE archivos ADD COLUMN IF NOT EXISTS fecha_documento DATE;

-- Índices
CREATE INDEX IF NOT EXISTS idx_archivos_empresa_categoria_tipo_periodo 
ON archivos(empresa_id, categoria, tipo, subtipo, periodo) 
WHERE activo = true;

CREATE INDEX IF NOT EXISTS idx_archivos_chat_id 
ON archivos(chat_id) 
WHERE activo = true;
```

### 5.2. Tabla `sesiones_conversacion`

```sql
CREATE TABLE IF NOT EXISTS sesiones_conversacion (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    chat_id BIGINT NOT NULL,
    estado VARCHAR(50) NOT NULL,
    intent VARCHAR(50), -- 'subir_archivo', 'descargar_archivo'
    data JSONB DEFAULT '{}'::jsonb,
    archivo_temp_id UUID,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    expires_at TIMESTAMPTZ DEFAULT NOW() + INTERVAL '1 hour'
);

-- Limpieza automática al consultar o manual con comando /cancelar
CREATE INDEX IF NOT EXISTS idx_sesiones_chat_id ON sesiones_conversacion(chat_id);
CREATE INDEX IF NOT EXISTS idx_sesiones_expires_at ON sesiones_conversacion(expires_at);
```

---

## 🔄 6. FLUJO ACTUALIZADO CON NUEVA ESTRUCTURA

### 6.1. Flujo de SUBIDA (Actualizado)

```
1. Usuario envía documento
   ↓
2. Crear sesión: intent='subir_archivo', estado='esperando_empresa'
   ↓
3. Consultar empresa del usuario (actualmente 1 por usuario)
   Si 1 empresa → auto-asignar, ir a paso 4
   Si >1 empresa → mostrar botones (futuro)
   ↓
4. estado='esperando_categoria'
   Bot: "¿Qué categoría de archivo es?"
   [⚖️ Legales] [💰 Financieros]
   ↓
5. estado='esperando_subtipo'
   Si eligió "Legales":
   [Estatutos empresa] [Poderes] [CI] [RUT] [Otros]
   Si eligió "Financieros":
   [Reporte mensual] [Estados financieros] [Carpeta tributaria] [F29] [F22] [Otros]
   ↓
6. Si eligió "Otros":
   estado='esperando_descripcion'
   Bot: "Describe brevemente el archivo"
   Usuario: "Contrato de arriendo"
   ↓
7. estado='esperando_periodo'
   Bot: "¿Para qué periodo es?"
   [🟢 Mes actual] [🟡 Mes anterior] [📅 Otro mes]
   ↓
8. Con todos los datos:
   - Subir archivo a StorageService
   - Registrar en BD con: categoria, tipo, subtipo, periodo, descripcion_personalizada
   - Limpiar sesión
   - Confirmar al usuario
```

### 6.2. Flujo de DESCARGA (Actualizado)

```
1. Usuario: "F29 de enero" o presiona "📁 Ver documentos"
   ↓
2. Parser intenta extraer: categoria?, tipo?, subtipo?, periodo?
   ↓
3. Validar empresa (debe ser la del usuario)
   ↓
4. Si falta categoria → preguntar con botones
   Si falta subtipo → preguntar según categoria
   Si falta periodo → preguntar
   ↓
5. Buscar archivos:
   - Filtrar por empresa_id del usuario (SEGURIDAD)
   - Filtrar por categoria, subtipo, periodo
   ↓
6. Generar URLs firmadas
   ↓
7. Enviar lista al usuario
```

---

## ✅ 7. CHECKLIST ACTUALIZADO

### FASE 1: Base de Datos
- [ ] Agregar `periodo` VARCHAR(7)
- [ ] Agregar `categoria` VARCHAR(50)
- [ ] Agregar `tipo` VARCHAR(50)
- [ ] Agregar `subtipo` VARCHAR(100)
- [ ] Agregar `descripcion_personalizada` TEXT
- [ ] Renombrar `tipo_archivo` → `mime_type`
- [ ] Agregar `usuario_subio_id` UUID (opcional)
- [ ] Agregar `fecha_documento` DATE (opcional)
- [ ] Crear tabla `sesiones_conversacion`
- [ ] Crear índices optimizados
- [ ] Crear función `limpiar_sesiones_expiradas()`

### FASE 2: Código - Estructura de Tipos
- [ ] Crear constante `TIPOS_ARCHIVO` con estructura jerárquica
- [ ] Implementar selección de categoría (Legal/Financiero)
- [ ] Implementar selección de subtipo según categoría
- [ ] Implementar campo de descripción para "Otros"

### FASE 3: Código - Servicios
- [ ] Crear `session_manager.py`
- [ ] Crear `file_handler.py` con validaciones de seguridad
- [ ] Modificar `storage_service.py` (agregar nuevos campos)
- [ ] Agregar métodos en `supabase.py`:
  - [ ] `get_user_empresas()` (preparado para futuro multiempresa)
  - [ ] `search_archivos()` con filtro de seguridad
  - [ ] Métodos de sesiones

### FASE 4: Código - Handlers
- [ ] Crear `file_handlers.py`
- [ ] Implementar flujo de subida con nueva estructura
- [ ] Implementar flujo de descarga con validaciones
- [ ] Implementar comando `/cancelar` para limpiar sesión

### FASE 5: Integración
- [ ] Registrar handlers en `bot_manager.py`
- [ ] Agregar botón "📁 Ver documentos" en menú
- [ ] Integrar con `production_handlers.py`

### FASE 6: Testing
- [ ] Probar subida completa (todas las categorías)
- [ ] Probar "Otros" con descripción
- [ ] Probar descarga con filtros
- [ ] Validar seguridad (usuario no puede ver archivos de otra empresa)
- [ ] Probar expiración de sesión (1 hora y /cancelar)

---

## 🎯 8. DECISIONES FINALES CONFIRMADAS

✅ **Formato de periodo:** YYYY-MM  
✅ **Expiración de sesiones:** 1 hora O cuando usuario presiona /cancelar  
✅ **Estructura de tipos:** Jerárquica (Categoría → Subtipo → Descripción si "Otros")  
✅ **Multiempresa:** Preparado para futuro, actualmente 1 empresa por usuario  
✅ **Seguridad:** Validaciones estrictas en subida y descarga  

---

**📌 PRÓXIMO PASO:** Implementar según este plan revisado.


