# 📋 Pendientes - ACA 4.0

**Última actualización:** 2025-11-13  
**Estado:** Consolidado y actualizado

---

## ✅ COMPLETADAS (2025-11-13)

### **Sistemas Principales:**
1. ✅ Sistema de descarga de archivos funcionando completamente
2. ✅ Sistema de subida de archivos funcionando completamente
3. ✅ Sistema multi-empresa funcionando
4. ✅ RLS y permisos corregidos (uso de SERVICE_KEY)
5. ✅ Handler de texto unificado
6. ✅ Análisis de períodos con IA (con fallback manual)
7. ✅ Comando /adduser simplificado (acepta RUT en lugar de UUID)
8. ✅ Menús estandarizados en 2 columnas
9. ✅ Campo "Empresa" en mensajes de resultados
10. ✅ Comandos de control (/start, Salir, Cancelar) funcionando
11. ✅ Sanitización de nombres de archivo (tildes y caracteres especiales)
12. ✅ Timestamp único en nombres de archivo (evita duplicados)
13. ✅ Enrutamiento de callbacks (upload_* y download_*)
14. ✅ Pregunta de empresa al FINAL del flujo de descarga

---

## 🔴 CRÍTICAS (Alta Prioridad)

### **1. Validaciones de permisos en handlers**
**Estado:** ⏳ Pendiente implementar

**Archivos a modificar:**
- `app/bots/handlers/file_upload_handler.py` - Validar `can_upload_files()` antes de subir
- `app/bots/handlers/file_download_handler.py` - Validar `can_download_files()` antes de descargar
- `app/bots/handlers/production_handlers.py` - Validar permisos en operaciones

**Acción requerida:**
```python
# En file_upload_handler.py, método handle_document:
if not security.can_upload_files(chat_id):
    await message.reply_text("❌ No tienes permisos para subir archivos.")
    return
```

**Impacto:** Usuarios sin permisos pueden intentar subir archivos (aunque el sistema puede rechazarlos después)

---

### **2. Verificar generación de URLs firmadas**
**Estado:** ⚠️ Logs agregados para debugging, pendiente verificar formato exacto

**Problema potencial:**
- `create_signed_url()` puede retornar diferentes formatos según versión de supabase-py
- Logs agregados para identificar formato exacto

**Acción:**
- Probar descarga de archivo en producción
- Revisar logs de "🔍 Respuesta de create_signed_url"
- Ajustar extracción de URL según formato real si es necesario

**Ubicación:** `app/services/storage_service.py` método `get_file_url()`

---

## 🟡 IMPORTANTES (Media Prioridad)

### **3. Tabla `pendientes` no existe**
**Estado:** ⏳ Pendiente crear o deshabilitar funcionalidad

**Problema:**
- El código intenta consultar tabla `pendientes` pero no existe
- Error: `Could not find the table 'public.pendientes' in the schema cache`
- Ubicación: `app/bots/handlers/production_handlers.py` línea 402

**Opciones:**
1. Crear tabla `pendientes` en Supabase
2. Deshabilitar funcionalidad temporalmente (comentar código)
3. Implementar como FASE 2

**Recomendación:** Marcar como FASE 2 hasta que se requiera (botón "Pendientes" está deshabilitado en menú)

---

### **4. Tablas de CxC y CxP no existen**
**Estado:** ⏳ Pendiente crear o deshabilitar

**Tablas faltantes:**
- `cuentas_cobrar` - Cuentas por cobrar
- `cuentas_pagar` - Cuentas por pagar

**Recomendación:** Marcar como FASE 2 (botones "CxC & CxP" están deshabilitados en menú)

---

### **5. Reporte CFO - Mejorar funcionalidad**
**Estado actual:**
- ✅ Botón existe en menú principal
- ✅ Handler básico funciona
- ⏳ Pendiente mejoras en visualización

**Mejoras pendientes:**
- Formato más legible de JSON (actualmente muestra JSON crudo)
- Gráficos o visualizaciones
- Exportar a PDF
- Formato de tabla más amigable

**Ubicación:** `app/bots/handlers/production_handlers.py` método `_handle_reporte_cfo()`

---

### **6. Testing de URLs firmadas en producción**
**Estado:** ⏳ Pendiente verificar en producción

**Pendiente:**
- Verificar que URLs firmadas funcionen correctamente
- Probar expiración después de 1 hora
- Verificar regeneración automática cuando expiran
- Probar con diferentes tipos de archivo

---

### **7. Migración SQL 004 - Constraints de Roles (Opcional)**
**Archivo:** `database/migrations/004_sistema_roles_permisos.sql`

