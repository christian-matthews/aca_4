#!/usr/bin/env python3
"""
🔍 Script para revisar estructura completa de Supabase
Lista todas las tablas, campos, índices, funciones y vistas
"""

import sys
from pathlib import Path

# Agregar el directorio raíz al path
sys.path.insert(0, str(Path(__file__).parent))

from app.database.supabase import get_supabase_client
from app.config import Config
import json

def revisar_tablas(supabase):
    """Revisar todas las tablas y sus campos"""
    print("\n" + "="*80)
    print("📊 TABLAS Y CAMPOS")
    print("="*80)
    
    # Lista de tablas conocidas del proyecto
    tablas_conocidas = [
        'empresas',
        'usuarios',
        'conversaciones',
        'usuarios_detalle',
        'intentos_acceso_negado',
        'security_logs',
        'bot_analytics',
        'archivos',
        'sesiones_conversacion'  # Puede que no exista aún
    ]
    
    resultados = {}
    
    for tabla in tablas_conocidas:
        try:
            # Intentar obtener estructura de la tabla
            # Usamos una consulta simple para verificar que existe
            result = supabase.table(tabla).select('*').limit(1).execute()
            
            print(f"\n✅ Tabla: {tabla}")
            print("-" * 80)
            
            # Obtener información de columnas usando RPC o consulta directa
            # Nota: Supabase Python client no tiene método directo para obtener schema
            # Usaremos una consulta de información del sistema vía SQL si es posible
            
            # Por ahora, intentamos inferir de los datos
            if result.data and len(result.data) > 0:
                print("Campos detectados (de muestra de datos):")
                for campo, valor in result.data[0].items():
                    tipo_valor = type(valor).__name__
                    print(f"  • {campo:30s} : {tipo_valor:15s} (ejemplo: {str(valor)[:50]})")
            else:
                print("  ⚠️  Tabla vacía - no se pueden inferir campos")
            
            resultados[tabla] = True
            
        except Exception as e:
            error_msg = str(e)
            if 'relation' in error_msg.lower() or 'does not exist' in error_msg.lower():
                print(f"\n❌ Tabla: {tabla} - NO EXISTE")
                resultados[tabla] = False
            else:
                print(f"\n⚠️  Tabla: {tabla} - Error: {error_msg[:100]}")
                resultados[tabla] = None
    
    return resultados

