# 🔄 Estrategias de Integración con Microsoft Teams - ACA 4.0

**Fecha:** 2025-11-14  
**Propósito:** Estrategias para conectar bot a Microsoft Teams y análisis de impacto en código

---

## 🎯 OBJETIVO

Integrar el sistema ACA 4.0 con Microsoft Teams sin romper la funcionalidad existente de Telegram.

---

## 📊 ANÁLISIS DE ARQUITECTURA ACTUAL

### Componentes Específicos de Telegram

**1. Bot Manager (`app/bots/bot_manager.py`):**
- Usa `telegram.ext.Application`
- Inicializa bots con tokens de Telegram
- Polling específico de Telegram
- **Impacto:** CRÍTICO - Todo el sistema de bots está acoplado a Telegram

**2. Handlers (todos en `app/bots/handlers/`):**
- Usan `Update` y `ContextTypes` de Telegram
- `InlineKeyboardButton` y `InlineKeyboardMarkup` (botones de Telegram)
- `update.message.reply_text()` (métodos específicos de Telegram)
- `update.callback_query` (callbacks de Telegram)
- **Impacto:** ALTO - Todos los handlers usan tipos de Telegram

**3. Identificación de Usuarios:**
- Usa `chat_id` (específico de Telegram)
- `update.effective_chat.id`
- **Impacto:** MEDIO - Necesita abstracción para múltiples plataformas

**4. Envío de Mensajes:**
- `message.reply_text()`
- `query.edit_message_text()`
- `context.bot.get_file()` (descarga de archivos)
- **Impacto:** ALTO - Métodos específicos de Telegram

---

### Componentes Reutilizables (Independientes de Telegram)

**1. Servicios Core:**
- `storage_service.py` - Gestión de archivos (independiente)
- `session_manager.py` - Gestión de sesiones (usa BD, independiente)
- `ai_service.py` - Integración OpenAI (independiente)
- `conversation_logger.py` - Logging (independiente)

**2. Base de Datos:**
- `supabase.py` - Cliente Supabase (independiente)
- Todas las tablas y queries (independientes)

**3. Seguridad:**
- `auth.py` - Validación de usuarios (usa `chat_id` pero puede abstraerse)

**4. Lógica de Negocio:**
- `file_types.py` - Tipos de archivo (independiente)
- Flujos de subida/descarga (lógica independiente, solo UI es específica)

---

## 🔄 ESTRATEGIAS DE INTEGRACIÓN

### Estrategia 1: Adapter Pattern (Recomendada)

**Concepto:**
- Crear capa de abstracción entre plataformas (Telegram/Teams) y lógica de negocio
- Adapters convierten eventos de cada plataforma a formato común
- Handlers trabajan con formato común, no específico de plataforma

**Arquitectura Propuesta:**
```
┌─────────────────────────────────────────┐
│         Plataformas (Telegram/Teams)   │
└──────────────┬──────────────────────────┘
               │
┌──────────────▼──────────────────────────┐
│      Adapters (TelegramAdapter/          │
│           TeamsAdapter)                 │
│  - Convierten eventos a formato común    │
│  - Convierten respuestas a formato nativo│
└──────────────┬──────────────────────────┘
               │
┌──────────────▼──────────────────────────┐
│    Handlers (Lógica de Negocio)         │
│  - Trabajan con formato común           │
│  - No conocen la plataforma             │
└──────────────┬──────────────────────────┘
               │
┌──────────────▼──────────────────────────┐
│      Servicios (Storage, Session, etc.)  │
│  - Completamente independientes         │
└─────────────────────────────────────────┘
```

**Ventajas:**
- ✅ Lógica de negocio reutilizable
- ✅ Fácil agregar más plataformas (WhatsApp, Slack, etc.)
- ✅ Mantiene código existente funcionando
- ✅ Testing más fácil (mock de adapters)

