# 👋 LÉEME PRIMERO - ACA 4.0

**Bienvenido al proyecto ACA 4.0**  
**Última actualización:** 2024-12-05  
**Versión:** 4.1.1

---

## 🎯 SI ESTÁS INICIANDO UNA NUEVA SESIÓN DE CHAT

**1. Abre y copia el contenido de:**
```
CONTEXTO_PROYECTO.md
```

**2. Pégalo al inicio del chat**

---

## 🆕 NOVEDADES (Diciembre 2024)

### 🤖 **Asesor IA con OpenAI Assistants**
- Búsqueda inteligente en PDFs de la empresa
- Vector Store por empresa (aislamiento de datos)
- NO inventa datos - solo información verificable

### 🎫 **Sistema de Tickets**
- ID único: `TKT-YYYYMMDD-XXXX`
- Automático cuando IA no puede responder
- Manual: "crear ticket", "necesito ayuda"

### 📤 **Subida automática a OpenAI**
- Reportes (reporte_mensual, estados_financieros)
- Solo archivos PDF
- Mensaje: "Disponible para consultas con Asesor IA"

### 📱 **Menús en 2 columnas**
- Todos los menús estandarizados
- Botón "Volver" después de subir archivo

---

## 🚀 INICIO RÁPIDO

```bash
# Iniciar
python3 run_production.py

# Detener
pkill -9 -f python

# Migrar PDFs a OpenAI
python3 scripts_testing/migrar_pdfs_openai.py
```

---

## ✅ ESTADO ACTUAL

**Sistema:** ✅ Funcional  
**Última prueba:** 2024-12-05

**Funcionalidades:**
- ✅ Subida/descarga de archivos
- ✅ Sistema multi-empresa
- ✅ Asesor IA con OpenAI Assistants
- ✅ Sistema de tickets con ID único
- ✅ Subida automática a OpenAI
- ✅ Menús en 2 columnas

---

## 📂 ARCHIVOS CLAVE

| Archivo | Descripción |
|---------|-------------|
| `CONTEXTO_PROYECTO.md` | Documento core |
| `README.md` | Documentación técnica |
| `RENDER_ENV_VARS.md` | Variables de entorno |
| `app/bots/handlers/advisor_handler.py` | Asesor IA + Tickets |
| `app/services/openai_assistant_service.py` | OpenAI Assistants |
| `app/bots/handlers/file_upload_handler.py` | Subida + OpenAI auto |

---

**Última actualización:** 2024-12-05
