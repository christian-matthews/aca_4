# 🔒 Sistema de Roles y Permisos - ACA 4.0

## 📋 Roles Disponibles

El sistema tiene **3 niveles de roles**:

### 1. 🔴 **super_admin**
**Usuarios:** The Wingman (7580149783), Christian Matthews (866310278)

**Permisos:**
- ✅ Todos los permisos del sistema
- ✅ Acceso al bot admin
- ✅ Crear empresas
- ✅ Asignar usuarios a empresas
- ✅ Subir archivos
- ✅ Descargar archivos
- ✅ Gestionar empresas
- ✅ Ver todas las empresas y usuarios

---

### 2. 🟡 **gestor**
**Usuarios:** Por asignar

**Permisos:**
- ✅ Asignar usuarios a empresas (solo empresas asignadas)
- ✅ Subir archivos
- ✅ Descargar archivos
- ✅ Ver empresas asignadas
- ❌ Crear nuevas empresas
- ❌ Acceso al bot admin

---

### 3. 🟢 **usuario**
**Usuarios:** Patricio Alarcon (2134113487)

**Permisos:**
- ✅ Descargar archivos
- ✅ Ver empresas asignadas
- ❌ Subir archivos
- ❌ Asignar usuarios a empresas
- ❌ Crear empresas
- ❌ Acceso al bot admin

---

## 🗄️ Estructura en Base de Datos

### Tabla `usuarios`
- Campo `rol`: Rol global del usuario (`super_admin`, `gestor`, `usuario`)
- Usado para permisos globales (bot admin, crear empresas)

### Tabla `usuarios_empresas`
- Campo `rol`: Rol del usuario en esa empresa específica (`super_admin`, `gestor`, `usuario`)
- Permite diferentes roles en diferentes empresas (multiempresa)

---

## 🔧 Métodos de Validación

### En `app/security/auth.py`:

```python
# Verificar si es super_admin
security.is_super_admin(chat_id) -> bool

# Verificar si puede subir archivos
security.can_upload_files(chat_id, empresa_id=None) -> bool

# Verificar si puede descargar archivos
security.can_download_files(chat_id, empresa_id=None) -> bool

# Verificar si puede gestionar empresas
security.can_manage_empresas(chat_id) -> bool

# Obtener rol en empresa específica
security.get_user_role_in_empresa(chat_id, empresa_id) -> str
```

---

## 📊 Matriz de Permisos

| Acción | super_admin | gestor | usuario |
|--------|-------------|--------|---------|
| Crear empresas | ✅ | ❌ | ❌ |
| Asignar usuarios a empresas | ✅ | ✅* | ❌ |
| Subir archivos | ✅ | ✅ | ❌ |
| Descargar archivos | ✅ | ✅ | ✅ |
| Acceso bot admin | ✅ | ❌ | ❌ |
| Ver todas las empresas | ✅ | ❌ | ❌ |

*Solo en empresas asignadas

---

## 🔄 Asignación de Roles

### Script: `asignar_roles_usuarios.py`

```bash
python asignar_roles_usuarios.py
```

Este script:
- Asigna `super_admin` a The Wingman y Christian
- Asigna `usuario` a Patricio Alarcon
- Actualiza roles en tabla `usuarios` y `usuarios_empresas`

---

## 📝 Migración SQL

**Archivo:** `database/migrations/004_sistema_roles_permisos.sql`

Esta migración:
- Crea constraints para validar roles válidos
- Actualiza comentarios de campos
- Mantiene compatibilidad con roles legacy (`admin`, `user`)

---

## ✅ Estado Actual

### Usuarios y Roles:

1. **The Wingman** (7580149783)
   - Rol: `super_admin`
   - Empresas: Empresa de Prueba ACA (super_admin)

2. **Christian Matthews** (866310278)
   - Rol: `super_admin`
   - Empresas: 
     - Empresa de Prueba ACA (super_admin)
     - Factor IT (super_admin)

3. **Patricio Alarcon** (2134113487)
   - Rol: `usuario`
   - Empresas: Factor IT (usuario)

---

## 🚀 Próximos Pasos

1. ✅ Migración SQL ejecutada
2. ✅ Roles asignados
3. ✅ Métodos de validación creados
4. ⏳ Actualizar handlers para usar validaciones de permisos
5. ⏳ Probar flujo completo con diferentes roles

---

**Última actualización:** 2025-11-12









