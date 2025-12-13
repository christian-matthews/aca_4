#!/usr/bin/env python3
"""
Entrypoint Wrapper para Telegram Worker
Inicia Telegram polling exactamente como hoy
NO modifica app/bots/bot_manager.py
Solo importa y ejecuta lo existente
"""

import os
import sys
import logging
from pathlib import Path

# Agregar el directorio raíz al path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.config import Config
from app.bots.bot_manager import bot_manager
from app.utils.helpers import setup_logging
from app.database.supabase import get_supabase_client

# Configurar logging
setup_logging()
logger = logging.getLogger(__name__)


def validate_configuration() -> bool:
    """Validar configuración"""
    try:
        Config.validate()
        logger.info("✅ Configuración validada correctamente")
        return True
    except ValueError as e:
        logger.error(f"❌ Error en configuración: {e}")
        return False


def check_supabase_connection() -> bool:
    """Verificar conexión con Supabase"""
    try:
        supabase = get_supabase_client()
        result = supabase.table('empresas').select('id').limit(1).execute()
        logger.info("✅ Conexión con Supabase verificada")
        return True
    except Exception as e:
        logger.error(f"❌ Error verificando Supabase: {e}")
        return False


async def start_telegram_bots():
    """Iniciar bots de Telegram (polling)"""
    try:
        # 1. Validar configuración
        if not validate_configuration():
            raise ValueError("Configuración inválida")
        
        # 2. Verificar conexión con Supabase
        if not check_supabase_connection():
            logger.warning("⚠️ No se pudo verificar conexión con Supabase")
        
        # 3. Inicializar bots (usa bot_manager existente)
        await bot_manager.initialize_bots()
        logger.info("✅ Bots inicializados correctamente")
        
        # 4. Iniciar bots con polling (usa bot_manager existente)
        await bot_manager.start_bots()
        logger.info("✅ Bots iniciados y escuchando mensajes (polling)")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Error iniciando bots de Telegram: {e}")
        raise


async def stop_telegram_bots():
    """Detener bots de Telegram"""
    try:
        await bot_manager.stop_bots()
        logger.info("✅ Bots detenidos correctamente")
        return True
    except Exception as e:
        logger.error(f"❌ Error deteniendo bots: {e}")
        return False


def main():
    """Función principal - Wrapper para Telegram polling"""
    import asyncio
    
    logger.info("🤖 Iniciando Telegram Worker (polling)...")
    logger.info("📱 Este proceso solo maneja Telegram")
    logger.info("⚠️ NO inicia servicio webhook de Teams")
    
    try:
        # Ejecutar bots en modo continuo
        loop = asyncio.get_event_loop()
        loop.run_until_complete(start_telegram_bots())
        
        # Mantener el proceso corriendo
        logger.info("🔄 Telegram Worker corriendo... (Ctrl+C para detener)")
        loop.run_forever()
        
    except KeyboardInterrupt:
        logger.info("\n👋 Deteniendo Telegram Worker...")
        loop = asyncio.get_event_loop()
        loop.run_until_complete(stop_telegram_bots())
        logger.info("✅ Telegram Worker detenido")
    except Exception as e:
        logger.error(f"❌ Error en Telegram Worker: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

