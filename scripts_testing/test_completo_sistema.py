#!/usr/bin/env python3
"""
🧪 Test completo del sistema ACA 4.0
"""

import sys
from app.config import Config
from app.database.supabase import get_supabase_client
from app.security.auth import security

def test_imports():
    """Test 1: Verificar imports"""
    print("="*80)
    print("TEST 1: IMPORTS")
    print("="*80)
    
    try:
        from app.config import Config
        from app.database.supabase import get_supabase_client
        from app.security.auth import security
        from app.bots.bot_manager import bot_manager
        from app.bots.handlers.admin_handlers import AdminHandlers
        from app.bots.handlers.production_handlers import ProductionHandlers
        from app.bots.handlers.file_upload_handler import FileUploadHandler
        from app.bots.handlers.file_download_handler import FileDownloadHandler
        print("✅ Todos los imports exitosos")
        return True
    except Exception as e:
        print(f"❌ Error en imports: {e}")
        return False

def test_config():
    """Test 2: Verificar configuración"""
    print("\n" + "="*80)
    print("TEST 2: CONFIGURACIÓN")
    print("="*80)
    
    try:
        Config.validate()
        print("✅ Configuración válida")
        return True
    except Exception as e:
        print(f"❌ Error en configuración: {e}")
        return False

def test_supabase_connection():
    """Test 3: Verificar conexión a Supabase"""
    print("\n" + "="*80)
    print("TEST 3: CONEXIÓN A SUPABASE")
    print("="*80)
    
    try:
        supabase = get_supabase_client()
        empresas = supabase.table('empresas').select('id').limit(1).execute()
        print("✅ Conexión a Supabase exitosa")
        return True
    except Exception as e:
        print(f"❌ Error de conexión: {e}")
        return False

def test_security_methods():
    """Test 4: Verificar métodos de seguridad"""
    print("\n" + "="*80)
    print("TEST 4: MÉTODOS DE SEGURIDAD")
    print("="*80)
    
    test_users = [
        (7580149783, 'The Wingman'),
        (866310278, 'Christian'),
        (2134113487, 'Patricio')
    ]
    
    todos_ok = True
    for chat_id, nombre in test_users:
        try:
            is_super = security.is_super_admin(chat_id)
            can_upload = security.can_upload_files(chat_id)
            can_download = security.can_download_files(chat_id)
            can_manage = security.can_manage_empresas(chat_id)
            
            print(f"✅ {nombre}: super={is_super}, upload={can_upload}, download={can_download}, manage={can_manage}")
        except Exception as e:
            print(f"❌ Error con {nombre}: {e}")
            todos_ok = False
    
    return todos_ok

def test_database_methods():
    """Test 5: Verificar métodos de base de datos"""
    print("\n" + "="*80)
    print("TEST 5: MÉTODOS DE BASE DE DATOS")
    print("="*80)
    
    try:
        supabase = get_supabase_client()
        test_chat_id = 866310278
        
        # get_user_by_chat_id
        user = supabase.get_user_by_chat_id(test_chat_id)
        if not user:
            print("❌ get_user_by_chat_id: Usuario no encontrado")
            return False
        print(f"✅ get_user_by_chat_id: {user.get('nombre', 'N/A')}")
        
        # get_user_empresas
        empresas = supabase.get_user_empresas(test_chat_id)
        if not empresas:
            print("❌ get_user_empresas: No se encontraron empresas")
            return False
        print(f"✅ get_user_empresas: {len(empresas)} empresa(s)")
        
        # user_has_access_to_empresa
        empresa_id = empresas[0]['id']
        has_access = supabase.user_has_access_to_empresa(test_chat_id, empresa_id)
        if not has_access:
            print("❌ user_has_access_to_empresa: Acceso denegado incorrectamente")
            return False
        print(f"✅ user_has_access_to_empresa: {has_access}")
        
        return True
    except Exception as e:
        print(f"❌ Error en métodos de BD: {e}")
        return False

def test_handlers_structure():
    """Test 6: Verificar estructura de handlers"""
    print("\n" + "="*80)
    print("TEST 6: ESTRUCTURA DE HANDLERS")
    print("="*80)
    
    try:
        from app.bots.handlers.file_upload_handler import FileUploadHandler
        from app.bots.handlers.file_download_handler import FileDownloadHandler
        from app.bots.handlers.production_handlers import ProductionHandlers
        
        metodos_requeridos = {
            'FileUploadHandler': ['handle_document', '_get_user_empresas'],
            'FileDownloadHandler': ['_get_user_empresas', '_ask_empresa'],  # handle_informacion está en ProductionHandlers
            'ProductionHandlers': ['start_command', 'handle_callback', '_show_main_menu', '_handle_informacion']
        }
        
        todos_ok = True
        for clase, metodos in metodos_requeridos.items():
            clase_obj = eval(clase)
            for metodo in metodos:
                if hasattr(clase_obj, metodo):
                    print(f"✅ {clase}.{metodo}")
                else:
                    print(f"❌ {clase}.{metodo} - NO EXISTE")
                    todos_ok = False
        
        return todos_ok
    except Exception as e:
        print(f"❌ Error verificando handlers: {e}")
        return False

def main():
    """Ejecutar todos los tests"""
    print("="*80)
    print("🧪 TEST COMPLETO DEL SISTEMA ACA 4.0")
    print("="*80)
    print()
    
    resultados = []
    
    resultados.append(("Imports", test_imports()))
    resultados.append(("Configuración", test_config()))
    resultados.append(("Conexión Supabase", test_supabase_connection()))
    resultados.append(("Métodos de Seguridad", test_security_methods()))
    resultados.append(("Métodos de BD", test_database_methods()))
    resultados.append(("Estructura Handlers", test_handlers_structure()))
    
    print("\n" + "="*80)
    print("📊 RESUMEN DE TESTS")
    print("="*80)
    print()
    
    exitos = sum(1 for _, resultado in resultados if resultado)
    total = len(resultados)
    
    for nombre, resultado in resultados:
        estado = "✅ PASS" if resultado else "❌ FAIL"
        print(f"{estado} - {nombre}")
    
    print()
    print("="*80)
    if exitos == total:
        print(f"✅ TODOS LOS TESTS PASARON ({exitos}/{total})")
        print("="*80)
        return 0
    else:
        print(f"⚠️  ALGUNOS TESTS FALLARON ({exitos}/{total})")
        print("="*80)
        return 1

if __name__ == "__main__":
    sys.exit(main())

