"""
🗣️ Servicio de Logging de Conversaciones
Registra todas las interacciones con los bots de Telegram
"""

import logging
import json
from datetime import datetime
from typing import Optional, Dict, Any
from telegram import Update, User
from app.database.supabase import get_supabase_client

logger = logging.getLogger(__name__)

class ConversationLogger:
    """Servicio para registrar conversaciones de Telegram"""
    
    def __init__(self):
        from supabase import create_client
        from app.config import Config
        # Usar service key para operaciones de logging (evitar RLS)
        self.supabase = create_client(Config.SUPABASE_URL, Config.SUPABASE_SERVICE_KEY)
    
    async def log_message(
        self,
        update: Update,
        response_text: str = None,
        bot_type: str = "production",
        command: str = None,
        parameters: Dict[str, Any] = None,
        response_time_ms: int = None,
        error: str = None,
        has_access: bool = None
    ) -> Optional[str]:
        """
        Registra un mensaje y su respuesta en la base de datos (TODOS los usuarios)
        
        Args:
            update: Update de Telegram
            response_text: Texto de respuesta del bot
            bot_type: Tipo de bot ('admin' o 'production')
            command: Comando ejecutado si aplica
            parameters: Parámetros del comando
            response_time_ms: Tiempo de respuesta en milisegundos
            error: Mensaje de error si ocurrió
            has_access: Si el usuario tiene acceso autorizado (None = detectar automáticamente)
            
        Returns:
            ID de la conversación registrada
        """
        try:
            # Extraer información completa del usuario y mensaje
            user_data = self._extract_user_data(update)
            message_data = self._extract_message_data(update)
            
            # Detectar si tiene acceso si no se especifica
            if has_access is None:
                has_access = await self._check_user_access(user_data["chat_id"])
            
            # Insertar usando función SQL simplificada (orden corregido)
            result = self.supabase.rpc(
                'log_conversacion_simple',
                {
                    'p_chat_id': user_data['chat_id'],
                    'p_mensaje': message_data['text'],
                    'p_user_id': user_data['user_id'],
                    'p_respuesta': response_text or error,
                    'p_first_name': user_data['first_name'],
                    'p_last_name': user_data['last_name'],
                    'p_username': user_data['username'],
                    'p_bot_tipo': bot_type,
                    'p_tiene_acceso': has_access
                }
            ).execute()
            
            if result.data:
                conversation_id = result.data[0] if isinstance(result.data, list) else result.data
                logger.info(f"💬 Conversación registrada: {conversation_id}")
                return conversation_id
            else:
                logger.warning("⚠️ No se pudo obtener ID de conversación")
                return None
                
        except Exception as e:
            logger.error(f"❌ Error registrando conversación: {e}")
            # Intentar registro directo si falla la función
            return await self._log_direct_insert(user_data, message_data, response_text, bot_type, command, parameters, error)
    
    async def _log_direct_insert(
        self, 
        user_data: Dict, 
        message_data: Dict, 
        response_text: str, 
        bot_type: str,
        command: str,
        parameters: Dict,
        error: str
    ) -> Optional[str]:
        """Inserción directa como fallback"""
        try:
            # Buscar empresa_id si existe usuario registrado
            empresa_id = None
            user_check = self.supabase.table('usuarios').select('empresa_id').eq('chat_id', user_data['chat_id']).execute()
            if user_check.data:
                empresa_id = user_check.data[0]['empresa_id']
            
            # Insertar conversación directamente
            result = self.supabase.table('conversaciones').insert({
                'chat_id': user_data['chat_id'],
                'empresa_id': empresa_id,
                'mensaje': message_data['text'],
                'respuesta': response_text or error,
                'usuario_nombre': f"{user_data['first_name'] or ''} {user_data['last_name'] or ''}".strip() or user_data.get('username', 'Usuario Desconocido'),
                'usuario_username': user_data['username'],
                'bot_tipo': bot_type,
                'comando': command,
                'parametros': parameters,
                'metadata': {
                    'message_id': message_data['message_id'],
                    'fallback_insert': True,
                    'error': error is not None
                }
            }).execute()
            
            if result.data:
                conversation_id = result.data[0]['id']
                logger.info(f"💬 Conversación registrada (fallback): {conversation_id}")
                return conversation_id
                
        except Exception as e:
            logger.error(f"❌ Error en fallback de conversación: {e}")
            return None
    
    def _extract_user_data(self, update: Update) -> Dict[str, Any]:
        """Extrae datos COMPLETOS del usuario de Telegram"""
        user: User = update.effective_user
        
        return {
            "chat_id": update.effective_chat.id,
            "user_id": user.id if user else None,
            "first_name": user.first_name if user else None,
            "last_name": user.last_name if user else None,
            "username": user.username if user else None,
            "language_code": user.language_code if user else None,
            "is_bot": user.is_bot if user else False,
            "is_premium": getattr(user, 'is_premium', False) if user else False
        }
    
    async def _check_user_access(self, chat_id: int) -> bool:
        """Verifica si un usuario tiene acceso autorizado"""
        try:
            result = self.supabase.table('usuarios')\
                .select('id')\
                .eq('chat_id', chat_id)\
                .eq('activo', True)\
                .execute()
            
            return len(result.data) > 0 if result.data else False
            
        except Exception as e:
            logger.error(f"❌ Error verificando acceso usuario {chat_id}: {e}")
            return False
    
    def _extract_message_data(self, update: Update) -> Dict[str, Any]:
        """Extrae datos del mensaje"""
        message = update.effective_message
        
        return {
            "message_id": message.message_id if message else None,
            "text": message.text or message.caption or "[Archivo/Media]" if message else "",
            "date": message.date.isoformat() if message and message.date else datetime.now().isoformat(),
            "chat_type": update.effective_chat.type if update.effective_chat else "private"
        }
    
    async def get_user_conversation_history(
        self, 
        chat_id: int, 
        limit: int = 50
    ) -> list:
        """Obtiene historial de conversaciones de un usuario"""
        try:
            result = self.supabase.table('conversaciones')\
                .select('*')\
                .eq('chat_id', chat_id)\
                .order('created_at', desc=True)\
                .limit(limit)\
                .execute()
            
            return result.data if result.data else []
            
        except Exception as e:
            logger.error(f"❌ Error obteniendo historial: {e}")
            return []
    
    async def get_daily_stats(self, date: str = None) -> Dict[str, Any]:
        """Obtiene estadísticas diarias de conversaciones"""
        try:
            target_date = date or datetime.now().strftime('%Y-%m-%d')
            
            # Generar estadísticas si no existen
            self.supabase.rpc('generar_estadisticas_bot', {'fecha_target': target_date}).execute()
            
            # Obtener estadísticas
            result = self.supabase.table('bot_analytics')\
                .select('*')\
                .eq('fecha', target_date)\
                .execute()
            
            return result.data if result.data else []
            
        except Exception as e:
            logger.error(f"❌ Error obteniendo estadísticas: {e}")
            return {}
    
    async def get_unauthorized_users(self, days: int = 7) -> list:
        """Obtiene usuarios NO AUTORIZADOS de los últimos N días"""
        try:
            # Usar la vista simplificada
            result = self.supabase.table('vista_usuarios_sin_acceso')\
                .select('*')\
                .order('intentos_acceso', desc=True)\
                .limit(100)\
                .execute()
            
            return result.data if result.data else []
            
        except Exception as e:
            logger.error(f"❌ Error obteniendo usuarios no autorizados: {e}")
            return []
    
    async def get_access_attempts(self, chat_id: int = None, days: int = 7) -> list:
        """Obtiene intentos de acceso negado"""
        try:
            query = self.supabase.table('intentos_acceso_negado')\
                .select('*')\
                .gte('timestamp', f'now() - interval \'{days} days\'')
            
            if chat_id:
                query = query.eq('chat_id', chat_id)
                
            result = query.order('timestamp', desc=True).execute()
            
            return result.data if result.data else []
            
        except Exception as e:
            logger.error(f"❌ Error obteniendo intentos de acceso: {e}")
            return []
    
    async def block_user(self, chat_id: int, reason: str, admin_notes: str = None) -> bool:
        """Bloquea un usuario no autorizado"""
        try:
            result = self.supabase.table('usuarios_detalle')\
                .update({
                    'tipo_acceso': 'bloqueado',
                    'bloqueado_razon': reason,
                    'notas_admin': admin_notes,
                    'updated_at': 'now()'
                })\
                .eq('chat_id', chat_id)\
                .execute()
            
            if result.data:
                logger.info(f"🚫 Usuario {chat_id} bloqueado: {reason}")
                return True
            return False
            
        except Exception as e:
            logger.error(f"❌ Error bloqueando usuario {chat_id}: {e}")
            return False
    
    async def get_conversation_analytics(self, days: int = 30) -> Dict[str, Any]:
        """Obtiene analíticas completas de conversaciones"""
        try:
            # Usar consulta más simple
            result = self.supabase.table('vista_conversaciones_recientes')\
                .select('*')\
                .limit(1000)\
                .execute()
            
            if not result.data:
                return {}
                
            # Procesar datos para dashboard
            analytics = {
                'total_usuarios_unicos': set(),
                'total_mensajes': 0,
                'mensajes_autorizados': 0,
                'mensajes_no_autorizados': 0,
                'usuarios_no_autorizados_unicos': set(),
                'por_bot': {},
                'por_dia': []
            }
            
            for row in result.data:
                analytics['total_mensajes'] += row['total_mensajes']
                analytics['mensajes_autorizados'] += row['mensajes_autorizados']
                analytics['mensajes_no_autorizados'] += row['mensajes_no_autorizados']
                
                bot_tipo = row['bot_tipo']
                if bot_tipo not in analytics['por_bot']:
                    analytics['por_bot'][bot_tipo] = {
                        'mensajes': 0,
                        'usuarios': 0,
                        'no_autorizados': 0
                    }
                
                analytics['por_bot'][bot_tipo]['mensajes'] += row['total_mensajes']
                analytics['por_bot'][bot_tipo]['usuarios'] += row['usuarios_unicos']
                analytics['por_bot'][bot_tipo]['no_autorizados'] += row['usuarios_no_autorizados']
                
                analytics['por_dia'].append(row)
            
            return analytics
            
        except Exception as e:
            logger.error(f"❌ Error obteniendo analíticas: {e}")
            return {}
    
    async def get_user_conversation_history(self, chat_id: int, limit: int = 50) -> list:
        """Obtiene historial de conversaciones de un usuario específico"""
        try:
            result = self.supabase.table('conversaciones')\
                .select('*')\
                .eq('chat_id', chat_id)\
                .order('created_at', desc=True)\
                .limit(limit)\
                .execute()
            
            return result.data if result.data else []
            
        except Exception as e:
            logger.error(f"❌ Error obteniendo historial de usuario {chat_id}: {e}")
            return []
    
    async def get_last_conversation(self, chat_id: Optional[int] = None) -> Optional[Dict[str, Any]]:
        """
        Obtiene el último chat/conversación registrado en el sistema
        
        Args:
            chat_id: Si se proporciona, obtiene el último chat de ese usuario específico.
                    Si es None, obtiene el último chat de todo el sistema.
        
        Returns:
            Diccionario con los datos de la última conversación o None si no hay conversaciones
        """
        try:
            query = self.supabase.table('conversaciones')\
                .select('*')\
                .order('created_at', desc=True)\
                .limit(1)
            
            if chat_id:
                query = query.eq('chat_id', chat_id)
            
            result = query.execute()
            
            if result.data and len(result.data) > 0:
                logger.info(f"✅ Último chat recuperado: ID {result.data[0].get('id')}")
                return result.data[0]
            
            return None
            
        except Exception as e:
            logger.error(f"❌ Error obteniendo último chat: {e}")
            return None


# Instancia global del logger
conversation_logger = ConversationLogger()

def get_conversation_logger() -> ConversationLogger:
    """Función helper para obtener la instancia del logger"""
    return conversation_logger