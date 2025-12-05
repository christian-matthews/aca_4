# 📊 Limitantes de Escalabilidad - ACA 4.0

**Fecha:** 2025-11-14  
**Propósito:** Análisis completo de limitantes de uso de la arquitectura actual

---

## 🎯 Resumen Ejecutivo

### Limitantes Principales

| Componente | Limitante | Valor Actual | Impacto |
|------------|-----------|--------------|---------|
| **Telegram Bot API** | Mensajes por segundo | ~30 msg/s por bot | 🟡 Medio |
| **Supabase PostgreSQL** | Conexiones simultáneas | 60 (Free) / 200 (Pro) | 🟡 Medio |
| **Supabase Storage** | Tamaño archivos | 50MB (Free) / 5GB (Pro) | 🟢 Bajo |
| **Render Starter** | RAM | 0.5 GB (512MB) | 🔴 **CRÍTICO** |
| **Render Starter** | CPU | 0.5 vCPU (dedicado) | 🟡 Medio |
| **Render Starter** | Workers | 1 worker | 🟡 Medio |
| **Render Starter** | Tiempo activo | Siempre activo | ✅ OK |
| **Arquitectura Actual** | Conexión Supabase | Singleton (1 conexión) | 🟡 Medio |

---

## 📱 1. TELEGRAM BOT API

### Límites de Rate Limiting

**Mensajes por segundo:**
- **Límite general:** ~30 mensajes por segundo por bot
- **Límite por chat:** ~20 mensajes por segundo por chat individual
- **Límite de archivos:** ~20 archivos por segundo

**Límites de tamaño:**
- **Archivos:** Máximo 50MB por archivo
- **Fotos:** Máximo 10MB
- **Videos:** Máximo 50MB

### Impacto en el Sistema

**Escenario actual:**
- 2 bots (admin + producción)
- Polling (no webhooks)
- Cada bot puede procesar ~30 mensajes/segundo

**Cálculo de capacidad:**
```
Capacidad teórica: 30 msg/s × 2 bots = 60 msg/s
Capacidad práctica: ~40-50 msg/s (con overhead)
```

**Usuarios concurrentes estimados:**
- Si cada usuario envía 1 mensaje cada 5 segundos: **200-250 usuarios concurrentes**
- Si cada usuario envía 1 mensaje cada 10 segundos: **400-500 usuarios concurrentes**

**Limitante real:** ⚠️ **Polling tiene latencia de 1-2 segundos**

### Recomendación

**Cambiar a Webhooks:**
- Latencia: <100ms
- Sin límite de polling
- Mejor para producción

**Riesgo actual:** Bajo (solo 3 usuarios activos)

---

## 🗄️ 2. SUPABASE (PostgreSQL + Storage)

### Límites de PostgreSQL

**Conexiones simultáneas:**

| Plan | Conexiones | Pool Size |
|------|-----------|-----------|
| **Free** | 60 | 15-20 recomendado |
| **Pro ($25/mes)** | 200 | 50-100 recomendado |
| **Team ($599/mes)** | 400 | 100-200 recomendado |

**Problema actual:**
```python
# app/database/supabase.py
# Singleton - UNA SOLA conexión compartida
self._client = create_client(Config.SUPABASE_URL, Config.SUPABASE_SERVICE_KEY)
```

**Impacto:**
- ✅ **Ventaja:** No hay problema de conexiones (1 conexión reutilizada)
- ⚠️ **Limitante:** No hay pooling, todas las requests comparten la misma conexión
- ⚠️ **Riesgo:** Si hay muchas requests simultáneas, pueden hacer cola

**Límites de Storage:**

| Plan | Almacenamiento | Transferencia |
|------|----------------|---------------|
| **Free** | 1GB | 2GB/mes |
| **Pro** | 100GB | 200GB/mes |
| **Team** | 1TB | 2TB/mes |

**Tamaño máximo por archivo:**
- **Free:** 50MB
- **Pro:** 5GB
- **Team:** 5GB

### Cálculo de Capacidad

**Archivos por mes (Free):**
```
1GB almacenamiento / 10MB promedio por archivo = ~100 archivos
```

**Archivos por mes (Pro):**
```
100GB / 10MB = ~10,000 archivos
```

**Limitante actual:** 🟢 **Bajo** (solo 2 empresas, pocos archivos)

---

## 🖥️ 3. RENDER (Hosting)

### Límites por Plan

**Free Tier:**
- ✅ 750 horas/mes gratis
- ❌ **1 worker** (no puede escalar horizontalmente)
- ❌ **Se "duerme" después de 15 minutos de inactividad**
- ❌ **Primera petición después de dormir: 30-60 segundos de latencia**
- ❌ CPU: Shared (recursos compartidos)
- ❌ RAM: Hasta 0.5 GB (512MB)

