#!/usr/bin/env python3
"""Verificar estructura de tabla sesiones_conversacion"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from app.database.supabase import get_supabase_client

def verificar_sesiones():
    supabase = get_supabase_client()
    
    print("🔍 Verificando tabla sesiones_conversacion...\n")
    
    try:
        # Intentar insertar un registro de prueba (luego lo eliminamos)
        test_data = {
            'chat_id': 999999999,
            'estado': 'idle',
            'intent': 'test',
            'data': {'test': True}
        }
        
        result = supabase.table('sesiones_conversacion').insert(test_data).execute()
        
        if result.data:
            print("✅ Tabla sesiones_conversacion existe y funciona correctamente")
            print("\n📋 Campos detectados:")
            print("-" * 60)
            for campo, valor in result.data[0].items():
                tipo = type(valor).__name__
                print(f"  • {campo:30s} : {tipo:15s}")
            
            # Eliminar registro de prueba
            supabase.table('sesiones_conversacion').delete().eq('chat_id', 999999999).execute()
            print("\n✅ Registro de prueba eliminado")
            
            return True
        else:
            print("⚠️ Tabla existe pero no se pudo insertar")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    verificar_sesiones()


