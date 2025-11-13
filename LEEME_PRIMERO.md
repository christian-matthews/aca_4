# 👋 LÉEME PRIMERO - ACA 4.0

**Bienvenido al proyecto ACA 4.0**  
**Última actualización:** 2025-11-13

---

## 🎯 SI ESTÁS INICIANDO UNA NUEVA SESIÓN DE CHAT

**1. Abre y copia el contenido de:**
```
CONTEXTO_PROYECTO.md
```

**2. Pégalo al inicio del chat y di:**
```
"Este es el contexto actual del proyecto ACA 4.0. 
Por favor léelo antes de hacer cualquier cambio para evitar 
sobrescribir avances o modificar cosas que ya funcionan."
```

**3. El asistente AI tendrá todo el contexto necesario**

---

## 📁 ESTRUCTURA SIMPLIFICADA

```
aca_4/
│
├── 🎯 CONTEXTO_PROYECTO.md        ← Documento CORE (pegar en cada sesión)
├── 📁 ESTRUCTURA_PROYECTO.md       ← Mapa del proyecto
├── 📄 LEEME_PRIMERO.md            ← Este archivo
├── 📄 README.md                    ← README técnico del proyecto
│
├── 📂 app/                         ← Código de la aplicación
│   ├── bots/handlers/             ← Lógica de los bots
│   ├── services/                  ← Servicios (Storage, IA, etc.)
│   ├── database/                  ← Cliente Supabase
│   └── utils/                     ← Utilidades
│
├── 📂 docs/                        ← Toda la documentación
│   ├── INDEX.md                   ← Índice completo
│   ├── NO_OLVIDAR.md             ← Puntos críticos ⚠️
│   ├── ESTADO_ACTUAL_SISTEMA.md  ← Estado completo
│   ├── REFERENCIA_RAPIDA.md      ← Comandos rápidos
│   └── [25+ documentos más...]
│
├── 📂 scripts_testing/            ← Scripts de testing
│   ├── README.md                  ← Documentación de scripts
│   ├── verificar_*.py            ← Scripts de verificación
│   └── [13 scripts más...]
│
├── 📂 database/migrations/        ← Migraciones SQL
│   ├── schema_completo.sql
│   ├── 001_add_campos_archivos.sql
│   └── [5 migraciones más...]
│
└── 📄 run.py                       ← Punto de entrada
```

---

## 📚 NAVEGACIÓN RÁPIDA

### **Para diferentes situaciones:**

**🆕 Nueva sesión de chat:**
→ `CONTEXTO_PROYECTO.md`

**🔍 Buscar algo específico:**
→ `ESTRUCTURA_PROYECTO.md` (dónde está cada cosa)

**📖 Ver toda la documentación:**
→ `docs/INDEX.md`

**⚡ Comandos rápidos:**
→ `docs/REFERENCIA_RAPIDA.md`

**⚠️ Antes de modificar código:**
→ `docs/NO_OLVIDAR.md`

**🧪 Testing:**
→ `scripts_testing/README.md`

**🐛 Debugging:**
→ `docs/CAMBIOS_2025-11-13.md` (problemas ya resueltos)

---

## 🚀 INICIO RÁPIDO

### **1. Iniciar el bot:**
```bash
python3 run.py
```

### **2. Detener el bot:**
```bash
lsof -ti:8000 | xargs kill -9
pkill -f "python.*run.py"
```

### **3. Ver logs:**
```bash
tail -f aca_bot.log | grep -E "(🔍|📋|❌|ERROR)"
```

### **4. Crear usuario:**
```bash
/adduser CHAT_ID NOMBRE ROL RUT_EMPRESA
```
Ejemplo: `/adduser 123456789 "Juan Perez" user 76142021-6`

---

## ✅ ESTADO ACTUAL

**Sistema:** ✅ Funcional y probado  
**Última prueba:** 2025-11-13 10:15  
**Problemas conocidos:** Ninguno crítico

**Funcionalidades principales:**
- ✅ Subida de archivos con clasificación completa
- ✅ Descarga de archivos con búsqueda
- ✅ Sistema multi-empresa funcionando
- ✅ Análisis de períodos con IA
- ✅ Comando /adduser simplificado
- ✅ Menús estandarizados en 2 columnas

---

## 📞 SOPORTE

**Documentación completa:** `docs/INDEX.md`  
**Problemas comunes:** `docs/REFERENCIA_RAPIDA.md` (sección Troubleshooting)  
**Puntos críticos:** `docs/NO_OLVIDAR.md`

---

**💡 Tip:** Mantén siempre actualizado `CONTEXTO_PROYECTO.md` después de cambios importantes

---

**Última actualización:** 2025-11-13