**Desventajas:**
- ⚠️ Requiere refactorización significativa
- ⚠️ Tiempo de implementación: 2-3 semanas
- ⚠️ Riesgo de romper funcionalidad existente

**Impacto en Código:**
- Crear `app/bots/adapters/telegram_adapter.py`
- Crear `app/bots/adapters/teams_adapter.py`
- Crear `app/bots/common/` con tipos comunes
- Refactorizar handlers para usar tipos comunes
- Mantener compatibilidad con código existente

---

### Estrategia 2: Bot Separado para Teams (Más Segura)

**Concepto:**
- Crear bot de Teams completamente separado
- Compartir solo servicios core (storage, session, BD)
- Handlers duplicados pero específicos para cada plataforma

**Arquitectura Propuesta:**
```
┌──────────────────┐         ┌──────────────────┐
│  Bot Telegram    │         │   Bot Teams      │
│  (Existente)     │         │   (Nuevo)        │
└────────┬─────────┘         └────────┬─────────┘
         │                            │
         └────────────┬───────────────┘
                      │
         ┌────────────▼───────────────┐
         │   Servicios Compartidos    │
         │  - storage_service         │
         │  - session_manager         │
         │  - supabase                │
         │  - ai_service              │
         └────────────────────────────┘
```

**Ventajas:**
- ✅ Cero riesgo de romper código existente
- ✅ Implementación más rápida (1 semana)
- ✅ Cada bot puede evolucionar independientemente
- ✅ Fácil de mantener

**Desventajas:**
- ⚠️ Duplicación de código de handlers
- ⚠️ Dos bots que mantener
- ⚠️ Cambios de lógica requieren actualizar ambos

**Impacto en Código:**
- Crear `app/bots/teams/` con estructura similar a `app/bots/handlers/`
- Crear `app/bots/teams_manager.py` similar a `bot_manager.py`
- Reutilizar servicios existentes
- No tocar código de Telegram

---

### Estrategia 3: Gateway Unificado (Más Compleja)

**Concepto:**
- Servicio gateway que recibe eventos de todas las plataformas
- Convierte a formato común y enruta a handlers unificados
- Handlers responden en formato común, gateway convierte a plataforma

**Arquitectura Propuesta:**
```
Telegram ──┐
Teams   ──┼──> Gateway ──> Handlers Unificados ──> Servicios
Slack   ──┘
```

**Ventajas:**
- ✅ Escalable a múltiples plataformas
- ✅ Lógica completamente unificada
- ✅ Un solo punto de entrada

**Desventajas:**
- ⚠️ Arquitectura más compleja
- ⚠️ Requiere rediseño significativo
- ⚠️ Tiempo: 1-2 meses

**Impacto en Código:**
- Rediseño completo de arquitectura
- Crear gateway service
- Refactorizar todo el sistema

---

## 🎯 RECOMENDACIÓN: Estrategia 2 (Bot Separado)

**Por qué:**
- ✅ Cero riesgo de romper código existente
- ✅ Implementación más rápida
- ✅ Mantenibilidad más simple
- ✅ Permite probar Teams sin afectar Telegram

---

## 📋 ANÁLISIS DE IMPACTO DETALLADO

### Archivos que NO se Modifican (Reutilizables)

**Servicios:**
- `app/services/storage_service.py` - ✅ Reutilizable 100%
- `app/services/session_manager.py` - ✅ Reutilizable 100%
- `app/services/ai_service.py` - ✅ Reutilizable 100%
- `app/services/conversation_logger.py` - ⚠️ Necesita adaptación (usa chat_id)

**Base de Datos:**
- `app/database/supabase.py` - ✅ Reutilizable 100%
- Todas las tablas - ✅ Reutilizables 100%

**Utilidades:**
- `app/utils/file_types.py` - ✅ Reutilizable 100%
- `app/utils/helpers.py` - ✅ Reutilizable 100%

**Seguridad:**
- `app/security/auth.py` - ⚠️ Necesita adaptación (usa chat_id, necesita abstracción)

