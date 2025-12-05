# 🧪 Scripts de Testing y Utilidades

**Propósito:** Scripts auxiliares para testing, verificación y administración del sistema  
**Fecha:** 2025-11-13

---

## 📋 SCRIPTS DISPONIBLES

### **🔍 Verificación y Diagnóstico**

#### **`revisar_estructura_supabase.py`**
**Propósito:** Verificar estructura completa de Supabase  
**Uso:**
```bash
python3 scripts_testing/revisar_estructura_supabase.py
```
**Qué hace:**
- Lista todas las tablas y sus campos
- Verifica campos de tabla `archivos` en detalle
- Compara con campos requeridos

#### **`verificar_bd.py`**
**Propósito:** Verificar estado de base de datos  
**Uso:**
```bash
python3 scripts_testing/verificar_bd.py
```

#### **`verificar_archivos.py`**
**Propósito:** Verificar archivos subidos en Storage  
**Uso:**
```bash
python3 scripts_testing/verificar_archivos.py
```

#### **`verificar_sesiones.py`**
**Propósito:** Ver sesiones activas  
**Uso:**
```bash
python3 scripts_testing/verificar_sesiones.py
```

#### **`verificar_sistema_completo.py`**
**Propósito:** Verificación completa del sistema  
**Uso:**
```bash
python3 scripts_testing/verificar_sistema_completo.py
```

#### **`revisar_variables_bd.py`**
**Propósito:** Revisar variables de entorno y conexión  
**Uso:**
```bash
python3 scripts_testing/revisar_variables_bd.py
```

#### **`revisar_cambios_supabase.py`**
**Propósito:** Revisar cambios recientes en Supabase  
**Uso:**
```bash
python3 scripts_testing/revisar_cambios_supabase.py
```

#### **`diagnosticar_comando_empresa.py`**
**Propósito:** Diagnosticar comandos relacionados con empresas  
**Uso:**
```bash
python3 scripts_testing/diagnosticar_comando_empresa.py
```

---

### **👥 Administración de Usuarios**

#### **`asignar_roles_usuarios.py`**
**Propósito:** Asignar roles a usuarios  
**Uso:**
```bash
python3 scripts_testing/asignar_roles_usuarios.py
```
**Qué hace:**
- Asigna roles a The Wingman y Christian Matthews como super_admin
- Asigna rol 'usuario' a Patricio Alarcon
- Actualiza tabla `usuarios` y `usuarios_empresas`

#### **`asociar_empresa_usuario.py`**
**Propósito:** Asociar usuario a empresa  
**Uso:**
```bash
python3 scripts_testing/asociar_empresa_usuario.py
```

---

### **🏢 Administración de Empresas**

#### **`crear_empresa_factorit.py`**
**Propósito:** Crear empresa Factor IT  
**Uso:**
```bash
python3 scripts_testing/crear_empresa_factorit.py
```

---

### **🔧 Migraciones y Configuración**

#### **`ejecutar_migracion_roles.py`**
**Propósito:** Ejecutar migración de sistema de roles  
**Uso:**
```bash
python3 scripts_testing/ejecutar_migracion_roles.py
```

---

### **🧪 Testing Completo**

#### **`test_completo_sistema.py`**
**Propósito:** Testing end-to-end del sistema  
**Uso:**
```bash
python3 scripts_testing/test_completo_sistema.py
```
**Qué hace:**
- Verifica configuración
- Verifica conexión Supabase
- Verifica usuarios y empresas
- Verifica sistema multi-empresa

---

## 🚀 EJECUCIÓN

Todos los scripts deben ejecutarse desde la raíz del proyecto:

```bash
cd "/Users/christianmatthews/Library/Mobile Documents/com~apple~CloudDocs/CURSOR/ACA 3.0/aca_4"
source venv/bin/activate
python3 scripts_testing/nombre_script.py
```

---

## 📝 NOTAS

- **Todos los scripts requieren** el entorno virtual activado
- **Todos los scripts requieren** variables de entorno configuradas (`.env`)
- **Algunos scripts modifican datos** - revisar código antes de ejecutar
- **Scripts de verificación** son seguros (solo lectura)

---

## ⚠️ PRECAUCIONES

### **Scripts que MODIFICAN datos:**
- `asignar_roles_usuarios.py` - Modifica roles
- `asociar_empresa_usuario.py` - Modifica relaciones usuario-empresa
- `crear_empresa_factorit.py` - Crea empresa en BD
- `ejecutar_migracion_roles.py` - Ejecuta migraciones

### **Scripts seguros (solo lectura):**
- `revisar_estructura_supabase.py`
- `verificar_bd.py`
- `verificar_archivos.py`
- `verificar_sesiones.py`
- `verificar_sistema_completo.py`
- `revisar_variables_bd.py`
- `revisar_cambios_supabase.py`
- `diagnosticar_comando_empresa.py`

---

**Última actualización:** 2025-11-13



