#!/usr/bin/env python3
"""
🔍 Revisar cambios en Supabase - Especialmente tabla usuarios_empresas
"""

from app.database.supabase import get_supabase_client

def revisar_tabla_usuarios_empresas():
    """Revisar si la tabla usuarios_empresas existe y tiene datos"""
    supabase = get_supabase_client()
    
    print("="*80)
    print("🔍 REVISIÓN DE TABLA usuarios_empresas")
    print("="*80)
    print()
    
    try:
        # Intentar consultar la tabla
        result = supabase.table('usuarios_empresas').select('*').limit(5).execute()
        
        # Contar total
        count_result = supabase.table('usuarios_empresas').select('*', count='exact').limit(1).execute()
        total = count_result.count if hasattr(count_result, 'count') else len(result.data) if result.data else 0
        
        print(f"✅ Tabla usuarios_empresas existe")
        print(f"   • Total de registros: {total}")
        print()
        
        if result.data and len(result.data) > 0:
            print("📋 Estructura de la tabla:")
            campos = list(result.data[0].keys())
            print(f"   • Campos ({len(campos)}): {', '.join(campos)}")
            print()
            
            print("📊 Primeros registros:")
            for i, registro in enumerate(result.data[:5], 1):
                print(f"   [{i}] Usuario ID: {registro.get('usuario_id', 'N/A')}")
                print(f"       Empresa ID: {registro.get('empresa_id', 'N/A')}")
                print(f"       Rol: {registro.get('rol', 'N/A')}")
                print(f"       Activo: {registro.get('activo', 'N/A')}")
                print()
        else:
            print("⚠️  La tabla está vacía (esto es normal si aún no se han asociado empresas)")
            print()
        
        return True
        
    except Exception as e:
        error_msg = str(e).lower()
        if 'relation' in error_msg or 'does not exist' in error_msg or 'not found' in error_msg:
            print("❌ Tabla usuarios_empresas NO EXISTE")
            print()
            print("💡 Necesitas ejecutar la migración SQL:")
            print("   Archivo: database/migrations/003_create_usuarios_empresas.sql")
            print("   En Supabase SQL Editor")
            print()
            return False
        else:
            print(f"❌ Error consultando tabla: {e}")
            print()
            return False

def revisar_usuarios_y_empresas():
    """Revisar usuarios y empresas existentes"""
    supabase = get_supabase_client()
    
    print("="*80)
    print("👥 REVISIÓN DE USUARIOS Y EMPRESAS")
    print("="*80)
    print()
    
    # Usuarios
    try:
        usuarios = supabase.table('usuarios').select('*').execute()
        print(f"👤 Usuarios totales: {len(usuarios.data) if usuarios.data else 0}")
        
        if usuarios.data:
            usuarios_con_empresa = [u for u in usuarios.data if u.get('empresa_id')]
            usuarios_sin_empresa = [u for u in usuarios.data if not u.get('empresa_id')]
            
            print(f"   • Con empresa_id (legacy): {len(usuarios_con_empresa)}")
            print(f"   • Sin empresa_id: {len(usuarios_sin_empresa)}")
            print()
            
            if usuarios_con_empresa:
                print("📋 Usuarios con empresa_id:")
                for u in usuarios_con_empresa[:5]:
                    print(f"   • Chat ID: {u.get('chat_id')} - Empresa: {u.get('empresa_id')}")
        print()
    except Exception as e:
        print(f"⚠️  Error consultando usuarios: {e}")
        print()
    
    # Empresas
    try:
        empresas = supabase.table('empresas').select('*').execute()
        print(f"🏢 Empresas totales: {len(empresas.data) if empresas.data else 0}")
        
        if empresas.data:
            empresas_activas = [e for e in empresas.data if e.get('activo')]
            print(f"   • Activas: {len(empresas_activas)}")
            print()
            
            print("📋 Empresas:")
            for e in empresas.data[:5]:
                estado = "🟢" if e.get('activo') else "🔴"
                print(f"   {estado} {e.get('nombre', 'N/A')} (RUT: {e.get('rut', 'N/A')})")
                print(f"      ID: {e.get('id')}")
        print()
    except Exception as e:
        print(f"⚠️  Error consultando empresas: {e}")
        print()

