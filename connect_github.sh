#!/bin/bash
# Script para conectar con GitHub usando token

echo "🔗 Conectar ACA 4.0 con GitHub"
echo "==============================="
echo ""

# Verificar que estamos en el directorio correcto
if [ ! -d ".git" ]; then
    echo "❌ Error: No se encontró repositorio Git"
    exit 1
fi

echo "📝 Necesito la siguiente información:"
echo ""
read -p "1. Tu usuario de GitHub: " GITHUB_USER
read -p "2. Nombre del repositorio (ej: aca-4): " REPO_NAME
read -p "3. Tu Personal Access Token: " GITHUB_TOKEN

if [ -z "$GITHUB_USER" ] || [ -z "$REPO_NAME" ] || [ -z "$GITHUB_TOKEN" ]; then
    echo "❌ Error: Todos los campos son requeridos"
    exit 1
fi

echo ""
echo "🔗 Conectando con GitHub..."

# Configurar remote con token en la URL
GITHUB_URL="https://${GITHUB_TOKEN}@github.com/${GITHUB_USER}/${REPO_NAME}.git"

# Verificar si ya existe origin
if git remote -v | grep -q "origin"; then
    echo "⚠️  Ya existe un remote 'origin', actualizándolo..."
    git remote set-url origin "$GITHUB_URL"
else
    git remote add origin "$GITHUB_URL"
fi

echo "✅ Repositorio conectado"
echo ""

# Configurar rama main
git branch -M main

echo "📊 Estado del repositorio:"
git log --oneline -1
echo ""

read -p "¿Quieres subir el código ahora? (s/n): " -n 1 -r
echo ""

if [[ $REPLY =~ ^[Ss]$ ]]; then
    echo ""
    echo "⬆️  Subiendo código a GitHub..."
    echo ""
    
    if git push -u origin main; then
        echo ""
        echo "✅ ¡ÉXITO! Código subido a GitHub"
        echo ""
        echo "🌐 Tu repositorio está en:"
        echo "   https://github.com/${GITHUB_USER}/${REPO_NAME}"
        echo ""
        echo "⚠️  IMPORTANTE: El token está en la URL del remote"
        echo "   Para mayor seguridad, considera usar SSH o Git Credential Helper"
    else
        echo ""
        echo "❌ Error al subir el código"
        echo "   Verifica que el token tenga permisos 'repo'"
    fi
else
    echo ""
    echo "📝 Para subir más tarde, ejecuta:"
    echo "   git push -u origin main"
fi

