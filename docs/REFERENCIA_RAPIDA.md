# ⚡ Referencia Rápida - ACA 4.0

**Fecha:** 2025-11-13  
**Versión:** 4.0.2

---

## 🚀 INICIO RÁPIDO

### **Iniciar aplicación:**
```bash
cd "ACA 4.0/aca_4"
source venv/bin/activate
python3 run.py
```

### **Detener aplicación:**
```bash
lsof -ti:8000 | xargs kill -9
pkill -f "python.*run.py"
```

### **Scripts de testing (ver scripts_testing/README.md):**
```bash
# Verificar sistema completo
python3 scripts_testing/verificar_sistema_completo.py

# Ver estructura de BD
python3 scripts_testing/revisar_estructura_supabase.py

# Listar todos los scripts
ls scripts_testing/
```

---

## 👤 CREAR USUARIO

### **Comando:**
```bash
/adduser CHAT_ID NOMBRE ROL RUT_EMPRESA
```

### **Ejemplo:**
```bash
/adduser 123456789 Juan Perez user 76142021-6
```

### **Roles:**
- `super_admin` - Todos los permisos
- `gestor` - Subir y bajar archivos
- `user` - Solo bajar archivos

---

## 📤 SUBIR ARCHIVO

### **Flujo:**
```
1. Enviar archivo → Bot
2. Empresa (si tiene múltiples)
3. Categoría (Legal/Financiero)
4. Subtipo (RUT, F29, etc.)
5. Descripción (si es "Otros")
6. Período (Actual/Anterior/Otro)
7. ✅ Subido
```

---

## 📥 BAJAR ARCHIVO

### **Flujo:**
```
1. "📊 Información"
2. Categoría (Legal/Financiero)
3. Subtipo (RUT, F29, etc.)
4. Período (Actual/Anterior/Otro)
5. Empresa (si tiene múltiples) ← AL FINAL
6. Ver/Descargar archivos
```

---

## 🗄️ ESTRUCTURA DE ARCHIVOS

### **Categorías:**
- `legal` - ⚖️ Legales
- `financiero` - 💰 Financieros

### **Subtipos Legales:**
- `estatutos_empresa` - Estatutos empresa
- `poderes` - Poderes
- `ci` - CI
- `rut` - RUT
- `otros` - Otros (requiere descripción)

### **Subtipos Financieros:**
- `reporte_mensual` - Reporte mensual
- `estados_financieros` - Estados financieros
- `carpeta_tributaria` - Carpeta tributaria
- `f29` - F29
- `f22` - F22
- `otros` - Otros (requiere descripción)

---

## 📊 CONSULTAS ÚTILES

### **Ver archivos de una empresa:**
```python
archivos = supabase.table('archivos')\
    .select('*')\
    .eq('empresa_id', 'UUID_EMPRESA')\
    .eq('activo', True)\
    .execute()
```

### **Ver empresas de un usuario:**
```python
empresas = supabase.get_user_empresas(chat_id)
```

### **Ver sesiones activas:**
```python
sesiones = supabase.table('sesiones_conversacion')\
    .select('*')\
    .execute()
```

---

## 🔧 TROUBLESHOOTING

### **Error: "RLS policy violation"**
✅ **Solución:** Verificar que se use `SUPABASE_SERVICE_KEY`

### **Error: "InvalidKey" en Storage**
✅ **Solución:** Método `_sanitize_filename()` ya lo maneja

### **Error: "Duplicate" en Storage**
✅ **Solución:** Timestamp único ya agregado

### **Usuario no recibe mensajes:**
✅ **Solución:** Verificar sesión activa y intent correcto

### **No pregunta por empresa:**
✅ **Solución:** Usuario tiene solo 1 empresa (comportamiento correcto)

---

## 📂 ARCHIVOS CLAVE

### **Handlers:**
- `app/bots/handlers/production_handlers.py` - Bot de producción
- `app/bots/handlers/admin_handlers.py` - Bot admin
- `app/bots/handlers/file_upload_handler.py` - Subida de archivos
- `app/bots/handlers/file_download_handler.py` - Descarga de archivos

### **Servicios:**
- `app/services/storage_service.py` - Gestión de Storage
- `app/services/ai_service.py` - Integración OpenAI
- `app/services/session_manager.py` - Gestión de sesiones
- `app/database/supabase.py` - Cliente Supabase

### **Configuración:**
- `app/config.py` - Variables de entorno
- `app/bots/bot_manager.py` - Registro de handlers
- `app/utils/file_types.py` - Tipos de archivo

---

## 🎯 DATOS DE EJEMPLO

### **The Wingman:**
- Chat ID: 7580149783
- Empresas: 2
  - Empresa de Prueba ACA (12345678-9)
  - Factor IT (76142021-6)
- Rol: super_admin

### **Empresas:**
- Empresa de Prueba ACA
  - RUT: 12345678-9
  - ID: da898459-a17b-4d6f-baf2-f9f6edccba6e

- Factor IT
  - RUT: 76142021-6
  - ID: a6fbf012-7d18-4f49-ae80-15586b173c2f

---

**Última actualización:** 2025-11-13

