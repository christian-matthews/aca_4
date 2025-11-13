# 📝 Cambios Recientes - ACA 4.0

**Fecha:** 2025-11-12  
**Versión:** 4.0.1

---

## 🎯 Cambios Principales

### 1. Simplificación del Flujo de Descarga

**Antes:**
- Detección automática de lenguaje natural
- Integración con OpenAI para extracción de intención
- Flujo híbrido (IA + estructurado)

**Ahora:**
- ✅ Flujo completamente estructurado con botones
- ✅ Usuario presiona "📊 Información" → selecciona categoría → subtipo → período
- ✅ Sin necesidad de escribir mensajes
- ✅ Más rápido y predecible

### 2. Menús en 2 Columnas

**Implementado:**
- ✅ Todos los menús organizados en formato de 2 columnas
- ✅ Función `organizar_botones_en_columnas()` para consistencia
- ✅ Aplicado a: categorías, subtipos, selección de archivos

**Beneficios:**
- Interfaz más compacta
- Mejor uso del espacio
- Experiencia visual consistente

### 3. Selección Múltiple de Archivos

**Funcionalidad:**
- ✅ Cuando hay múltiples archivos en una carpeta/mes:
  - Botón "📦 Descargar todos" al inicio
  - Botones individuales para cada archivo (máximo 10)
  - Organizados en 2 columnas
  - Si hay más de 10, mensaje indicando usar "Descargar todos"

**Métodos nuevos:**
- `_mostrar_menu_seleccion_archivos()` - Muestra menú de selección
- `_enviar_archivo_individual()` - Envía un archivo específico
- `_enviar_todos_los_archivos()` - Envía todos los archivos

### 4. URLs Firmadas

**Implementado:**
- ✅ Generación de URLs firmadas con `create_signed_url()`
- ✅ Expiración de 1 hora
- ✅ Regeneración automática al listar archivos
- ✅ Funciona incluso si el bucket es privado

**Fallbacks:**
- Si falla URL firmada → intenta URL pública
- Si falla URL pública → construye URL manualmente

### 5. Comandos de Control

**Nuevos comandos:**
- `/start` - Limpia sesiones activas y muestra menú principal
- `/cancelar` - Cancela sesión activa explícitamente

**Botón "Salir":**
- Ahora también limpia sesiones activas antes de salir

### 6. Nuevo Botón en Menú Principal

**Agregado:**
- "📈 Reporte CFO" al lado de "📊 Información"
- Handler creado: `_handle_reporte_cfo()`
- Estado: Funcionalidad en desarrollo (placeholder)

### 7. Correcciones de Errores

**Corregidos:**
- ✅ Error en IA: `datetime.timedelta` → `timedelta`
- ✅ Error de URLs: Implementación de URLs firmadas
- ✅ Error de Storage: Uso de clave de servicio para bypass RLS
- ✅ Error de sanitización: Nombres de archivo con caracteres especiales
- ✅ Error de callbacks: Manejo correcto de `Message` vs `CallbackQuery`

---

## 📊 Estructura del Menú Principal

```
┌─────────────────┬─────────────────┐
│ 📊 Información  │ 📈 Reporte CFO  │
├─────────────────┼─────────────────┤
│ ⏳ Pendientes   │ 💰 CxC & CxP    │
├─────────────────┼─────────────────┤
│ 🤖 Asesor IA    │ 📅 Agendar      │
├─────────────────┼─────────────────┤
│ ℹ️ Ayuda        │ 🚪 Salir        │
└─────────────────┴─────────────────┘
```

---

## 🔧 Cambios Técnicos

### Archivos Modificados

1. **`app/utils/file_types.py`**
   - Agregada función `organizar_botones_en_columnas()`

2. **`app/bots/handlers/production_handlers.py`**
   - Menú principal reorganizado
   - Agregado botón "Reporte CFO"
   - Eliminada detección de lenguaje natural
   - Comandos `/start` y `/cancelar` mejorados

3. **`app/bots/handlers/file_download_handler.py`**
   - Flujo completamente estructurado
   - Menús en 2 columnas
   - Selección múltiple de archivos
   - Métodos para envío individual y múltiple

4. **`app/services/storage_service.py`**
   - URLs firmadas implementadas
   - Sanitización de nombres de archivo
   - Uso de clave de servicio

5. **`app/services/ai_service.py`**
   - Corrección de error `datetime.timedelta`
   - Código preservado para uso futuro

---

## 📈 Mejoras de UX

### Antes vs Ahora

| Aspecto | Antes | Ahora |
|---------|-------|-------|
| **Descarga** | Lenguaje natural + IA | Botones estructurados |
| **Menús** | 1 columna | 2 columnas |
| **Múltiples archivos** | Lista de links | Menú de selección |
| **URLs** | Públicas (pueden fallar) | Firmadas (siempre funcionan) |
| **Sesiones** | Sin control | `/start` y `/cancelar` |

---

## ✅ Estado Actual

### Funcionalidades Completas
- ✅ Subida de archivos (flujo completo)
- ✅ Descarga de archivos (flujo estructurado)
- ✅ Menús en 2 columnas
- ✅ Selección múltiple
- ✅ URLs firmadas
- ✅ Comandos de control
- ✅ Botón Reporte CFO (placeholder)

### Pendiente
- ⏳ Implementación completa de Reporte CFO
- ⏳ Testing end-to-end
- ⏳ Métricas y analytics

---

## 🆕 Cambios del 2025-11-12

### 7. Sistema de Roles y Permisos ⭐ **NUEVO**

**Implementado:**
- ✅ 3 niveles de roles: `super_admin`, `gestor`, `usuario`
- ✅ Validaciones de permisos antes de cada operación
- ✅ Métodos de seguridad: `can_upload_files()`, `can_download_files()`, `can_manage_empresas()`
- ✅ Roles asignados:
  - **super_admin**: The Wingman (7580149783), Christian Matthews (866310278)
  - **usuario**: Patricio Alarcon (2134113487) - Solo puede descargar archivos

**Permisos por rol:**
- **super_admin**: Todos los permisos (crear empresas, asignar usuarios, subir/bajar archivos)
- **gestor**: Asignar empresas, subir y bajar archivos
- **usuario**: Solo descargar archivos (NO puede subir)

### 8. Multiempresa ⭐ **NUEVO**

**Implementado:**
- ✅ Tabla `usuarios_empresas` creada (relación muchos a muchos)
- ✅ Migración automática de datos existentes
- ✅ Métodos `get_user_empresas()` y `user_has_access_to_empresa()` funcionando
- ✅ Usuario con múltiples empresas: Christian Matthews (2 empresas)

**Funcionalidad:**
- Si usuario tiene 1 empresa → se asigna automáticamente
- Si usuario tiene múltiples empresas → muestra menú de selección
- Roles diferentes por empresa para el mismo usuario

### 9. Migraciones SQL

**Nuevas migraciones:**
- `003_create_usuarios_empresas.sql` - Tabla multiempresa
- `004_sistema_roles_permisos.sql` - Sistema de roles y permisos

---

**Última actualización:** 2025-11-12


