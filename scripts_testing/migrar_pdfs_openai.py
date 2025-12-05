"""
📤 Script para migrar PDFs existentes a OpenAI Assistants
Ejecutar una vez para procesar los PDFs ya subidos a Supabase
"""

import asyncio
import os
import sys
from pathlib import Path

# Agregar el directorio raíz al path
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
load_dotenv()

from app.database.supabase import get_supabase_client
from app.services.openai_assistant_service import get_assistant_service
from app.services.storage_service import get_storage_service


async def migrar_pdfs():
    """Migrar todos los PDFs existentes a OpenAI"""
    
    print("🚀 Iniciando migración de PDFs a OpenAI...")
    print("=" * 60)
    
    supabase = get_supabase_client()
    assistant_service = get_assistant_service()
    storage_service = get_storage_service()
    
    # Obtener todos los archivos PDF sin openai_file_id
    result = supabase.table('archivos')\
        .select('id, nombre_original, nombre_archivo, empresa_id, url_archivo, storage_path')\
        .is_('openai_file_id', 'null')\
        .eq('activo', True)\
        .execute()
    
    archivos = result.data or []
    
    # Filtrar solo PDFs
    pdfs = [a for a in archivos if (a.get('nombre_original') or a.get('nombre_archivo', '')).lower().endswith('.pdf')]
    
    print(f"📁 Encontrados {len(pdfs)} PDFs para migrar")
    print()
    
    if not pdfs:
        print("✅ No hay PDFs pendientes de migrar")
        return
    
    # Agrupar por empresa
    empresas = {}
    for pdf in pdfs:
        emp_id = pdf['empresa_id']
        if emp_id not in empresas:
            empresas[emp_id] = []
        empresas[emp_id].append(pdf)
    
    print(f"🏢 PDFs distribuidos en {len(empresas)} empresa(s)")
    print()
    
    # Procesar cada empresa
    for empresa_id, archivos_empresa in empresas.items():
        # Obtener nombre de empresa
        empresa = supabase.table('empresas').select('nombre').eq('id', empresa_id).execute()
        empresa_nombre = empresa.data[0]['nombre'] if empresa.data else 'Desconocida'
        
        print(f"📂 Procesando empresa: {empresa_nombre}")
        print(f"   {len(archivos_empresa)} PDF(s) a migrar")
        
        # Crear o obtener Assistant para la empresa
        assistant_id = await assistant_service.get_or_create_assistant(empresa_id, empresa_nombre)
        
        if not assistant_id:
            print(f"   ❌ No se pudo crear Assistant para {empresa_nombre}")
            continue
        
        print(f"   ✅ Assistant: {assistant_id}")
        
        # Procesar cada PDF
        for pdf in archivos_empresa:
            nombre = pdf.get('nombre_original') or pdf.get('nombre_archivo', 'Sin nombre')
            print(f"   📄 Procesando: {nombre}...", end=" ")
            
            try:
                # Descargar archivo de Supabase Storage usando el ID
                archivo_id = pdf.get('id')
                if not archivo_id:
                    print("⚠️ Sin ID")
                    continue
                
                # Obtener bytes del archivo
                file_bytes = await storage_service.download_file(archivo_id)
                
                if not file_bytes:
                    print("⚠️ No se pudo descargar")
                    continue
                
                # Subir a OpenAI
                file_id = await assistant_service.upload_file_to_openai(
                    file_bytes=file_bytes,
                    filename=nombre,
                    empresa_id=empresa_id,
                    archivo_id=pdf['id']
                )
                
                if file_id:
                    print(f"✅ {file_id}")
                else:
                    print("❌ Error al subir")
                    
            except Exception as e:
                print(f"❌ Error: {e}")
        
        print()
    
    print("=" * 60)
    print("✅ Migración completada")
    
    # Resumen final
    migrados = supabase.table('archivos')\
        .select('id', count='exact')\
        .not_.is_('openai_file_id', 'null')\
        .execute()
    
    print(f"📊 Total PDFs en OpenAI: {migrados.count or 0}")


async def verificar_estado():
    """Verificar estado actual de la migración"""
    
    print("📊 Estado de migración de PDFs")
    print("=" * 60)
    
    supabase = get_supabase_client()
    
    # Total de archivos
    total = supabase.table('archivos')\
        .select('id', count='exact')\
        .eq('activo', True)\
        .execute()
    
    # PDFs totales
    all_files = supabase.table('archivos')\
        .select('nombre_original, nombre_archivo')\
        .eq('activo', True)\
        .execute()
    
    pdfs_total = len([f for f in (all_files.data or []) 
                      if (f.get('nombre_original') or f.get('nombre_archivo', '')).lower().endswith('.pdf')])
    
    # PDFs migrados
    migrados = supabase.table('archivos')\
        .select('id', count='exact')\
        .not_.is_('openai_file_id', 'null')\
        .execute()
    
    # Empresas con Assistant
    empresas_con_assistant = supabase.table('empresas')\
        .select('id', count='exact')\
        .not_.is_('openai_assistant_id', 'null')\
        .execute()
    
    print(f"📁 Total archivos activos: {total.count or 0}")
    print(f"📄 PDFs totales: {pdfs_total}")
    print(f"✅ PDFs migrados a OpenAI: {migrados.count or 0}")
    print(f"⏳ PDFs pendientes: {pdfs_total - (migrados.count or 0)}")
    print(f"🏢 Empresas con Assistant: {empresas_con_assistant.count or 0}")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Migrar PDFs a OpenAI Assistants')
    parser.add_argument('--verificar', action='store_true', help='Solo verificar estado')
    args = parser.parse_args()
    
    if args.verificar:
        asyncio.run(verificar_estado())
    else:
        asyncio.run(migrar_pdfs())