---

### Archivos que SÍ se Modifican/Crean

**Nuevos Archivos para Teams:**
- `app/bots/teams/teams_manager.py` - Gestor de bot Teams
- `app/bots/teams/handlers/teams_production_handlers.py` - Handlers específicos Teams
- `app/bots/teams/handlers/teams_file_upload_handler.py` - Subida para Teams
- `app/bots/teams/handlers/teams_file_download_handler.py` - Descarga para Teams
- `app/bots/teams/handlers/teams_admin_handlers.py` - Admin para Teams (si aplica)

**Archivos a Modificar:**
- `app/config.py` - Agregar variables de Teams (TEAMS_APP_ID, TEAMS_APP_PASSWORD, etc.)
- `app/main.py` - Inicializar bot de Teams además de Telegram
- `app/security/auth.py` - Adaptar para soportar user_id de Teams además de chat_id

**Archivos que NO se Tocan:**
- Todo en `app/bots/handlers/` (Telegram) - ✅ Sin cambios
- `app/bots/bot_manager.py` (Telegram) - ✅ Sin cambios

---

## 🔧 DIFERENCIAS CLAVE: Telegram vs Teams

### Identificación de Usuarios

**Telegram:**
- Usa `chat_id` (número único)
- `update.effective_chat.id`

**Teams:**
- Usa `user_id` o `aadObjectId` (string UUID)
- `turn_context.activity.from.id`

**Solución:**
- Crear tabla `usuarios_plataformas` o agregar campo `teams_user_id` a tabla `usuarios`
- Adaptar `auth.py` para buscar por chat_id (Telegram) o teams_user_id (Teams)

---

### Envío de Mensajes

**Telegram:**
- `message.reply_text(text, reply_markup=keyboard)`
- `query.edit_message_text(text, reply_markup=keyboard)`
- Soporta Markdown

**Teams:**
- `turn_context.send_activity(Activity)` con `HeroCard` o `MessageFactory`
- No soporta Markdown directamente (usa Adaptive Cards)
- Botones diferentes (ActionCard vs InlineKeyboardButton)

**Solución:**
- Crear funciones helper que conviertan formato común a formato de cada plataforma
- Ejemplo: `create_keyboard_telegram()` vs `create_keyboard_teams()`

---

### Archivos/Adjuntos

**Telegram:**
- `update.message.document`
- `context.bot.get_file(file_id)`
- Descarga directa desde Telegram

**Teams:**
- `turn_context.activity.attachments`
- URLs de archivos en OneDrive/SharePoint
- Descarga desde URLs

**Solución:**
- Adaptar `file_upload_handler.py` para manejar ambos formatos
- O crear handlers separados que llamen a `storage_service` común

---

### Callbacks/Botones

**Telegram:**
- `callback_query.data` - String simple
- `query.answer()` - Confirmación
- `query.edit_message_text()` - Editar mensaje

**Teams:**
- `turn_context.activity.value` - Objeto JSON con datos
- `MessageFactory.attachment()` - Crear nueva tarjeta
- No hay "editar mensaje" directo (enviar nueva tarjeta)

**Solución:**
- Normalizar callbacks a formato común
- Adapter convierte formato común a formato de plataforma

---

## 📦 COMPONENTES A CREAR PARA TEAMS

### 1. Teams Manager

**Concepto:**
- Similar a `bot_manager.py` pero para Teams
- Inicializa bot de Teams con Bot Framework
- Registra handlers específicos de Teams
- Maneja webhooks de Teams (no polling)

**Dependencias:**
- `botbuilder-core` (Microsoft Bot Framework)
- `botbuilder-teams` (extensión para Teams)

---

### 2. Teams Handlers

**Concepto:**
- Handlers específicos para Teams
- Misma lógica de negocio que handlers de Telegram
- Diferente formato de entrada/salida

