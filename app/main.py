"""
🚀 ACA 4.0 - Sistema de Bots de Telegram con Supabase
Main simplificado con funciones reutilizables
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import logging
from typing import Dict, Any

from app.config import Config
from app.bots.bot_manager import bot_manager
from app.utils.helpers import setup_logging
from app.database.supabase import get_supabase_client
from app.api.conversation_logs import router as conversation_router

# Configurar logging
setup_logging()
logger = logging.getLogger(__name__)

# Crear aplicación FastAPI
app = FastAPI(
    title="ACA 4.0 - Sistema de Bots de Telegram",
    description="API para gestionar bots de Telegram con integración a Supabase",
    version="4.0.0"
)

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Incluir routers de APIs
app.include_router(conversation_router)


# ============================================
# FUNCIONES DE INICIALIZACIÓN
# ============================================

def validate_configuration() -> bool:
    """
    Validar que todas las variables de entorno requeridas estén configuradas
    
    Returns:
        True si la configuración es válida
        
    Raises:
        ValueError: Si faltan variables requeridas
    """
    try:
        Config.validate()
        logger.info("✅ Configuración validada correctamente")
        return True
    except ValueError as e:
        logger.error(f"❌ Error en configuración: {e}")
        raise


async def initialize_bots() -> bool:
    """
    Inicializar los bots de Telegram
    
    Returns:
        True si se inicializaron correctamente
        
    Raises:
        Exception: Si hay error al inicializar
    """
    try:
        await bot_manager.initialize_bots()
        logger.info("✅ Bots inicializados correctamente")
        return True
    except Exception as e:
        logger.error(f"❌ Error inicializando bots: {e}")
        raise


async def start_bots() -> bool:
    """
    Iniciar los bots de Telegram (polling)
    
    Returns:
        True si se iniciaron correctamente
        
    Raises:
        Exception: Si hay error al iniciar
    """
    try:
        await bot_manager.start_bots()
        logger.info("✅ Bots iniciados y escuchando mensajes")
        return True
    except Exception as e:
        logger.error(f"❌ Error iniciando bots: {e}")
        raise


async def stop_bots() -> bool:
    """
    Detener los bots de Telegram
    
    Returns:
        True si se detuvieron correctamente
    """
    try:
        await bot_manager.stop_bots()
        logger.info("✅ Bots detenidos correctamente")
        return True
    except Exception as e:
        logger.error(f"❌ Error deteniendo bots: {e}")
        return False


def check_supabase_connection() -> bool:
    """
    Verificar conexión con Supabase
    
    Returns:
        True si la conexión es exitosa
    """
    try:
        supabase = get_supabase_client()
        # Intentar una consulta simple
        result = supabase.table('empresas').select('id').limit(1).execute()
        logger.info("✅ Conexión con Supabase verificada")
        return True
    except Exception as e:
        logger.error(f"❌ Error verificando Supabase: {e}")
        return False


# ============================================
# EVENTOS DE FASTAPI
# ============================================

@app.on_event("startup")
async def startup_event():
    """Evento de inicio de la aplicación"""
    try:
        # 1. Validar configuración
        validate_configuration()
        
        # 2. Verificar conexión con Supabase
        if not check_supabase_connection():
            logger.warning("⚠️ No se pudo verificar conexión con Supabase")
        
        # 3. Inicializar bots
        await initialize_bots()
        
        # 4. Iniciar bots
        await start_bots()
        
        logger.info("🚀 ACA 4.0 iniciado correctamente")
        
    except Exception as e:
        logger.error(f"❌ Error en startup: {e}")
        raise


@app.on_event("shutdown")
async def shutdown_event():
    """Evento de cierre de la aplicación"""
    try:
        await stop_bots()
        logger.info("👋 ACA 4.0 cerrado correctamente")
    except Exception as e:
        logger.error(f"❌ Error en shutdown: {e}")


# ============================================
# ENDPOINTS BÁSICOS
# ============================================

@app.get("/")
async def root() -> Dict[str, Any]:
    """
    Endpoint raíz
    
    Returns:
        Información básica del sistema
    """
    return {
        "message": "ACA 4.0 - Sistema de Bots de Telegram",
        "status": "running",
        "version": "4.0.0",
        "description": "Sistema de gestión de bots con Supabase"
    }


@app.get("/health")
async def health_check() -> Dict[str, Any]:
    """
    Endpoint de verificación de salud del sistema
    
    Returns:
        Estado de salud del sistema y bots
    """
    try:
        # Verificar estado de bots
        admin_running = bot_manager.admin_app and bot_manager.admin_app.updater.running if bot_manager.admin_app else False
        production_running = bot_manager.production_app and bot_manager.production_app.updater.running if bot_manager.production_app else False
        
        # Verificar Supabase
        supabase_status = check_supabase_connection()
        
        return {
            "status": "healthy",
            "bots": {
                "admin": "running" if admin_running else "stopped",
                "production": "running" if production_running else "stopped"
            },
            "database": {
                "supabase": "connected" if supabase_status else "disconnected"
            },
            "config": {
                "environment": Config.ENVIRONMENT,
                "debug": Config.DEBUG
            }
        }
    except Exception as e:
        logger.error(f"Error en health check: {e}")
        return {
            "status": "unhealthy",
            "error": str(e)
        }


@app.get("/status")
async def get_status() -> Dict[str, Any]:
    """
    Obtener estado detallado del sistema
    
    Returns:
        Estado completo del sistema
    """
    try:
        return {
            "bots": {
                "admin": "running" if bot_manager.admin_app else "stopped",
                "production": "running" if bot_manager.production_app else "stopped"
            },
            "config": {
                "environment": Config.ENVIRONMENT,
                "debug": Config.DEBUG
            },
            "database": {
                "supabase_connected": check_supabase_connection()
            }
        }
    except Exception as e:
        logger.error(f"Error obteniendo estado: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================
# ENDPOINTS DE CONTROL DE BOTS
# ============================================

@app.post("/bots/start")
async def start_bots_endpoint() -> Dict[str, str]:
    """
    Iniciar bots manualmente
    
    Returns:
        Mensaje de confirmación
    """
    try:
        await start_bots()
        return {"message": "Bots iniciados correctamente"}
    except Exception as e:
        logger.error(f"Error iniciando bots: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/bots/stop")
async def stop_bots_endpoint() -> Dict[str, str]:
    """
    Detener bots manualmente
    
    Returns:
        Mensaje de confirmación
    """
    try:
        await stop_bots()
        return {"message": "Bots detenidos correctamente"}
    except Exception as e:
        logger.error(f"Error deteniendo bots: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/bots/restart")
async def restart_bots_endpoint() -> Dict[str, str]:
    """
    Reiniciar bots (detener y volver a iniciar)
    
    Returns:
        Mensaje de confirmación
    """
    try:
        await stop_bots()
        await initialize_bots()
        await start_bots()
        return {"message": "Bots reiniciados correctamente"}
    except Exception as e:
        logger.error(f"Error reiniciando bots: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================
# FUNCIÓN PRINCIPAL PARA EJECUCIÓN DIRECTA
# ============================================

def run_server(host: str = "0.0.0.0", port: int = 8000, reload: bool = False):
    """
    Ejecutar servidor FastAPI
    
    Args:
        host: Host donde escuchar
        port: Puerto donde escuchar
        reload: Activar recarga automática (solo desarrollo)
    """
    uvicorn.run(
        "app.main:app",
        host=host,
        port=port,
        reload=reload,
        log_level="info"
    )


if __name__ == "__main__":
    # Ejecutar servidor directamente
    run_server(reload=Config.DEBUG)


