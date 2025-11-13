# ⚠️ NO OLVIDAR - Puntos Críticos del Sistema

**Fecha:** 2025-11-13  
**Propósito:** Prevenir "alucinaciones" y errores en futuras sesiones

---

## 🔴 CRÍTICO - CONFIGURACIÓN

### **1. Cliente Supabase DEBE usar SERVICE_KEY**

**Archivo:** `app/database/supabase.py` línea 19

```python
# ✅ CORRECTO:
create_client(Config.SUPABASE_URL, Config.SUPABASE_SERVICE_KEY)

# ❌ INCORRECTO:
create_client(Config.SUPABASE_URL, Config.SUPABASE_KEY)
```

**Por qué:** El SUPABASE_KEY (anon key) está sujeto a RLS y bloqueará operaciones de backend.

---

## 🔴 CRÍTICO - SISTEMA MULTI-EMPRESA

### **2. Método para obtener empresas del usuario**

**Archivos:**
- `app/bots/handlers/file_upload_handler.py`
- `app/bots/handlers/file_download_handler.py`

```python
# ✅ CORRECTO:
empresas = supabase.get_user_empresas(chat_id)
# Retorna TODAS las empresas desde tabla usuarios_empresas

# ❌ INCORRECTO:
user = supabase.get_user_by_chat_id(chat_id)
empresa_id = user.get('empresa_id')  # Solo retorna 1 empresa (legacy)
```

**Por qué:** The Wingman y otros usuarios tienen múltiples empresas asignadas.

---

## 🔴 CRÍTICO - ORDEN DE PREGUNTAS EN DESCARGA

### **3. Pregunta de empresa AL FINAL**

**Archivo:** `app/bots/handlers/file_download_handler.py`

**Orden CORRECTO:**
```
1. Categoría
2. Subtipo
3. Período
4. Empresa (SOLO si tiene múltiples) ← AL FINAL
5. Buscar archivos
```

**Orden INCORRECTO:**
```
1. Empresa ← ❌ NO AL INICIO
2. Categoría
3. Subtipo
4. Período
```

**Por qué:** La documentación especifica que la empresa se pregunta al final del flujo.

---

## 🔴 CRÍTICO - HANDLERS DE TEXTO

### **4. Handler unificado de texto**

**Archivo:** `app/bots/bot_manager.py` líneas 66-89

**Debe haber UN SOLO handler de texto que delegue según intent:**

```python
async def unified_text_handler(update, context):
    session = session_manager.get_session(chat_id)
    
    if session:
        intent = session.get('intent')
        if intent == 'descargar_archivo':
            await FileDownloadHandler.handle_text_during_download(...)
        elif intent == 'subir_archivo':
            await FileUploadHandler.handle_text_during_upload(...)
    else:
        await ProductionHandlers.handle_message(...)
```

**❌ NO hacer:**
```python
# Múltiples handlers que compiten:
add_handler(FileDownloadHandler.handle_text_during_download)
add_handler(FileUploadHandler.handle_text_during_upload)
add_handler(ProductionHandlers.handle_message)
```

**Por qué:** El primer handler intercepta todos los mensajes y los demás nunca se ejecutan.

---

## 🔴 CRÍTICO - SANITIZACIÓN DE NOMBRES

### **5. Nombres de archivo DEBEN sanitizarse**

**Archivo:** `app/services/storage_service.py` líneas 260-293

**Proceso obligatorio:**
1. Normalizar Unicode (tildes → ASCII)
2. Reemplazar espacios por guiones bajos
3. Eliminar caracteres especiales
4. Agregar timestamp único

**Ejemplo:**
```
"Evaluación desempeño.pdf" → "Evaluacion_desempeno_20251113_094500.pdf"
```

**Por qué:** Supabase Storage rechaza nombres con tildes y caracteres especiales.

---

## 🔴 CRÍTICO - CALLBACKS

### **6. Enrutamiento de callbacks en ProductionHandlers**

**Archivo:** `app/bots/handlers/production_handlers.py`

**DEBE incluir:**
```python
# Callbacks de DESCARGA
if callback_data.startswith("download_"):
    await FileDownloadHandler.handle_download_callback(update, context)
    return

# Callbacks de SUBIDA  
if callback_data.startswith("upload_"):
    await FileUploadHandler.handle_upload_callback(update, context)
    return
```

**Por qué:** Sin esto, los botones del flujo de descarga/subida no funcionan.

---

## 🔴 CRÍTICO - COMANDOS QUE CANCELAN SESIONES

### **7. /start y Salir deben limpiar sesiones**

**Archivos:**
- `app/bots/handlers/production_handlers.py`

**En /start:**
```python
session = session_manager.get_session(chat_id)
if session:
    session_manager.clear_session(chat_id)
```

