"""
🏢 Company Guard - Control de Acceso por Empresa
Componente centralizado para validar y gestionar acceso a empresas
"""

import logging
from typing import List, Dict, Any, Optional, Tuple
from app.database.supabase import get_supabase_client

logger = logging.getLogger(__name__)


class CompanyAccessError(Exception):
    """Error de acceso a empresa"""
    pass


class NoCompanySelectedError(CompanyAccessError):
    """No hay empresa seleccionada"""
    pass


class CompanyNotAuthorizedError(CompanyAccessError):
    """Usuario no tiene acceso a la empresa"""
    pass


class CompanyGuard:
    """
    Guardia de acceso por empresa.
    Valida que todas las operaciones de lectura tengan company_id válido.
    """
    
    def __init__(self):
        self.supabase = get_supabase_client()
    
    def get_allowed_companies(self, chat_id: int) -> List[Dict[str, Any]]:
        """
        Obtener lista de empresas a las que el usuario tiene acceso.
        
        Args:
            chat_id: Chat ID del usuario en Telegram
            
        Returns:
            Lista de empresas: [{'id': 'uuid', 'nombre': 'Nombre', 'rut': '...', 'rol': 'user'}, ...]
        """
        try:
            empresas = self.supabase.get_user_empresas(chat_id)
            logger.info(f"🏢 Usuario {chat_id} tiene acceso a {len(empresas)} empresa(s)")
            return empresas
        except Exception as e:
            logger.error(f"❌ Error obteniendo empresas para usuario {chat_id}: {e}")
            return []
    
    def resolve_company(
        self, 
        chat_id: int, 
        session_data: Optional[Dict[str, Any]] = None
    ) -> Tuple[Optional[Dict[str, Any]], str]:
        """
        Resolver empresa para el usuario.
        
        Args:
            chat_id: Chat ID del usuario
            session_data: Datos de sesión actuales (opcional)
            
        Returns:
            Tuple de (empresa_dict o None, acción a tomar)
            Acciones posibles:
            - "ready": Empresa ya seleccionada, listo para usar
            - "auto_selected": Se auto-seleccionó (1 empresa), listo para usar
            - "ask_selection": Debe pedir al usuario que elija
            - "no_companies": Usuario sin empresas asignadas
        """
        session_data = session_data or {}
        
        # Verificar si ya hay empresa seleccionada en sesión
        selected_company_id = session_data.get('selected_company_id')
        if selected_company_id:
            # Validar que aún tiene acceso
            if self.validate_access(chat_id, selected_company_id):
                empresa = self._get_empresa_info(selected_company_id)
                logger.info(f"✅ Empresa ya seleccionada: {empresa.get('nombre') if empresa else selected_company_id}")
                return empresa, "ready"
            else:
                logger.warning(f"⚠️ Usuario {chat_id} ya no tiene acceso a empresa {selected_company_id}")
                # Continuar para re-resolver
        
        # Obtener empresas del usuario
        empresas = self.get_allowed_companies(chat_id)
        
        if not empresas:
            logger.warning(f"⚠️ Usuario {chat_id} no tiene empresas asignadas")
            return None, "no_companies"
        
        if len(empresas) == 1:
            # Auto-seleccionar única empresa
            empresa = empresas[0]
            logger.info(f"✅ Auto-seleccionada única empresa: {empresa.get('nombre')}")
            return empresa, "auto_selected"
        
        # Múltiples empresas: debe elegir
        logger.info(f"📋 Usuario {chat_id} tiene {len(empresas)} empresas, debe elegir")
        return None, "ask_selection"
    
    def require_company(
        self, 
        chat_id: int,
        session_data: Optional[Dict[str, Any]] = None,
        requested_company_id: Optional[str] = None
    ) -> str:
        """
        Validar que hay una empresa seleccionada y el usuario tiene acceso.
        
        Args:
            chat_id: Chat ID del usuario
            session_data: Datos de sesión
            requested_company_id: ID de empresa solicitada (opcional)
            
        Returns:
            company_id válido
            
        Raises:
            NoCompanySelectedError: Si no hay empresa seleccionada
            CompanyNotAuthorizedError: Si no tiene acceso
        """
        session_data = session_data or {}
        
        # Determinar qué company_id usar
        company_id = requested_company_id or session_data.get('selected_company_id')
        
        if not company_id:
            logger.warning(f"❌ No hay empresa seleccionada para usuario {chat_id}")
            raise NoCompanySelectedError("No hay empresa seleccionada. Por favor, selecciona una empresa primero.")
        
        # Validar acceso
        if not self.validate_access(chat_id, company_id):
            logger.error(f"🚫 ACCESO DENEGADO: Usuario {chat_id} intentó acceder a empresa {company_id}")
            raise CompanyNotAuthorizedError("No tienes acceso a esta empresa.")
        
        # Validar que coincide con la empresa activa en sesión (si hay)
        active_company = session_data.get('selected_company_id')
        if active_company and active_company != company_id:
            logger.warning(f"⚠️ Empresa solicitada {company_id} no coincide con activa {active_company}")
            raise CompanyNotAuthorizedError("La empresa solicitada no coincide con la empresa activa.")
        
        return company_id
    
    def validate_access(self, chat_id: int, empresa_id: str) -> bool:
        """
        Validar si un usuario tiene acceso a una empresa específica.
        
        Args:
            chat_id: Chat ID del usuario
            empresa_id: ID de la empresa a validar
            
        Returns:
            True si tiene acceso, False en caso contrario
        """
        try:
            has_access = self.supabase.user_has_access_to_empresa(chat_id, empresa_id)
            if not has_access:
                logger.warning(f"🚫 Usuario {chat_id} NO tiene acceso a empresa {empresa_id}")
            return has_access
        except Exception as e:
            logger.error(f"❌ Error validando acceso: {e}")
            return False
    
    def _get_empresa_info(self, empresa_id: str) -> Optional[Dict[str, Any]]:
        """Obtener información de una empresa por ID"""
        try:
            result = self.supabase.table('empresas')\
                .select('id, nombre, rut')\
                .eq('id', empresa_id)\
                .eq('activo', True)\
                .execute()
            
            if result.data:
                return result.data[0]
            return None
        except Exception as e:
            logger.error(f"❌ Error obteniendo info de empresa {empresa_id}: {e}")
            return None
    
    def detect_company_change_attempt(self, message: str) -> bool:
        """
        Detectar si el mensaje intenta cambiar/consultar otra empresa.
        
        Args:
            message: Mensaje del usuario
            
        Returns:
            True si detecta intento de cambio de empresa
        """
        change_patterns = [
            "otra empresa",
            "la otra",
            "en la otra",
            "de la otra",
            "cambiar empresa",
            "cambiar de empresa",
            "otra compañía",
            "en otra empresa",
            "de otra empresa",
            "distinta empresa",
            "diferente empresa"
        ]
        
        message_lower = message.lower()
        for pattern in change_patterns:
            if pattern in message_lower:
                logger.info(f"🔄 Detectado intento de cambio de empresa: '{pattern}' en mensaje")
                return True
        
        return False


# Instancia global
_company_guard = None


def get_company_guard() -> CompanyGuard:
    """Obtener instancia del guardia de empresas"""
    global _company_guard
    if _company_guard is None:
        _company_guard = CompanyGuard()
    return _company_guard

