"""
Módulo de autenticación y seguridad para ACA 3.0
"""

import logging
from app.database.supabase import supabase

logger = logging.getLogger(__name__)

class SecurityManager:
    """Gestor de seguridad y autenticación"""
    
    def __init__(self):
        # Chat IDs de administradores - usar el ADMIN_CHAT_ID de la configuración
        from app.config import Config
        self.admin_chat_ids = [Config.ADMIN_CHAT_ID] if Config.ADMIN_CHAT_ID else [123456789]
    
    def validate_user(self, chat_id: int):
        """
        Validar usuario y obtener sus datos (soporte multiempresa)
        
        Returns:
            {
                'valid': True/False,
                'user_data': {
                    'id': uuid,
                    'chat_id': int,
                    'nombre': str,
                    'rol': str,
                    'empresas': [{'id': uuid, 'nombre': str, 'rut': str, 'rol': str}, ...],  # Lista de empresas
                    'empresa_id': uuid,  # Primera empresa (compatibilidad)
                    'empresa_nombre': str,  # Primera empresa (compatibilidad)
                    'empresa_rut': str  # Primera empresa (compatibilidad)
                }
            }
        """
        try:
            user = supabase.get_user_by_chat_id(chat_id)
            
            if not user:
                return {
                    'valid': False,
                    'message': "❌ Usuario no registrado. Contacta al administrador para registrarte."
                }
            
            # Obtener todas las empresas del usuario (multiempresa)
            empresas = supabase.get_user_empresas(chat_id)
            
            if not empresas:
                return {
                    'valid': False,
                    'message': "❌ No tienes empresas asignadas. Contacta al administrador."
                }
            
            # Primera empresa para compatibilidad con código legacy
            primera_empresa = empresas[0]
            
            return {
                'valid': True,
                'user_data': {
                    'id': user['id'],
                    'chat_id': user['chat_id'],
                    'nombre': user['nombre'],
                    'rol': user['rol'],
                    'empresas': empresas,  # Lista completa de empresas
                    'empresa_id': primera_empresa['id'],  # Primera empresa (compatibilidad)
                    'empresa_nombre': primera_empresa['nombre'],  # Primera empresa (compatibilidad)
                    'empresa_rut': primera_empresa['rut']  # Primera empresa (compatibilidad)
                }
            }
            
        except Exception as e:
            logger.error(f"Error validando usuario {chat_id}: {e}")
            return {
                'valid': False,
                'message': "❌ Error de validación. Intenta nuevamente."
            }
    
    def user_has_access_to_empresa(self, chat_id: int, empresa_id: str) -> bool:
        """
        Validar si un usuario tiene acceso a una empresa específica
        
        Args:
            chat_id: Chat ID del usuario
            empresa_id: ID de la empresa a validar
            
        Returns:
            True si el usuario tiene acceso, False en caso contrario
        """
        return supabase.user_has_access_to_empresa(chat_id, empresa_id)
    
    def get_user_empresas(self, chat_id: int):
        """
        Obtener todas las empresas asociadas a un usuario
        
        Args:
            chat_id: Chat ID del usuario
            
        Returns:
            Lista de empresas: [{'id': uuid, 'nombre': str, 'rut': str, 'rol': str}, ...]
        """
        return supabase.get_user_empresas(chat_id)
    
    def is_admin(self, chat_id: int):
        """Verificar si el usuario es administrador (super_admin o admin legacy)"""
        # Verificar si es super_admin en configuración
        if chat_id in self.admin_chat_ids:
            return True
        
        # Verificar si tiene rol super_admin en la BD
        try:
            user = supabase.get_user_by_chat_id(chat_id)
            if user and user.get('rol') == 'super_admin':
                return True
        except:
            pass
        
        return False
    
    def is_super_admin(self, chat_id: int) -> bool:
        """
        Verificar si el usuario es super_admin
        
        Args:
            chat_id: Chat ID del usuario
            
        Returns:
            True si es super_admin, False en caso contrario
        """
        # Verificar configuración
        if chat_id in self.admin_chat_ids:
            return True
        
        # Verificar rol en BD
        try:
            user = supabase.get_user_by_chat_id(chat_id)
            if user and user.get('rol') == 'super_admin':
                return True
        except:
            pass
        
        return False
    
    def get_user_role_in_empresa(self, chat_id: int, empresa_id: str) -> str:
        """
        Obtener el rol de un usuario en una empresa específica
        
        Args:
            chat_id: Chat ID del usuario
            empresa_id: ID de la empresa
            
        Returns:
            Rol del usuario en la empresa: 'super_admin', 'gestor', 'usuario' o None
        """
        try:
            empresas = supabase.get_user_empresas(chat_id)
            for empresa in empresas:
                if empresa['id'] == empresa_id:
                    return empresa.get('rol', 'usuario')
            return None
        except Exception as e:
            logger.error(f"Error obteniendo rol de usuario {chat_id} en empresa {empresa_id}: {e}")
            return None
    
    def can_upload_files(self, chat_id: int, empresa_id: str = None) -> bool:
        """
        Verificar si el usuario puede subir archivos
        
        Args:
            chat_id: Chat ID del usuario
            empresa_id: ID de la empresa (opcional, si None verifica en todas)
            
        Returns:
            True si puede subir archivos, False en caso contrario
        """
        # Super admin siempre puede
        if self.is_super_admin(chat_id):
            return True
        
        # Si se especifica empresa, verificar rol en esa empresa
        if empresa_id:
            rol = self.get_user_role_in_empresa(chat_id, empresa_id)
            return rol in ['super_admin', 'gestor']
        
        # Si no se especifica empresa, verificar si tiene al menos una empresa con permiso
        try:
            empresas = supabase.get_user_empresas(chat_id)
            for empresa in empresas:
                if empresa.get('rol') in ['super_admin', 'gestor']:
                    return True
            return False
        except:
            return False
    
    def can_download_files(self, chat_id: int, empresa_id: str = None) -> bool:
        """
        Verificar si el usuario puede descargar archivos
        
        Args:
            chat_id: Chat ID del usuario
            empresa_id: ID de la empresa (opcional)
            
        Returns:
            True si puede descargar archivos, False en caso contrario
        """
        # Todos los usuarios registrados pueden descargar
        # Solo validamos que tenga acceso a la empresa
        if empresa_id:
            return self.user_has_access_to_empresa(chat_id, empresa_id)
        
        # Si no se especifica empresa, verificar que tenga al menos una empresa
        try:
            empresas = supabase.get_user_empresas(chat_id)
            return len(empresas) > 0
        except:
            return False
    
    def can_manage_empresas(self, chat_id: int) -> bool:
        """
        Verificar si el usuario puede gestionar empresas (asignar usuarios a empresas)
        
        Args:
            chat_id: Chat ID del usuario
            
        Returns:
            True si puede gestionar empresas, False en caso contrario
        """
        # Solo super_admin y gestor pueden gestionar empresas
        if self.is_super_admin(chat_id):
            return True
        
        # Verificar si tiene rol gestor en alguna empresa
        try:
            empresas = supabase.get_user_empresas(chat_id)
            for empresa in empresas:
                if empresa.get('rol') == 'gestor':
                    return True
            return False
        except:
            return False
    
    def log_security_event(self, chat_id: int, event_type: str, description: str):
        """Registrar evento de seguridad"""
        try:
            data = {
                'chat_id': chat_id,
                'event_type': event_type,
                'description': description,
                'timestamp': 'now()'
            }
            supabase.client.table('security_logs').insert(data).execute()
        except Exception as e:
            logger.error(f"Error registrando evento de seguridad: {e}")

# Instancia global
security = SecurityManager() 