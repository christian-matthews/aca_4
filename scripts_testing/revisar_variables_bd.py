#!/usr/bin/env python3
"""
🔍 Script para revisar variables de BD usadas en código vs estructura real
"""

import sys
import re
from pathlib import Path
from collections import defaultdict

sys.path.insert(0, str(Path(__file__).parent))

from app.database.supabase import get_supabase_client

def obtener_campos_reales_supabase():
    """Obtener campos reales de las tablas en Supabase"""
    supabase = get_supabase_client()
    
    tablas = {
        'archivos': {},
        'sesiones_conversacion': {},
        'usuarios': {},
        'empresas': {}
    }
    
    for tabla in tablas.keys():
        try:
            result = supabase.table(tabla).select('*').limit(1).execute()
            if result.data and len(result.data) > 0:
                for campo in result.data[0].keys():
                    tipo_python = type(result.data[0][campo]).__name__
                    tablas[tabla][campo] = tipo_python
        except Exception as e:
            print(f"⚠️ Error obteniendo campos de {tabla}: {e}")
    
    return tablas

def buscar_uso_campos_en_codigo():
    """Buscar qué campos se usan en el código"""
    uso_campos = defaultdict(set)
    
    archivos_python = list(Path('app').rglob('*.py'))
    
    for archivo in archivos_python:
        try:
            contenido = archivo.read_text(encoding='utf-8')
            
            # Buscar referencias a tablas
            if 'archivos' in contenido.lower():
                # Buscar campos específicos
                campos_archivos = [
                    'tipo_archivo', 'mime_type', 'periodo', 'categoria', 
                    'tipo', 'subtipo', 'descripcion_personalizada',
                    'usuario_subio_id', 'fecha_documento'
                ]
                
                for campo in campos_archivos:
                    if campo in contenido:
                        uso_campos['archivos'].add((campo, str(archivo)))
            
            if 'sesiones_conversacion' in contenido.lower():
                campos_sesiones = [
                    'chat_id', 'estado', 'intent', 'data', 
                    'archivo_temp_id', 'expires_at'
                ]
                for campo in campos_sesiones:
                    if campo in contenido:
                        uso_campos['sesiones_conversacion'].add((campo, str(archivo)))
                        
        except Exception as e:
            pass
    
    return uso_campos

def analizar_storage_service():
    """Analizar específicamente storage_service.py"""
    archivo = Path('app/services/storage_service.py')
    
    if not archivo.exists():
        return {}
    
    contenido = archivo.read_text(encoding='utf-8')
    
    problemas = []
    
    # Buscar uso de 'tipo_archivo' (debe ser 'mime_type')
    if "'tipo_archivo'" in contenido or '"tipo_archivo"' in contenido:
        problemas.append({
            'tipo': 'campo_obsoleto',
            'campo': 'tipo_archivo',
            'debe_ser': 'mime_type',
            'archivo': 'app/services/storage_service.py',
            'linea': contenido.split("'tipo_archivo'")[0].count('\n') + 1 if "'tipo_archivo'" in contenido else None
        })
    
    # Buscar campos que deberían estar pero no están
    campos_requeridos = ['periodo', 'categoria', 'tipo', 'subtipo', 'descripcion_personalizada']
    campos_faltantes = []
    
    for campo in campos_requeridos:
        if campo not in contenido:
            campos_faltantes.append(campo)
    
    if campos_faltantes:
        problemas.append({
            'tipo': 'campos_faltantes',
            'campos': campos_faltantes,
            'archivo': 'app/services/storage_service.py'
        })
    
    return problemas

def main():
    print("\n" + "="*80)
    print("🔍 REVISIÓN: Variables de BD en Código vs Supabase")
    print("="*80)
    
    # 1. Obtener estructura real de Supabase
    print("\n📊 Obteniendo estructura real de Supabase...")
    campos_reales = obtener_campos_reales_supabase()
    
    # 2. Analizar uso en código
    print("📝 Analizando uso en código...")
    uso_codigo = buscar_uso_campos_en_codigo()
    
    # 3. Analizar storage_service específicamente
    print("🔍 Analizando storage_service.py...")
    problemas_storage = analizar_storage_service()
    
    # 4. Reporte
    print("\n" + "="*80)
    print("📋 REPORTE DE INCONSISTENCIAS")
    print("="*80)
    
    # Tabla archivos
    print("\n📁 TABLA: archivos")
    print("-" * 80)
    
    campos_reales_archivos = set(campos_reales.get('archivos', {}).keys())
    print(f"\n✅ Campos en Supabase ({len(campos_reales_archivos)}):")
    for campo in sorted(campos_reales_archivos):
        print(f"  • {campo}")
    
    # Problemas encontrados
    print("\n⚠️ PROBLEMAS ENCONTRADOS:")
    
    if problemas_storage:
        for problema in problemas_storage:
            if problema['tipo'] == 'campo_obsoleto':
                print(f"\n  ❌ {problema['archivo']}")
                print(f"     Usa campo obsoleto: '{problema['campo']}'")
                print(f"     Debe usar: '{problema['debe_ser']}'")
                if problema.get('linea'):
                    print(f"     Línea aproximada: {problema['linea']}")
            
            elif problema['tipo'] == 'campos_faltantes':
                print(f"\n  ⚠️  {problema['archivo']}")
                print(f"     No usa campos nuevos: {', '.join(problema['campos'])}")
    
    # Verificar uso de campos en código
    print("\n📝 Campos usados en código:")
    if 'archivos' in uso_codigo:
        campos_usados = {campo for campo, _ in uso_codigo['archivos']}
        print(f"  Campos encontrados: {', '.join(sorted(campos_usados))}")
        
        # Verificar si usa campos obsoletos
        if 'tipo_archivo' in campos_usados:
            print(f"\n  ❌ PROBLEMA: Código usa 'tipo_archivo' (obsoleto)")
            print(f"     Archivos afectados:")
            for campo, archivo in uso_codigo['archivos']:
                if campo == 'tipo_archivo':
                    print(f"       - {archivo}")
    
    # Resumen
    print("\n" + "="*80)
    print("📊 RESUMEN")
    print("="*80)
    
    if problemas_storage:
        print("\n❌ Se encontraron problemas que deben corregirse:")
        print("   1. storage_service.py usa 'tipo_archivo' → debe usar 'mime_type'")
        print("   2. storage_service.py no incluye campos nuevos en upload_file()")
    else:
        print("\n✅ No se encontraron problemas críticos")
    
    print("\n" + "="*80)

if __name__ == "__main__":
    main()


