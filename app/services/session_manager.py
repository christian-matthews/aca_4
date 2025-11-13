"""
🗣️ Gestor de Sesiones Conversacionales
Maneja el estado de las conversaciones para flujos de subida/descarga de archivos
"""

import logging
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
from app.database.supabase import get_supabase_client

logger = logging.getLogger(__name__)

class SessionManager:
    """Gestor de sesiones conversacionales"""
    
    def __init__(self):
        self.supabase = get_supabase_client()
        self.default_expiry_hours = 1  # 1 hora por defecto
    
    def get_session(self, chat_id: int) -> Optional[Dict[str, Any]]:
        """
        Obtener sesión activa de un usuario
        
        Args:
            chat_id: ID del chat de Telegram
            
        Returns:
            Diccionario con datos de la sesión o None si no existe o está expirada
        """
        try:
            # Buscar sesión activa (no expirada)
            result = self.supabase.table('sesiones_conversacion')\
                .select('*')\
                .eq('chat_id', chat_id)\
                .gt('expires_at', datetime.now().isoformat())\
                .order('created_at', desc=True)\
                .limit(1)\
                .execute()
            
            if result.data and len(result.data) > 0:
                session = result.data[0]
                logger.info(f"✅ Sesión encontrada para chat_id {chat_id}: estado={session.get('estado')}")
                return session
            
            # Si no hay sesión activa, limpiar cualquier sesión expirada
            self._cleanup_expired_session(chat_id)
            return None
            
        except Exception as e:
            logger.error(f"❌ Error obteniendo sesión para chat_id {chat_id}: {e}")
            return None
    
    def create_session(
        self,
        chat_id: int,
        intent: str,
        estado: str = 'esperando_empresa',
        data: Optional[Dict[str, Any]] = None,
        archivo_temp_id: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Crear nueva sesión conversacional
        
        Args:
            chat_id: ID del chat de Telegram
            intent: Intención ('subir_archivo' o 'descargar_archivo')
            estado: Estado inicial (default: 'esperando_empresa')
            data: Datos iniciales de la sesión
            archivo_temp_id: ID temporal del archivo si aplica
            
        Returns:
            Diccionario con la sesión creada o None si falla
        """
        try:
            # Limpiar sesión anterior si existe
            self.clear_session(chat_id)
            
            # Calcular expiración
            expires_at = datetime.now() + timedelta(hours=self.default_expiry_hours)
            
            # Crear sesión
            session_data = {
                'chat_id': chat_id,
                'estado': estado,
                'intent': intent,
                'data': data or {},
                'archivo_temp_id': archivo_temp_id,
                'expires_at': expires_at.isoformat()
            }
            
            result = self.supabase.table('sesiones_conversacion')\
                .insert(session_data)\
                .execute()
            
            if result.data:
                logger.info(f"✅ Sesión creada para chat_id {chat_id}: intent={intent}, estado={estado}")
                return result.data[0]
            
            return None
            
        except Exception as e:
            logger.error(f"❌ Error creando sesión para chat_id {chat_id}: {e}")
            return None
    
    def update_session(
        self,
        chat_id: int,
        estado: Optional[str] = None,
        data: Optional[Dict[str, Any]] = None,
        archivo_temp_id: Optional[str] = None,
        extend_expiry: bool = True
    ) -> bool:
        """
        Actualizar sesión existente
        
        Args:
            chat_id: ID del chat de Telegram
            estado: Nuevo estado (opcional)
            data: Datos a actualizar/agregar (se mergean con datos existentes)
            archivo_temp_id: ID temporal del archivo (opcional)
            extend_expiry: Si True, extiende la expiración 1 hora más
            
        Returns:
            True si se actualizó correctamente, False en caso contrario
        """
        try:
            # Obtener sesión actual
            session = self.get_session(chat_id)
            if not session:
                logger.warning(f"⚠️ No hay sesión activa para chat_id {chat_id}")
                return False
            
            # Preparar datos de actualización
            update_data = {
                'updated_at': datetime.now().isoformat()
            }
            
            if estado:
                update_data['estado'] = estado
            
            if data is not None:
                # Mergear datos existentes con nuevos
                existing_data = session.get('data', {}) or {}
                existing_data.update(data)
                update_data['data'] = existing_data
            
            if archivo_temp_id is not None:
                update_data['archivo_temp_id'] = archivo_temp_id
            
            # Extender expiración si se solicita
            if extend_expiry:
                expires_at = datetime.now() + timedelta(hours=self.default_expiry_hours)
                update_data['expires_at'] = expires_at.isoformat()
            
            # Actualizar en BD
            result = self.supabase.table('sesiones_conversacion')\
                .update(update_data)\
                .eq('id', session['id'])\
                .execute()
            
            if result.data:
                logger.info(f"✅ Sesión actualizada para chat_id {chat_id}: estado={estado or session.get('estado')}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"❌ Error actualizando sesión para chat_id {chat_id}: {e}")
            return False
    
    def clear_session(self, chat_id: int) -> bool:
        """
        Limpiar/eliminar sesión de un usuario
        
        Args:
            chat_id: ID del chat de Telegram
            
        Returns:
            True si se eliminó correctamente, False en caso contrario
        """
        try:
            result = self.supabase.table('sesiones_conversacion')\
                .delete()\
                .eq('chat_id', chat_id)\
                .execute()
            
            logger.info(f"✅ Sesión eliminada para chat_id {chat_id}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error eliminando sesión para chat_id {chat_id}: {e}")
            return False
    
    def _cleanup_expired_session(self, chat_id: int) -> int:
        """
        Limpiar sesiones expiradas de un usuario específico
        
        Args:
            chat_id: ID del chat de Telegram
            
        Returns:
            Número de sesiones eliminadas
        """
        try:
            result = self.supabase.table('sesiones_conversacion')\
                .delete()\
                .eq('chat_id', chat_id)\
                .lt('expires_at', datetime.now().isoformat())\
                .execute()
            
            deleted_count = len(result.data) if result.data else 0
            if deleted_count > 0:
                logger.info(f"🧹 Limpiadas {deleted_count} sesiones expiradas para chat_id {chat_id}")
            
            return deleted_count
            
        except Exception as e:
            logger.error(f"❌ Error limpiando sesiones expiradas para chat_id {chat_id}: {e}")
            return 0
    
    def cleanup_expired_sessions(self) -> int:
        """
        Limpiar todas las sesiones expiradas del sistema
        
        Returns:
            Número de sesiones eliminadas
        """
        try:
            # Usar función SQL si está disponible
            result = self.supabase.client.rpc('limpiar_sesiones_expiradas').execute()
            
            if result.data:
                deleted_count = result.data if isinstance(result.data, int) else result.data[0] if result.data else 0
                logger.info(f"🧹 Limpiadas {deleted_count} sesiones expiradas del sistema")
                return deleted_count
            else:
                # Fallback: limpiar manualmente
                result = self.supabase.table('sesiones_conversacion')\
                    .delete()\
                    .lt('expires_at', datetime.now().isoformat())\
                    .execute()
                
                deleted_count = len(result.data) if result.data else 0
                if deleted_count > 0:
                    logger.info(f"🧹 Limpiadas {deleted_count} sesiones expiradas del sistema")
                
                return deleted_count
                
        except Exception as e:
            logger.error(f"❌ Error limpiando sesiones expiradas: {e}")
            return 0
    
    def get_session_data(self, chat_id: int, key: str = None) -> Any:
        """
        Obtener dato específico de la sesión
        
        Args:
            chat_id: ID del chat de Telegram
            key: Clave del dato a obtener (si None, retorna todos los datos)
            
        Returns:
            Valor del dato o diccionario completo si key es None
        """
        session = self.get_session(chat_id)
        if not session:
            return None
        
        data = session.get('data', {}) or {}
        
        if key is None:
            return data
        
        return data.get(key)
    
    def set_session_data(self, chat_id: int, key: str, value: Any) -> bool:
        """
        Establecer un dato específico en la sesión
        
        Args:
            chat_id: ID del chat de Telegram
            key: Clave del dato
            value: Valor del dato
            
        Returns:
            True si se actualizó correctamente
        """
        return self.update_session(chat_id, data={key: value})

# Instancia global
_session_manager = None

def get_session_manager() -> SessionManager:
    """Obtener instancia del gestor de sesiones"""
    global _session_manager
    if _session_manager is None:
        _session_manager = SessionManager()
    return _session_manager


