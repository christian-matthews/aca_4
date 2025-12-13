# 🛡️ TEAMS PILOT - GUARDRAILS Y REGLAS

**Fecha:** 2025-12-12  
**Rama:** `teams-pilot`  
**Objetivo:** Agregar Microsoft Teams como canal nuevo SIN tocar Telegram

---

## ⚠️ REGLA CERO (CRÍTICA — NO NEGOCIABLE)

### Archivos Intocables

**NO modificar, mover, renombrar ni refactorizar:**

- ❌ `app/bots/bot_manager.py`
- ❌ `app/bots/handlers/` (cualquier archivo dentro)
  - `admin_handlers.py`
  - `production_handlers.py`
  - `advisor_handler.py`
  - `file_download_handler.py`
  - `file_upload_handler.py`
- ❌ `app/main.py` (puede tener lógica de Telegram)
- ❌ Cualquier import o dependencia de `python-telegram-bot`

### Regla de No-Refactor

- NO refactorizar código existente
- NO extraer funciones comunes
- NO crear abstracciones compartidas
- NO modificar imports existentes
- NO cambiar estructura de carpetas existentes

### Regla de No-Mezcla de Procesos

- Teams y Telegram deben ser procesos separados
- NO compartir Application/Updater entre ambos
- NO mezclar handlers en el mismo módulo
- NO usar el mismo entrypoint para ambos
- Teams: Webhook HTTP (nuevo proceso)
- Telegram: Polling (proceso existente, intacto)

### Regla de No-Cambios en Dependencias

- NO agregar dependencias nuevas si no son necesarias
- NO modificar `requirements.txt` sin justificación
- NO cambiar versiones de dependencias existentes

### Regla de Detenerse

**Si algo no está explícitamente permitido, NO hacerlo y detenerse.**

---

## ✅ ALCANCE PERMITIDO

### Archivos Nuevos Permitidos

- ✅ `app/bots/teams/` (carpeta completa nueva)
- ✅ `app/web/teams_router.py` (nuevo)
- ✅ `app/run_teams.py` (nuevo entrypoint)
- ✅ `app/run_telegram_worker.py` (nuevo wrapper)
- ✅ `TEAMS_PILOT_GUARDRAILS.md` (este archivo)

### Modificaciones Permitidas

- ✅ Agregar variables de entorno nuevas
- ✅ Crear nuevos endpoints HTTP
- ✅ Crear nuevos servicios (sin tocar existentes)
- ✅ Documentación nueva

---

## 📋 CHECKLIST PREVIO A COMMIT

### 1. Verificación de Archivos Modificados

```bash
# Verificar que NO se modificaron archivos intocables
git diff --name-only main...HEAD | grep -E "(bot_manager\.py|app/bots/handlers/)"

# Output esperado: (vacío - ningún archivo)
```

### 2. Verificación de Archivos Nuevos

```bash
# Verificar que solo se crearon archivos nuevos
git diff --name-only main...HEAD

# Debe mostrar SOLO:
# - TEAMS_PILOT_GUARDRAILS.md
# - app/bots/teams/...
# - app/web/teams_router.py
# - app/run_teams.py
# - app/run_telegram_worker.py
```

### 3. Verificación de Compilación

```bash
# Verificar que el código compila sin errores
python -m compileall app

# Output esperado: (sin errores)
```

### 4. Verificación de Imports

```bash
# Verificar que no hay imports rotos
python -c "import app.bots.teams; import app.web.teams_router; import app.run_teams; import app.run_telegram_worker"

# Output esperado: (sin errores)
```

### 5. Verificación de Diferencias Específicas

```bash
# Confirmar explícitamente que bot_manager.py no cambió
git diff main -- app/bots/bot_manager.py

# Output esperado: (vacío)

# Confirmar explícitamente que handlers/ no cambió
git diff main -- app/bots/handlers/

# Output esperado: (vacío)
```

---

## 🚨 SI ALGO FALLA

1. **Detener inmediatamente**
2. **NO hacer commit**
3. **Revisar qué archivo causó el problema**
4. **Si es archivo intocable: REVERTIR cambios**
5. **Si es archivo nuevo: corregir SIN tocar Telegram**
6. **Repetir verificaciones**

---

## 📝 NOTAS

- Este es un piloto experimental
- Telegram sigue siendo producción
- Teams vive aislado
- Ante cualquier duda: **DETENERSE Y PREGUNTAR**

---

**Última actualización:** 2025-12-12  
**Rama:** teams-pilot

