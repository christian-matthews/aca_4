# 📥 Lógica de Descarga de Documentos - Flujo de Empresas

**Fecha:** 2025-11-12  
**Estado:** ✅ **IMPLEMENTADO Y FUNCIONANDO**

---

## 📋 FLUJO ACTUAL DE DESCARGA

### **1. Usuario presiona "📊 Información"**
**Ubicación:** `app/bots/handlers/production_handlers.py:147-163`

```python
if callback_data == "informacion":
    session_manager.create_session(
        chat_id=chat_id,
        intent='descargar_archivo',
        estado='esperando_categoria',
        data={}  # ✅ NO SE PREGUNTA EMPRESA AQUÍ
    )
    await FileDownloadHandler._ask_categoria(query)
```

**Resultado:** Crea sesión SIN empresa_id, muestra menú de categorías.

---

### **2. Usuario selecciona Categoría (Legal/Financiero)**
**Ubicación:** `app/bots/handlers/file_download_handler.py:663-687`

```python
if callback_data.startswith("download_categoria_"):
    categoria = callback_data.replace("download_categoria_", "")
    
    session_data['categoria'] = categoria  # Guarda categoría
    session_manager.update_session(
        chat_id=chat_id,
        estado='esperando_subtipo',
        data=session_data  # ✅ AÚN NO HAY empresa_id
    )
    await FileDownloadHandler._ask_subtipo(query, categoria)
```

**Resultado:** Guarda categoría, muestra subtipos.

---

### **3. Usuario selecciona Subtipo**
**Ubicación:** `app/bots/handlers/file_download_handler.py:729-758`

```python
if callback_data.startswith("download_subtipo_"):
    categoria = parts[0]
    subtipo = parts[1]
    
    session_data['subtipo'] = subtipo  # Guarda subtipo
    session_manager.update_session(
        chat_id=chat_id,
        estado='esperando_periodo',
        data=session_data  # ✅ TODAVÍA NO HAY empresa_id
    )
    await FileDownloadHandler._ask_periodo(query)
```

**Resultado:** Guarda subtipo, muestra períodos.

---

### **4. Usuario selecciona Período**
**Ubicación:** `app/bots/handlers/file_download_handler.py:760-807`

```python
if callback_data.startswith("download_periodo_"):
    periodo = callback_data.replace("download_periodo_", "")
    
    # Normalizar período (actual, anterior, otro)
    if periodo == "actual":
        periodo = datetime.now().strftime("%Y-%m")
    elif periodo == "anterior":
        mes_anterior = datetime.now().replace(day=1) - timedelta(days=1)
        periodo = mes_anterior.strftime("%Y-%m")
    
    session_data['periodo'] = periodo  # Guarda período
    
    # ✅ AHORA SÍ: Verificar si necesita preguntar por empresa
    empresas = await FileDownloadHandler._get_user_empresas(chat_id)
    
    if len(empresas) > 1 and not session_data.get('empresa_id'):
        # ✅ Usuario tiene MÚLTIPLES empresas → PREGUNTAR
        session_manager.update_session(
            chat_id=chat_id,
            estado='esperando_empresa',
            data=session_data
        )
        await FileDownloadHandler._ask_empresa(query, empresas, {})
    else:
        # ✅ Usuario tiene SOLO 1 empresa → AUTO-ASIGNAR
        session_manager.update_session(
            chat_id=chat_id,
            estado='listo',
            data=session_data
        )
        # Finalizar descarga directamente
        await FileDownloadHandler._finalizar_descarga(query, session_data, empresas)
```

**Resultado:**
- **Si tiene 1 empresa:** Auto-asigna y busca archivos
- **Si tiene múltiples empresas:** Muestra botones para seleccionar empresa

---

### **5. (Opcional) Usuario selecciona Empresa**
**Ubicación:** `app/bots/handlers/file_download_handler.py:705-726`

```python
if callback_data.startswith("download_empresa_"):
    empresa_id = callback_data.replace("download_empresa_", "")
    empresa = supabase.table('empresas').select('*').eq('id', empresa_id).execute()
    
    if empresa.data:
        session_data['empresa_id'] = empresa_id  # ✅ GUARDA empresa_id
        session_data['empresa_nombre'] = empresa.data[0]['nombre']
        
        session_manager.update_session(
            chat_id=chat_id,
            estado='procesando',
            data=session_data
        )
        
        # Finalizar descarga
        empresas = await FileDownloadHandler._get_user_empresas(chat_id)
        await FileDownloadHandler._finalizar_descarga(query, session_data, empresas)
```

**Resultado:** Guarda empresa seleccionada y busca archivos.

---

