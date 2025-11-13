# 🧩 Definición de Procesos ACA 4.0 – Gestión de Archivos (Subida y Bajada)

Este documento describe los procesos conversacionales y de negocio para la gestión de archivos en **ACA 4.0**, integrando bots de Telegram y almacenamiento en Supabase.

---

## 🚀 1. Proceso: SUBIDA DE ARCHIVOS

**Objetivo:**  

Permitir que un usuario autorizado suba un archivo al bot, el sistema lo clasifique (empresa, tipo, período) y lo registre en Supabase (storage + tabla `archivos`).

### 1.1. Disparador

- Evento: el usuario envía un **documento** al bot de producción (PDF, XLSX, JPG).

- El bot detecta que es un archivo y **no** un mensaje de texto.

### 1.2. Estados del proceso

1. `esperando_empresa`  

2. `esperando_tipo`  

3. `esperando_periodo`  

4. `finalizado`

### 1.3. Paso a paso

**Paso 1 – Identificar empresa**

- El bot consulta qué empresas tiene asignadas ese `chat_id`.  

- Si hay **1 sola**, la asigna directo y pasa al paso 2.  

- Si hay **más de una**, responde:  

  > "¿De qué empresa es este archivo?"  

  y muestra **botones** con las empresas asignadas.  

- Al seleccionar, guardar en la sesión:  

  - `empresa_id`  

  - `nombre_empresa`  

  - `nombre_original_archivo` (del mensaje original)

**Paso 2 – Clasificación rápida**

- El bot responde:  

  > "¿Qué tipo de archivo es?"  

- Botones sugeridos:

  - 🧾 Factura  

  - 💳 Cartola  

  - 📑 Contrato  

  - 📦 Documentación  

  - 🗃️ Otro  

- Al seleccionar, guardar en la sesión:  

  - `tipo`

**Paso 3 – Periodo**

- El bot responde:  

  > "¿Para qué periodo es?"  

- Botones:

  - 🟢 Mes actual (YYYY-MM)  

  - 🟡 Mes anterior (YYYY-MM)  

  - 📅 Otro mes

- Si elige "otro mes", el bot pide texto:  

  > "Ingresa el mes en formato AAAA-MM"  

- Al responder, guardar en la sesión:  

  - `periodo` (normalizado a `YYYY-MM`)

**Paso 4 – Registrar**

- Cuando ya hay `empresa_id`, `tipo`, `periodo` y datos del archivo original:

  - Se envían los datos al servicio de almacenamiento.

  - Se crea un registro en la tabla `archivos`.

- El bot confirma:  

  > "Listo ✅. Guardé el archivo como **{tipo}** de **{empresa}** para **{periodo}**."

### 1.4. Salida del proceso

- Registro en tabla `archivos` con:

  - `empresa_id`

  - `usuario_chat_id`

  - `tipo`

  - `periodo`

  - `nombre_original`

  - `ruta_storage`

  - `metadata` opcional

### 1.5. Reglas de negocio

- Si el usuario cancela en medio → resetear sesión.  

- Si intenta subir sin empresas asignadas → mensaje de advertencia.  

- Todos los botones se construyen dinámicamente desde la BD.

---

## 📥 2. Proceso: BAJADA / CONSULTA DE ARCHIVOS

**Objetivo:**  

El usuario pide archivos en lenguaje natural ("cartolas de mayo de Orbit").  

El bot valida todos los campos (empresa, tipo, periodo) antes de entregar los archivos.  

Si hay errores, corrige con botones.

### 2.1. Disparadores

- Mensaje de texto con intención de descarga: "cartolas", "facturas", "ver documentos", etc.

- Botón "📁 Ver documentos".

### 2.2. Estados del proceso

1. `idle`  

2. `esperando_empresa`  

3. `esperando_periodo`  

4. `esperando_tipo` (si no vino en la frase)  

5. `listo_para_responder`  

6. `finalizado`