**Estructura:**
- `teams_production_handlers.py` - Menú principal, comandos
- `teams_file_upload_handler.py` - Subida de archivos
- `teams_file_download_handler.py` - Descarga de archivos
- `teams_admin_handlers.py` - Administración (si aplica)

---

### 3. Adapter de Autenticación

**Concepto:**
- Adaptar `auth.py` para soportar ambos tipos de ID
- Buscar usuario por `chat_id` (Telegram) o `teams_user_id` (Teams)
- Misma lógica de validación y permisos

**Cambios en BD:**
- Opción A: Agregar campo `teams_user_id` a tabla `usuarios`
- Opción B: Crear tabla `usuarios_plataformas` (más escalable)

---

### 4. Helper de UI

**Concepto:**
- Funciones para crear botones/tarjetas según plataforma
- Convertir formato común a formato específico
- Manejar diferencias de Markdown/Adaptive Cards

---

## 🔄 FLUJO DE INTEGRACIÓN PROPUESTO

### Fase 1: Setup Básico (1 semana)

1. **Registrar bot en Azure:**
   - Crear Azure Bot Resource
   - Obtener App ID y App Password
   - Configurar endpoint (webhook)

2. **Crear estructura básica:**
   - `app/bots/teams/` con estructura similar
   - `teams_manager.py` básico
   - Endpoint `/api/teams/messages` para recibir webhooks

3. **Configurar variables:**
   - `TEAMS_APP_ID`
   - `TEAMS_APP_PASSWORD`
   - `TEAMS_WEBHOOK_URL`

---

### Fase 2: Handlers Básicos (1 semana)

1. **Handler de inicio:**
   - `/start` equivalente en Teams
   - Menú principal adaptado a Teams
   - Validación de usuario

2. **Handler de mensajes:**
   - Mensajes de texto básicos
   - Enrutamiento a handlers correctos

---

### Fase 3: Funcionalidades Core (2 semanas)

1. **Subida de archivos:**
   - Adaptar flujo de subida para Teams
   - Manejar adjuntos de Teams
   - Reutilizar `storage_service`

2. **Descarga de archivos:**
   - Adaptar flujo de descarga
   - Crear tarjetas de Teams con links
   - Reutilizar lógica de búsqueda

---

### Fase 4: Testing y Refinamiento (1 semana)

1. **Testing end-to-end:**
   - Probar flujos completos
   - Verificar permisos
   - Validar multiempresa

2. **Ajustes de UX:**
   - Mejorar formato de mensajes
   - Optimizar tarjetas de Teams

---

## 🗄️ CAMBIOS EN BASE DE DATOS

### Opción A: Campo Adicional (Simple)

**Tabla `usuarios`:**
- Agregar campo `teams_user_id` (VARCHAR, nullable)
- Índice en `teams_user_id`
- Modificar queries para buscar por `chat_id` O `teams_user_id`

**Ventajas:**
- ✅ Simple y rápido
- ✅ Mínimos cambios

**Desventajas:**
- ⚠️ No escalable a más plataformas
- ⚠️ Lógica de búsqueda más compleja

---

### Opción B: Tabla de Plataformas (Escalable)

**Nueva tabla `usuarios_plataformas`:**
```sql
- id (UUID)
- usuario_id (UUID FK)
- plataforma (VARCHAR) - 'telegram' o 'teams'
- plataforma_user_id (VARCHAR) - chat_id o teams_user_id
- activo (BOOLEAN)
```

**Ventajas:**
- ✅ Escalable a múltiples plataformas
- ✅ Un usuario puede tener múltiples cuentas en diferentes plataformas
- ✅ Lógica más clara

**Desventajas:**
- ⚠️ Requiere migración de datos
- ⚠️ Queries más complejas (JOIN)

---

## 🔐 IMPACTO EN SEGURIDAD

### Autenticación

**Telegram:**
- Validación por `chat_id`
- Usuario debe estar en tabla `usuarios`

