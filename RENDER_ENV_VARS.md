# 🔐 Variables de Entorno para Render

## 📋 Lista Completa de Variables

Copia y pega estas variables en Render Dashboard → Environment Variables

### 🔴 REQUERIDAS (Críticas - Sin estas el bot NO funcionará)

```bash
BOT_ADMIN_TOKEN=
BOT_PRODUCTION_TOKEN=
ADMIN_CHAT_ID=
SUPABASE_URL=
SUPABASE_KEY=
SUPABASE_SERVICE_KEY=
SUPABASE_STORAGE_BUCKET=ACA_4
```

### 🟡 OPCIONALES (Recomendadas)

```bash
OPENAI_API_KEY=
ENVIRONMENT=production
DEBUG=false
MAX_FILE_SIZE_MB=50
```

## 📝 Cómo Obtener Cada Variable

### Telegram Bots

#### BOT_ADMIN_TOKEN
1. Abre Telegram
2. Busca `@BotFather`
3. Envía `/mybots`
4. Selecciona tu bot admin
5. Copia el **Token**

#### BOT_PRODUCTION_TOKEN
1. Mismo proceso con el bot de producción
2. O crea un nuevo bot con `/newbot`

#### ADMIN_CHAT_ID
1. Abre Telegram
2. Busca `@userinfobot`
3. Envía cualquier mensaje
4. Copia tu **ID** (número)

### Supabase

#### SUPABASE_URL
1. Ve a tu proyecto en [supabase.com](https://supabase.com)
2. Settings → **API**
3. Copia **Project URL**

#### SUPABASE_KEY (anon/public key)
1. Mismo lugar: Settings → **API**
2. Copia **anon/public** key

#### SUPABASE_SERVICE_KEY (service_role key)
1. Settings → **API**
2. Copia **service_role** key
3. ⚠️ **MUY IMPORTANTE**: Esta key tiene permisos completos
4. ⚠️ **NUNCA** la compartas públicamente

#### SUPABASE_STORAGE_BUCKET
1. Storage → **Buckets**
2. Verifica que exista el bucket `ACA_4`
3. Si no existe, créalo con permisos públicos

### OpenAI (Opcional - Solo si usas Asesor IA)

#### OPENAI_API_KEY
1. Ve a [platform.openai.com](https://platform.openai.com)
2. API Keys → **Create new secret key**
3. Copia el key (solo se muestra una vez)

## ✅ Verificación

Después de agregar todas las variables, verifica:

1. ✅ Todas las variables REQUERIDAS están configuradas
2. ✅ No hay espacios extra antes/después de los valores
3. ✅ Los valores no tienen comillas (Render las agrega automáticamente)
4. ✅ `SUPABASE_STORAGE_BUCKET` coincide con el nombre real del bucket

## 🔒 Seguridad

**NUNCA:**
- ❌ Compartas estas variables públicamente
- ❌ Las subas a GitHub (están en `.gitignore`)
- ❌ Las incluyas en screenshots o documentación pública

**SÍ:**
- ✅ Úsalas solo en Render Dashboard
- ✅ Guárdalas en un gestor de contraseñas
- ✅ Rótalas periódicamente (especialmente tokens de API)

## 📊 Template para Copiar

```
BOT_ADMIN_TOKEN=1234567890:ABCdefGHIjklMNOpqrsTUVwxyz
BOT_PRODUCTION_TOKEN=9876543210:ZYXwvuTSRqpoNMLkjihGFEdcba
ADMIN_CHAT_ID=123456789
SUPABASE_URL=https://xxxxx.supabase.co
SUPABASE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
SUPABASE_SERVICE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
SUPABASE_STORAGE_BUCKET=ACA_4
OPENAI_API_KEY=sk-...
ENVIRONMENT=production
DEBUG=false
MAX_FILE_SIZE_MB=50
```

**⚠️ Reemplaza los valores de ejemplo con tus valores reales**

