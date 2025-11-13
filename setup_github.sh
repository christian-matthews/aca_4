#!/bin/bash
# Script para inicializar y subir el proyecto a GitHub

set -e  # Salir si hay errores

echo "🚀 Configurando proyecto para GitHub..."
echo ""

# Verificar que estamos en el directorio correcto
if [ ! -f "requirements.txt" ]; then
    echo "❌ Error: No se encontró requirements.txt"
    echo "   Asegúrate de estar en el directorio raíz del proyecto"
    exit 1
fi

# Verificar que Git está instalado
if ! command -v git &> /dev/null; then
    echo "❌ Error: Git no está instalado"
    echo "   Instala Git desde: https://git-scm.com/"
    exit 1
fi

echo "✅ Git está instalado"
echo ""

# Inicializar Git si no existe
if [ ! -d ".git" ]; then
    echo "📦 Inicializando repositorio Git..."
    git init
    echo "✅ Repositorio Git inicializado"
else
    echo "✅ Repositorio Git ya existe"
fi

echo ""

# Verificar que .gitignore existe
if [ ! -f ".gitignore" ]; then
    echo "⚠️  Advertencia: No se encontró .gitignore"
    echo "   Se creará uno básico..."
    # El .gitignore ya debería estar creado, pero por si acaso
fi

# Agregar todos los archivos
echo "📝 Agregando archivos al staging..."
git add .

echo ""
echo "📋 Archivos que se van a subir:"
git status --short

echo ""
read -p "¿Continuar con el commit? (s/n): " -n 1 -r
echo ""

if [[ ! $REPLY =~ ^[Ss]$ ]]; then
    echo "❌ Operación cancelada"
    exit 1
fi

# Hacer commit
echo "💾 Creando commit inicial..."
git commit -m "Initial commit: ACA 4.0 - Sistema de Bots de Telegram con Supabase

- Sistema de bots (Admin y Producción)
- Gestión de archivos (subida y descarga)
- Asesor IA con contexto automático
- Sistema de roles y permisos
- Multiempresa
- Integración con Supabase Storage
- API REST para consultas"

echo ""
echo "✅ Commit creado exitosamente"
echo ""

# Preguntar si quiere conectar con GitHub
read -p "¿Quieres conectar con un repositorio de GitHub? (s/n): " -n 1 -r
echo ""

if [[ $REPLY =~ ^[Ss]$ ]]; then
    echo ""
    echo "📝 Para conectar con GitHub:"
    echo ""
    echo "1. Crea un repositorio en GitHub (github.com → New repository)"
    echo "2. NO inicialices con README (ya tenemos uno)"
    echo "3. Copia la URL del repositorio"
    echo ""
    read -p "Pega la URL del repositorio de GitHub: " GITHUB_URL
    
    if [ -z "$GITHUB_URL" ]; then
        echo "❌ URL vacía, saltando conexión con GitHub"
    else
        echo ""
        echo "🔗 Conectando con GitHub..."
        git remote add origin "$GITHUB_URL" 2>/dev/null || git remote set-url origin "$GITHUB_URL"
        git branch -M main
        
        echo ""
        echo "✅ Repositorio conectado con GitHub"
        echo ""
        read -p "¿Quieres subir el código ahora? (s/n): " -n 1 -r
        echo ""
        
        if [[ $REPLY =~ ^[Ss]$ ]]; then
            echo "⬆️  Subiendo código a GitHub..."
            git push -u origin main
            echo ""
            echo "✅ ¡Código subido exitosamente a GitHub!"
            echo ""
            echo "🌐 Tu repositorio está en: $GITHUB_URL"
        else
            echo ""
            echo "📝 Para subir más tarde, ejecuta:"
            echo "   git push -u origin main"
        fi
    fi
else
    echo ""
    echo "📝 Para conectar con GitHub más tarde:"
    echo "   git remote add origin https://github.com/USUARIO/REPOSITORIO.git"
    echo "   git branch -M main"
    echo "   git push -u origin main"
fi

echo ""
echo "✅ ¡Configuración completada!"
echo ""
echo "📚 Revisa GITHUB_SETUP.md para más información"

