import logging
from datetime import datetime
import re

logger = logging.getLogger(__name__)

def setup_logging():
    """Configurar logging para la aplicación"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('aca_bot.log'),
            logging.StreamHandler()
        ]
    )

def validate_rut(rut: str) -> bool:
    """
    Validar formato de RUT chileno
    Args:
        rut: RUT a validar
    Returns:
        bool: True si es válido, False en caso contrario
    """
    try:
        # Limpiar RUT
        rut = rut.replace('.', '').replace('-', '').upper()
        
        if len(rut) < 2:
            return False
        
        # Separar número y dígito verificador
        numero = rut[:-1]
        dv = rut[-1]
        
        # Validar que el número sea numérico
        if not numero.isdigit():
            return False
        
        # Calcular dígito verificador
        suma = 0
        multiplicador = 2
        
        for digito in reversed(numero):
            suma += int(digito) * multiplicador
            multiplicador = multiplicador + 1 if multiplicador < 7 else 2
        
        resto = suma % 11
        dv_calculado = 11 - resto if resto != 0 else 0
        
        if dv_calculado == 10:
            dv_calculado = 'K'
        else:
            dv_calculado = str(dv_calculado)
        
        return dv == dv_calculado
        
    except Exception as e:
        logger.error(f"Error validando RUT {rut}: {e}")
        return False

def format_currency(amount: float) -> str:
    """
    Formatear cantidad como moneda chilena
    Args:
        amount: Cantidad a formatear
    Returns:
        str: Cantidad formateada
    """
    try:
        return f"${amount:,.0f}"
    except:
        return str(amount)

def format_date(date_str: str) -> str:
    """
    Formatear fecha para mostrar
    Args:
        date_str: Fecha en formato string
    Returns:
        str: Fecha formateada
    """
    try:
        if 'T' in date_str:
            # Formato ISO
            dt = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
            return dt.strftime('%d/%m/%Y %H:%M')
        else:
            # Solo fecha
            dt = datetime.fromisoformat(date_str)
            return dt.strftime('%d/%m/%Y')
    except:
        return date_str

def sanitize_text(text: str) -> str:
    """
    Sanitizar texto para evitar inyección de código
    Args:
        text: Texto a sanitizar
    Returns:
        str: Texto sanitizado
    """
    if not text:
        return ""
    
    # Remover caracteres peligrosos
    dangerous_chars = ['<', '>', '&', '"', "'"]
    for char in dangerous_chars:
        text = text.replace(char, '')
    
    # Limitar longitud
    if len(text) > 1000:
        text = text[:1000] + "..."
    
    return text.strip()

def extract_chat_id_from_text(text: str) -> int:
    """
    Extraer chat_id de un texto
    Args:
        text: Texto que puede contener un chat_id
    Returns:
        int: Chat ID encontrado o None
    """
    try:
        # Buscar números en el texto
        numbers = re.findall(r'\d+', text)
        if numbers:
            return int(numbers[-1])  # Tomar el último número encontrado
    except:
        pass
    return None

def truncate_text(text: str, max_length: int = 100) -> str:
    """
    Truncar texto a una longitud máxima
    Args:
        text: Texto a truncar
        max_length: Longitud máxima
    Returns:
        str: Texto truncado
    """
    if len(text) <= max_length:
        return text
    return text[:max_length-3] + "..."

def is_valid_email(email: str) -> bool:
    """
    Validar formato de email
    Args:
        email: Email a validar
    Returns:
        bool: True si es válido
    """
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email)) 