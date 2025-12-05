"""
🧪 Tests para Company Guard
Tests obligatorios para validar control de acceso por empresa
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import sys
import os

# Agregar el directorio raíz al path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestCompanyGuard:
    """Tests para CompanyGuard"""
    
    @pytest.fixture
    def mock_supabase(self):
        """Mock del cliente Supabase"""
        with patch('app.security.company_guard.get_supabase_client') as mock:
            mock_client = MagicMock()
            mock.return_value = mock_client
            yield mock_client
    
    @pytest.fixture
    def company_guard(self, mock_supabase):
        """Instancia de CompanyGuard con mock de Supabase"""
        from app.security.company_guard import CompanyGuard
        guard = CompanyGuard()
        guard.supabase = mock_supabase
        return guard
    
    # =========================================
    # TEST 1: Usuario con 2 empresas, sin selected_company_id → bloqueo
    # =========================================
    def test_user_with_multiple_companies_no_selection_blocks(self, company_guard, mock_supabase):
        """
        Usuario con 2 empresas, sin empresa seleccionada.
        Cualquier tool de datos debe bloquear y pedir selección.
        """
        # Configurar mock: usuario tiene 2 empresas
        mock_supabase.get_user_empresas.return_value = [
            {'id': 'empresa-1', 'nombre': 'Empresa A', 'rut': '12345678-9', 'rol': 'user'},
            {'id': 'empresa-2', 'nombre': 'Empresa B', 'rut': '98765432-1', 'rol': 'user'}
        ]
        
        chat_id = 12345
        session_data = {}  # Sin empresa seleccionada
        
        # Resolver empresa
        empresa, action = company_guard.resolve_company(chat_id, session_data)
        
        # Debe pedir selección
        assert action == "ask_selection"
        assert empresa is None
        
        # Intentar require_company sin selección debe lanzar excepción
        from app.security.company_guard import NoCompanySelectedError
        
        with pytest.raises(NoCompanySelectedError):
            company_guard.require_company(chat_id, session_data)
    
    # =========================================
    # TEST 2: Usuario con 1 empresa → se auto-selecciona
    # =========================================
    def test_user_with_single_company_auto_selects(self, company_guard, mock_supabase):
        """
        Usuario con 1 sola empresa.
        Se auto-selecciona y puede responder.
        """
        # Configurar mock: usuario tiene 1 empresa
        mock_supabase.get_user_empresas.return_value = [
            {'id': 'empresa-unica', 'nombre': 'Mi Empresa', 'rut': '11111111-1', 'rol': 'admin'}
        ]
        mock_supabase.user_has_access_to_empresa.return_value = True
        
        chat_id = 12345
        session_data = {}
        
        # Resolver empresa
        empresa, action = company_guard.resolve_company(chat_id, session_data)
        
        # Debe auto-seleccionar
        assert action == "auto_selected"
        assert empresa is not None
        assert empresa['id'] == 'empresa-unica'
        assert empresa['nombre'] == 'Mi Empresa'
        
        # require_company debe funcionar después de auto-selección
        session_data_with_company = {'selected_company_id': empresa['id']}
        company_id = company_guard.require_company(chat_id, session_data_with_company)
        assert company_id == 'empresa-unica'
    
    # =========================================
    # TEST 3: Intento de tool con company_id no autorizado → bloqueo
    # =========================================
    def test_unauthorized_company_access_blocked(self, company_guard, mock_supabase):
        """
        Intento de acceder a empresa no autorizada.
        Debe bloquear y registrar intento.
        """
        # Configurar mock: usuario NO tiene acceso a la empresa solicitada
        mock_supabase.user_has_access_to_empresa.return_value = False
        
        chat_id = 12345
        empresa_no_autorizada = 'empresa-ajena'
        
        # validate_access debe retornar False
        has_access = company_guard.validate_access(chat_id, empresa_no_autorizada)
        assert has_access is False
        
        # require_company con empresa no autorizada debe lanzar excepción
        from app.security.company_guard import CompanyNotAuthorizedError
        
        session_data = {'selected_company_id': empresa_no_autorizada}
        
        with pytest.raises(CompanyNotAuthorizedError):
            company_guard.require_company(chat_id, session_data)
    
    # =========================================
    # TEST 4: Usuario sin empresas asignadas
    # =========================================
    def test_user_with_no_companies(self, company_guard, mock_supabase):
        """
        Usuario sin empresas asignadas.
        Debe indicar que no tiene empresas.
        """
        # Configurar mock: usuario sin empresas
        mock_supabase.get_user_empresas.return_value = []
        
        chat_id = 12345
        session_data = {}
        
        # Resolver empresa
        empresa, action = company_guard.resolve_company(chat_id, session_data)
        
        # Debe indicar que no tiene empresas
        assert action == "no_companies"
        assert empresa is None
    
    # =========================================
    # TEST 5: Empresa ya seleccionada en sesión
    # =========================================
    def test_company_already_selected_in_session(self, company_guard, mock_supabase):
        """
        Si ya hay empresa seleccionada en sesión, debe usarla.
        """
        # Configurar mock
        mock_supabase.user_has_access_to_empresa.return_value = True
        mock_supabase.table.return_value.select.return_value.eq.return_value.eq.return_value.execute.return_value = MagicMock(
            data=[{'id': 'empresa-previa', 'nombre': 'Empresa Previa', 'rut': '99999999-9'}]
        )
        
        chat_id = 12345
        session_data = {
            'selected_company_id': 'empresa-previa',
            'selected_company_name': 'Empresa Previa'
        }
        
        # Resolver empresa
        empresa, action = company_guard.resolve_company(chat_id, session_data)
        
        # Debe usar la ya seleccionada
        assert action == "ready"
        assert empresa is not None
        assert empresa['id'] == 'empresa-previa'
    
    # =========================================
    # TEST 6: Detectar intento de cambio de empresa
    # =========================================
    def test_detect_company_change_attempt(self, company_guard):
        """
        Detectar cuando el usuario intenta consultar otra empresa.
        """
        # Mensajes que indican cambio de empresa
        change_messages = [
            "¿Y en la otra empresa cómo está?",
            "dame los datos de otra empresa",
            "quiero cambiar de empresa",
            "en la otra compañía",
            "de la otra empresa"
        ]
        
        for msg in change_messages:
            assert company_guard.detect_company_change_attempt(msg) is True, f"No detectó: '{msg}'"
        
        # Mensajes normales que NO indican cambio
        normal_messages = [
            "¿Cuál es el balance de este mes?",
            "dame los reportes financieros",
            "necesito ver los estados de cuenta"
        ]
        
        for msg in normal_messages:
            assert company_guard.detect_company_change_attempt(msg) is False, f"Falso positivo: '{msg}'"
    
    # =========================================
    # TEST 7: Empresa seleccionada no coincide con solicitada
    # =========================================
    def test_company_mismatch_blocked(self, company_guard, mock_supabase):
        """
        Si la empresa solicitada no coincide con la activa en sesión,
        debe bloquear la operación.
        """
        mock_supabase.user_has_access_to_empresa.return_value = True
        
        chat_id = 12345
        session_data = {'selected_company_id': 'empresa-A'}
        
        # Intentar acceder a empresa diferente
        from app.security.company_guard import CompanyNotAuthorizedError
        
        with pytest.raises(CompanyNotAuthorizedError):
            company_guard.require_company(
                chat_id, 
                session_data, 
                requested_company_id='empresa-B'  # Diferente a la activa
            )


class TestAdvisorHandlerIntegration:
    """Tests de integración para AdvisorHandler"""
    
    @pytest.fixture
    def mock_dependencies(self):
        """Mock de todas las dependencias"""
        with patch('app.bots.handlers.advisor_handler.security') as mock_security, \
             patch('app.bots.handlers.advisor_handler.get_company_guard') as mock_guard, \
             patch('app.bots.handlers.advisor_handler.get_session_manager') as mock_session, \
             patch('app.bots.handlers.advisor_handler.get_ai_service') as mock_ai:
            
            # Configurar security
            mock_security.validate_user.return_value = {
                'valid': True,
                'user_data': {'nombre': 'Test User', 'empresa_id': 'test-empresa'}
            }
            
            yield {
                'security': mock_security,
                'guard': mock_guard,
                'session': mock_session,
                'ai': mock_ai
            }
    
    def test_forbidden_action_detection(self):
        """Detectar acciones prohibidas"""
        from app.bots.handlers.advisor_handler import AdvisorHandler
        
        # Acciones prohibidas
        forbidden = [
            "quiero pagar una factura",
            "necesito hacer una transferencia",
            "quiero cerrar período de octubre",
            "emitir factura para el cliente",
            "borrar ese registro"
        ]
        
        for msg in forbidden:
            assert AdvisorHandler._detect_forbidden_action(msg) is True, f"No detectó: '{msg}'"
        
        # Acciones permitidas
        allowed = [
            "¿cuál es el balance?",
            "dame los reportes",
            "necesito ver los estados financieros"
        ]
        
        for msg in allowed:
            assert AdvisorHandler._detect_forbidden_action(msg) is False, f"Falso positivo: '{msg}'"


# =========================================
# Ejecutar tests
# =========================================
if __name__ == "__main__":
    pytest.main([__file__, "-v"])