**Teams:**
- Validación por `teams_user_id` o `aadObjectId`
- Usuario debe estar en tabla `usuarios` (con Teams ID)
- Puede requerir OAuth de Microsoft (depende de configuración)

**Solución:**
- Adaptar `security.validate_user()` para aceptar ambos tipos de ID
- Buscar en tabla según plataforma
- Misma lógica de permisos y roles

---

## 📊 MÉTRICAS Y LOGGING

### Conversaciones

**Tabla `conversaciones`:**
- Agregar campo `plataforma` ('telegram' o 'teams')
- Mantener mismo formato de logging
- Filtrar por plataforma en queries

**Impacto:**
- Mínimo - solo agregar campo
- Queries existentes siguen funcionando

---

## 🚨 RIESGOS Y CONSIDERACIONES

### Riesgos Técnicos

1. **Diferencias de UI:**
   - Teams usa Adaptive Cards (más complejo que botones de Telegram)
   - Puede requerir rediseño de algunos flujos
   - **Mitigación:** Crear helpers de conversión

2. **Rate Limiting:**
   - Teams tiene límites diferentes a Telegram
   - Puede requerir ajustes en manejo de requests
   - **Mitigación:** Implementar rate limiting propio

3. **Archivos:**
   - Teams puede tener límites de tamaño diferentes
   - Formato de URLs diferente
   - **Mitigación:** Validar en `storage_service`

---

### Riesgos de Negocio

1. **Usuarios Duplicados:**
   - Mismo usuario en Telegram y Teams
   - Puede causar confusión
   - **Mitigación:** Permitir múltiples plataformas por usuario (tabla usuarios_plataformas)

2. **Sesiones:**
   - Sesión activa en Telegram y Teams simultáneamente
   - Puede causar conflictos
   - **Mitigación:** Sesiones por plataforma o sesión unificada con campo plataforma

---

## 💡 RECOMENDACIONES FINALES

### Estrategia Recomendada: Bot Separado (Estrategia 2)

**Razones:**
1. ✅ Cero riesgo de romper código existente
2. ✅ Implementación más rápida (4-5 semanas)
3. ✅ Mantenibilidad más simple
4. ✅ Permite probar Teams sin afectar producción de Telegram

### Orden de Implementación

1. **Semana 1:** Setup básico y estructura
2. **Semana 2:** Handlers básicos (menú, mensajes)
3. **Semana 3-4:** Funcionalidades core (subida/descarga)
4. **Semana 5:** Testing y refinamiento

### Cambios Mínimos Necesarios

1. **BD:** Agregar campo `teams_user_id` o tabla `usuarios_plataformas`
2. **Config:** Variables de Teams
3. **Auth:** Adaptar búsqueda de usuarios
4. **Main:** Inicializar bot de Teams
5. **Nuevos archivos:** Estructura completa de Teams (sin tocar Telegram)

---

## 📋 CHECKLIST DE IMPLEMENTACIÓN

### Preparación
- [ ] Registrar bot en Azure Portal
- [ ] Obtener App ID y App Password
- [ ] Configurar webhook endpoint
- [ ] Decidir estructura de BD (campo adicional vs tabla)

### Desarrollo
- [ ] Crear estructura `app/bots/teams/`
- [ ] Implementar `teams_manager.py`
- [ ] Crear handlers básicos
- [ ] Adaptar autenticación
- [ ] Implementar subida de archivos
- [ ] Implementar descarga de archivos
- [ ] Crear helpers de UI (botones/tarjetas)

### Testing
- [ ] Probar flujo completo de subida
- [ ] Probar flujo completo de descarga
- [ ] Verificar permisos y roles
- [ ] Validar multiempresa
- [ ] Probar con usuarios reales

### Despliegue
- [ ] Configurar variables de entorno
- [ ] Desplegar endpoint de webhook
- [ ] Configurar bot en Teams
- [ ] Monitorear logs y errores

---

**Última actualización:** 2025-11-14


