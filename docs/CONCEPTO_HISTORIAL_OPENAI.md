# 🧠 Concepto: Historial de Conversación e Integración con OpenAI

> **⚠️ NOTA IMPORTANTE (2025-11-11):**  
> El sistema ahora usa un **flujo estructurado con botones** por defecto. La integración con OpenAI está disponible pero **no es requerida**. Este documento explica el concepto original de IA, que puede reactivarse en el futuro si se necesita.

---

## 📋 Índice
1. [Sistema Actual de Logging](#sistema-actual)
2. [Concepto de Historial Conversacional](#historial-conversacional)
3. [Integración con OpenAI](#integracion-openai)
4. [Flujo Completo: Descarga de Archivos con IA](#flujo-completo)
5. [Implementación Propuesta](#implementacion)

---

## 1. Sistema Actual de Logging {#sistema-actual}

### 1.1. ¿Qué se registra actualmente?

**Tabla `conversaciones`:**
```sql
- id (UUID)
- chat_id (BIGINT) - ID del chat de Telegram
- empresa_id (UUID) - Empresa del usuario
- mensaje (TEXT) - Mensaje del usuario
- respuesta (TEXT) - Respuesta del bot
- usuario_nombre (VARCHAR)
- usuario_username (VARCHAR)
- bot_tipo (VARCHAR) - 'admin' o 'production'
- comando (VARCHAR) - Si fue un comando
- parametros (JSONB) - Parámetros del comando
- metadata (JSONB) - Metadatos adicionales
- created_at (TIMESTAMPTZ)
```

### 1.2. ¿Cómo se registra?

**Automáticamente con decoradores:**
```python
@log_production_conversation
async def handle_message(update, context):
    # El decorador registra automáticamente:
    # - Mensaje del usuario
    # - Respuesta del bot
    # - Timestamp
    # - Metadatos
```

**Servicio `ConversationLogger`:**
```python
conversation_logger.log_message(
    update=update,
    response_text="Respuesta del bot",
    bot_type="production"
)
```

### 1.3. ¿Para qué sirve actualmente?

✅ **Auditoría**: Ver qué dijo cada usuario  
✅ **Analíticas**: Estadísticas de uso  
✅ **Debugging**: Ver errores y problemas  
❌ **NO se usa para contexto conversacional** (aún)

---

## 2. Concepto de Historial Conversacional {#historial-conversacional}

### 2.1. ¿Qué es el "contexto conversacional"?

**Problema:**
```
Usuario: "Quiero ver las cartolas de mayo"
Bot: "¿De qué empresa?"  ← No recuerda que el usuario solo tiene 1 empresa
Usuario: "Orbit"
Bot: "¿Qué mes?"  ← Ya dijo "mayo" pero el bot no lo recuerda
```

**Solución con contexto:**
```
Usuario: "Quiero ver las cartolas de mayo"
Bot: [Consulta historial] → Usuario tiene 1 empresa: Orbit
Bot: [Extrae con IA] → tipo="cartola", periodo="2024-05"
Bot: "Encontré 3 cartolas de Orbit para mayo 2024"
```

### 2.2. ¿Cómo mantener el contexto?

**Opción 1: Sesiones Conversacionales (YA IMPLEMENTADO)**
```python
# Tabla: sesiones_conversacion
{
    "chat_id": 123456,
    "estado": "esperando_periodo",
    "intent": "descargar_archivo",
    "data": {
        "empresa_id": "uuid-empresa",
        "tipo": "cartola",
        "periodo_previo": "mayo"
    }
}
```

**Opción 2: Historial de Últimas N Conversaciones**
```python
# Obtener últimas 10 conversaciones del usuario
historial = conversation_logger.get_user_conversation_history(
    chat_id=123456,
    limit=10
)

# Formato:
[
    {"mensaje": "Hola", "respuesta": "Bienvenido", "created_at": "..."},
    {"mensaje": "Quiero ver archivos", "respuesta": "¿Qué tipo?", "created_at": "..."},
    ...
]
```

**Opción 3: Combinación (RECOMENDADO)**
- **Sesiones**: Para flujos estructurados (subida/descarga)
- **Historial**: Para contexto general y extracción con IA

---

## 3. Integración con OpenAI {#integracion-openai}

### 3.1. ¿Para qué usar OpenAI?

**Caso de uso: Extracción de Intención**

**Sin IA:**
```
Usuario: "Necesito las facturas de Orbit del mes pasado"
Bot: "¿Qué tipo de archivo?"  ← Pregunta innecesaria
Bot: "¿De qué empresa?"  ← Ya lo dijo
Bot: "¿Qué mes?"  ← Ya lo dijo
```

**Con IA:**
```
Usuario: "Necesito las facturas de Orbit del mes pasado"
Bot: [IA analiza] → {
    "tipo": "factura",
    "empresa": "Orbit",
    "periodo": "2024-04",  # mes pasado
    "confianza": 0.95
}
Bot: "Encontré 5 facturas de Orbit para abril 2024"
```

### 3.2. ¿Cómo funciona la extracción?

**Prompt para OpenAI:**
```python
prompt = f"""
Analiza el siguiente mensaje de un usuario que quiere descargar archivos.

Mensaje: "{mensaje_usuario}"

Contexto:
- Empresas disponibles: {empresas_usuario}
- Si solo hay 1 empresa, NO preguntes por empresa (usa esa automáticamente)
- Mes actual: {mes_actual}
- Historial reciente: {ultimas_3_conversaciones}
- Sesión activa: {sesion_activa}  # Si hay sesión de descarga, úsala como contexto

TIPOS DE ARCHIVO VÁLIDOS (usa EXACTAMENTE estos):
Categoría LEGAL:
  - estatutos_empresa
  - poderes
  - ci
  - rut
  - otros (requiere descripción)

Categoría FINANCIERO:
  - reporte_mensual
  - estados_financieros
  - carpeta_tributaria
  - f29
  - f22
  - otros (requiere descripción)

Extrae:
1. categoria: "legal" | "financiero" | null
2. subtipo: uno de los tipos válidos arriba | null
3. empresa: "nombre_empresa" | null (SOLO si hay múltiples empresas)
4. periodo: "YYYY-MM" | "mes_actual" | "mes_anterior" | null
5. confianza: 0.0 a 1.0

IMPORTANTE:
- Si el usuario tiene SOLO 1 empresa, NO extraigas empresa (se asignará automáticamente)
- Usa los nombres EXACTOS de los subtipos listados arriba
- Si menciona "cartola" o "factura", mapea a los tipos correctos (reporte_mensual, estados_financieros, etc.)

Responde SOLO en JSON:
{{
    "categoria": "legal" | "financiero" | null,
    "subtipo": "estatutos_empresa" | "reporte_mensual" | ... | null,
    "empresa": "nombre_empresa" | null,
    "periodo": "YYYY-MM" | "mes_actual" | "mes_anterior" | null,
    "confianza": 0.85
}}
"""
```

**Respuesta de OpenAI:**
```json
{
    "categoria": "financiero",
    "subtipo": "reporte_mensual",
    "empresa": null,  // Usuario tiene solo 1 empresa, no se extrae
    "periodo": "2024-04",
    "confianza": 0.92
}
```

### 3.3. ¿Cuándo usar IA vs. Flujo Estructurado?

**Usar IA si:**
- ✅ `confianza >= 0.75` → Responder directo
- ✅ Usuario autorizado → Validar y entregar
- ✅ Todos los campos extraídos → No preguntar nada
- ✅ Si tiene 1 empresa → NO preguntar empresa (asignar automáticamente)

**Usar flujo estructurado si:**
- ❌ `confianza < 0.75` → Preguntar para confirmar
- ❌ Falta algún campo → Preguntar específicamente
- ❌ Empresa no coincide → Mostrar botones
- ❌ Si tiene múltiples empresas y no especificó → Preguntar empresa

---

## 4. Flujo Completo: Descarga de Archivos con IA {#flujo-completo}

### 4.1. Flujo Propuesto

```
┌─────────────────────────────────────────────────────────┐
│ 1. Usuario envía mensaje: "cartolas de mayo"            │
└─────────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────┐
│ 2. Obtener contexto:                                    │
│    - Historial últimas 5 conversaciones                 │
│    - Empresas asignadas al usuario                       │
│    - Sesión activa de descarga (si existe) ← CONTEXTO   │
│    - Tipos de archivo válidos (de file_types.py)        │
└─────────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────┐
│ 3. Enviar a OpenAI para extracción:                    │
│    - Mensaje original                                   │
│    - Contexto completo                                  │
│    - Prompt estructurado                                 │
└─────────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────┐
│ 4. Procesar respuesta de IA:                           │
│    - Validar JSON                                       │
│    - Verificar confianza                                │
│    - Validar empresa (seguridad)                        │
└─────────────────────────────────────────────────────────┘
                        ↓
        ┌───────────────┴───────────────┐
        │                               │
   confianza >= 0.75            confianza < 0.75
        │                               │
        ↓                               ↓
┌───────────────┐              ┌───────────────┐
│ 5a. Responder │              │ 5b. Flujo    │
│    directo    │              │    estructurado│
│               │              │               │
│ - Validar     │              │ - Preguntar   │
│   empresa     │              │   empresa     │
│ - Buscar      │              │ - Preguntar   │
│   archivos    │              │   tipo        │
│ - Entregar    │              │ - Preguntar   │
│   links       │              │   período     │
└───────────────┘              └───────────────┘
```

### 4.2. Ejemplo Real

**Input del usuario:**
```
"Necesito los reportes mensuales de mayo"
```

**Contexto obtenido:**
```python
{
    "historial": [
        {"mensaje": "Hola", "respuesta": "Bienvenido"},
        {"mensaje": "¿Qué puedo hacer?", "respuesta": "Puedes subir o descargar archivos"}
    ],
    "empresas": ["Orbit"],  # Solo 1 empresa
    "mes_actual": "2024-05",
    "mes_anterior": "2024-04",
    "sesion_activa": None,  # Primera solicitud
    "tipos_validos": {
        "legal": ["estatutos_empresa", "poderes", "ci", "rut", "otros"],
        "financiero": ["reporte_mensual", "estados_financieros", "carpeta_tributaria", "f29", "f22", "otros"]
    }
}
```

**Prompt a OpenAI:**
```
Analiza: "Necesito los reportes mensuales de mayo"
Empresas: ["Orbit"] (SOLO 1 - NO preguntes por empresa)
Mes actual: 2024-05
Tipos válidos: [lista completa de subtipos]
```

**Respuesta de OpenAI:**
```json
{
    "categoria": "financiero",
    "subtipo": "reporte_mensual",
    "empresa": null,  // No se extrae porque solo tiene 1 empresa
    "periodo": "2024-05",
    "confianza": 0.95
}
```

**Acción del bot:**
```python
if confianza >= 0.75:
    # Asignar empresa automáticamente (solo tiene 1)
    empresa_id = empresas_usuario[0]['id']
    
    # Buscar archivos con tipos correctos
    archivos = buscar_archivos(
        empresa_id=empresa_id,
        categoria="financiero",
        subtipo="reporte_mensual",
        periodo="2024-05"
    )
    # Responder con links
    responder_con_archivos(archivos)
```

**Ejemplo con sesión activa (contexto previo):**
```
Usuario: "Quiero ver archivos"
Bot: "¿Qué tipo de archivo?"  ← Inicia sesión de descarga
Usuario: "Reportes de mayo"
Bot: [IA usa sesión como contexto] → Ya sabe que es descarga
     [IA extrae] → subtipo="reporte_mensual", periodo="2024-05"
Bot: "Encontré 3 reportes mensuales para mayo 2024"
```

---

## 5. Implementación Propuesta {#implementacion}

### 5.1. Servicio de IA (`app/services/ai_service.py`)

```python
class AIService:
    """Servicio para integración con OpenAI"""
    
    def __init__(self):
        self.openai_key = Config.OPENAI_API_KEY
        self.client = OpenAI(api_key=self.openai_key) if self.openai_key else None
    
    async def extract_file_intent(
        self,
        mensaje: str,
        empresas_usuario: list,
        historial: list = None,
        sesion_activa: Dict = None
    ) -> Dict[str, Any]:
        """
        Extrae intención de descarga de archivos usando OpenAI
        
        Args:
            mensaje: Mensaje del usuario
            empresas_usuario: Lista de empresas del usuario
            historial: Últimas conversaciones (opcional)
            sesion_activa: Sesión activa de descarga (opcional) ← CONTEXTO IMPORTANTE
        
        Returns:
            {
                "categoria": "legal" | "financiero" | null,
                "subtipo": "reporte_mensual" | "estatutos_empresa" | ... | null,
                "empresa": "Orbit" | null,  # null si solo tiene 1 empresa
                "periodo": "2024-05" | null,
                "confianza": 0.85
            }
        """
        if not self.client:
            return {"confianza": 0.0}  # Sin IA disponible
        
        # Construir prompt con contexto (incluyendo sesión activa)
        # Obtener tipos válidos dinámicamente desde file_types.py
        from app.utils.file_types import get_todos_subtipos
        tipos_validos = get_todos_subtipos()
        
        prompt = self._build_extraction_prompt(
            mensaje, empresas_usuario, historial, sesion_activa, tipos_validos
        )
        
        # Llamar a OpenAI
        response = await self.client.chat.completions.create(
            model="gpt-4o-mini",  # Modelo económico
            messages=[
                {"role": "system", "content": "Eres un asistente que extrae información de solicitudes de archivos."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,  # Bajo para respuestas consistentes
            response_format={"type": "json_object"}
        )
        
        # Parsear respuesta
        return json.loads(response.choices[0].message.content)
```

### 5.2. Handler de Descarga Mejorado

```python
async def handle_download_request(update, context):
    """Manejar solicitud de descarga con IA"""
    
    mensaje = update.message.text
    chat_id = update.effective_chat.id
    
    # 1. Obtener contexto
    historial = conversation_logger.get_user_conversation_history(
        chat_id, limit=5
    )
    empresas = get_user_empresas(chat_id)
    
    # 2. Obtener sesión activa (si existe) ← CONTEXTO PARA IA
    session_manager = get_session_manager()
    sesion_activa = session_manager.get_session(chat_id)
    
    # Si no hay sesión, crear una nueva para mantener contexto
    if not sesion_activa or sesion_activa.get('intent') != 'descargar_archivo':
        session_manager.create_session(
            chat_id=chat_id,
            intent='descargar_archivo',
            estado='procesando_ia',
            data={}
        )
        sesion_activa = session_manager.get_session(chat_id)
    
    # 3. Extraer intención con IA (incluyendo sesión como contexto)
    ai_service = AIService()
    intent = await ai_service.extract_file_intent(
        mensaje, empresas, historial, sesion_activa
    )
    
    # 4. Si solo tiene 1 empresa, asignarla automáticamente
    if len(empresas) == 1:
        intent['empresa'] = None  # No se pregunta
        intent['empresa_id'] = empresas[0]['id']  # Se asigna automáticamente
    
    # 5. Decidir flujo
    if intent['confianza'] >= 0.75 and all([
        intent.get('categoria'),
        intent.get('subtipo'),
        intent.get('periodo')
    ]):
        # Flujo directo (validar empresa si tiene múltiples)
        if len(empresas) > 1 and not intent.get('empresa'):
            # Tiene múltiples pero no especificó → preguntar
            await process_ask_empresa(update, empresas)
        else:
            # Responder directo
            await process_direct_download(update, intent, empresas)
    else:
        # Flujo estructurado (completar campos faltantes)
        await process_structured_download(update, intent, sesion_activa)
```

### 5.3. Ventajas de este Enfoque

✅ **Flexible**: Funciona con o sin OpenAI  
✅ **Seguro**: Valida empresa antes de entregar  
✅ **Eficiente**: Responde directo si confianza alta  
✅ **Robusto**: Cae a flujo estructurado si IA falla  
✅ **Contextual**: Usa historial para mejor extracción

---

## 📊 Resumen

| Aspecto | Sin IA | Con IA |
|---------|--------|--------|
| **Extracción** | Manual (preguntas) | Automática |
| **Velocidad** | 3-5 mensajes | 1 mensaje |
| **Experiencia** | Robótica | Natural |
| **Costo** | $0 | ~$0.001 por mensaje |
| **Fallback** | N/A | Flujo estructurado |

---

## 🚀 Próximos Pasos

1. ✅ Crear `AIService` con integración OpenAI
2. ✅ Modificar handler de descarga para usar IA
3. ✅ Implementar fallback a flujo estructurado
4. ✅ Agregar logging de extracciones IA
5. ✅ Testing con casos reales

