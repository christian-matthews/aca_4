"""
Microsoft Teams Webhook Router
Endpoint HTTP para recibir mensajes de Teams
"""

from fastapi import APIRouter, Request, HTTPException, Header
from fastapi.responses import JSONResponse
import logging
import os

from app.bots.teams.handlers.home_contador_handler import (
    get_home_contador_card,
    create_home_contador_response
)
from app.bots.teams.handlers.subir_documento_handler import (
    get_subir_documento_card,
    create_subir_documento_response
)
from app.bots.teams.handlers.home_cliente_handler import (
    get_home_cliente_card,
    create_home_cliente_response
)
from app.bots.teams.handlers.home_supervisor_handler import (
    get_home_supervisor_card,
    create_home_supervisor_response
)
from app.bots.teams.handlers.home_cfo_handler import (
    get_home_cfo_card,
    create_home_cfo_response
)

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


@router.get("/cards/home-contador")
async def get_card_home_contador():
    """
    Obtener el Adaptive Card HOME_CONTADOR (para preview/debug)
    
    Returns:
        El Adaptive Card como JSON
    """
    try:
        card = get_home_contador_card()
        return card
    except Exception as e:
        logger.error(f"Error obteniendo card HOME_CONTADOR: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/cards/home-contador/response")
async def get_card_home_contador_response():
    """
    Obtener la respuesta completa de Teams con el card HOME_CONTADOR
    
    Returns:
        Respuesta formateada para Teams Bot Framework
    """
    try:
        response = create_home_contador_response()
        return response
    except Exception as e:
        logger.error(f"Error creando respuesta HOME_CONTADOR: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/cards/subir-documento")
async def get_card_subir_documento():
    """
    Obtener el Adaptive Card SUBIR_DOCUMENTO (para preview/debug)
    
    Returns:
        El Adaptive Card como JSON
    """
    try:
        card = get_subir_documento_card()
        return card
    except Exception as e:
        logger.error(f"Error obteniendo card SUBIR_DOCUMENTO: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/cards/subir-documento/response")
async def get_card_subir_documento_response():
    """
    Obtener la respuesta completa de Teams con el card SUBIR_DOCUMENTO
    
    Returns:
        Respuesta formateada para Teams Bot Framework
    """
    try:
        response = create_subir_documento_response()
        return response
    except Exception as e:
        logger.error(f"Error creando respuesta SUBIR_DOCUMENTO: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/cards/home-cliente")
async def get_card_home_cliente():
    """
    Obtener el Adaptive Card HOME_CLIENTE (para preview/debug)
    
    Returns:
        El Adaptive Card como JSON
    """
    try:
        card = get_home_cliente_card()
        return card
    except Exception as e:
        logger.error(f"Error obteniendo card HOME_CLIENTE: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/cards/home-cliente/response")
async def get_card_home_cliente_response():
    """
    Obtener la respuesta completa de Teams con el card HOME_CLIENTE
    
    Returns:
        Respuesta formateada para Teams Bot Framework
    """
    try:
        response = create_home_cliente_response()
        return response
    except Exception as e:
        logger.error(f"Error creando respuesta HOME_CLIENTE: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/cards/home-supervisor")
async def get_card_home_supervisor():
    """
    Obtener el Adaptive Card HOME_SUPERVISOR (para preview/debug)
    
    Returns:
        El Adaptive Card como JSON
    """
    try:
        card = get_home_supervisor_card()
        return card
    except Exception as e:
        logger.error(f"Error obteniendo card HOME_SUPERVISOR: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/cards/home-supervisor/response")
async def get_card_home_supervisor_response():
    """
    Obtener la respuesta completa de Teams con el card HOME_SUPERVISOR
    
    Returns:
        Respuesta formateada para Teams Bot Framework
    """
    try:
        response = create_home_supervisor_response()
        return response
    except Exception as e:
        logger.error(f"Error creando respuesta HOME_SUPERVISOR: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/cards/home-cfo")
async def get_card_home_cfo():
    """
    Obtener el Adaptive Card HOME_CFO (para preview/debug)
    
    Returns:
        El Adaptive Card como JSON
    """
    try:
        card = get_home_cfo_card()
        return card
    except Exception as e:
        logger.error(f"Error obteniendo card HOME_CFO: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/cards/home-cfo/response")
async def get_card_home_cfo_response():
    """
    Obtener la respuesta completa de Teams con el card HOME_CFO
    
    Returns:
        Respuesta formateada para Teams Bot Framework
    """
    try:
        response = create_home_cfo_response()
        return response
    except Exception as e:
        logger.error(f"Error creando respuesta HOME_CFO: {e}")
        raise HTTPException(status_code=500, detail=str(e))

