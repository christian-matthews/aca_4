"""
📊 API Endpoints para Logs de Conversaciones
Endpoints para visualizar y gestionar logs en el dashboard
"""

from fastapi import APIRouter, HTTPException, Query
from typing import List, Dict, Any, Optional
from datetime import datetime, date
import logging

from app.services.conversation_logger import get_conversation_logger

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/conversations", tags=["Conversation Logs"])

@router.get("/recent", response_model=List[Dict[str, Any]])
async def get_recent_conversations(
    limit: int = Query(50, ge=1, le=500, description="Número de conversaciones a obtener"),
    bot_type: Optional[str] = Query(None, description="Filtrar por tipo de bot (admin/production)"),
    authorized_only: bool = Query(False, description="Solo mostrar usuarios autorizados")
):
    """Obtiene conversaciones recientes del dashboard"""
    try:
        conversation_logger = get_conversation_logger()
        
        # Query base - usar vista simplificada
        query = conversation_logger.supabase.table('vista_conversaciones_recientes')\
            .select('*')\
            .limit(limit)
        
        # Aplicar filtros
        if bot_type:
            query = query.eq('bot_tipo', bot_type)
        
        if authorized_only:
            query = query.is_not('empresa_id', 'null')
        
        result = query.execute()
        
        return result.data if result.data else []
        
    except Exception as e:
        logger.error(f"❌ Error obteniendo conversaciones recientes: {e}")
        raise HTTPException(status_code=500, detail="Error obteniendo conversaciones")

@router.get("/unauthorized", response_model=List[Dict[str, Any]])
async def get_unauthorized_users(
    days: int = Query(7, ge=1, le=90, description="Días hacia atrás"),
    limit: int = Query(100, ge=1, le=500, description="Límite de usuarios")
):
    """Obtiene usuarios no autorizados que han intentado usar el bot"""
    try:
        conversation_logger = get_conversation_logger()
        unauthorized_users = await conversation_logger.get_unauthorized_users(days=days)
        
        return unauthorized_users[:limit]
        
    except Exception as e:
        logger.error(f"❌ Error obteniendo usuarios no autorizados: {e}")
        raise HTTPException(status_code=500, detail="Error obteniendo usuarios no autorizados")

@router.get("/attempts/{chat_id}", response_model=List[Dict[str, Any]])
async def get_user_access_attempts(
    chat_id: int,
    days: int = Query(30, ge=1, le=365, description="Días hacia atrás")
):
    """Obtiene intentos de acceso de un usuario específico"""
    try:
        conversation_logger = get_conversation_logger()
        attempts = await conversation_logger.get_access_attempts(chat_id=chat_id, days=days)
        
        return attempts
        
    except Exception as e:
        logger.error(f"❌ Error obteniendo intentos de acceso para {chat_id}: {e}")
        raise HTTPException(status_code=500, detail="Error obteniendo intentos de acceso")

@router.post("/block/{chat_id}")
async def block_user(
    chat_id: int,
    reason: str = Query(..., description="Razón del bloqueo"),
    admin_notes: Optional[str] = Query(None, description="Notas del administrador")
):
    """Bloquea un usuario no autorizado"""
    try:
        conversation_logger = get_conversation_logger()
        success = await conversation_logger.block_user(
            chat_id=chat_id,
            reason=reason,
            admin_notes=admin_notes
        )
        
        if success:
            return {"status": "success", "message": f"Usuario {chat_id} bloqueado correctamente"}
        else:
            raise HTTPException(status_code=400, detail="No se pudo bloquear el usuario")
            
    except Exception as e:
        logger.error(f"❌ Error bloqueando usuario {chat_id}: {e}")
        raise HTTPException(status_code=500, detail="Error bloqueando usuario")

@router.get("/analytics", response_model=Dict[str, Any])
async def get_conversation_analytics(
    days: int = Query(30, ge=1, le=365, description="Días hacia atrás para analíticas")
):
    """Obtiene analíticas completas de conversaciones"""
    try:
        conversation_logger = get_conversation_logger()
        analytics = await conversation_logger.get_conversation_analytics(days=days)
        
        return analytics
        
    except Exception as e:
        logger.error(f"❌ Error obteniendo analíticas: {e}")
        raise HTTPException(status_code=500, detail="Error obteniendo analíticas")