**En Salir:**
```python
session = session_manager.get_session(chat_id)
if session:
    session_manager.clear_session(chat_id)
```

**Por qué:** Evita que usuarios queden atrapados en procesos incompletos.

---

## 🔴 CRÍTICO - FORMATO ADDUSER

### **8. Comando /adduser simplificado**

**Formato CORRECTO:**
```
/adduser CHAT_ID NOMBRE ROL RUT_EMPRESA
```

**Ejemplo:**
```
/adduser 123456789 Juan Perez user 76142021-6
```

**❌ Formato INCORRECTO (legacy):**
```
/adduser CHAT_ID UUID_EMPRESA
```

**Por qué:** El RUT es más fácil de recordar que el UUID.

---

## 🔴 CRÍTICO - MENÚS EN 2 COLUMNAS

### **9. Todos los menús deben usar 2 columnas**

```python
from app.utils.file_types import organizar_botones_en_columnas

botones = [btn1, btn2, btn3, btn4]
keyboard = organizar_botones_en_columnas(botones, columnas=2)
```

**Menús que DEBEN estar en 2 columnas:**
- ✅ Categorías
- ✅ Subtipos
- ✅ Empresas
- ✅ Selección múltiple de archivos

**Por qué:** Consistencia visual y mejor uso del espacio.

---

## 🔴 CRÍTICO - MESSAGE VS CALLBACKQUERY

### **10. Detectar tipo de objeto antes de editar mensaje**

```python
# ✅ CORRECTO:
is_callback = hasattr(message_or_query, 'edit_message_text')

if is_callback:
    await message_or_query.edit_message_text(text)
else:
    await message_or_query.reply_text(text)

# ❌ INCORRECTO:
await message_or_query.edit_message_text(text)  # Falla si es Message
```

**Por qué:** `Message` no tiene método `edit_message_text()`, solo `CallbackQuery` lo tiene.

---

## 📊 CAMPOS DE BD - TABLA ARCHIVOS

### **11. Campos correctos en tabla archivos**

**Campo para tipo MIME:**
```
mime_type  ← ✅ CORRECTO
tipo_archivo ← ❌ INCORRECTO (legacy)
```

**Campos de clasificación:**
```
categoria - 'legal' o 'financiero'
tipo - Categoría principal
subtipo - estatutos_empresa, f29, etc.
periodo - Formato YYYY-MM
descripcion_personalizada - Para subtipo "otros"
```

**Por qué:** La migración 001 renombró `tipo_archivo` a `mime_type`.

---

## 🔍 DEBUGGING

### **12. Logs importantes para depuración**

**Cuando hay problemas:**
```bash
tail -f aca_bot.log | grep -E "(🔍|📋|📁|❌|ERROR)"
```

**Logs clave agregados:**
- `🔍 Callback recibido: 'download_categoria_legal'`
- `📋 session_data actual: empresa_id=..., categoria=..., subtipo=..., periodo=...`
- `🏢 Usuario tiene 2 empresa(s)`
- `✅ Usuario tiene 2 empresas, preguntando cuál seleccionar`
- `📄 Mostrando archivo: nombre.pdf, URL generada: True`

---

## 📝 DOCUMENTACIÓN ACTUALIZADA

**Lee SIEMPRE estos documentos antes de hacer cambios:**

1. **ESTADO_ACTUAL_SISTEMA.md** - Estado completo y actual
2. **REFERENCIA_RAPIDA.md** - Comandos y flujos
3. **NO_OLVIDAR.md** - Este archivo (puntos críticos)
4. **CAMBIOS_2025-11-13.md** - Log de cambios de hoy
5. **LOGICA_DESCARGA_EMPRESA.md** - Flujo de descarga detallado

**❌ NO confiar en:**
- Documentos antiguos sin fecha de actualización
- Comentarios en código que puedan estar desactualizados
- Suposiciones sobre el comportamiento sin verificar logs

---

## ✅ CHECKLIST ANTES DE MODIFICAR

Antes de hacer cualquier cambio al sistema, verificar:

- [ ] ¿El cliente Supabase usa SERVICE_KEY?
- [ ] ¿Los métodos usan `get_user_empresas()` correcto?
- [ ] ¿La pregunta de empresa está al FINAL?
- [ ] ¿Hay un solo handler unificado de texto?
- [ ] ¿Los nombres de archivo se sanitizan?
- [ ] ¿Los callbacks tienen enrutamiento correcto?
- [ ] ¿/start y Salir cancelan sesiones?
- [ ] ¿/adduser usa formato simplificado?
- [ ] ¿Los menús están en 2 columnas?
- [ ] ¿Se detecta Message vs CallbackQuery?

---

**Última actualización:** 2025-11-13 10:20


