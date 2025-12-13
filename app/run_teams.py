#!/usr/bin/env python3
"""
Entrypoint para Microsoft Teams Webhook Service
Servicio HTTP independiente para recibir webhooks de Teams
NO inicia polling de Telegram
"""

import os
import sys
import logging
from pathlib import Path

# Agregar el directorio raíz al path
sys.path.insert(0, str(Path(__file__).parent.parent))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from app.web.teams_router import router as teams_router
from app.utils.helpers import setup_logging

# Configurar logging
setup_logging()
logger = logging.getLogger(__name__)

# Crear aplicación FastAPI para Teams
app = FastAPI(
    title="ACA 4.0 - Microsoft Teams Webhook Service",
    description="Servicio webhook HTTP para Microsoft Teams",
    version="0.1.0"
)

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Incluir router de Teams
app.include_router(teams_router)


@app.get("/")
async def root():
    """Endpoint raíz"""
    return {
        "service": "teams-webhook",
        "status": "running",
        "version": "0.1.0",
        "description": "Microsoft Teams webhook service (pilot)"
    }


@app.get("/health")
async def health_check():
    """Health check del servicio"""
    teams_enabled = os.getenv("TEAMS_ENABLED", "false").lower() == "true"
    
    return {
        "status": "healthy",
        "service": "teams-webhook",
        "teams_enabled": teams_enabled
    }


def main():
    """Función principal"""
    # Obtener puerto de variable de entorno (Render usa PORT)
    port = int(os.getenv("PORT", "8001"))
    host = "0.0.0.0"
    
    logger.info(f"🚀 Iniciando Teams Webhook Service en {host}:{port}")
    logger.info("📡 Endpoint: POST /api/teams/messages")
    logger.info("🔍 Health check: GET /health")
    
    # NO iniciar polling de Telegram
    # Este servicio solo recibe webhooks HTTP
    
    uvicorn.run(
        "app.run_teams:app",
        host=host,
        port=port,
        reload=False,
        log_level="info"
    )


if __name__ == "__main__":
    main()