@router.get("/daily-stats", response_model=List[Dict[str, Any]])
async def get_daily_stats(
    start_date: Optional[date] = Query(None, description="Fecha de inicio (YYYY-MM-DD)"),
    end_date: Optional[date] = Query(None, description="Fecha de fin (YYYY-MM-DD)")
):
    """Obtiene estadísticas diarias de conversaciones"""
    try:
        conversation_logger = get_conversation_logger()
        
        # Si no se proporcionan fechas, usar últimos 30 días
        if not start_date:
            start_date = datetime.now().date()
        if not end_date:
            end_date = start_date
        
        # Obtener datos simplificados
        result = conversation_logger.supabase.table('conversaciones')\
            .select('created_at, bot_tipo, chat_id, empresa_id')\
            .gte('created_at', start_date.isoformat())\
            .lte('created_at', end_date.isoformat())\
            .order('created_at', desc=True)\
            .execute()
        
        return result.data if result.data else []
        
    except Exception as e:
        logger.error(f"❌ Error obteniendo estadísticas diarias: {e}")
        raise HTTPException(status_code=500, detail="Error obteniendo estadísticas diarias")

@router.get("/user-history/{chat_id}", response_model=List[Dict[str, Any]])
async def get_user_conversation_history(
    chat_id: int,
    limit: int = Query(50, ge=1, le=200, description="Número de conversaciones")
):
    """Obtiene historial completo de conversaciones de un usuario"""
    try:
        conversation_logger = get_conversation_logger()
        history = await conversation_logger.get_user_conversation_history(
            chat_id=chat_id, 
            limit=limit
        )
        
        return history
        
    except Exception as e:
        logger.error(f"❌ Error obteniendo historial de usuario {chat_id}: {e}")
        raise HTTPException(status_code=500, detail="Error obteniendo historial de usuario")

@router.get("/last", response_model=Dict[str, Any])
async def get_last_conversation(
    chat_id: Optional[int] = Query(None, description="Chat ID específico para obtener su último chat")
):
    """Obtiene el último chat/conversación registrado"""
    try:
        conversation_logger = get_conversation_logger()
        last_chat = await conversation_logger.get_last_conversation(chat_id=chat_id)
        
        if last_chat:
            return last_chat
        else:
            raise HTTPException(status_code=404, detail="No se encontraron conversaciones")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error obteniendo último chat: {e}")
        raise HTTPException(status_code=500, detail="Error obteniendo último chat")

@router.get("/summary")
async def get_conversation_summary():
    """Obtiene resumen rápido para el dashboard principal"""
    try:
        conversation_logger = get_conversation_logger()
        
        # Obtener estadísticas de hoy
        today = datetime.now().date().isoformat()
        
        # Conversaciones de hoy
        today_conversations = conversation_logger.supabase.table('conversaciones')\
            .select('chat_id, empresa_id, bot_tipo')\
            .gte('created_at', f'{today}T00:00:00')\
            .execute()
        
        # Usuarios no autorizados de la última semana
        unauthorized = await conversation_logger.get_unauthorized_users(days=7)
        
        # Procesar datos
        data = today_conversations.data if today_conversations.data else []
        
        summary = {
            'hoy': {
                'total_conversaciones': len(data),
                'usuarios_unicos': len(set(conv['chat_id'] for conv in data)),
                'usuarios_autorizados': len([conv for conv in data if conv['empresa_id']]),
                'usuarios_no_autorizados': len([conv for conv in data if not conv['empresa_id']]),
                'bot_admin': len([conv for conv in data if conv['bot_tipo'] == 'admin']),
                'bot_production': len([conv for conv in data if conv['bot_tipo'] == 'production'])
            },
            'semana': {
                'usuarios_no_autorizados': len(unauthorized),
                'intentos_totales': sum(user.get('intentos_acceso', 0) for user in unauthorized)
            }
        }
        
        return summary
        
    except Exception as e:
        logger.error(f"❌ Error obteniendo resumen de conversaciones: {e}")
        raise HTTPException(status_code=500, detail="Error obteniendo resumen")