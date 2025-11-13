# 📋 Pendientes - ACA 4.0

**Última actualización:** 2025-11-12

---

## 🔴 CRÍTICOS (Alta Prioridad)

### 1. Tabla `pendientes` no existe en Supabase
**Problema:**
- El código intenta consultar tabla `pendientes` pero no existe
- Error: `Could not find the table 'public.pendientes' in the schema cache`
- Ubicación: `app/bots/handlers/production_handlers.py` línea 402

**Solución:**
- Crear tabla `pendientes` en Supabase
- O deshabilitar funcionalidad hasta que se implemente

**Estado:** ⚠️ Error activo en producción

---

### 2. Actualizar Handlers para Validaciones de Permisos
**Archivos pendientes:**
- `app/bots/handlers/file_upload_handler.py` - Validar `can_upload_files()` antes de subir
- `app/bots/handlers/file_download_handler.py` - Validar `can_download_files()` antes de descargar
- `app/bots/handlers/production_handlers.py` - Validar permisos en operaciones

**Estado:** ⏳ Pendiente de implementar

---

## 🟡 IMPORTANTES (Media Prioridad)

### 3. Tablas faltantes en Base de Datos
**Tablas que el código intenta usar pero no existen:**
- `pendientes` - Tareas pendientes por empresa
- `cuentas_cobrar` - Cuentas por cobrar
- `cuentas_pagar` - Cuentas por pagar

**Estado:** ⏳ Pendiente crear tablas o deshabilitar funcionalidad

---

### 4. Reporte CFO - Funcionalidad Incompleta
**Estado actual:**
- Botón existe en menú principal
- Handler creado pero es placeholder
- Método `get_reportes_cfo()` existe pero funcionalidad básica

**Estado:** ⏳ En desarrollo

---

### 5. Migración SQL 004 - Constraints de Roles
**Archivo:** `database/migrations/004_sistema_roles_permisos.sql`

**Estado:**
- Script creado
- ⏳ Pendiente ejecutar en Supabase SQL Editor
- Los roles funcionan sin esto, pero agrega validación a nivel BD

**Estado:** ⏳ Opcional (sistema funciona sin esto)

---

## 🟢 MEJORAS (Baja Prioridad)

### 6. Testing End-to-End
**Pendiente:**
- Probar flujo completo de subida con diferentes roles
- Probar flujo completo de descarga con diferentes roles
- Probar multiempresa con usuarios reales
- Validar que usuarios sin permisos no pueden subir

**Estado:** ⏳ Pendiente

---

### 7. Métricas y Analytics
**Pendiente:**
- Dashboard de métricas
- Estadísticas de uso
- Reportes de actividad

**Estado:** ⏳ Pendiente

---

## 📊 Resumen por Categoría

### Errores Activos
- ❌ Tabla `pendientes` no existe (causa error 404)

### Funcionalidades Incompletas
- ⏳ Validaciones de permisos en handlers
- ⏳ Reporte CFO
- ⏳ Tablas de CxC y CxP

### Mejoras Futuras
- ⏳ Testing completo
- ⏳ Métricas y analytics
- ⏳ Migración SQL 004 (opcional)

---

## 🎯 Prioridad de Implementación

### Urgente (Esta semana)
1. ✅ Crear tabla `pendientes` o deshabilitar funcionalidad
2. ✅ Actualizar handlers con validaciones de permisos

### Importante (Próximas semanas)
3. ⏳ Completar Reporte CFO
4. ⏳ Crear tablas CxC y CxP o deshabilitar funcionalidad

### Mejoras (Futuro)
5. ⏳ Testing end-to-end
6. ⏳ Métricas y analytics
7. ⏳ Ejecutar migración SQL 004

---

**Última actualización:** 2025-11-12








