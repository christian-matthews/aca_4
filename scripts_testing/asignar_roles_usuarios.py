#!/usr/bin/env python3
"""
👤 Asignar roles a usuarios según el sistema de 3 niveles
"""

from app.database.supabase import get_supabase_client
from app.config import Config
import sys

def asignar_roles():
    """Asignar roles según especificación"""
    
    print("="*80)
    print("👤 ASIGNACIÓN DE ROLES")
    print("="*80)
    print()
    
    supabase = get_supabase_client()
    
    # Super Admins (todos los permisos)
    super_admins = [
        Config.ADMIN_CHAT_ID,  # The Wingman
        866310278  # Christian Matthews (tú)
    ]
    
    # Usuarios con rol específico
    usuarios_roles = {
        2134113487: 'usuario',  # Patricio Alarcon - solo puede bajar archivos
    }
    
    print("🔧 Configurando roles...")
    print()
    
    # 1. Asignar super_admin a usuarios en tabla usuarios
    print("1️⃣ Super Admins (tabla usuarios):")
    for chat_id in super_admins:
        try:
            usuario = supabase.table('usuarios').select('*').eq('chat_id', chat_id).execute()
            if usuario.data:
                supabase.table('usuarios').update({
                    'rol': 'super_admin'
                }).eq('chat_id', chat_id).execute()
                print(f"   ✅ Chat ID {chat_id}: super_admin")
            else:
                print(f"   ⚠️  Chat ID {chat_id}: Usuario no encontrado")
        except Exception as e:
            print(f"   ❌ Error con chat_id {chat_id}: {e}")
    print()
    
    # 2. Asignar roles en usuarios_empresas
    print("2️⃣ Roles por empresa (tabla usuarios_empresas):")
    
    # Obtener todas las relaciones
    relaciones = supabase.table('usuarios_empresas').select('*, usuarios(chat_id)').execute()
    
    if relaciones.data:
        for rel in relaciones.data:
            usuario_info = rel.get('usuarios', {}) if rel.get('usuarios') else {}
            chat_id = usuario_info.get('chat_id')
            
            if not chat_id:
                continue
            
            # Determinar rol
            nuevo_rol = None
            
            if chat_id in super_admins:
                nuevo_rol = 'super_admin'
            elif chat_id in usuarios_roles:
                nuevo_rol = usuarios_roles[chat_id]
            else:
                # Por defecto, mantener el rol actual o asignar 'gestor'
                nuevo_rol = rel.get('rol', 'gestor')
            
            # Actualizar rol
            try:
                supabase.table('usuarios_empresas').update({
                    'rol': nuevo_rol
                }).eq('id', rel['id']).execute()
                
                usuario_nombre = usuario_info.get('nombre', f'Chat ID {chat_id}')
                print(f"   ✅ {usuario_nombre} (Chat ID: {chat_id}): {nuevo_rol}")
            except Exception as e:
                print(f"   ❌ Error actualizando {chat_id}: {e}")
    else:
        print("   ⚠️  No hay relaciones en usuarios_empresas")
    print()
    
    # 3. Verificar resultados
    print("="*80)
    print("✅ VERIFICACIÓN DE ROLES ASIGNADOS")
    print("="*80)
    print()
    
    # Verificar super admins
    print("🔴 Super Admins:")
    for chat_id in super_admins:
        usuario = supabase.table('usuarios').select('*').eq('chat_id', chat_id).execute()
        if usuario.data:
            print(f"   • Chat ID {chat_id}: {usuario.data[0].get('rol', 'N/A')}")
    print()
    
    # Verificar roles por empresa
    print("📋 Roles por empresa:")
    relaciones_final = supabase.table('usuarios_empresas')\
        .select('*, usuarios(chat_id, nombre), empresas(nombre)')\
        .execute()
    
    if relaciones_final.data:
        for rel in relaciones_final.data:
            usuario_info = rel.get('usuarios', {}) if rel.get('usuarios') else {}
            empresa_info = rel.get('empresas', {}) if rel.get('empresas') else {}
            
            usuario_nombre = usuario_info.get('nombre', 'N/A')
            empresa_nombre = empresa_info.get('nombre', 'N/A')
            rol = rel.get('rol', 'N/A')
            
            print(f"   • {usuario_nombre} → {empresa_nombre}: {rol}")
    print()
    
    print("="*80)
    print("✅ PROCESO COMPLETADO")
    print("="*80)
    print()
    print("📋 Resumen de roles:")
    print("   • super_admin: Todos los permisos (The Wingman, Christian)")
    print("   • gestor: Puede asignar empresas, subir y bajar archivos")
    print("   • usuario: Solo puede bajar archivos (Patricio)")
    print()

if __name__ == "__main__":
    asignar_roles()







