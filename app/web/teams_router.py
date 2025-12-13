"""
Microsoft Teams Webhook Router
Endpoint HTTP para recibir mensajes de Teams
"""

from fastapi import APIRouter, Request, HTTPException, Header
from fastapi.responses import JSONResponse
import logging
import os

logger = logging.getLogger(__name__)

# Crear router
router = APIRouter(prefix="/api/teams", tags=["teams"])


@router.post("/messages")
async def teams_webhook(
    request: Request,
    authorization: str = Header(None)
):
    """
    Endpoint webhook para recibir mensajes de Microsoft Teams
    
    Args:
        request: Request de FastAPI
        authorization: Header de autorización (opcional)
    
    Returns:
        HTTP 200 con respuesta temporal
    """
    # Verificar si Teams está habilitado
    teams_enabled = os.getenv("TEAMS_ENABLED", "false").lower() == "true"
    
    if not teams_enabled:
        logger.warning("Teams webhook recibido pero TEAMS_ENABLED=false")
        raise HTTPException(status_code=503, detail="Teams service disabled")
    
    # Leer variables de entorno
    teams_app_id = os.getenv("TEAMS_APP_ID")
    teams_app_password = os.getenv("TEAMS_APP_PASSWORD")
    
    if not teams_app_id or not teams_app_password:
        logger.warning("Teams webhook recibido pero faltan credenciales")
        raise HTTPException(
            status_code=500,
            detail="Teams configuration incomplete"
        )
    
    # Leer body del request
    try:
        body = await request.json()
        logger.info(f"Teams webhook recibido: {type(body)}")
    except Exception as e:
        logger.error(f"Error leyendo body de Teams webhook: {e}")
        body = {}
    
    # Respuesta temporal: HTTP 200 con "pong"
    return JSONResponse(
        status_code=200,
        content={"status": "pong", "message": "Teams webhook received"}
    )


@router.get("/health")
async def teams_health():
    """
    Health check para Teams service
    
    Returns:
        Estado del servicio Teams
    """
    teams_enabled = os.getenv("TEAMS_ENABLED", "false").lower() == "true"
    teams_app_id = os.getenv("TEAMS_APP_ID")
    teams_app_password = os.getenv("TEAMS_APP_PASSWORD")
    
    return {
        "service": "teams",
        "enabled": teams_enabled,
        "configured": bool(teams_app_id and teams_app_password),
        "status": "ok" if teams_enabled else "disabled"
    }

