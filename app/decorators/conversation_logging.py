"""
🎯 Decoradores para Logging Automático de Conversaciones
Automatiza el registro de todas las interacciones con los bots
"""

import time
import asyncio
import logging
from functools import wraps
from typing import Callable, Any
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from app.services.conversation_logger import get_conversation_logger

logger = logging.getLogger(__name__)

def log_conversation(bot_type: str = "production"):
    """
    Decorator para registrar automáticamente conversaciones
    
    Args:
        bot_type: Tipo de bot ('admin' o 'production')
    """
    def decorator(handler_func: Callable):
        @wraps(handler_func)
        async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
            start_time = time.time()
            conversation_logger = get_conversation_logger()
            response_text = None
            error_message = None
            command = None
            parameters = None
            
            try:
                # Extraer comando y parámetros si es un comando
                if update.message and update.message.text:
                    text = update.message.text
                    if text.startswith('/'):
                        parts = text.split()
                        command = parts[0]
                        parameters = {'args': parts[1:]} if len(parts) > 1 else None
                
                # Ejecutar handler original
                result = await handler_func(update, context, *args, **kwargs)
                
                # Capturar respuesta si el handler la retorna
                if isinstance(result, str):
                    response_text = result
                elif hasattr(context, 'bot_response'):
                    response_text = context.bot_response
                else:
                    # Intentar obtener el último mensaje enviado por el bot
                    response_text = "Respuesta procesada"
                
                return result
                
            except Exception as e:
                error_message = f"Error en {handler_func.__name__}: {str(e)}"
                logger.error(error_message)
                
                # Re-lanzar la excepción para que el bot la maneje
                raise e
                
            finally:
                # Calcular tiempo de respuesta
                response_time_ms = int((time.time() - start_time) * 1000)
                
                # Registrar conversación en background
                asyncio.create_task(
                    conversation_logger.log_message(
                        update=update,
                        response_text=response_text,
                        bot_type=bot_type,
                        command=command,
                        parameters=parameters,
                        response_time_ms=response_time_ms,
                        error=error_message
                    )
                )
        
        return wrapper
    return decorator

def log_admin_action(action: str):
    """
    Decorator específico para acciones administrativas
    
    Args:
        action: Descripción de la acción administrativa
    """
    def decorator(handler_func: Callable):
        @wraps(handler_func)
        async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
            start_time = time.time()
            conversation_logger = get_conversation_logger()
            
            try:
                # Verificar que sea usuario autorizado
                chat_id = update.effective_chat.id
                has_access = await conversation_logger._check_user_access(chat_id)
                
                if not has_access:
                    # Registrar intento no autorizado
                    await conversation_logger.log_message(
                        update=update,
                        response_text=f"Acceso denegado para acción: {action}",
                        bot_type="admin",
                        command=action,
                        has_access=False,
                        error="Acceso no autorizado"
                    )
                    
                    # Enviar mensaje de error
                    await update.message.reply_text(
                        "🚫 No tienes permisos para ejecutar esta acción.\n"
                        "Contacta al administrador si crees que esto es un error."
                    )
                    return
                
                # Ejecutar acción si está autorizado
                result = await handler_func(update, context, *args, **kwargs)
                
                # Registrar acción exitosa
                response_time_ms = int((time.time() - start_time) * 1000)
                await conversation_logger.log_message(
                    update=update,
                    response_text=f"Acción administrativa completada: {action}",
                    bot_type="admin",
                    command=action,
                    response_time_ms=response_time_ms,
                    has_access=True
                )
                
                return result
                
            except Exception as e:
                # Registrar error en acción administrativa
                response_time_ms = int((time.time() - start_time) * 1000)
                await conversation_logger.log_message(
                    update=update,
                    response_text=f"Error en acción administrativa: {action}",
                    bot_type="admin",
                    command=action,
                    response_time_ms=response_time_ms,
                    error=str(e),
                    has_access=True
                )
                
                # Re-lanzar excepción
                raise e
        
        return wrapper
    return decorator

def log_unauthorized_access():
    """
    Decorator para manejar y registrar accesos no autorizados
    """
    def decorator(handler_func: Callable):
        @wraps(handler_func)
        async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
            conversation_logger = get_conversation_logger()
            
            # Registrar intento de acceso no autorizado
            await conversation_logger.log_message(
                update=update,
                response_text="Acceso denegado - Usuario no autorizado",
                bot_type="production",
                has_access=False,
                error="Usuario no registrado en el sistema"
            )
            
            # Crear botón de contacto directo
            keyboard = [
                [InlineKeyboardButton("💬 Contactar a @wingmanbod", url="https://t.me/wingmanbod")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            # Enviar mensaje explicativo con botón
            await update.message.reply_text(
                "👋 ¡Hola! Veo que intentas usar este bot.\n\n"
                "🔒 Este bot es privado y solo está disponible para empresas registradas.\n\n"
                "📝 Si tu empresa debería tener acceso, contacta al administrador presionando el botón:\n\n"
                "📞 Para más información y registro de tu empresa.",
                reply_markup=reply_markup
            )
            
            # No ejecutar el handler original
            return None
        
        return wrapper
    return decorator

# Decoradores específicos para diferentes tipos de bots
def log_admin_conversation(handler_func: Callable):
    """Shortcut para conversaciones del bot admin"""
    return log_conversation(bot_type="admin")(handler_func)

def log_production_conversation(handler_func: Callable):
    """Shortcut para conversaciones del bot de producción"""
    return log_conversation(bot_type="production")(handler_func)