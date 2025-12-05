# 📋 Tareas Pendientes - ACA 4.0

**Fecha actualización:** 2025-11-13  
**Estado:** Actualizado después de sesión de correcciones

---

## ✅ COMPLETADAS (2025-11-13)

### **Sistemas Principales:**
1. ✅ Sistema de descarga de archivos funcionando completamente
2. ✅ Sistema de subida de archivos funcionando completamente
3. ✅ Sistema multi-empresa funcionando
4. ✅ RLS y permisos corregidos
5. ✅ Handler de texto unificado
6. ✅ Análisis de períodos con IA
7. ✅ Comando /adduser simplificado
8. ✅ Menús estandarizados en 2 columnas
9. ✅ Campo "Empresa" en mensajes
10. ✅ Comandos de control (/start, Salir, Cancelar)

---

## 🔴 CRÍTICAS (Alta Prioridad)

### **1. Verificar generación de URLs firmadas**
**Estado:** ⚠️ Logs agregados para debugging, pendiente verificar formato exacto

**Problema potencial:**
- `create_signed_url()` puede retornar diferentes formatos según versión de supabase-py
- Logs agregados para identificar formato exacto

**Acción:**
- Probar descarga de archivo
- Revisar logs de "🔍 Respuesta de create_signed_url"
- Ajustar extracción de URL según formato real

---

### **2. Validaciones de permisos en handlers**
**Estado:** ⏳ Pendiente implementar

**Archivos:**
- `app/bots/handlers/file_upload_handler.py` - Validar `can_upload_files()` antes de subir
- `app/bots/handlers/file_download_handler.py` - Validar `can_download_files()` antes de descargar

**Acción:**
- Agregar `if not security.can_upload_files(chat_id):` en handle_document
- Agregar validaciones similares en otros handlers

---

## 🟡 IMPORTANTES (Media Prioridad)

### **3. Tabla `pendientes` no existe**
**Estado:** ⏳ Pendiente crear o deshabilitar funcionalidad

**Opciones:**
1. Crear tabla `pendientes` en Supabase
2. Deshabilitar funcionalidad temporalmente
3. Implementar como FASE 2

**Recomendación:** Marcar como FASE 2 hasta que se requiera

---

### **4. Tablas de CxC y CxP**
**Estado:** ⏳ Pendiente crear o deshabilitar

**Tablas faltantes:**
- `cuentas_cobrar`
- `cuentas_pagar`

**Recomendación:** Marcar como FASE 2

---

### **5. Reporte CFO - Mejorar funcionalidad**
**Estado actual:**
- ✅ Botón existe
- ✅ Handler básico funciona
- ⏳ Pendiente mejoras en visualización

**Mejoras pendientes:**
- Formato más legible de JSON
- Gráficos o visualizaciones
- Exportar a PDF

---

### **6. Testing de URLs firmadas en producción**
**Estado:** ⏳ Pendiente verificar en producción

**Pendiente:**
- Verificar que URLs firmadas funcionen correctamente
- Probar expiración después de 1 hora
- Verificar regeneración automática

---

## 🟢 MEJORAS (Baja Prioridad)

### **7. Documentación de API**
**Estado:** ⏳ Pendiente

**Pendiente:**
- Documentar endpoints de API REST
- Agregar ejemplos de uso
- Swagger/OpenAPI specs

---

### **8. Tests automatizados**
**Estado:** ⏳ Pendiente

**Pendiente:**
- Tests unitarios de servicios
- Tests de integración de handlers
- Tests de flujos completos

---

### **9. Métricas y Analytics**
**Estado:** ⏳ Pendiente

**Pendiente:**
- Dashboard de métricas
- Estadísticas de uso
- Reportes de actividad

---

### **10. Optimizaciones de rendimiento**
**Estado:** ⏳ Opcional

**Posibles mejoras:**
- Cache de consultas frecuentes
- Paginación en listados largos
- Compresión de archivos grandes

---

## 📊 Resumen por Estado

### ✅ Completadas: 10 tareas
- Sistema de archivos completo
- Multi-empresa funcionando
- Comando /adduser simplificado
- Menús estandarizados
- Handler de texto unificado

### ⚠️ En progreso: 1 tarea
- Verificación de URLs firmadas (logs agregados)

### ⏳ Pendientes Alta: 1 tarea
- Validaciones de permisos en handlers

### ⏳ Pendientes Media: 4 tareas
- Tablas faltantes
- Mejoras en Reporte CFO
- Testing de URLs

### ⏳ Pendientes Baja: 4 tareas
- Documentación API
- Tests automatizados
- Métricas
- Optimizaciones

---

## 🎯 Roadmap

### **Fase Actual (Completada):**
- ✅ Sistema de archivos funcionando
- ✅ Multi-empresa funcionando
- ✅ Comandos administrativos simplificados

### **Próxima Fase:**
1. Validaciones de permisos completas
2. Verificar URLs firmadas
3. Decidir sobre tablas pendientes/CxC/CxP

### **Futuro:**
- Reporte CFO mejorado
- Tests automatizados
- Métricas y analytics

---

**Última actualización:** 2025-11-13



