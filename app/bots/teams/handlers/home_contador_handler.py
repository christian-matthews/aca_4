"""
Handler para el card HOME_CONTADOR
Renderiza el card de inicio para contadores en Microsoft Teams
"""

import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

# Ruta al archivo JSON del card
CARD_PATH = Path(__file__).parent.parent / "cards" / "home_contador.card.json"


def get_home_contador_card() -> dict:
    """
    Obtener el Adaptive Card HOME_CONTADOR.
    
    Returns:
        dict: El Adaptive Card como diccionario
    """
    try:
        with open(CARD_PATH, "r", encoding="utf-8") as f:
            card = json.load(f)
        logger.info("Card HOME_CONTADOR cargado correctamente")
        return card
    except FileNotFoundError:
        logger.error(f"Archivo de card no encontrado: {CARD_PATH}")
        raise
    except json.JSONDecodeError as e:
        logger.error(f"Error parseando JSON del card: {e}")
        raise


def create_home_contador_response() -> dict:
    """
    Crear respuesta de Teams con el card HOME_CONTADOR.
    
    Returns:
        dict: Respuesta formateada para Teams Bot Framework
    """
    card = get_home_contador_card()
    
    # Formato de respuesta para Teams Bot Framework
    response = {
        "type": "message",
        "attachments": [
            {
                "contentType": "application/vnd.microsoft.card.adaptive",
                "content": card
            }
        ]
    }
    
    return response

