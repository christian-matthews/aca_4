# 📋 Resumen de Menús Implementados en Telegram

Este documento resume todos los menús y funcionalidades implementadas en los bots de Telegram del sistema ACA.

---

## 🎯 Índice

1. [Menú Principal - Bot de Producción](#menú-principal---bot-de-producción)
2. [Menú de Administración](#menú-de-administración)
3. [Flujo de Descarga de Archivos](#flujo-de-descarga-de-archivos)
4. [Flujo de Subida de Archivos](#flujo-de-subida-de-archivos)
5. [Asesor IA](#asesor-ia)
6. [Menús de Información y Reportes](#menús-de-información-y-reportes)

---

## 🏠 Menú Principal - Bot de Producción

**Ubicación:** `app/bots/handlers/production_handlers.py`

**Acceso:** Comando `/start` o callback `back_main`

### Botones del Menú Principal

```
┌─────────────────────────────────────┐
│  📊 Información  │  📈 Reporte CFO │
├─────────────────────────────────────┤
│  🤖 Asesor IA    │  ℹ️ Ayuda       │
├─────────────────────────────────────┤
│         🚪 Salir                    │
└─────────────────────────────────────┘
```

### Opciones Disponibles

1. **📊 Información** (`callback_data="informacion"`)
   - Inicia flujo de descarga de archivos
   - Muestra menú de categorías de archivos

2. **📈 Reporte CFO** (`callback_data="reporte_cfo"`)
   - Muestra reporte CFO del mes actual o más reciente
   - Formato JSON estructurado

3. **🤖 Asesor IA** (`callback_data="asesor_ia"`)
   - Inicia sesión con Asesor IA
   - Permite consultas financiero-contables

4. **ℹ️ Ayuda** (`callback_data="ayuda"`)
   - Muestra información de ayuda
   - Botón de contacto con @WingmanBOD

5. **🚪 Salir** (`callback_data="salir"`)
   - Limpia sesiones activas
   - Mensaje de despedida

---

## 🔧 Menú de Administración

**Ubicación:** `app/bots/handlers/admin_handlers.py`

**Acceso:** Comando `/start` en bot de administración (solo admins)

### Botones del Menú Principal

```
┌─────────────────────────────────────┐
│ 📊 Crear Empresa │ 👥 Ver Empresas │
├─────────────────────────────────────┤
│ ➕ Agregar Usuario│ 📋 Ver Usuarios│
├─────────────────────────────────────┤
│ 📈 Estadísticas  │ ⚙️ Configuración│
├─────────────────────────────────────┤
│      🔄 Reiniciar Bots              │
└─────────────────────────────────────┘
```

### Opciones Disponibles

1. **📊 Crear Empresa** (`callback_data="create_empresa"`)
   - Muestra formulario para crear empresa
   - Formato: `/crear_empresa RUT NOMBRE CHAT_ID`

2. **👥 Ver Empresas** (`callback_data="list_empresas"`)
   - Lista todas las empresas registradas
   - Botones en 2 columnas para seleccionar empresa
   - Muestra detalles de cada empresa

3. **➕ Agregar Usuario** (`callback_data="add_user"`)
   - Muestra instrucciones del comando `/adduser`
   - Formato: `/adduser CHAT_ID NOMBRE ROL RUT_EMPRESA`

4. **📋 Ver Usuarios** (`callback_data="list_users"`)
   - Lista usuarios registrados con sus empresas

5. **📈 Estadísticas** (`callback_data="stats"`)
   - Muestra estadísticas del sistema:
     - Empresas activas
     - Usuarios registrados
     - Conversaciones totales

6. **⚙️ Configuración** (`callback_data="config"`)
   - Muestra configuración del sistema
   - Estado de variables de entorno

7. **🔄 Reiniciar Bots** (`callback_data="restart_bots"`)
   - Solicita reinicio de bots (en desarrollo)

---

## 📥 Flujo de Descarga de Archivos

**Ubicación:** `app/bots/handlers/file_download_handler.py`

**Acceso:** Desde menú principal → "📊 Información" o mensaje de texto con solicitud

### Flujo Completo

#### 1. Menú de Categorías

**Botones disponibles (2 columnas):**

```
┌─────────────────────────────────────┐
│  ⚖️ Legales    │  💰 Financieros   │
├─────────────────────────────────────┤
│         ❌ Cancelar                 │
└─────────────────────────────────────┘
```

**Categorías:**
- ⚖️ Legales (`categoria_legal`)
- 💰 Financieros (`categoria_financiero`)

#### 2. Menú de Subtipos (según categoría)

**Categoría: Legales**

```
┌─────────────────────────────────────┐
│ 📜 Estatutos  │ 📋 Poderes         │
├─────────────────────────────────────┤
│ 🆔 CI         │ 🆔 RUT             │
├─────────────────────────────────────┤
│ 🗃️ Otros                            │
├─────────────────────────────────────┤
│ 🔙 Volver     │ ❌ Cancelar        │
└─────────────────────────────────────┘
```

**Categoría: Financieros**

```
┌─────────────────────────────────────┐
│ 📊 Reporte mensual│ 📈 Estados fin. │
├─────────────────────────────────────┤
│ 📁 Carpeta tributaria│ 📄 F29       │
├─────────────────────────────────────┤
│ 📄 F22        │ 🗃️ Otros           │
├─────────────────────────────────────┤
│ 🔙 Volver     │ ❌ Cancelar        │
└─────────────────────────────────────┘
```

#### 3. Menú de Período

```
┌─────────────────────────────────────┐
│ 🟢 Actual (YYYY-MM)│🟡 Anterior    │
├─────────────────────────────────────┤
│ 📅 Otro mes   │ ❌ Cancelar        │
└─────────────────────────────────────┘
```

**Opciones:**
- 🟢 Actual: Mes actual
- 🟡 Anterior: Mes anterior
- 📅 Otro mes: Permite escribir período en texto (con análisis IA)

#### 4. Menú de Selección de Empresa (si tiene múltiples)

```
┌─────────────────────────────────────┐
│ 🏢 Empresa 1  │ 🏢 Empresa 2       │
├─────────────────────────────────────┤
│         ❌ Cancelar                 │
└─────────────────────────────────────┘
```

#### 5. Menú de Selección de Archivos (si hay múltiples)

```
┌─────────────────────────────────────┐
│ 📄 Archivo 1  │ 📄 Archivo 2        │
├─────────────────────────────────────┤
│ 📄 Archivo 3  │ 📄 Archivo 4       │
├─────────────────────────────────────┤
│ ✅ Buscar otro período              │
├─────────────────────────────────────┤
│ 🔙 Volver al menú                   │
└─────────────────────────────────────┘
```

**Callbacks:**
- `download_archivo_{archivo_id}`: Descargar archivo específico
- `download_buscar_otro_periodo`: Buscar otro período
- `download_volver_menu`: Volver al menú principal
- `download_cancelar`: Cancelar proceso

---

## 📤 Flujo de Subida de Archivos

**Ubicación:** `app/bots/handlers/file_upload_handler.py`

**Acceso:** Enviar documento/archivo al bot

### Flujo Completo

#### 1. Menú de Selección de Empresa (si tiene múltiples)

```
┌─────────────────────────────────────┐
│ 🏢 Empresa 1  │ 🏢 Empresa 2       │
├─────────────────────────────────────┤
│         ❌ Cancelar                 │
└─────────────────────────────────────┘
```

#### 2. Menú de Categorías

```
┌─────────────────────────────────────┐
│  ⚖️ Legales    │  💰 Financieros   │
├─────────────────────────────────────┤
│         ❌ Cancelar                 │
└─────────────────────────────────────┘
```

#### 3. Menú de Subtipos (según categoría)

Mismo formato que en descarga, con botones:
- `upload_subtipo_{categoria}_{subtipo}`
- `upload_back_categoria`: Volver a categorías
- `upload_cancelar`: Cancelar

#### 4. Menú de Período

```
┌─────────────────────────────────────┐
│ 🟢 Actual (YYYY-MM)│🟡 Anterior    │
├─────────────────────────────────────┤
│ 📅 Otro mes   │ ❌ Cancelar        │
└─────────────────────────────────────┘
```

**Nota:** Si selecciona "Otro mes", puede escribir en texto natural (ej: "mayo 2024") y el sistema usa IA para interpretarlo.

#### 5. Confirmación de Subida

Después de completar todos los pasos, muestra:
- ✅ Confirmación de subida exitosa
- Detalles del archivo subido
- Botón: "🔙 Volver al menú"

**Callbacks:**
- `upload_empresa_{empresa_id}`: Seleccionar empresa
- `upload_categoria_{categoria}`: Seleccionar categoría
- `upload_subtipo_{categoria}_{subtipo}`: Seleccionar subtipo
- `upload_periodo_actual`: Período actual
- `upload_periodo_anterior`: Período anterior
- `upload_periodo_otro`: Otro período (texto)
- `upload_back_categoria`: Volver a categorías
- `upload_cancelar`: Cancelar proceso

---

## 🤖 Asesor IA

**Ubicación:** `app/bots/handlers/advisor_handler.py`

**Acceso:** Menú principal → "🤖 Asesor IA"

### Menú de Selección de Empresa (si tiene múltiples)

```
┌─────────────────────────────────────┐
│ 🏢 Empresa 1  │ 🏢 Empresa 2       │
├─────────────────────────────────────┤
│         🔙 Volver                   │
└─────────────────────────────────────┘
```

### Interfaz del Asesor IA

```
┌─────────────────────────────────────┐
│ 🔄 Cambiar empresa│🔙 Menú principal│
└─────────────────────────────────────┘
```

**Funcionalidades:**
- Permite hacer preguntas en texto libre
- Analiza consultas sobre reportes financieros
- Detecta acciones prohibidas y escala a ticket
- Detecta solicitudes de ticket y crea ticket automático
- Usa OpenAI Assistants si hay PDFs procesados
- Usa método tradicional (metadatos) como fallback

**Callbacks:**
- `advisor_empresa_{empresa_id}`: Seleccionar empresa
- `advisor_change_company`: Cambiar empresa
- `advisor_create_ticket`: Crear ticket de ayuda
- `advisor_continue`: Continuar con empresa actual
- `back_main`: Volver al menú principal

---

## 📊 Menús de Información y Reportes

**Ubicación:** `app/bots/handlers/production_handlers.py`

### Menú de Información (desde "📊 Información")

**Nota:** Este menú está siendo reemplazado por el flujo de descarga de archivos, pero aún existe en el código.

```
┌─────────────────────────────────────┐
│ 📈 Reportes │ 🏢 Información Comp. │
├─────────────────────────────────────┤
│      🔙 Volver al Menú              │
└─────────────────────────────────────┘
```

### Menú de Reportes

Muestra meses del año actual en 2 columnas:

```
┌─────────────────────────────────────┐
│ Enero      │ Febrero                │
├─────────────────────────────────────┤
│ Marzo      │ Abril                  │
├─────────────────────────────────────┤
│ ... (todos los meses)               │
├─────────────────────────────────────┤
│      🔙 Volver                      │
└─────────────────────────────────────┘
```

**Callback:** `mes_{year}_{month}` (ej: `mes_2024_05`)

### Menú de Detalle de Reporte Mensual

```
┌─────────────────────────────────────┐
│ 📄 Crear Reporte│📎 Adjuntar Archivo│
├─────────────────────────────────────┤
│ 📝 Agregar Comentario│📊 Ver Datos  │
├─────────────────────────────────────┤
│      🔙 Volver a Reportes           │
└─────────────────────────────────────┘
```

**Callbacks:**
- `crear_reporte_{year}_{month}`
- `adjuntar_{year}_{month}`
- `comentario_{year}_{month}`
- `datos_{year}_{month}`

### Menú de Información de Compañía

```
┌─────────────────────────────────────┐
│ ⚖️ Legal      │ 💰 Financiera       │
├─────────────────────────────────────┤
│ 📊 Tributaria │ 📁 Carpeta Tribut. │
├─────────────────────────────────────┤
│      🔙 Volver                      │
└─────────────────────────────────────┘
```

### Menú de Categoría de Información

```
┌─────────────────────────────────────┐
│ 📝 Agregar Info│📎 Adjuntar Archivo │
├─────────────────────────────────────┤
│ 📄 Ver Documentos│📊 Exportar       │
├─────────────────────────────────────┤
│      🔙 Volver                      │
└─────────────────────────────────────┘
```

**Callbacks:**
- `add_{categoria}`
- `attach_{categoria}`
- `docs_{categoria}`
- `export_{categoria}`

---

## 🎨 Características Generales de los Menús

### Formato Estándar

- **Botones en 2 columnas:** Todos los menús usan el helper `organizar_botones_en_columnas()` para organizar botones en 2 columnas
- **Botones de navegación:** 
  - `🔙 Volver`: Regresa al paso anterior
  - `❌ Cancelar`: Cancela el proceso actual
  - `🔙 Volver al Menú` / `back_main`: Regresa al menú principal
- **Iconos:** Cada opción tiene un icono emoji para identificación visual

### Estados de Sesión

Los menús mantienen estado mediante `SessionManager`:

- **Descarga:** `intent='descargar_archivo'`
  - Estados: `procesando_ia`, `esperando_categoria`, `esperando_subtipo`, `esperando_periodo`, `esperando_empresa`

- **Subida:** `intent='subir_archivo'`
  - Estados: `esperando_empresa`, `esperando_categoria`, `esperando_subtipo`, `esperando_descripcion`, `esperando_periodo`, `esperando_periodo_texto_ia`, `confirmando_periodo_upload`, `listo_para_subir`

- **Asesor IA:** `intent='asesor_ia'`
  - Estados: `activo`

### Validaciones

- Todos los menús validan usuario antes de mostrar opciones
- Los menús de empresa validan acceso multi-empresa
- Los callbacks validan sesión activa antes de procesar

---

## 📝 Notas Técnicas

### Archivos Relacionados

- `app/bots/handlers/production_handlers.py`: Menú principal y reportes
- `app/bots/handlers/admin_handlers.py`: Menú de administración
- `app/bots/handlers/file_download_handler.py`: Flujo de descarga
- `app/bots/handlers/file_upload_handler.py`: Flujo de subida
- `app/bots/handlers/advisor_handler.py`: Asesor IA
- `app/utils/file_types.py`: Definición de categorías y subtipos

### Callbacks Comunes

- `back_main`: Volver al menú principal
- `{action}_cancelar`: Cancelar proceso (ej: `download_cancelar`, `upload_cancelar`)
- `{action}_back_{step}`: Volver a paso anterior (ej: `download_back_categoria`)

### Integración con IA

- **Descarga:** Usa IA para extraer intención de mensajes de texto
- **Subida:** Usa IA para interpretar períodos en texto natural
- **Asesor IA:** Usa OpenAI Assistants API o método tradicional según disponibilidad de PDFs

---

## 🔄 Flujos de Navegación

### Flujo de Descarga Completo

```
Menú Principal
    ↓
📊 Información
    ↓
Categorías (⚖️ Legales / 💰 Financieros)
    ↓
Subtipos (según categoría)
    ↓
Período (🟢 Actual / 🟡 Anterior / 📅 Otro)
    ↓
Empresa (solo si tiene múltiples)
    ↓
Resultados / Selección de archivos
    ↓
Descarga / Volver al menú
```

### Flujo de Subida Completo

```
Enviar archivo
    ↓
Empresa (solo si tiene múltiples)
    ↓
Categorías (⚖️ Legales / 💰 Financieros)
    ↓
Subtipos (según categoría)
    ↓
Descripción (solo si requiere)
    ↓
Período (🟢 Actual / 🟡 Anterior / 📅 Otro)
    ↓
Confirmación de subida
    ↓
Volver al menú
```

### Flujo de Asesor IA

```
Menú Principal
    ↓
🤖 Asesor IA
    ↓
Empresa (solo si tiene múltiples)
    ↓
Interfaz del Asesor
    ↓
Preguntas en texto libre
    ↓
Respuestas / Tickets
```

---

**Última actualización:** 2025-01-XX
**Versión del sistema:** ACA 4.0

