# 🔒 Próximos Pasos - Validación de Permisos de Subida

**Fecha:** 2025-11-14  
**Problema:** Sistema de roles no se aplica en subida de archivos  
**Estado:** Pendiente de decisión e implementación

---

## 🎯 Problema Identificado

### Situación Actual

**Lo que funciona:**
- ✅ Usuario debe estar registrado
- ✅ Usuario debe tener empresas asignadas
- ✅ Solo puede subir a empresas donde está asignado (multiempresa)
- ✅ Sistema de roles está implementado (`can_upload_files()` existe)

**Lo que no funciona:**
- ❌ No se valida el rol del usuario antes de subir
- ❌ Usuario con rol `usuario` puede subir archivos
- ❌ Sistema de roles no se aplica en la práctica

### Escenario de Riesgo

**Usuario:** Patricio Alarcon (rol: `usuario`)  
**Empresa:** Factor IT  
**Esperado:** Solo puede descargar archivos  
**Actual:** Puede subir archivos sin restricción

### Impacto del Problema

**Riesgo de seguridad:** Bajo
- No puede acceder a otras empresas
- Validación de empresa funciona correctamente

**Riesgo funcional:** Medio
- Contaminación de datos (archivos subidos sin autorización)
- Clasificación incorrecta posible
- Auditoría: no se distingue quién debería poder subir
- Violación del diseño del sistema de roles

---

## 🔄 Alternativa 1: Bot Separado para Subida

### Descripción

Crear un bot de Telegram adicional exclusivamente para subida de archivos, separado del bot de producción actual.

### Arquitectura Propuesta

```
Bot Producción (actual):
- Descarga de archivos
- Consultas
- Asesor IA
- Reporte CFO
- TODOS los usuarios

Bot Subida (nuevo):
- Solo subida de archivos
- Solo usuarios con rol super_admin o gestor
- Token separado
```

### Pros

- ✅ Separación clara de responsabilidades
- ✅ No tocamos código que funciona (cero riesgo de romper)
- ✅ Control total sobre quién accede (configuración de usuarios en Telegram)
- ✅ Aislamiento de funcionalidad crítica
- ✅ Más fácil de auditar (logs separados)

### Contras

- ❌ Usuarios necesitan 2 bots diferentes (confusión UX)
- ❌ Duplicación de código (handlers, sesiones, storage)
- ❌ Más complejo de mantener (2 bots en vez de 1)
- ❌ Más costoso operativamente (más recursos, monitoreo)
- ❌ Fragmentación de la experiencia de usuario

### Pasos de Implementación

1. **Crear nuevo bot en Telegram:**
   - Ir a @BotFather
   - `/newbot` → nombre: "ACA Upload Bot"
   - Obtener token: `BOT_UPLOAD_TOKEN`

2. **Agregar token a .env:**
   ```bash
   BOT_UPLOAD_TOKEN=nuevo_token_aqui
   ```

3. **Crear nuevo handler:**
   - Duplicar `file_upload_handler.py`
   - Crear `upload_bot_manager.py`
   - Configurar solo handlers de subida

4. **Modificar main.py:**
   - Agregar inicialización de bot de subida
   - Registrar handlers

5. **Configurar usuarios:**
   - Solo agregar super_admin y gestor al nuevo bot
   - Remover handler de documentos del bot producción

6. **Testing:**
   - Probar subida con nuevo bot
   - Verificar que bot producción no permite subida
   - Probar descarga desde bot producción

### Riesgo de Implementación

**Nivel:** ⚠️ Bajo (no rompe nada)  
**Tiempo estimado:** 4-6 horas  
**Complejidad operativa:** Alta  
**Recomendado:** No (complejidad innecesaria)

---

## ✅ Alternativa 2: Agregar Validación en Código Actual

### Descripción

Agregar validación de permisos en los puntos de entrada del flujo de subida actual.

### Opción 2A: Validación al Inicio (Recomendada)

#### Ubicación del Cambio

**Archivo:** `app/bots/handlers/file_upload_handler.py`  
**Método:** `handle_document()`  
**Línea:** Después de línea 48 (después de `validation = security.validate_user()`)

#### Código a Agregar

```python
# Después de línea 48 (validation exitosa)
user_data = validation['user_data']
document = update.message.document

# ⬇️ AGREGAR ESTAS 6 LÍNEAS (línea ~51)
# Validar permisos de subida
empresas = await FileUploadHandler._get_user_empresas(chat_id)
if empresas and not security.can_upload_files(chat_id, empresas[0]['id']):
    await update.message.reply_text(
        "❌ No tienes permisos para subir archivos.\n\n"
        "Contacta al administrador si necesitas este acceso."
    )
    return

# Continúa código existente...
file_info = await context.bot.get_file(document.file_id)
```