**Starter ($7/mes):**
- ✅ Siempre activo (no se duerme)
- ✅ **1 worker** (aún no puede escalar)
- ✅ CPU: 0.5 vCPU (dedicado)
- ✅ RAM: 512MB
- ✅ Mejor rendimiento

**Tu configuración actual (Starter $7/mes):**
- ✅ **CPU: 0.5 vCPU (dedicado)** - Mejor que Shared
- ⚠️ **RAM: 0.5 GB** (512MB) - **LIMITANTE CRÍTICO**
- ✅ **Siempre activo** (no se duerme)
- ⚠️ **1 worker único**

**Standard ($25/mes):**
- ✅ Siempre activo
- ✅ **1 worker** (puede escalar a múltiples workers con plan más alto)
- ✅ CPU: 1 vCPU
- ✅ RAM: 2GB
- ✅ Mejor para producción

### Impacto en el Sistema

**Problemas críticos con tu configuración actual (Starter):**

1. **RAM limitada (0.5GB) - CRÍTICO:**
```
Python runtime: ~100-150MB
FastAPI + Uvicorn: ~50-100MB
Bots de Telegram: ~100-150MB
Supabase client: ~50MB
Sesiones en memoria: ~50-100MB
= ~350-550MB (MUY APRETADO, riesgo de OOM)
```

2. **CPU 0.5 vCPU (dedicado pero limitado):**
```
CPU dedicado (mejor que Shared)
Pero solo 0.5 vCPU = 50% de 1 CPU core
Puede ser limitante con muchas requests simultáneas
Latencia puede aumentar bajo carga
```

**Ventajas de tu plan Starter:**
- ✅ Siempre activo (no se duerme)
- ✅ CPU dedicado (no compartido)
- ✅ Mejor rendimiento que Free Tier

**Capacidad de procesamiento (Tu configuración actual - Starter: 0.5GB RAM, 0.5 vCPU dedicado):**
- **Requests simultáneas:** ~10-15 (limitado principalmente por RAM de 0.5GB)
- **Usuarios concurrentes:** ~15-25 (si cada uno hace 1 request cada 5 segundos)
- **Problema principal:** RAM muy limitada para Python + FastAPI + Bots + Supabase client
- **Problema secundario:** CPU 0.5 vCPU puede ser limitante con muchas requests simultáneas

**Capacidad de procesamiento (Standard - 2GB RAM):**
- **Requests simultáneas:** ~30-50
- **Usuarios concurrentes:** ~50-100

### Recomendación

**Para producción:** 
- ✅ **Starter ($7/mes):** OK para hasta 15-20 usuarios (tu plan actual)
- ✅ **Standard ($25/mes):** Recomendado para 20+ usuarios (2GB RAM, 1 vCPU)

---

## 🔧 4. ARQUITECTURA ACTUAL

### Análisis de Código

**Conexión Supabase:**
```python
# Singleton pattern - UNA conexión compartida
class SupabaseManager:
    _instance = None
    _client: Client = None
```

**Ventajas:**
- ✅ No hay problema de conexiones (1 conexión reutilizada)
- ✅ Simple y funcional para bajo volumen

**Desventajas:**
- ⚠️ No hay pooling de conexiones
- ⚠️ Si hay muchas requests simultáneas, pueden hacer cola
- ⚠️ No optimizado para alta concurrencia

**Sesiones:**
```python
# Sesiones almacenadas en PostgreSQL
# Tabla: sesiones_conversacion
# Expiración: 1 hora automática
```

**Impacto:**
- ✅ Escalable (BD maneja sesiones)
- ⚠️ Cada consulta de sesión = 1 query a BD
- ⚠️ Si hay 100 usuarios activos = 100 queries simultáneas posibles

**FastAPI/Uvicorn:**
```python
# app/main.py
uvicorn.run(
    "app.main:app",
    host=host,
    port=port,
    reload=reload,
    log_level="info"
)
```

**Configuración actual:**
- **Workers:** 1 (default de uvicorn)
- **Threads:** No configurado (async, no necesita threads)
- **Concurrencia:** Limitada por el worker único

---

## 📊 5. CÁLCULOS DE CAPACIDAD

### Escenario 1: Uso Actual (3 usuarios)

**Carga:**
- 3 usuarios activos
- ~1 mensaje cada 30 segundos por usuario
- = 0.1 mensajes/segundo total

**Capacidad disponible:**
- Telegram: 30 msg/s → **0.3% de uso**
- Supabase: 60 conexiones → **1 conexión en uso**
- Render: 1 worker → **<1% de uso**

