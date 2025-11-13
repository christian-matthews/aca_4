#!/usr/bin/env python3
"""
🚀 Script de inicio para ACA 4.0 en PRODUCCIÓN (Render)
Ejecuta la aplicación sin reload y usando el puerto de Render
"""

import os
import sys
import logging
from pathlib import Path

# Agregar el directorio raíz al path
sys.path.insert(0, str(Path(__file__).parent))

def setup_environment():
    """Configurar entorno de producción"""
    # Configurar logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # En producción, las variables de entorno vienen de Render
    # No necesitamos verificar archivo .env
    
    return True

def validate_config():
    """Validar configuración"""
    try:
        from app.config import Config
        Config.validate()
        print("✅ Configuración validada correctamente")
        return True
    except Exception as e:
        print(f"❌ Error en configuración: {e}")
        return False

def main():
    """Función principal para producción"""
    print("🚀 Iniciando ACA 4.0 en PRODUCCIÓN...")
    
    # Configurar entorno
    if not setup_environment():
        print("❌ Error configurando entorno")
        sys.exit(1)
    
    # Validar configuración
    if not validate_config():
        print("❌ Error validando configuración")
        sys.exit(1)
    
    print("✅ Entorno configurado correctamente")
    print("🤖 Iniciando bots de Telegram...")
    
    try:
        # Importar y ejecutar la aplicación
        from app.main import app, run_server
        
        # Obtener puerto de Render (variable de entorno PORT)
        port = int(os.getenv("PORT", "8000"))
        host = "0.0.0.0"
        
        print(f"🌐 Servidor web iniciado en {host}:{port}")
        print(f"📊 Documentación API en http://{host}:{port}/docs")
        print(f"🔍 Health check en http://{host}:{port}/health")
        print("📱 Bots de Telegram iniciados")
        
        # Ejecutar sin reload en producción
        run_server(host=host, port=port, reload=False)
        
    except KeyboardInterrupt:
        print("\n👋 Aplicación detenida")
    except Exception as e:
        print(f"❌ Error ejecutando aplicación: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()