def revisar_tabla_archivos_detallado(supabase):
    """Revisar tabla archivos en detalle"""
    print("\n" + "="*80)
    print("📁 TABLA ARCHIVOS - ANÁLISIS DETALLADO")
    print("="*80)
    
    try:
        # Intentar obtener un registro
        result = supabase.table('archivos').select('*').limit(1).execute()
        
        if result.data and len(result.data) > 0:
            print("\n✅ Tabla archivos existe")
            print("\nCampos actuales:")
            print("-" * 80)
            
            registro = result.data[0]
            campos_actuales = {}
            
            for campo, valor in registro.items():
                tipo_python = type(valor).__name__
                # Inferir tipo SQL aproximado
                if tipo_python == 'str':
                    tipo_sql = 'VARCHAR/TEXT'
                elif tipo_python == 'int':
                    tipo_sql = 'INTEGER/BIGINT'
                elif tipo_python == 'bool':
                    tipo_sql = 'BOOLEAN'
                elif tipo_python == 'dict':
                    tipo_sql = 'JSONB'
                else:
                    tipo_sql = tipo_python.upper()
                
                campos_actuales[campo] = tipo_sql
                print(f"  • {campo:30s} : {tipo_sql:20s}")
            
            # Verificar campos que necesitamos
            print("\n" + "-" * 80)
            print("Verificación de campos requeridos:")
            print("-" * 80)
            
            campos_requeridos = {
                'periodo': 'VARCHAR(7)',
                'categoria': 'VARCHAR(50)',
                'tipo': 'VARCHAR(50)',
                'subtipo': 'VARCHAR(100)',
                'descripcion_personalizada': 'TEXT',
                'mime_type': 'VARCHAR(100)',  # Renombrado de tipo_archivo
                'usuario_subio_id': 'UUID',
                'fecha_documento': 'DATE'
            }
            
            campos_existentes = set(campos_actuales.keys())
            campos_necesarios = set(campos_requeridos.keys())
            
            # Campos que faltan
            faltantes = campos_necesarios - campos_existentes
            if faltantes:
                print("\n❌ Campos FALTANTES:")
                for campo in faltantes:
                    print(f"  • {campo:30s} : {campos_requeridos[campo]}")
            else:
                print("\n✅ Todos los campos requeridos existen")
            
            # Campos que existen pero tienen nombre diferente
            if 'tipo_archivo' in campos_existentes and 'mime_type' not in campos_existentes:
                print("\n⚠️  Campo 'tipo_archivo' existe - necesita renombrarse a 'mime_type'")
            
            # Campos que ya existen
            existentes = campos_necesarios & campos_existentes
            if existentes:
                print("\n✅ Campos que YA EXISTEN:")
                for campo in existentes:
                    print(f"  • {campo:30s} : {campos_actuales[campo]}")
            
            return campos_actuales, campos_requeridos
            
        else:
            print("\n⚠️  Tabla archivos existe pero está vacía")
            print("No se pueden inferir campos desde datos")
            return {}, {}
            
    except Exception as e:
        print(f"\n❌ Error revisando tabla archivos: {e}")
        return {}, {}

def revisar_indices(supabase):
    """Intentar revisar índices (limitado con Supabase client)"""
    print("\n" + "="*80)
    print("🔍 ÍNDICES")
    print("="*80)
    print("\n⚠️  Nota: El cliente Python de Supabase no expone información de índices")
    print("Revisa los índices directamente en Supabase Dashboard > Database > Indexes")

def generar_reporte_completo(supabase):
    """Generar reporte completo"""
    print("\n" + "🔍"*40)
    print("REVISIÓN COMPLETA DE ESTRUCTURA SUPABASE")
    print("🔍"*40)
    
    # Información de conexión
    print(f"\n📡 Conexión:")
    print(f"  URL: {Config.SUPABASE_URL[:50]}...")
    print(f"  Key: {'✅ Configurado' if Config.SUPABASE_KEY else '❌ Faltante'}")
    
    # Revisar tablas
    tablas = revisar_tablas(supabase)
    
    # Revisar tabla archivos en detalle
    campos_actuales, campos_requeridos = revisar_tabla_archivos_detallado(supabase)
    
    # Revisar índices
    revisar_indices(supabase)
    
    # Resumen
    print("\n" + "="*80)
    print("📊 RESUMEN")
    print("="*80)
    
    tablas_existentes = sum(1 for v in tablas.values() if v is True)
    tablas_faltantes = sum(1 for v in tablas.values() if v is False)
    
    print(f"\nTablas:")
    print(f"  ✅ Existentes: {tablas_existentes}")
    print(f"  ❌ Faltantes: {tablas_faltantes}")
    
    if campos_requeridos:
        campos_faltantes = len(set(campos_requeridos.keys()) - set(campos_actuales.keys()))
        print(f"\nCampos en tabla archivos:")
        print(f"  ✅ Existentes: {len(campos_actuales)}")
        print(f"  ❌ Faltantes: {campos_faltantes}")
    
    print("\n" + "="*80)
    print("\n💡 PRÓXIMOS PASOS:")
    print("  1. Revisa los campos faltantes en tabla archivos")
    print("  2. Ejecuta la migración SQL en Supabase")
    print("  3. Verifica que todos los campos se crearon correctamente")
    print("\n" + "="*80)

def main():
    """Función principal"""
    try:
        supabase = get_supabase_client()
        generar_reporte_completo(supabase)
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()