### 2.3. Extracción inicial (IA o parser)

La IA o un parser debe intentar extraer:

- `empresa` (texto)

- `tipo` (cartola, factura, contrato…)

- `periodo` (mes actual, mes anterior, "mayo")

- `confianza`

Si falta alguno o la empresa no coincide, se entra en modo conversacional.

---

### 2.4. Paso a paso

**Paso 1 – Confirmar empresa**

- Condición: nombre no coincide con las asignadas o mal escrito.

- Bot:

  > "Por favor confirma la empresa 👇"

- Muestra solo las empresas asignadas al usuario.  

- Al hacer clic, guardar:

  - `empresa_id`

  - `empresa_nombre`

**Paso 2 – Confirmar periodo**

- Si el usuario dijo "mayo" sin año:

  > "¿A qué mayo te refieres?"

  - 🟢 Mayo 2025

  - 🟡 Mayo 2024

  - 📅 Otro mes

- Si elige "otro mes" → pedir formato `AAAA-MM`  

- Si no dijo periodo:

  > "¿Qué periodo quieres?"

  - 🟢 Mes actual (YYYY-MM)

  - 🟡 Mes anterior (YYYY-MM)

  - 📅 Otro mes  

- Guardar:  

  - `periodo = YYYY-MM`

**Paso 3 – Confirmar tipo (si falta)**

- Si el mensaje original no especifica tipo:

  > "¿Qué tipo de documento quieres?"

  - 🧾 Cartolas  

  - 💳 Facturas  

  - 📑 Contratos  

  - 📦 Otros  

- Guardar:  

  - `tipo`

**Paso 4 – Consultar archivos**

Con los 3 campos validados (`empresa_id`, `tipo`, `periodo`):

- Consultar en Supabase la tabla `archivos`.

- Si encuentra resultados, listar los links firmados.  

- Si no encuentra:

  > "No encontré archivos de ese tipo para ese periodo. ¿Quieres que te muestre los más recientes?"

**Paso 5 – Responder**

- Si hay archivos:  

  > "Encontré {n} archivos de **{empresa}** para **{periodo}** (**{tipo}**). Toca para descargar 👇"

- Si no hay: ofrecer mostrar recientes.

**Paso 6 – Finalizar**

- Limpiar sesión.  

- Volver a estado `idle`.

---

### 2.5. Integración con IA + validación humana (opcional)

**Lógica:**

- Si IA detecta los 3 campos con `confianza ≥ 0.75` y usuario autorizado → responder directo.  

- Si `confianza < 0.75` → seguir flujo conversacional (confirmar empresa, mes, etc.).  

- Si empresa no autorizada → enviar a bot admin con:

  - texto original

  - interpretación IA

  - botones: "Aprobar y enviar" / "Rechazar"

- Si admin aprueba → el bot responde al usuario y cierra sesión.

---

### 2.6. Datos que guarda la sesión

```json
{
  "chat_id": 123456,
  "estado": "esperando_periodo",
  "intent": "descargar_archivo",
  "data": {
    "empresa_id": 10,
    "empresa_nombre": "OrbitX",
    "tipo": "cartola",
    "periodo_previo": "mayo",
    "periodo": null
  }
}
```

---

## 🧭 3. Resumen para implementación

1. Crear tabla de sesiones: `chat_id`, `estado`, `intent`, `data (json)`.  

2. Flujo de **SUBIDA**:  

   documento → empresa → tipo → periodo → registrar.  

3. Flujo de **BAJADA**:  

   solicitud natural → IA extrae → validación paso a paso → respuesta.  

4. Botones siempre desde la BD (empresas asignadas).  

5. Conversación bloqueante: hasta completar los campos, el bot no responde a nuevos comandos.

---

📘 **Resultado esperado:**  

- Subidas y descargas 100% trazables por empresa, tipo y periodo.  

- Experiencia conversacional natural pero segura.  

- Compatible con multiempresa y futura validación humana.


