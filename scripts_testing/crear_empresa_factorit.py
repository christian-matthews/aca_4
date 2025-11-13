#!/usr/bin/env python3
"""
🏢 Crear empresa FactorIT directamente en la base de datos
"""

from app.database.supabase import get_supabase_client
from app.security.auth import security
import sys

def crear_empresa_factorit(rut=None, nombre="FactorIT", admin_chat_id=None, nombre_admin="Administrador"):
    """Crear empresa FactorIT"""
    
    print("="*80)
    print("🏢 CREAR EMPRESA FACTORIT")
    print("="*80)
    print()
    
    # Si no se proporcionan parámetros, usar valores por defecto o solicitar
    if not rut:
        print("📝 Información requerida:")
        print()
        print("   Uso: python crear_empresa_factorit.py RUT ADMIN_CHAT_ID [NOMBRE] [NOMBRE_ADMIN]")
        print()
        print("   Ejemplo:")
        print("   python crear_empresa_factorit.py 12345678-9 123456789")
        print("   python crear_empresa_factorit.py 12345678-9 123456789 FactorIT 'Juan Pérez'")
        print()
        return False
    
    if not admin_chat_id:
        print("❌ Error: Se requiere RUT y ADMIN_CHAT_ID")
        print()
        print("   Uso: python crear_empresa_factorit.py RUT ADMIN_CHAT_ID [NOMBRE] [NOMBRE_ADMIN]")
        return False
    
    try:
        admin_chat_id = int(admin_chat_id)
    except ValueError:
        print("❌ Error: ADMIN_CHAT_ID debe ser un número")
        return False
    
    print("📋 Información a crear:")
    print(f"   • RUT: {rut}")
    print(f"   • Nombre: {nombre}")
    print(f"   • Admin Chat ID: {admin_chat_id}")
    print(f"   • Nombre Admin: {nombre_admin}")
    print()
    
    print("🔄 Creando empresa...")
    
    try:
        supabase = get_supabase_client()
        
        # Verificar si la empresa ya existe
        empresa_existente = supabase.table('empresas').select('*').eq('rut', rut).execute()
        if empresa_existente.data:
            print(f"⚠️  Ya existe una empresa con RUT {rut}")
            empresa_id = empresa_existente.data[0]['id']
            print(f"   • ID Empresa existente: {empresa_id}")
            print(f"   • Nombre: {empresa_existente.data[0]['nombre']}")
            
            # Verificar si el usuario admin ya existe
            usuario_existente = supabase.table('usuarios').select('*').eq('chat_id', admin_chat_id).execute()
            if usuario_existente.data:
                print(f"   ⚠️  Ya existe un usuario con chat_id {admin_chat_id}")
                return False
            
            # Crear solo el usuario admin
            print()
            print("🔄 Creando usuario admin para empresa existente...")
            usuario_data = {
                'chat_id': admin_chat_id,
                'empresa_id': empresa_id,
                'nombre': nombre_admin,
                'rol': 'admin',
                'activo': True
            }
            
            usuario_response = supabase.table('usuarios').insert(usuario_data).execute()
            
            if usuario_response.data:
                print(f"   ✅ Usuario admin creado: {usuario_response.data[0]['id']}")
                print()
                print("="*80)
                print("✅ USUARIO ADMIN CREADO EXITOSAMENTE")
                print("="*80)
                print(f"   • ID Empresa: {empresa_id}")
                print(f"   • Admin Chat ID: {admin_chat_id}")
                return True
            else:
                print("   ❌ Error al crear usuario admin")
                return False
        
        # 1. Crear empresa
        empresa_data = {
            'rut': rut,
            'nombre': nombre,
            'activo': True
        }
        
        empresa_response = supabase.table('empresas').insert(empresa_data).execute()
        
        if not empresa_response.data:
            print("❌ Error: No se pudo crear la empresa")
            return False
        
        empresa_id = empresa_response.data[0]['id']
        print(f"   ✅ Empresa creada: {empresa_id}")
        
        # 2. Crear usuario admin
        usuario_data = {
            'chat_id': admin_chat_id,
            'empresa_id': empresa_id,
            'nombre': nombre_admin,
            'rol': 'admin',
            'activo': True
        }
        
        usuario_response = supabase.table('usuarios').insert(usuario_data).execute()
        
        if not usuario_response.data:
            print("   ⚠️  Empresa creada pero error al crear usuario admin")
            print(f"   💡 Puedes crear el usuario manualmente con: /adduser {admin_chat_id} {empresa_id}")
            return False
        
        print(f"   ✅ Usuario admin creado: {usuario_response.data[0]['id']}")
        
        # 3. Registrar evento de seguridad
        try:
            security.log_security_event(
                admin_chat_id,
                "empresa_creada",
                f"Empresa {nombre} (ID: {empresa_id}) creada mediante script"
            )
            print("   ✅ Evento registrado en security_logs")
        except Exception as e:
            print(f"   ⚠️  No se pudo registrar evento de seguridad: {e}")
        
        print()
        print("="*80)
        print("✅ EMPRESA CREADA EXITOSAMENTE")
        print("="*80)
        print()
        print(f"📋 Información:")
        print(f"   • ID Empresa: {empresa_id}")
        print(f"   • Nombre: {nombre}")
        print(f"   • RUT: {rut}")
        print(f"   • Admin Chat ID: {admin_chat_id}")
        print(f"   • Nombre Admin: {nombre_admin}")
        print()
        print("💡 La empresa ya puede usar el bot de producción")
        print("="*80)
        
        return True
        
    except Exception as e:
        print(f"❌ Error creando empresa: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    # Leer argumentos de línea de comandos
    if len(sys.argv) < 3:
        print("="*80)
        print("🏢 CREAR EMPRESA FACTORIT")
        print("="*80)
        print()
        print("📝 Uso:")
        print("   python crear_empresa_factorit.py RUT ADMIN_CHAT_ID [NOMBRE] [NOMBRE_ADMIN]")
        print()
        print("📋 Ejemplos:")
        print("   python crear_empresa_factorit.py 12345678-9 123456789")
        print("   python crear_empresa_factorit.py 12345678-9 123456789 FactorIT")
        print("   python crear_empresa_factorit.py 12345678-9 123456789 FactorIT 'Juan Pérez'")
        print()
        print("💡 Parámetros:")
        print("   • RUT: RUT de la empresa (requerido)")
        print("   • ADMIN_CHAT_ID: Chat ID de Telegram del administrador (requerido)")
        print("   • NOMBRE: Nombre de la empresa (opcional, default: FactorIT)")
        print("   • NOMBRE_ADMIN: Nombre del administrador (opcional, default: Administrador)")
        print()
        sys.exit(1)
    
    rut = sys.argv[1]
    admin_chat_id = sys.argv[2]
    nombre = sys.argv[3] if len(sys.argv) > 3 else "FactorIT"
    nombre_admin = sys.argv[4] if len(sys.argv) > 4 else "Administrador"
    
    success = crear_empresa_factorit(rut, nombre, admin_chat_id, nombre_admin)
    sys.exit(0 if success else 1)
