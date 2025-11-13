"""
📁 Tipos de Archivo - Estructura Jerárquica
Define las categorías y subtipos de archivos para clasificación
"""

# ============================================
# ESTRUCTURA JERÁRQUICA DE TIPOS DE ARCHIVO
# ============================================

TIPOS_ARCHIVO = {
    'legal': {
        'nombre': '⚖️ Legales',
        'icon': '⚖️',
        'subtipos': {
            'estatutos_empresa': {
                'nombre': 'Estatutos empresa',
                'icon': '📜'
            },
            'poderes': {
                'nombre': 'Poderes',
                'icon': '📋'
            },
            'ci': {
                'nombre': 'CI',
                'icon': '🆔'
            },
            'rut': {
                'nombre': 'RUT',
                'icon': '🆔'
            },
            'otros': {
                'nombre': 'Otros',
                'icon': '🗃️',
                'requiere_descripcion': True
            }
        }
    },
    'financiero': {
        'nombre': '💰 Financieros',
        'icon': '💰',
        'subtipos': {
            'reporte_mensual': {
                'nombre': 'Reporte mensual',
                'icon': '📊'
            },
            'estados_financieros': {
                'nombre': 'Estados financieros',
                'icon': '📈'
            },
            'carpeta_tributaria': {
                'nombre': 'Carpeta tributaria',
                'icon': '📁'
            },
            'f29': {
                'nombre': 'F29',
                'icon': '📄'
            },
            'f22': {
                'nombre': 'F22',
                'icon': '📄'
            },
            'otros': {
                'nombre': 'Otros',
                'icon': '🗃️',
                'requiere_descripcion': True
            }
        }
    }
}

# ============================================
# FUNCIONES HELPER
# ============================================

def get_categorias():
    """Obtener lista de categorías disponibles"""
    return list(TIPOS_ARCHIVO.keys())

def get_categoria_nombre(categoria: str) -> str:
    """Obtener nombre legible de una categoría"""
    return TIPOS_ARCHIVO.get(categoria, {}).get('nombre', categoria)

def get_subtipos(categoria: str) -> dict:
    """Obtener subtipos de una categoría"""
    return TIPOS_ARCHIVO.get(categoria, {}).get('subtipos', {})

def get_subtipo_nombre(categoria: str, subtipo: str) -> str:
    """Obtener nombre legible de un subtipo"""
    subtipos = get_subtipos(categoria)
    return subtipos.get(subtipo, {}).get('nombre', subtipo)

def requiere_descripcion(categoria: str, subtipo: str) -> bool:
    """Verificar si un subtipo requiere descripción personalizada"""
    subtipos = get_subtipos(categoria)
    return subtipos.get(subtipo, {}).get('requiere_descripcion', False)

def get_subtipo_icon(categoria: str, subtipo: str) -> str:
    """Obtener icono de un subtipo"""
    subtipos = get_subtipos(categoria)
    return subtipos.get(subtipo, {}).get('icon', '📄')

def validar_categoria(categoria: str) -> bool:
    """Validar que una categoría existe"""
    return categoria in TIPOS_ARCHIVO

def validar_subtipo(categoria: str, subtipo: str) -> bool:
    """Validar que un subtipo existe en una categoría"""
    if not validar_categoria(categoria):
        return False
    subtipos = get_subtipos(categoria)
    return subtipo in subtipos

def get_todos_subtipos() -> dict:
    """Obtener todos los subtipos organizados por categoría"""
    resultado = {}
    for categoria, datos in TIPOS_ARCHIVO.items():
        resultado[categoria] = {
            'nombre': datos['nombre'],
            'icon': datos['icon'],
            'subtipos': list(datos['subtipos'].keys())
        }
    return resultado

# ============================================
# CONSTANTES PARA BOTONES DE TELEGRAM
# ============================================

def get_botones_categorias():
    """Obtener botones para seleccionar categoría (en formato 2 columnas)"""
    botones = []
    for categoria, datos in TIPOS_ARCHIVO.items():
        botones.append({
            'text': f"{datos['icon']} {datos['nombre']}",
            'callback_data': f"categoria_{categoria}"
        })
    return botones

def get_botones_subtipos(categoria: str):
    """Obtener botones para seleccionar subtipo de una categoría (en formato 2 columnas)"""
    subtipos = get_subtipos(categoria)
    botones = []
    
    for subtipo_key, subtipo_data in subtipos.items():
        botones.append({
            'text': f"{subtipo_data['icon']} {subtipo_data['nombre']}",
            'callback_data': f"subtipo_{categoria}_{subtipo_key}"
        })
    
    return botones

def organizar_botones_en_columnas(botones: list, columnas: int = 2) -> list:
    """Organizar botones en filas de N columnas"""
    keyboard = []
    for i in range(0, len(botones), columnas):
        fila = botones[i:i+columnas]
        keyboard.append(fila)
    return keyboard

# ============================================
# VALIDACIÓN Y NORMALIZACIÓN
# ============================================

def normalizar_categoria(categoria: str) -> str:
    """Normalizar nombre de categoría (case-insensitive)"""
    categoria_lower = categoria.lower()
    for cat_key in TIPOS_ARCHIVO.keys():
        if cat_key.lower() == categoria_lower:
            return cat_key
    return categoria

def normalizar_subtipo(categoria: str, subtipo: str) -> str:
    """Normalizar nombre de subtipo (case-insensitive)"""
    subtipos = get_subtipos(categoria)
    subtipo_lower = subtipo.lower()
    
    for subtipo_key, subtipo_data in subtipos.items():
        if subtipo_key.lower() == subtipo_lower:
            return subtipo_key
        if subtipo_data['nombre'].lower() == subtipo_lower:
            return subtipo_key
    
    return subtipo

