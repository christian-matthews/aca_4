#!/usr/bin/env python3
"""
🔗 Asociar empresa(s) a un usuario existente
Soporte para multiempresa: un usuario puede tener múltiples empresas
"""

from app.database.supabase import get_supabase_client
import sys

def asociar_empresa_usuario(chat_id, empresa_ids, rol='user'):
    """
    Asociar una o múltiples empresas a un usuario
    
    Args:
        chat_id: Chat ID del usuario en Telegram
        empresa_ids: Lista de IDs de empresas (UUIDs) o un solo ID
        rol: Rol del usuario en la(s) empresa(s) (default: 'user')
    """
    
    print("="*80)
    print("🔗 ASOCIAR EMPRESA(S) A USUARIO")
    print("="*80)
    print()
    
    try:
        chat_id = int(chat_id)
    except ValueError:
        print("❌ Error: chat_id debe ser un número")
        return False
    
    # Convertir empresa_ids a lista si es un solo valor
    if isinstance(empresa_ids, str):
        empresa_ids = [empresa_ids]
    elif not isinstance(empresa_ids, list):
        empresa_ids = [empresa_ids]
    
    supabase = get_supabase_client()
    
    # 1. Verificar que el usuario existe
    usuario = supabase.table('usuarios').select('*').eq('chat_id', chat_id).execute()
    
    if not usuario.data:
        print(f"❌ Error: No existe un usuario con chat_id {chat_id}")
        print()
        print("💡 Primero debes crear el usuario con /adduser o crear una empresa")
        return False
    
    usuario_id = usuario.data[0]['id']
    nombre_usuario = usuario.data[0].get('nombre', 'Usuario')
    
    print(f"👤 Usuario encontrado:")
    print(f"   • Nombre: {nombre_usuario}")
    print(f"   • Chat ID: {chat_id}")
    print(f"   • ID Usuario: {usuario_id}")
    print()
    
    # 2. Verificar que las empresas existen
    empresas_validas = []
    empresas_invalidas = []
    
    for empresa_id in empresa_ids:
        empresa = supabase.table('empresas').select('*').eq('id', empresa_id).execute()
        if empresa.data:
            empresas_validas.append({
                'id': empresa_id,
                'nombre': empresa.data[0]['nombre'],
                'rut': empresa.data[0].get('rut', '')
            })
        else:
            empresas_invalidas.append(empresa_id)
    
    if empresas_invalidas:
        print(f"⚠️  Empresas no encontradas: {empresas_invalidas}")
        print()
    
    if not empresas_validas:
        print("❌ Error: No se encontraron empresas válidas")
        return False
    
    print(f"🏢 Empresas a asociar ({len(empresas_validas)}):")
    for empresa in empresas_validas:
        print(f"   • {empresa['nombre']} (RUT: {empresa['rut']}) - ID: {empresa['id']}")
    print()
    
    # 3. Verificar relaciones existentes
    relaciones_existentes = supabase.table('usuarios_empresas')\
        .select('*, empresas(nombre, rut)')\
        .eq('usuario_id', usuario_id)\
        .execute()
    
    empresas_ya_asociadas = []
    if relaciones_existentes.data:
        print("📋 Empresas ya asociadas:")
        for rel in relaciones_existentes.data:
            empresa_nombre = rel.get('empresas', {}).get('nombre', 'N/A') if rel.get('empresas') else 'N/A'
            empresas_ya_asociadas.append(rel['empresa_id'])
            estado = "🟢 Activa" if rel.get('activo') else "🔴 Inactiva"
            print(f"   • {empresa_nombre} - {estado}")
        print()
    
    # 4. Crear nuevas asociaciones
    nuevas_asociaciones = []
    ya_existentes = []
    
    for empresa in empresas_validas:
        empresa_id = empresa['id']
        
        # Verificar si ya existe la relación
        if empresa_id in empresas_ya_asociadas:
            ya_existentes.append(empresa['nombre'])
            continue
        
        # Crear nueva relación
        try:
            relacion_data = {
                'usuario_id': usuario_id,
                'empresa_id': empresa_id,
                'rol': rol,
                'activo': True
            }
            
            resultado = supabase.table('usuarios_empresas').insert(relacion_data).execute()
            
            if resultado.data:
                nuevas_asociaciones.append(empresa['nombre'])
                print(f"   ✅ Asociada: {empresa['nombre']}")
            else:
                print(f"   ❌ Error asociando: {empresa['nombre']}")
                
        except Exception as e:
            error_msg = str(e)
            if 'duplicate' in error_msg.lower() or 'unique' in error_msg.lower():
                ya_existentes.append(empresa['nombre'])
                print(f"   ⚠️  Ya asociada: {empresa['nombre']}")
            else:
                print(f"   ❌ Error: {empresa['nombre']} - {error_msg[:50]}")
    
    print()
    print("="*80)
    print("📊 RESUMEN")
    print("="*80)
    print()
    
    if nuevas_asociaciones:
        print(f"✅ Nuevas asociaciones creadas ({len(nuevas_asociaciones)}):")
        for nombre in nuevas_asociaciones:
            print(f"   • {nombre}")
        print()
    
    if ya_existentes:
        print(f"ℹ️  Ya estaban asociadas ({len(ya_existentes)}):")
        for nombre in ya_existentes:
            print(f"   • {nombre}")
        print()
    
    # 5. Mostrar todas las empresas del usuario
    todas_relaciones = supabase.table('usuarios_empresas')\
        .select('*, empresas(nombre, rut, activo)')\
        .eq('usuario_id', usuario_id)\
        .eq('activo', True)\
        .execute()
    
    if todas_relaciones.data:
        print(f"🏢 Total de empresas asociadas: {len(todas_relaciones.data)}")
        for rel in todas_relaciones.data:
            empresa_info = rel.get('empresas', {}) if rel.get('empresas') else {}
            nombre_empresa = empresa_info.get('nombre', 'N/A')
            rut_empresa = empresa_info.get('rut', 'N/A')
            rol_empresa = rel.get('rol', 'user')
            print(f"   • {nombre_empresa} (RUT: {rut_empresa}) - Rol: {rol_empresa}")
    
    print()
    print("="*80)
    print("✅ PROCESO COMPLETADO")
    print("="*80)
    print()
    
    return len(nuevas_asociaciones) > 0

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("="*80)
        print("🔗 ASOCIAR EMPRESA(S) A USUARIO")
        print("="*80)
        print()
        print("📝 Uso:")
        print("   python asociar_empresa_usuario.py CHAT_ID EMPRESA_ID [EMPRESA_ID2 ...] [--rol ROL]")
        print()
        print("📋 Ejemplos:")
        print("   # Asociar una empresa")
        print("   python asociar_empresa_usuario.py 123456789 uuid-empresa-1")
        print()
        print("   # Asociar múltiples empresas")
        print("   python asociar_empresa_usuario.py 123456789 uuid-empresa-1 uuid-empresa-2")
        print()
        print("   # Asociar con rol específico")
        print("   python asociar_empresa_usuario.py 123456789 uuid-empresa-1 --rol admin")
        print()
        print("💡 Parámetros:")
        print("   • CHAT_ID: Chat ID de Telegram del usuario (requerido)")
        print("   • EMPRESA_ID: ID(s) de la(s) empresa(s) a asociar (requerido, puede ser múltiples)")
        print("   • --rol: Rol del usuario en la empresa (opcional, default: 'user')")
        print()
        sys.exit(1)
    
    # Parsear argumentos
    chat_id = sys.argv[1]
    empresa_ids = []
    rol = 'user'
    
    i = 2
    while i < len(sys.argv):
        if sys.argv[i] == '--rol' and i + 1 < len(sys.argv):
            rol = sys.argv[i + 1]
            i += 2
        else:
            empresa_ids.append(sys.argv[i])
            i += 1
    
    if not empresa_ids:
        print("❌ Error: Debes proporcionar al menos un EMPRESA_ID")
        sys.exit(1)
    
    success = asociar_empresa_usuario(chat_id, empresa_ids, rol)
    sys.exit(0 if success else 1)