#### Pros

- ✅ Falla rápido (antes de iniciar flujo)
- ✅ Usuario sabe inmediatamente que no puede
- ✅ No gasta sesiones ni procesa archivo innecesariamente
- ✅ Cambio mínimo (solo 6 líneas)
- ✅ Implementación en un solo lugar
- ✅ No duplicación de código
- ✅ Fácil de entender y mantener

#### Contras

- ⚠️ Usuario envía archivo → recibe rechazo inmediato
- ⚠️ Puede ser frustrante si no conoce las reglas (pero es el comportamiento esperado)

#### Riesgo de Romper Algo

**Nivel:** 🟢 Muy Bajo

**Por qué:**
- Se ejecuta después de validaciones existentes
- No modifica flujo de usuarios con permisos
- Solo agrega un return temprano para usuarios sin permisos
- No toca lógica de sesiones, storage o callbacks
- Cambio aislado y específico

---

### Opción 2B: Validación Antes de Subir (Alternativa)

#### Ubicación del Cambio

**Archivo:** `app/bots/handlers/file_upload_handler.py`  
**Método:** `_confirmar_subida()`  
**Línea:** Antes de llamar `storage_service.upload_file()`

#### Código a Agregar

```python
# Antes de subir a storage (línea ~510)
# Validar permisos una última vez
if not security.can_upload_files(chat_id, empresa_id):
    mensaje_error = (
        "❌ No tienes permisos para subir archivos a esta empresa.\n\n"
        "Contacta al administrador."
    )
    if is_callback:
        await message_or_query.edit_message_text(mensaje_error)
    else:
        await message_or_query.reply_text(mensaje_error)
    
    # Limpiar sesión
    session_manager.clear_session(chat_id)
    return

# Continúa con upload_file()...
```

#### Pros

- ✅ Usuario completa todo el flujo de clasificación
- ✅ Validación justo antes de acción crítica
- ✅ Si usuario cambia de empresa en el flujo, valida la empresa correcta
- ✅ Útil si en el futuro permitimos cambiar empresa mid-flow

#### Contras

- ❌ Usuario pierde tiempo clasificando si no puede subir
- ❌ Sesión se crea y luego falla
- ❌ Experiencia de usuario subóptima

#### Riesgo de Romper Algo

**Nivel:** 🟢 Muy Bajo

**Por qué:**
- Se ejecuta justo antes de `storage_service.upload_file()`
- No afecta el resto del flujo
- Limpia sesión correctamente antes de salir

---

## 🎯 Recomendación Final

### ✅ Opción 2A (Validación al Inicio)

**Por qué:**

1. **Seguridad:** Falla rápido, evita procesamiento innecesario
2. **UX:** Usuario sabe inmediatamente su situación
3. **Riesgo mínimo:** Solo 6 líneas agregadas después de validaciones existentes
4. **No rompe nada:** Usuarios con permisos no ven ningún cambio
5. **Implementación simple:** Un solo punto de cambio
6. **Mantenibilidad:** Fácil de entender y modificar en el futuro

### Comparación de Alternativas

| Aspecto | Alt 1: Bot Separado | Alt 2A: Validación Inicio | Alt 2B: Validación Final |
|---------|---------------------|---------------------------|--------------------------|
| **Riesgo de romper** | 🟢 Ninguno | 🟢 Muy bajo | 🟢 Muy bajo |
| **Complejidad** | 🔴 Alta | 🟢 Muy baja | 🟡 Baja |
| **UX** | 🔴 Confusa | 🟢 Clara | 🟡 Aceptable |
| **Mantenibilidad** | 🔴 Difícil | 🟢 Fácil | 🟢 Fácil |
| **Tiempo implementación** | 4-6 horas | 15 minutos | 20 minutos |
| **Costo operativo** | 🔴 Alto | 🟢 Ninguno | 🟢 Ninguno |

---

## 📋 Plan de Implementación (Opción 2A)

### Paso 1: Backup

```bash
# Hacer backup del handler actual
cp app/bots/handlers/file_upload_handler.py app/bots/handlers/file_upload_handler.py.backup
```

### Paso 2: Modificar Código

**Archivo:** `app/bots/handlers/file_upload_handler.py`

**Ubicación exacta:** Después de línea 48

**Código actual:**
```python
    validation = security.validate_user(chat_id)
    if not validation['valid']:
        await update.message.reply_text(validation['message'])
        return
    
    user_data = validation['user_data']
    document = update.message.document
    
    # Obtener información del archivo
    file_info = await context.bot.get_file(document.file_id)
```

