# 🔍 Explicación: Multiempresa y Seguridad

---

## 🏢 MULTIEMPRESA

### ¿Qué es?

**Situación actual:** ✅ **IMPLEMENTADO**
- Tabla `usuarios_empresas` creada para relación muchos a muchos
- Un usuario puede tener MÚLTIPLES empresas asignadas
- Cada relación tiene un rol específico (`super_admin`, `gestor`, `usuario`)
- Ejemplo: Christian Matthews tiene 2 empresas (Empresa de Prueba ACA y Factor IT)

**Escenario multiempresa:**
- Un usuario puede trabajar para MÚLTIPLES empresas
- Cada empresa puede tener un rol diferente para el mismo usuario
- Ejemplo: Un contador que maneja 3 empresas diferentes con diferentes permisos

### ¿Cómo afecta al flujo de archivos?

#### Escenario 1: Usuario con 1 empresa (ACTUAL)
```
Usuario: Juan (chat_id: 123)
Empresa asignada: Empresa A

Usuario sube archivo
  ↓
Sistema consulta: ¿Cuántas empresas tiene Juan?
  ↓
Respuesta: 1 empresa (Empresa A)
  ↓
AUTO-ASIGNAR Empresa A (sin preguntar)
  ↓
Continuar con: tipo y periodo
```

#### Escenario 2: Usuario con múltiples empresas (FUTURO)
```
Usuario: María (chat_id: 456)
Empresas asignadas: Empresa A, Empresa B, Empresa C

Usuario sube archivo
  ↓
Sistema consulta: ¿Cuántas empresas tiene María?
  ↓
Respuesta: 3 empresas
  ↓
Preguntar: "¿De qué empresa es este archivo?"
  ↓
Mostrar botones:
  [🏢 Empresa A] [🏢 Empresa B] [🏢 Empresa C]
  ↓
Usuario selecciona: Empresa B
  ↓
Continuar con: tipo y periodo
```

### Implementación ✅ **COMPLETADO**

**Estado actual:**
- ✅ Tabla `usuarios_empresas` implementada
- ✅ Métodos `get_user_empresas()` y `user_has_access_to_empresa()` funcionando
- ✅ El flujo pregunta empresa solo si detecta múltiples empresas
- ✅ Si tiene 1 empresa, se asigna automáticamente
- ✅ Validaciones de seguridad implementadas

**Código preparado:**
```python
def get_user_empresas(chat_id):
    """Obtener empresas del usuario (preparado para multiempresa)"""
    # Actualmente retorna 1 empresa
    # En futuro podría retornar múltiples
    user = get_user_by_chat_id(chat_id)
    return [user['empresa_id']]  # Por ahora lista de 1
```

---

## 🔒 SEGURIDAD

### ¿Qué es?

**Problema a resolver:**
- Un usuario NO debe poder ver archivos de empresas a las que NO pertenece
- Un usuario NO debe poder subir archivos a empresas que NO le corresponden

### Ejemplo de Ataque (Sin Seguridad)

```
Usuario A (Empresa X) intenta acceder a archivos de Empresa Y

Sin validación:
  Usuario A: "Dame archivos de Empresa Y"
  Sistema: "Aquí están los archivos" ❌ PERMITIÓ ACCESO NO AUTORIZADO
```

### Validaciones Necesarias

#### 1. Al SUBIR archivo

```python
# ❌ SIN SEGURIDAD (MALO)
def subir_archivo(chat_id, empresa_id, archivo):
    # Permite subir a cualquier empresa
    supabase.table('archivos').insert({
        'chat_id': chat_id,
        'empresa_id': empresa_id,  # ← Cualquier empresa
        'archivo': archivo
    })
```

```python
# ✅ CON SEGURIDAD (BUENO)
def subir_archivo(chat_id, empresa_id, archivo):
    # Validar que usuario pertenece a esa empresa
    user = supabase.get_user_by_chat_id(chat_id)
    
    if user['empresa_id'] != empresa_id:
        return "❌ No tienes acceso a esta empresa"  # ← BLOQUEADO
    
    # Solo si pertenece, permitir subida
    supabase.table('archivos').insert({
        'chat_id': chat_id,
        'empresa_id': empresa_id,  # ← Validado
        'archivo': archivo
    })
```

#### 2. Al DESCARGAR archivo

```python
# ❌ SIN SEGURIDAD (MALO)
def descargar_archivo(file_id):
    # Permite descargar cualquier archivo
    archivo = supabase.table('archivos').select('*').eq('id', file_id).execute()
    return archivo['url']  # ← Cualquier usuario puede descargar
```

```python
# ✅ CON SEGURIDAD (BUENO)
def descargar_archivo(chat_id, file_id):
    # Obtener archivo
    archivo = supabase.table('archivos').select('*').eq('id', file_id).execute()
    
    # Obtener usuario
    user = supabase.get_user_by_chat_id(chat_id)
    
    # Validar que archivo pertenece a empresa del usuario
    if archivo['empresa_id'] != user['empresa_id']:
        return "❌ No tienes acceso a este archivo"  # ← BLOQUEADO
    
    # Solo si pertenece, permitir descarga
    return archivo['url']  # ← Validado
```

#### 3. En BÚSQUEDAS

```python
# ❌ SIN SEGURIDAD (MALO)
def buscar_archivos(tipo, periodo):
    # Busca en TODAS las empresas
    archivos = supabase.table('archivos')\
        .select('*')\
        .eq('tipo', tipo)\
        .eq('periodo', periodo)\
        .execute()
    # ← Usuario podría ver archivos de otras empresas
```

```python
# ✅ CON SEGURIDAD (BUENO)
def buscar_archivos(chat_id, tipo, periodo):
    # Obtener empresa del usuario
    user = supabase.get_user_by_chat_id(chat_id)
    
    # Buscar SOLO en empresa del usuario
    archivos = supabase.table('archivos')\
        .select('*')\
        .eq('empresa_id', user['empresa_id'])\  # ← FILTRO CRÍTICO
        .eq('tipo', tipo)\
        .eq('periodo', periodo)\
        .execute()
    # ← Solo archivos de su empresa
```

### URLs Firmadas

**Supabase Storage** genera URLs firmadas:
- URL válida por tiempo limitado (ej: 1 hora)
- No se puede acceder sin la URL firmada
- Previene acceso no autorizado incluso si alguien obtiene la URL

```python
# Generar URL firmada (válida 1 hora)
url = supabase.storage.from_('archivos-bot')\
    .create_signed_url('path/to/file.pdf', 3600)  # 3600 segundos = 1 hora

# URL generada:
# https://xxx.supabase.co/storage/v1/object/sign/archivos-bot/path/to/file.pdf?token=abc123...
# ↑ Esta URL expira en 1 hora
```

---

## 📊 RESUMEN

### Multiempresa
- **Actual:** 1 empresa por usuario
- **Futuro:** Múltiples empresas por usuario
- **Código:** Preparado para ambos escenarios

### Seguridad
- **Validación en subida:** Usuario solo puede subir a su empresa
- **Validación en descarga:** Usuario solo puede ver archivos de su empresa
- **Filtros en búsquedas:** Siempre filtrar por empresa_id del usuario
- **URLs firmadas:** Expiración automática

---

**✅ Con estas validaciones, el sistema es seguro y está preparado para multiempresa.**


