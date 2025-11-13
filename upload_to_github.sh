#!/bin/bash
# Script interactivo para subir el proyecto a GitHub

set -e

echo "🚀 Guía para Subir ACA 4.0 a GitHub"
echo "===================================="
echo ""

# Verificar que estamos en el directorio correcto
if [ ! -d ".git" ]; then
    echo "❌ Error: No se encontró repositorio Git"
    echo "   Ejecuta primero: git init"
    exit 1
fi

echo "✅ Repositorio Git encontrado"
echo ""

# Verificar si ya tiene un remote configurado
if git remote -v | grep -q "origin"; then
    echo "⚠️  Ya tienes un remote 'origin' configurado:"
    git remote -v | grep origin
    echo ""
    read -p "¿Quieres usar este remote? (s/n): " -n 1 -r
    echo ""
    if [[ ! $REPLY =~ ^[Ss]$ ]]; then
        echo "Para cambiar el remote, ejecuta:"
        echo "  git remote remove origin"
        echo "  git remote add origin TU_URL"
        exit 0
    fi
    REMOTE_URL=$(git remote get-url origin)
else
    echo "📝 Necesitas crear un repositorio en GitHub primero"
    echo ""
    echo "PASO 1: Crear repositorio en GitHub"
    echo "-----------------------------------"
    echo "1. Abre tu navegador y ve a: https://github.com/new"
    echo "2. Completa:"
    echo "   - Repository name: aca-4 (o el nombre que prefieras)"
    echo "   - Description: Sistema de Bots de Telegram con Supabase"
    echo "   - Visibility: Público o Privado"
    echo "   - ⚠️  NO marques 'Initialize with README'"
    echo "   - ⚠️  NO marques 'Add .gitignore'"
    echo "3. Haz clic en 'Create repository'"
    echo ""
    read -p "¿Ya creaste el repositorio en GitHub? (s/n): " -n 1 -r
    echo ""
    
    if [[ ! $REPLY =~ ^[Ss]$ ]]; then
        echo ""
        echo "❌ Crea el repositorio primero y luego ejecuta este script nuevamente"
        exit 1
    fi
    
    echo ""
    echo "PASO 2: Conectar con GitHub"
    echo "---------------------------"
    echo "GitHub te mostrará una URL como:"
    echo "  https://github.com/TU_USUARIO/aca-4.git"
    echo ""
    read -p "Pega la URL completa de tu repositorio: " REMOTE_URL
    
    if [ -z "$REMOTE_URL" ]; then
        echo "❌ URL vacía"
        exit 1
    fi
    
    echo ""
    echo "🔗 Conectando con GitHub..."
    git remote add origin "$REMOTE_URL"
    echo "✅ Repositorio conectado"
fi

echo ""
echo "PASO 3: Configurar rama main"
echo "-----------------------------"
git branch -M main
echo "✅ Rama configurada como 'main'"

echo ""
echo "PASO 4: Verificar estado"
echo "------------------------"
echo "Último commit:"
git log --oneline -1
echo ""
echo "Archivos listos para subir:"
git status --short | head -10
if [ $(git status --short | wc -l) -gt 10 ]; then
    echo "... y más archivos"
fi

echo ""
read -p "¿Quieres subir el código ahora? (s/n): " -n 1 -r
echo ""

if [[ ! $REPLY =~ ^[Ss]$ ]]; then
    echo ""
    echo "❌ Operación cancelada"
    echo ""
    echo "Para subir más tarde, ejecuta:"
    echo "  git push -u origin main"
    exit 0
fi

echo ""
echo "⬆️  Subiendo código a GitHub..."
echo ""

# Intentar hacer push
if git push -u origin main; then
    echo ""
    echo "✅ ¡ÉXITO! Código subido a GitHub"
    echo ""
    echo "🌐 Tu repositorio está en: $REMOTE_URL"
    echo ""
    echo "📝 Próximos pasos:"
    echo "   - Configura las variables de entorno en Render"
    echo "   - Conecta Render con este repositorio"
    echo "   - El despliegue se hará automáticamente"
else
    echo ""
    echo "❌ Error al subir el código"
    echo ""
    echo "Posibles causas:"
    echo "1. No estás autenticado en GitHub"
    echo "2. Necesitas un Personal Access Token"
    echo ""
    echo "Solución:"
    echo "1. Ve a: https://github.com/settings/tokens"
    echo "2. Crea un 'Personal access token' (classic)"
    echo "3. Permisos: repo (acceso completo)"
    echo "4. Copia el token"
    echo "5. Cuando Git pida contraseña, usa el token"
    echo ""
    echo "O configura SSH:"
    echo "  https://docs.github.com/en/authentication/connecting-to-github-with-ssh"
fi