**Conclusión:** ✅ **Sobrado de capacidad**

---

### Escenario 2: Crecimiento Moderado (50 usuarios)

**Carga estimada:**
- 50 usuarios activos
- ~1 mensaje cada 10 segundos por usuario
- = 5 mensajes/segundo total

**Capacidad disponible:**
- Telegram: 30 msg/s → **16% de uso** ✅
- Supabase: 1 conexión compartida → **OK** ✅
- **Tu configuración (Starter: 0.5GB RAM, 0.5 vCPU):** ⚠️ **Cuello de botella** - RAM insuficiente
- Render Standard (2GB RAM, 1 vCPU): ✅ **OK**

**Conclusión:** ⚠️ **Necesita mínimo Standard plan ($25/mes) para 50+ usuarios**

---

### Escenario 3: Crecimiento Alto (200 usuarios)

**Carga estimada:**
- 200 usuarios activos
- ~1 mensaje cada 5 segundos por usuario
- = 40 mensajes/segundo total

**Capacidad disponible:**
- Telegram: 30 msg/s → **133% de uso** ❌ **EXCEDE LÍMITE**
- Supabase: 1 conexión → **Posible cuello de botella** ⚠️
- Render Starter: 1 worker → **Cuello de botella** ⚠️
- Render Standard: 1 worker → **OK** ✅

**Conclusión:** ❌ **Necesita optimizaciones y plan más alto**

---

### Escenario 4: Crecimiento Extremo (1000 usuarios)

**Carga estimada:**
- 1000 usuarios activos
- ~1 mensaje cada 5 segundos por usuario
- = 200 mensajes/segundo total

**Problemas:**
- ❌ Telegram: Límite de 30 msg/s → **Necesita múltiples bots o webhooks**
- ❌ Supabase: 1 conexión → **Necesita connection pooling**
- ❌ Render: 1 worker → **Necesita múltiples workers o arquitectura diferente**

**Conclusión:** ❌ **Requiere rediseño arquitectónico**

---

## 🚨 6. CUELLOS DE BOTELLA IDENTIFICADOS

### Orden de Prioridad

**1. RAM Limitada (0.5GB) - CRÍTICO**
- **Problema:** Solo 512MB de RAM disponible
- **Impacto:** Riesgo de Out of Memory (OOM), muy pocos usuarios concurrentes
- **Solución:** Upgrade a Standard ($25/mes) con 2GB RAM mínimo

**2. CPU 0.5 vCPU (Limitado)**
- **Problema:** Solo 50% de 1 CPU core disponible
- **Impacto:** Puede ser limitante con muchas requests simultáneas, latencia puede aumentar
- **Solución:** Upgrade a Standard ($25/mes) con 1 vCPU completo

**2. Telegram Rate Limiting**
- **Problema:** 30 msg/s por bot
- **Impacto:** Con >200 usuarios activos, puede haber cola
- **Solución:** Cambiar a webhooks + múltiples bots si es necesario

**3. Supabase Connection (Singleton)**
- **Problema:** 1 conexión compartida, no hay pooling
- **Impacto:** Con >100 requests simultáneas, puede haber cola
- **Solución:** Implementar connection pooling (opcional, no crítico aún)

**4. Render Workers**
- **Problema:** 1 worker único
- **Impacto:** Con >50 usuarios concurrentes, puede haber cola
- **Solución:** Upgrade a plan que permita múltiples workers

---

## 📈 7. RECOMENDACIONES POR ESCALA

### Escala Pequeña (1-50 usuarios)

**Configuración actual (Starter):**
- ⚠️ **RAM 0.5GB → CRÍTICO para >20 usuarios concurrentes**
- ⚠️ **CPU 0.5 vCPU → Puede ser limitante con alta carga**
- ✅ **Siempre activo** (no se duerme) - Ventaja sobre Free
- ✅ **CPU dedicado** (mejor que Shared) - Ventaja sobre Free
- ✅ Telegram Polling → **OK**
- ✅ Supabase Singleton → **OK**
- ✅ 1 Worker → **OK**

**Acciones:**
1. **Upgrade a Render Standard ($25/mes)** - 2GB RAM y 1 vCPU completo
2. Monitorear uso de RAM y CPU
3. Considerar optimizaciones de memoria mientras tanto

---

### Escala Media (50-200 usuarios)

**Configuración necesaria:**
- ✅ Render Standard ($25/mes)
- ✅ Telegram Webhooks (recomendado)
- ✅ Supabase Singleton → **Considerar pooling**
- ✅ 1 Worker → **OK**

**Acciones:**
1. Upgrade a Render Standard
2. Cambiar a webhooks
3. Implementar connection pooling (opcional)
4. Monitorear métricas

---

