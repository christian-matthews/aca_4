#!/usr/bin/env python3
"""
Script para verificar archivos subidos en Supabase
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from app.database.supabase import get_supabase_client
from datetime import datetime

def verificar_archivos():
    """Verificar archivos en la base de datos"""
    try:
        supabase = get_supabase_client()
        
        print("🔍 Verificando archivos en la base de datos...\n")
        
        # Obtener todos los archivos activos
        result = supabase.table('archivos')\
            .select('*')\
            .eq('activo', True)\
            .order('created_at', desc=True)\
            .limit(20)\
            .execute()
        
        if not result.data:
            print("❌ No se encontraron archivos en la base de datos")
            print("\n💡 Esto puede significar:")
            print("   - Aún no se ha subido ningún archivo")
            print("   - Los archivos están marcados como inactivos")
            print("   - Hay un problema con la conexión a la base de datos")
            return
        
        print(f"✅ Se encontraron {len(result.data)} archivo(s):\n")
        print("=" * 80)
        
        for i, archivo in enumerate(result.data, 1):
            print(f"\n📄 Archivo #{i}")
            print(f"   ID: {archivo.get('id')}")
            print(f"   Nombre: {archivo.get('nombre_archivo', 'N/A')}")
            print(f"   Chat ID: {archivo.get('chat_id')}")
            print(f"   Empresa ID: {archivo.get('empresa_id', 'N/A')}")
            print(f"   Categoría: {archivo.get('categoria', 'N/A')}")
            print(f"   Subtipo: {archivo.get('subtipo', 'N/A')}")
            print(f"   Período: {archivo.get('periodo', 'N/A')}")
            print(f"   Tamaño: {archivo.get('tamaño_bytes', 0):,} bytes")
            print(f"   MIME Type: {archivo.get('mime_type', 'N/A')}")
            print(f"   Storage Path: {archivo.get('storage_path', 'N/A')}")
            print(f"   URL: {archivo.get('url_archivo', 'N/A')[:80]}..." if archivo.get('url_archivo') else "   URL: N/A")
            print(f"   Creado: {archivo.get('created_at', 'N/A')}")
            if archivo.get('descripcion_personalizada'):
                print(f"   Descripción: {archivo.get('descripcion_personalizada')}")
            print("-" * 80)
        
        # Estadísticas
        print("\n📊 Estadísticas:")
        
        # Por categoría
        categorias = {}
        for archivo in result.data:
            cat = archivo.get('categoria', 'Sin categoría')
            categorias[cat] = categorias.get(cat, 0) + 1
        
        print("   Por categoría:")
        for cat, count in categorias.items():
            print(f"      {cat}: {count}")
        
        # Por período
        periodos = {}
        for archivo in result.data:
            periodo = archivo.get('periodo', 'Sin período')
            periodos[periodo] = periodos.get(periodo, 0) + 1
        
        print("\n   Por período:")
        for periodo, count in sorted(periodos.items()):
            print(f"      {periodo}: {count}")
        
        # Verificar Storage
        print("\n🔍 Verificando Storage...")
        try:
            storage_result = supabase.client.storage.from_('archivos-bot').list()
            if storage_result:
                print(f"   ✅ Storage accesible")
                print(f"   📁 Archivos en Storage: {len(storage_result)}")
            else:
                print("   ⚠️  No se encontraron archivos en Storage")
        except Exception as e:
            print(f"   ⚠️  Error accediendo a Storage: {e}")
        
    except Exception as e:
        print(f"❌ Error verificando archivos: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    verificar_archivos()


