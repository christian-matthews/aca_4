#!/usr/bin/env python3
"""
🔍 Script de verificación de integración con Supabase
Verifica conexión, tablas, funciones y operaciones básicas
"""

import sys
from pathlib import Path

# Agregar el directorio raíz al path
sys.path.insert(0, str(Path(__file__).parent))

from app.database.supabase import get_supabase_client
from app.config import Config
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def verificar_configuracion():
    """Verificar que las variables de entorno estén configuradas"""
    print("\n" + "="*60)
    print("1️⃣ VERIFICANDO CONFIGURACIÓN")
    print("="*60)
    
    try:
        Config.validate()
        print("✅ Variables de entorno configuradas correctamente")
        print(f"   - SUPABASE_URL: {Config.SUPABASE_URL[:30]}...")
        print(f"   - SUPABASE_KEY: {'✅ Configurado' if Config.SUPABASE_KEY else '❌ Faltante'}")
        print(f"   - SUPABASE_SERVICE_KEY: {'✅ Configurado' if Config.SUPABASE_SERVICE_KEY else '❌ Faltante'}")
        return True
    except ValueError as e:
        print(f"❌ Error en configuración: {e}")
        return False

def verificar_conexion():
    """Verificar conexión básica con Supabase"""
    print("\n" + "="*60)
    print("2️⃣ VERIFICANDO CONEXIÓN CON SUPABASE")
    print("="*60)
    
    try:
        supabase = get_supabase_client()
        
        # Intentar una consulta simple
        result = supabase.table('empresas').select('id').limit(1).execute()
        print("✅ Conexión con Supabase exitosa")
        print(f"   - Cliente inicializado correctamente")
        return True, supabase
    except Exception as e:
        print(f"❌ Error de conexión: {e}")
        return False, None

def verificar_tablas(supabase):
    """Verificar que las tablas críticas existan"""
    print("\n" + "="*60)
    print("3️⃣ VERIFICANDO TABLAS CRÍTICAS")
    print("="*60)
    
    tablas_criticas = [
        'empresas',
        'usuarios',
        'conversaciones',
        'usuarios_detalle',
        'intentos_acceso_negado'
    ]
    
    tablas_opcionales = [
        'security_logs',
        'bot_analytics',
        'archivos'
    ]
    
    resultados = {}
    
    # Verificar tablas críticas
    print("\n📋 Tablas Críticas:")
    for tabla in tablas_criticas:
        try:
            result = supabase.table(tabla).select('*').limit(1).execute()
            print(f"   ✅ {tabla:30s} - OK (registros: {len(result.data) if result.data else 0})")
            resultados[tabla] = True
        except Exception as e:
            print(f"   ❌ {tabla:30s} - ERROR: {str(e)[:50]}")
            resultados[tabla] = False
    
    # Verificar tablas opcionales
    print("\n📋 Tablas Opcionales:")
    for tabla in tablas_opcionales:
        try:
            result = supabase.table(tabla).select('*').limit(1).execute()
            print(f"   ✅ {tabla:30s} - OK (registros: {len(result.data) if result.data else 0})")
            resultados[tabla] = True
        except Exception as e:
            print(f"   ⚠️  {tabla:30s} - No disponible: {str(e)[:50]}")
            resultados[tabla] = False
    
    return resultados

def verificar_funciones_sql(supabase):
    """Verificar que las funciones SQL estén disponibles"""
    print("\n" + "="*60)
    print("4️⃣ VERIFICANDO FUNCIONES SQL")
    print("="*60)
    
    funciones = ['log_conversacion_simple']
    
    resultados = {}
    
    for funcion in funciones:
        try:
            # Intentar llamar la función con parámetros de prueba
            if funcion == 'log_conversacion_simple':
                result = supabase.client.rpc(
                    funcion,
                    {
                        'p_chat_id': 999999999,  # Chat ID de prueba
                        'p_mensaje': 'Test de verificación',
                        'p_user_id': 999999999,
                        'p_respuesta': 'Test OK',
                        'p_first_name': 'Test',
                        'p_last_name': 'User',
                        'p_username': 'testuser',
                        'p_bot_tipo': 'production',
                        'p_tiene_acceso': False
                    }
                ).execute()
                print(f"   ✅ {funcion:30s} - OK")
                resultados[funcion] = True
        except Exception as e:
            error_msg = str(e)
            if 'does not exist' in error_msg.lower() or 'function' in error_msg.lower():
                print(f"   ❌ {funcion:30s} - No existe: {str(e)[:60]}")
            else:
                print(f"   ⚠️  {funcion:30s} - Error: {str(e)[:60]}")
            resultados[funcion] = False
    
    return resultados

def verificar_vistas(supabase):
    """Verificar que las vistas estén disponibles"""
    print("\n" + "="*60)
    print("5️⃣ VERIFICANDO VISTAS")
    print("="*60)
    
    vistas = [
        'vista_conversaciones_recientes',
        'vista_usuarios_sin_acceso'
    ]
    
    resultados = {}
    
    for vista in vistas:
        try:
            result = supabase.table(vista).select('*').limit(1).execute()
            print(f"   ✅ {vista:30s} - OK")
            resultados[vista] = True
        except Exception as e:
            print(f"   ⚠️  {vista:30s} - No disponible: {str(e)[:50]}")
            resultados[vista] = False
    
    return resultados

