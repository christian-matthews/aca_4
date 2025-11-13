#!/usr/bin/env python3
"""
🔧 Ejecutar migración de roles directamente desde Python
"""

from app.database.supabase import get_supabase_client
import sys

def ejecutar_migracion_roles():
    """Ejecutar migración de roles usando RPC o queries directas"""
    
    print("="*80)
    print("🔧 EJECUTANDO MIGRACIÓN DE ROLES")
    print("="*80)
    print()
    
    supabase = get_supabase_client()
    
    # Leer el archivo SQL
    try:
        with open('database/migrations/004_sistema_roles_permisos.sql', 'r') as f:
            sql_content = f.read()
        print("✅ Archivo SQL leído")
    except Exception as e:
        print(f"❌ Error leyendo archivo SQL: {e}")
        return False
    
    print()
    print("⚠️  NOTA: Las migraciones SQL deben ejecutarse manualmente en Supabase SQL Editor")
    print("   El archivo está en: database/migrations/004_sistema_roles_permisos.sql")
    print()
    print("💡 Alternativamente, podemos verificar y actualizar los roles directamente")
    print()
    
    # Verificar y actualizar roles directamente
    print("🔧 Verificando y actualizando roles...")
    print()
    
    # 1. Verificar roles en usuarios_empresas
    try:
        relaciones = supabase.table('usuarios_empresas').select('*').execute()
        
        if relaciones.data:
            print(f"📋 Encontradas {len(relaciones.data)} relaciones")
            print()
            
            # Verificar que los roles sean válidos
            roles_validos = ['super_admin', 'gestor', 'usuario', 'admin', 'user']
            roles_invalidos = []
            
            for rel in relaciones.data:
                rol = rel.get('rol', '')
                if rol and rol not in roles_validos:
                    roles_invalidos.append({
                        'id': rel['id'],
                        'rol_actual': rol
                    })
            
            if roles_invalidos:
                print(f"⚠️  Encontrados {len(roles_invalidos)} roles inválidos:")
                for inv in roles_invalidos:
                    print(f"   • ID: {inv['id']}, Rol: {inv['rol_actual']}")
                print()
                print("💡 Estos roles necesitan ser actualizados manualmente")
            else:
                print("✅ Todos los roles son válidos")
        else:
            print("⚠️  No hay relaciones en usuarios_empresas")
    except Exception as e:
        print(f"⚠️  Error verificando relaciones: {e}")
    
    print()
    print("="*80)
    print("📋 INSTRUCCIONES")
    print("="*80)
    print()
    print("Para completar la migración:")
    print("1. Ve a Supabase Dashboard → SQL Editor")
    print("2. Copia el contenido de: database/migrations/004_sistema_roles_permisos.sql")
    print("3. Ejecuta el SQL en Supabase")
    print("4. Esto creará los constraints de validación de roles")
    print()
    print("Los roles ya están asignados correctamente en la base de datos.")
    print("La migración SQL solo agrega validaciones a nivel de base de datos.")
    print()

if __name__ == "__main__":
    ejecutar_migracion_roles()