**Código modificado:**
```python
    validation = security.validate_user(chat_id)
    if not validation['valid']:
        await update.message.reply_text(validation['message'])
        return
    
    user_data = validation['user_data']
    document = update.message.document
    
    # ⬇️ NUEVO: Validar permisos de subida
    empresas = await FileUploadHandler._get_user_empresas(chat_id)
    if empresas and not security.can_upload_files(chat_id, empresas[0]['id']):
        await update.message.reply_text(
            "❌ No tienes permisos para subir archivos.\n\n"
            "Contacta al administrador si necesitas este acceso."
        )
        return
    # ⬆️ FIN NUEVO
    
    # Obtener información del archivo
    file_info = await context.bot.get_file(document.file_id)
```

### Paso 3: Testing

**Test 1 - Usuario con permisos (super_admin o gestor):**
```bash
# Enviar archivo como The Wingman o Christian Matthews
# Esperado: Flujo normal, archivo se sube correctamente
```

**Test 2 - Usuario sin permisos (usuario):**
```bash
# Enviar archivo como Patricio Alarcon
# Esperado: Mensaje "❌ No tienes permisos para subir archivos"
```

**Test 3 - Usuario sin registro:**
```bash
# Enviar archivo con usuario no registrado
# Esperado: Mensaje "❌ Usuario no registrado" (comportamiento actual)
```

### Paso 4: Rollback si Falla

```bash
# Si algo sale mal, restaurar backup
cp app/bots/handlers/file_upload_handler.py.backup app/bots/handlers/file_upload_handler.py

# Reiniciar bot
pkill -f "python.*run.py"
python3 run.py
```

### Paso 5: Documentar

- Actualizar `docs/ESTADO_ACTUAL_SISTEMA.md`
- Marcar como completado en `docs/PENDIENTES.md`
- Agregar en `docs/CAMBIOS_RECIENTES.md`

---

## 🧪 Casos de Prueba

### Caso 1: Usuario super_admin

**Usuario:** The Wingman (7580149783)  
**Acción:** Enviar archivo PDF  
**Esperado:** ✅ Flujo normal, archivo se sube

### Caso 2: Usuario gestor

**Usuario:** (Por asignar con rol gestor)  
**Acción:** Enviar archivo PDF  
**Esperado:** ✅ Flujo normal, archivo se sube

### Caso 3: Usuario usuario

**Usuario:** Patricio Alarcon (2134113487)  
**Acción:** Enviar archivo PDF  
**Esperado:** ❌ Mensaje "No tienes permisos para subir archivos"

### Caso 4: Usuario no registrado

**Usuario:** Chat ID aleatorio  
**Acción:** Enviar archivo PDF  
**Esperado:** ❌ Mensaje "Usuario no registrado"

---

## 📊 Análisis de Impacto

### Usuarios Afectados

**Actualmente:**
- The Wingman: super_admin → ✅ Sin cambios (puede subir)
- Christian Matthews: super_admin → ✅ Sin cambios (puede subir)
- Patricio Alarcon: usuario → ⚠️ Se bloqueará (no podrá subir)

**Total usuarios afectados negativamente:** 1 (Patricio)

### Acciones Post-Implementación

Si Patricio necesita subir archivos:
```bash
# Opción 1: Cambiar su rol a gestor
UPDATE usuarios_empresas 
SET rol = 'gestor' 
WHERE chat_id = 2134113487 AND empresa_id = 'uuid_factorit';

# Opción 2: Actualizar con comando
/adduser 2134113487 "Patricio Alarcon" gestor 76142021-6
```

---

## ⏭️ Próximos Pasos Después de Implementar

1. ✅ Implementar validación de permisos en subida
2. ⏳ Verificar URLs firmadas en producción (logs ya agregados)
3. ⏳ Testing end-to-end con diferentes roles
4. ⏳ Decidir sobre tablas pendientes/CxC/CxP (FASE 2)
5. ⏳ Mejorar visualización de Reporte CFO

---

## 🤔 Preguntas para Decidir

1. ¿Patricio Alarcon debería poder subir archivos?
   - Si sí → cambiar su rol a `gestor`
   - Si no → implementar validación como está

2. ¿Preferimos bot separado o validación en código actual?
   - Bot separado: más seguro pero más complejo
   - Validación en código: más simple y efectivo

3. ¿Cuándo implementar?
   - Ahora: riesgo muy bajo, cambio pequeño
   - Después: el problema persiste

---

**Última actualización:** 2025-11-14  
**Estado:** Pendiente de decisión  
**Recomendación:** Alternativa 2A (Validación al Inicio)








