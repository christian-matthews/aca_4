#!/usr/bin/env python3
"""
🔍 Diagnosticar problema con comando /crear_empresa
"""

from app.config import Config
from app.security.auth import security
from app.database.supabase import get_supabase_client

print("="*80)
print("🔍 DIAGNÓSTICO DEL COMANDO /crear_empresa")
print("="*80)
print()

# 1. Verificar configuración
print("1️⃣ CONFIGURACIÓN:")
print(f"   • ADMIN_CHAT_ID configurado: {Config.ADMIN_CHAT_ID}")
print(f"   • BOT_ADMIN_TOKEN configurado: {'✅ Sí' if Config.BOT_ADMIN_TOKEN else '❌ No'}")
print()

# 2. Verificar permisos
print("2️⃣ PERMISOS DE ADMIN:")
if Config.ADMIN_CHAT_ID:
    print(f"   • Chat ID configurado: {Config.ADMIN_CHAT_ID}")
    print(f"   • Es admin: {security.is_admin(Config.ADMIN_CHAT_ID)}")
    print(f"   • Admin chat IDs permitidos: {security.admin_chat_ids}")
else:
    print("   ⚠️  ADMIN_CHAT_ID no está configurado")
print()

# 3. Verificar conexión a Supabase
print("3️⃣ CONEXIÓN A SUPABASE:")
try:
    supabase = get_supabase_client()
    # Intentar una consulta simple
    result = supabase.table('empresas').select('id').limit(1).execute()
    print("   ✅ Conexión exitosa")
    print(f"   • Empresas existentes: {len(result.data) if result.data else 0}")
except Exception as e:
    print(f"   ❌ Error de conexión: {e}")
print()

# 4. Verificar función create_empresa
print("4️⃣ FUNCIÓN create_empresa:")
try:
    from app.database.supabase import supabase
    # Verificar que el método existe
    if hasattr(supabase, 'create_empresa'):
        print("   ✅ Método create_empresa existe")
    else:
        print("   ❌ Método create_empresa NO existe")
except Exception as e:
    print(f"   ❌ Error: {e}")
print()

# 5. Verificar handler registrado
print("5️⃣ HANDLER DEL COMANDO:")
try:
    from app.bots.bot_manager import bot_manager
    if bot_manager.admin_app:
        handlers = bot_manager.admin_app.handlers[0] if bot_manager.admin_app.handlers else []
        crear_empresa_registrado = any(
            hasattr(h, 'callback') and 'crear_empresa' in str(h.callback)
            for h in handlers
        )
        print(f"   • Bot admin inicializado: ✅")
        print(f"   • Handler crear_empresa registrado: {'✅' if crear_empresa_registrado else '❌'}")
    else:
        print("   ⚠️  Bot admin no está inicializado")
except Exception as e:
    print(f"   ❌ Error: {e}")
print()

print("="*80)
print("💡 RECOMENDACIONES:")
print("="*80)
print()
if not Config.ADMIN_CHAT_ID:
    print("   ⚠️  Configura ADMIN_CHAT_ID en el archivo .env")
    print()
if Config.ADMIN_CHAT_ID and not security.is_admin(Config.ADMIN_CHAT_ID):
    print(f"   ⚠️  Tu chat_id ({Config.ADMIN_CHAT_ID}) no está en la lista de admins")
    print(f"   • Admins permitidos: {security.admin_chat_ids}")
    print()
print("   💡 Si el comando no funciona, puedes crear la empresa con un script Python")
print("="*80)