def verificar_operaciones_basicas(supabase):
    """Verificar operaciones CRUD básicas"""
    print("\n" + "="*60)
    print("6️⃣ VERIFICANDO OPERACIONES BÁSICAS")
    print("="*60)
    
    operaciones = {
        'SELECT': False,
        'INSERT': False,
        'UPDATE': False,
        'DELETE': False
    }
    
    try:
        # SELECT
        result = supabase.table('empresas').select('id').limit(1).execute()
        print("   ✅ SELECT - OK")
        operaciones['SELECT'] = True
    except Exception as e:
        print(f"   ❌ SELECT - Error: {str(e)[:50]}")
    
    # No probamos INSERT/UPDATE/DELETE para no modificar datos reales
    print("   ⚠️  INSERT/UPDATE/DELETE - Omitido (protección de datos)")
    
    return operaciones

def verificar_metodos_helper(supabase):
    """Verificar métodos helper del SupabaseManager"""
    print("\n" + "="*60)
    print("7️⃣ VERIFICANDO MÉTODOS HELPER")
    print("="*60)
    
    metodos = {
        'get_user_by_chat_id': False,
        'table': False,
        'create_empresa': False
    }
    
    try:
        # Verificar método table()
        result = supabase.table('empresas')
        print("   ✅ table() - OK")
        metodos['table'] = True
    except Exception as e:
        print(f"   ❌ table() - Error: {str(e)[:50]}")
    
    try:
        # Verificar método get_user_by_chat_id (sin datos reales)
        result = supabase.get_user_by_chat_id(999999999)
        print("   ✅ get_user_by_chat_id() - OK (retorna None para ID inexistente)")
        metodos['get_user_by_chat_id'] = True
    except Exception as e:
        print(f"   ❌ get_user_by_chat_id() - Error: {str(e)[:50]}")
    
    print("   ⚠️  create_empresa() - Omitido (no crear datos de prueba)")
    
    return metodos

def generar_reporte(resultados):
    """Generar reporte final"""
    print("\n" + "="*60)
    print("📊 REPORTE FINAL")
    print("="*60)
    
    total_tablas_criticas = sum(1 for k, v in resultados.get('tablas', {}).items() 
                                if k in ['empresas', 'usuarios', 'conversaciones', 'usuarios_detalle', 'intentos_acceso_negado'] and v)
    
    tablas_criticas_ok = total_tablas_criticas == 5
    
    funciones_ok = all(resultados.get('funciones', {}).values())
    operaciones_ok = resultados.get('operaciones', {}).get('SELECT', False)
    
    print(f"\n✅ Tablas críticas: {total_tablas_criticas}/5")
    print(f"{'✅' if funciones_ok else '⚠️ '} Funciones SQL: {'OK' if funciones_ok else 'Revisar'}")
    print(f"{'✅' if operaciones_ok else '❌'} Operaciones básicas: {'OK' if operaciones_ok else 'Error'}")
    
    if tablas_criticas_ok and funciones_ok and operaciones_ok:
        print("\n🎉 INTEGRACIÓN CON BASE DE DATOS: ✅ CORRECTA")
    elif tablas_criticas_ok and operaciones_ok:
        print("\n⚠️  INTEGRACIÓN CON BASE DE DATOS: ⚠️  PARCIAL (revisar funciones SQL)")
    else:
        print("\n❌ INTEGRACIÓN CON BASE DE DATOS: ❌ REQUIERE ATENCIÓN")

def main():
    """Función principal"""
    print("\n" + "🔍"*30)
    print("VERIFICACIÓN DE INTEGRACIÓN CON SUPABASE")
    print("🔍"*30)
    
    resultados = {}
    
    # 1. Verificar configuración
    if not verificar_configuracion():
        print("\n❌ Error en configuración. Revisa las variables de entorno.")
        sys.exit(1)
    
    # 2. Verificar conexión
    conexion_ok, supabase = verificar_conexion()
    if not conexion_ok:
        print("\n❌ No se pudo establecer conexión con Supabase.")
        sys.exit(1)
    
    # 3. Verificar tablas
    resultados['tablas'] = verificar_tablas(supabase)
    
    # 4. Verificar funciones SQL
    resultados['funciones'] = verificar_funciones_sql(supabase)
    
    # 5. Verificar vistas
    resultados['vistas'] = verificar_vistas(supabase)
    
    # 6. Verificar operaciones básicas
    resultados['operaciones'] = verificar_operaciones_basicas(supabase)
    
    # 7. Verificar métodos helper
    resultados['metodos'] = verificar_metodos_helper(supabase)
    
    # Generar reporte final
    generar_reporte(resultados)
    
    print("\n" + "="*60 + "\n")

if __name__ == "__main__":
    main()