### Escala Grande (200-1000 usuarios)

**Configuración necesaria:**
- ✅ Render Standard o más alto
- ✅ Telegram Webhooks + múltiples bots (si es necesario)
- ✅ Supabase Connection Pooling
- ✅ Múltiples workers o arquitectura distribuida

**Acciones:**
1. Rediseñar arquitectura
2. Implementar connection pooling
3. Considerar múltiples instancias
4. Implementar queue system (Redis/RabbitMQ)

---

## 🔍 8. MÉTRICAS A MONITOREAR

### Métricas Críticas

**Telegram:**
- Mensajes por segundo
- Tasa de error (429 - Too Many Requests)
- Latencia de respuesta

**Supabase:**
- Conexiones activas
- Queries por segundo
- Tiempo de respuesta de queries
- Uso de Storage (GB)

**Render:**
- CPU usage
- RAM usage
- Requests por segundo
- Tiempo de respuesta

**Aplicación:**
- Usuarios activos simultáneos
- Sesiones activas
- Archivos subidos/descargados por día

---

## 💡 9. OPTIMIZACIONES FUTURAS

### Corto Plazo (1-3 meses)

1. **Cambiar a Webhooks:**
   - Reducir latencia de 1-2s a <100ms
   - Mejor para producción

2. **Upgrade Render:**
   - Free → Starter ($7/mes)
   - Evitar sleep de 15 minutos

3. **Implementar Caching:**
   - Cache de empresas por usuario
   - Cache de tipos de archivo
   - Reducir queries a BD

### Mediano Plazo (3-6 meses)

1. **Connection Pooling:**
   - Implementar pool de conexiones Supabase
   - Mejorar concurrencia

2. **Métricas y Monitoring:**
   - Dashboard de métricas
   - Alertas de uso

3. **Optimización de Queries:**
   - Índices adicionales si es necesario
   - Optimizar queries frecuentes

### Largo Plazo (6+ meses)

1. **Arquitectura Distribuida:**
   - Múltiples workers
   - Queue system para procesamiento asíncrono

2. **CDN para Archivos:**
   - Si hay muchos archivos, considerar CDN

3. **Microservicios:**
   - Separar bots de API
   - Escalar independientemente

---

## 📋 10. CHECKLIST DE ESCALABILIDAD

### Para Escala Pequeña (1-50 usuarios)
- [ ] Upgrade Render Free → Starter
- [ ] Monitorear uso básico
- [ ] Documentar límites actuales

### Para Escala Media (50-200 usuarios)
- [ ] Upgrade Render Starter → Standard
- [ ] Cambiar a webhooks
- [ ] Implementar connection pooling
- [ ] Dashboard de métricas

### Para Escala Grande (200+ usuarios)
- [ ] Rediseñar arquitectura
- [ ] Múltiples workers/instancias
- [ ] Queue system
- [ ] CDN para archivos
- [ ] Load balancing

---

## 🎯 CONCLUSIÓN

### Estado Actual

**Capacidad:** ⚠️ **Aceptable para uso actual (3 usuarios) pero limitado para crecimiento**

**Limitantes identificados:**
1. 🔴 **RAM 0.5GB** (CRÍTICO - riesgo de OOM con >20 usuarios concurrentes)
2. 🟡 **CPU 0.5 vCPU** (puede ser limitante con alta carga simultánea)
3. ✅ **Siempre activo** (no se duerme - ventaja sobre Free)
4. ✅ **CPU dedicado** (mejor rendimiento que Shared)
5. 🟡 **Telegram rate limiting** (solo con >200 usuarios)
6. 🟡 **Supabase singleton** (solo con >100 usuarios concurrentes)

### Recomendación Inmediata

**Upgrade a Render Standard ($25/mes):**
- ✅ **2GB RAM** (4x más que actual) - Elimina riesgo de OOM
- ✅ **CPU dedicado** (mejor rendimiento, latencia consistente)
- ✅ Siempre activo (no se duerme)
- ✅ Mejor para producción
- **ROI:** Alto (necesario para escalar más allá de 20 usuarios)

### Proyección

**Con tu configuración actual (Starter: 0.5GB RAM, 0.5 vCPU dedicado):**
- ✅ **Hasta 15-20 usuarios:** OK pero apretado
- ⚠️ **20-50 usuarios:** RAM insuficiente, riesgo de OOM
- ❌ **50+ usuarios:** No viable

**Con Render Standard (2GB RAM, 1 vCPU dedicado):**
- ✅ **Hasta 50 usuarios:** OK
- ⚠️ **50-200 usuarios:** Necesita optimizaciones
- ❌ **200+ usuarios:** Necesita rediseño

---

**Última actualización:** 2025-11-14

