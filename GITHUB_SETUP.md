# 🚀 Guía para Subir el Proyecto a GitHub

## 📋 Pasos para Subir a GitHub

### 1. Verificar que Git está instalado

```bash
git --version
```

Si no está instalado:
- **macOS**: `brew install git`
- **Linux**: `sudo apt-get install git`
- **Windows**: Descargar de [git-scm.com](https://git-scm.com/)

### 2. Inicializar el repositorio Git

```bash
cd "/Users/christianmatthews/Library/Mobile Documents/com~apple~CloudDocs/CURSOR/ACA 3.0/aca_4"

# Inicializar Git
git init

# Verificar que .gitignore existe
ls -la .gitignore
```

### 3. Agregar todos los archivos

```bash
# Agregar todos los archivos (excepto los ignorados en .gitignore)
git add .

# Verificar qué se va a subir
git status
```

### 4. Hacer el primer commit

```bash
git commit -m "Initial commit: ACA 4.0 - Sistema de Bots de Telegram con Supabase"
```

### 5. Crear repositorio en GitHub

1. Ve a [github.com](https://github.com)
2. Haz clic en **"New repository"** (o el botón **"+"** → **"New repository"**)
3. Nombre del repositorio: `aca-4` (o el nombre que prefieras)
4. Descripción: "Sistema de Bots de Telegram con Supabase - Gestión de archivos y Asesor IA"
5. **NO marques** "Initialize with README" (ya tenemos uno)
6. **NO marques** "Add .gitignore" (ya tenemos uno)
7. Haz clic en **"Create repository"**

### 6. Conectar el repositorio local con GitHub

```bash
# Reemplaza TU_USUARIO con tu usuario de GitHub
# Reemplaza aca-4 con el nombre de tu repositorio

git remote add origin https://github.com/TU_USUARIO/aca-4.git

# Verificar que se agregó correctamente
git remote -v
```

### 7. Subir el código a GitHub

```bash
# Subir a la rama main
git branch -M main
git push -u origin main
```

Si GitHub te pide autenticación:
- **Token de acceso personal**: GitHub ya no acepta contraseñas, necesitas un token
- Crea uno en: GitHub → Settings → Developer settings → Personal access tokens → Tokens (classic)
- Permisos necesarios: `repo` (acceso completo a repositorios)

### 8. Verificar en GitHub

Ve a tu repositorio en GitHub y verifica que todos los archivos estén ahí.

## 🔒 Archivos que NO se suben (gracias a .gitignore)

- ✅ `venv/` - Entorno virtual
- ✅ `.env` - Variables de entorno con credenciales
- ✅ `__pycache__/` - Archivos compilados de Python
- ✅ `*.log` - Archivos de log
- ✅ `.DS_Store` - Archivos del sistema macOS

## 📝 Comandos útiles para el futuro

### Ver cambios
```bash
git status
```

### Agregar cambios específicos
```bash
git add archivo.py
git commit -m "Descripción del cambio"
git push
```

### Agregar todos los cambios
```bash
git add .
git commit -m "Descripción del cambio"
git push
```

### Ver historial
```bash
git log --oneline
```

### Crear una nueva rama
```bash
git checkout -b nombre-de-rama
git push -u origin nombre-de-rama
```

## ⚠️ Importante

**NUNCA subas:**
- ❌ Archivo `.env` con credenciales reales
- ❌ Tokens de API
- ❌ Service keys de Supabase
- ❌ Contraseñas

**SÍ sube:**
- ✅ `.env.example` (sin credenciales reales)
- ✅ Código fuente
- ✅ Documentación
- ✅ `requirements.txt`
- ✅ Scripts de migración SQL

## 🚀 Después de subir a GitHub

Una vez que el código esté en GitHub, puedes:

1. **Conectar con Render** para despliegue automático
2. **Compartir el repositorio** con otros desarrolladores
3. **Usar GitHub Actions** para CI/CD
4. **Crear issues** para tracking de bugs
5. **Usar Pull Requests** para code review

## 📚 Recursos

- [Documentación de Git](https://git-scm.com/doc)
- [GitHub Guides](https://guides.github.com/)
- [Crear Personal Access Token](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/creating-a-personal-access-token)