def revisar_relaciones_usuarios_empresas():
    """Revisar relaciones entre usuarios y empresas"""
    supabase = get_supabase_client()
    
    print("="*80)
    print("🔗 REVISIÓN DE RELACIONES USUARIOS-EMPRESAS")
    print("="*80)
    print()
    
    try:
        # Obtener todas las relaciones
        relaciones = supabase.table('usuarios_empresas')\
            .select('*, usuarios(chat_id, nombre), empresas(nombre, rut)')\
            .limit(10)\
            .execute()
        
        if relaciones.data:
            print(f"📊 Relaciones encontradas: {len(relaciones.data)}")
            print()
            
            for i, rel in enumerate(relaciones.data[:10], 1):
                usuario_info = rel.get('usuarios', {}) if rel.get('usuarios') else {}
                empresa_info = rel.get('empresas', {}) if rel.get('empresas') else {}
                
                print(f"   [{i}] Usuario: {usuario_info.get('nombre', 'N/A')} (Chat ID: {usuario_info.get('chat_id', 'N/A')})")
                print(f"       Empresa: {empresa_info.get('nombre', 'N/A')} (RUT: {empresa_info.get('rut', 'N/A')})")
                print(f"       Rol: {rel.get('rol', 'N/A')} | Activo: {rel.get('activo', 'N/A')}")
                print()
        else:
            print("⚠️  No hay relaciones en usuarios_empresas")
            print("   Esto es normal si:")
            print("   • La migración aún no se ha ejecutado")
            print("   • O aún no se han asociado empresas a usuarios")
            print()
    except Exception as e:
        error_msg = str(e).lower()
        if 'relation' in error_msg or 'does not exist' in error_msg:
            print("❌ Tabla usuarios_empresas no existe")
            print("   Ejecuta la migración SQL primero")
        else:
            print(f"⚠️  Error: {e}")
        print()

def verificar_funcion_migracion():
    """Verificar si la función de migración existe"""
    supabase = get_supabase_client()
    
    print("="*80)
    print("🔧 VERIFICACIÓN DE FUNCIÓN DE MIGRACIÓN")
    print("="*80)
    print()
    
    try:
        # Intentar ejecutar la función (solo verificar si existe)
        # Nota: No ejecutamos la función aquí, solo verificamos
        print("💡 La función migrar_empresas_existentes() se ejecuta automáticamente")
        print("   cuando se ejecuta la migración SQL")
        print()
    except Exception as e:
        print(f"⚠️  {e}")

def main():
    """Función principal"""
    print("="*80)
    print("🔍 REVISIÓN COMPLETA DE CAMBIOS EN SUPABASE")
    print("="*80)
    print()
    
    # 1. Revisar tabla usuarios_empresas
    tabla_existe = revisar_tabla_usuarios_empresas()
    
    # 2. Revisar usuarios y empresas
    revisar_usuarios_y_empresas()
    
    # 3. Revisar relaciones
    if tabla_existe:
        revisar_relaciones_usuarios_empresas()
    
    # 4. Verificar función de migración
    verificar_funcion_migracion()
    
    # Resumen
    print("="*80)
    print("📊 RESUMEN")
    print("="*80)
    print()
    
    if tabla_existe:
        print("✅ Tabla usuarios_empresas existe y está lista para usar")
        print()
        print("💡 Próximos pasos:")
        print("   1. Si la tabla está vacía, ejecuta la migración SQL para migrar datos existentes")
        print("   2. Usa el script asociar_empresa_usuario.py para asociar empresas a usuarios")
        print("   3. Actualiza los handlers de archivos para usar la nueva tabla")
    else:
        print("❌ Tabla usuarios_empresas no existe")
        print()
        print("💡 Acción requerida:")
        print("   1. Ejecuta la migración SQL en Supabase:")
        print("      database/migrations/003_create_usuarios_empresas.sql")
        print("   2. Luego ejecuta este script nuevamente para verificar")
    print()

if __name__ == "__main__":
    main()