**Estado:**
- Script creado
- ⏳ Pendiente ejecutar en Supabase SQL Editor
- Los roles funcionan sin esto, pero agrega validación a nivel BD

**Nota:** Sistema funciona correctamente sin esta migración, es opcional para validación adicional

---

## 🟢 MEJORAS (Baja Prioridad)

### **8. Testing End-to-End**
**Estado:** ⏳ Pendiente

**Pendiente:**
- Probar flujo completo de subida con diferentes roles (super_admin, gestor, usuario)
- Probar flujo completo de descarga con diferentes roles
- Probar multiempresa con usuarios reales
- Validar que usuarios sin permisos no pueden subir
- Probar con múltiples empresas por usuario
- Probar cancelación de procesos

---

### **9. Documentación de API**
**Estado:** ⏳ Pendiente

**Pendiente:**
- Documentar endpoints de API REST
- Agregar ejemplos de uso
- Swagger/OpenAPI specs
- Documentar parámetros y respuestas

**Endpoints principales:**
- `/api/conversations/recent`
- `/api/conversations/unauthorized`
- `/api/conversations/user-history/{chat_id}`
- `/api/conversations/analytics`

---

### **10. Tests automatizados**
**Estado:** ⏳ Pendiente

**Pendiente:**
- Tests unitarios de servicios (storage_service, ai_service, session_manager)
- Tests de integración de handlers
- Tests de flujos completos (subida, descarga)
- Tests de validaciones de permisos
- Tests de sistema multi-empresa

---

### **11. Métricas y Analytics**
**Estado:** ⏳ Pendiente

**Pendiente:**
- Dashboard de métricas
- Estadísticas de uso (archivos subidos, descargados, por empresa)
- Reportes de actividad
- Análisis de uso por usuario
- Métricas de rendimiento

---

### **12. Optimizaciones de rendimiento**
**Estado:** ⏳ Opcional

**Posibles mejoras:**
- Cache de consultas frecuentes (empresas de usuario, tipos de archivo)
- Paginación en listados largos (si hay muchos archivos)
- Compresión de archivos grandes antes de subir
- Optimización de consultas SQL

---

## 📊 Resumen por Estado

### ✅ Completadas: 14 tareas
- Sistema de archivos completo (subida y descarga)
- Multi-empresa funcionando
- Comando /adduser simplificado
- Menús estandarizados en 2 columnas
- Handler de texto unificado
- Correcciones de RLS, callbacks, sanitización, etc.

### ⚠️ En progreso: 1 tarea
- Verificación de URLs firmadas (logs agregados, pendiente probar)

### ⏳ Pendientes Alta: 2 tareas
- Validaciones de permisos en handlers
- Verificar URLs firmadas

### ⏳ Pendientes Media: 5 tareas
- Tabla pendientes (FASE 2)
- Tablas CxC y CxP (FASE 2)
- Mejoras en Reporte CFO
- Testing de URLs en producción
- Migración SQL 004 (opcional)

### ⏳ Pendientes Baja: 4 tareas
- Testing end-to-end
- Documentación API
- Tests automatizados
- Métricas y analytics
- Optimizaciones

---

## 🎯 Roadmap

### **Fase Actual (Completada):**
- ✅ Sistema de archivos funcionando completamente
- ✅ Multi-empresa funcionando
- ✅ Comandos administrativos simplificados
- ✅ Correcciones críticas (RLS, callbacks, sanitización)

### **Próxima Fase (Prioridad Alta):**
1. ⏳ Implementar validaciones de permisos en handlers
2. ⏳ Verificar y ajustar URLs firmadas si es necesario

### **Fase 2 (Cuando se requiera):**
- ⏳ Crear tablas pendientes, CxC y CxP
- ⏳ Implementar funcionalidad completa de estas tablas

### **Mejoras Futuras:**
- ⏳ Reporte CFO mejorado (visualización)
- ⏳ Tests automatizados
- ⏳ Métricas y analytics
- ⏳ Optimizaciones de rendimiento

---

## 📝 Notas

- **Tablas faltantes:** Las tablas `pendientes`, `cuentas_cobrar` y `cuentas_pagar` están marcadas como FASE 2 porque los botones correspondientes están deshabilitados en el menú principal
- **Validaciones de permisos:** Aunque el sistema tiene métodos de seguridad (`can_upload_files`, `can_download_files`), no se están llamando en todos los handlers. Es importante implementarlas para seguridad completa
- **URLs firmadas:** El sistema genera URLs firmadas correctamente, pero se agregaron logs para verificar el formato exacto de la respuesta de Supabase

---

**Última actualización:** 2025-11-13