### **6. Búsqueda de archivos (Finalizar)**
**Ubicación:** `app/bots/handlers/file_download_handler.py:532-571`

```python
async def _finalizar_descarga(message_or_query, session_data: dict, empresas: list):
    # Determinar empresa_id
    empresa_id = session_data.get('empresa_id')
    if not empresa_id and len(empresas) == 1:
        empresa_id = empresas[0]['id']  # ✅ AUTO-ASIGNA si solo tiene 1
    
    if not empresa_id:
        await message_or_query.reply_text("❌ No se pudo determinar la empresa.")
        return
    
    # Buscar archivos con todos los criterios
    archivos = await FileDownloadHandler._buscar_archivos(
        empresa_id=empresa_id,  # ✅ Empresa asignada o seleccionada
        categoria=session_data.get('categoria'),
        subtipo=session_data.get('subtipo'),
        periodo=session_data.get('periodo')
    )
    
    # Mostrar resultados
    await FileDownloadHandler._responder_con_archivos(message_or_query, archivos, intent, empresas)
```

---

## 📊 DIAGRAMA DE FLUJO

### **Usuario con 1 EMPRESA:**

```
📊 Información
  ↓
📁 Categoría (Legal/Financiero)
  ↓
📄 Subtipo (RUT, F29, etc.)
  ↓
📅 Período (Actual/Anterior/Otro)
  ↓
✅ AUTO-ASIGNA empresa única
  ↓
🔍 Buscar archivos
  ↓
📦 Mostrar resultados
```

### **Usuario con MÚLTIPLES EMPRESAS:**

```
📊 Información
  ↓
📁 Categoría (Legal/Financiero)
  ↓
📄 Subtipo (RUT, F29, etc.)
  ↓
📅 Período (Actual/Anterior/Otro)
  ↓
❓ ¿De qué empresa? (PREGUNTA AL FINAL)
  ↓
🏢 Usuario selecciona empresa
  ↓
🔍 Buscar archivos
  ↓
📦 Mostrar resultados
```

---

## ✅ PUNTOS CLAVE DE LA IMPLEMENTACIÓN

### **1. La empresa NO se pregunta al inicio:**
- ✅ Cuando se presiona "Información", la sesión se crea SIN `empresa_id`
- ✅ No se pregunta por empresa inmediatamente

### **2. La empresa se pregunta AL FINAL:**
- ✅ Después de seleccionar: categoría → subtipo → período
- ✅ Solo si el usuario tiene **más de 1 empresa**
- ✅ Si tiene solo 1 empresa, se asigna automáticamente

### **3. Verificación en dos lugares:**

**A) En el callback de período (líneas 785-807):**
```python
# Después de seleccionar período
if len(empresas) > 1 and not session_data.get('empresa_id'):
    # Preguntar empresa
    await FileDownloadHandler._ask_empresa(query, empresas, {})
else:
    # Auto-asignar si tiene 1 empresa
    await FileDownloadHandler._finalizar_descarga(query, session_data, empresas)
```

**B) En _finalizar_descarga (líneas 537-539):**
```python
# Auto-asignar empresa si solo tiene 1
if not empresa_id and len(empresas) == 1:
    empresa_id = empresas[0]['id']
```

---

## 🔍 EJEMPLO REAL

### **The Wingman (tiene 2 empresas: Empresa de Prueba ACA y Factor IT)**

**Flujo:**
1. Presiona "📊 Información"
2. Selecciona "💰 Financieros"
3. Selecciona "🆔 RUT"
4. Selecciona "🟢 Mes actual (2025-11)"
5. **AQUÍ SE PREGUNTA:** "🏢 ¿De qué empresa quieres los archivos?"
   - Botón: "🏢 Empresa de Prueba ACA"
   - Botón: "🏢 Factor IT"
6. Usuario selecciona "Factor IT"
7. Se buscan archivos de Factor IT con:
   - Categoría: financiero
   - Subtipo: rut
   - Período: 2025-11
   - **Empresa:** Factor IT

---

## ⚠️ NOTA IMPORTANTE

La lógica actual **SÍ cumple** con tu requerimiento:
- ✅ Pregunta empresa al FINAL (después de categoría, subtipo y período)
- ✅ Solo pregunta si el usuario tiene más de 1 empresa
- ✅ Auto-asigna si tiene solo 1 empresa

**Si no te preguntó por la empresa**, puede ser por uno de estos motivos:
1. El usuario solo tiene 1 empresa asignada (auto-asignación)
2. La sesión ya tenía `empresa_id` de una selección anterior
3. Hubo un error en la obtención de empresas

---

**Última actualización:** 2025-11-12


