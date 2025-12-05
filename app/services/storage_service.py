"""
📁 Servicio de Almacenamiento de Archivos en Supabase Storage
Preparado para FASE 2 - Manejo de archivos desde bots de Telegram
"""

import logging
from typing import Optional, Dict, Any, BinaryIO
from app.database.supabase import get_supabase_client
from app.config import Config

logger = logging.getLogger(__name__)

class StorageService:
    """Servicio para gestionar archivos en Supabase Storage"""
    
    def __init__(self):
        self.supabase = get_supabase_client().client
        self.bucket_name = Config.SUPABASE_STORAGE_BUCKET
    
    async def upload_file(
        self,
        file_bytes: bytes,
        filename: str,
        chat_id: int,
        empresa_id: Optional[str] = None,
        categoria: Optional[str] = None,
        tipo: Optional[str] = None,
        subtipo: Optional[str] = None,
        periodo: Optional[str] = None,
        descripcion_personalizada: Optional[str] = None,
        usuario_subio_id: Optional[str] = None,
        folder: str = "uploads"
    ) -> Optional[Dict[str, Any]]:
        """
        Subir archivo a Supabase Storage
        
        Args:
            file_bytes: Contenido del archivo en bytes
            filename: Nombre del archivo
            chat_id: ID del chat de Telegram
            empresa_id: ID de la empresa (opcional)
            categoria: Categoría del archivo ('legal' o 'financiero')
            tipo: Tipo de archivo (categoría principal)
            subtipo: Subtipo específico (estatutos_empresa, f29, etc.)
            periodo: Período en formato YYYY-MM
            descripcion_personalizada: Descripción cuando subtipo es "Otros"
            usuario_subio_id: ID del usuario que subió el archivo
            folder: Carpeta dentro del bucket
        
        Returns:
            Diccionario con información del archivo subido o None si falla
        """
        try:
            # Sanitizar nombre de archivo para Storage
            safe_filename = self._sanitize_filename(filename)
            
            # Agregar timestamp para evitar duplicados
            from datetime import datetime
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            name, ext = safe_filename.rsplit('.', 1) if '.' in safe_filename else (safe_filename, '')
            unique_filename = f"{name}_{timestamp}.{ext}" if ext else f"{name}_{timestamp}"
            
            # Construir path del archivo
            file_path = f"{folder}/{chat_id}/{unique_filename}"
            
            # Subir archivo a Supabase Storage
            response = self.supabase.storage.from_(self.bucket_name).upload(
                path=file_path,
                file=file_bytes,
                file_options={"content-type": self._get_content_type(filename)}
            )
            
            if response:
                # Obtener URL pública del archivo
                url_response = self.supabase.storage.from_(self.bucket_name).get_public_url(file_path)
                
                # Guardar registro en base de datos con todos los campos
                archivo_data = {
                    'chat_id': chat_id,
                    'empresa_id': empresa_id,
                    'nombre_archivo': unique_filename,
                    'nombre_original': filename,
                    'mime_type': self._get_content_type(filename),  # ✅ Usar mime_type en lugar de tipo_archivo
                    'extension': self._get_extension(filename),
                    'tamaño_bytes': len(file_bytes),
                    'url_archivo': url_response,
                    'storage_provider': 'supabase',
                    'storage_path': file_path,
                    'activo': True
                }
                
                # Agregar campos de clasificación si están presentes
                if categoria:
                    archivo_data['categoria'] = categoria
                if tipo:
                    archivo_data['tipo'] = tipo
                if subtipo:
                    archivo_data['subtipo'] = subtipo
                if periodo:
                    archivo_data['periodo'] = periodo
                if descripcion_personalizada:
                    archivo_data['descripcion_personalizada'] = descripcion_personalizada
                if usuario_subio_id:
                    archivo_data['usuario_subio_id'] = usuario_subio_id
                
                result = self.supabase.table('archivos').insert(archivo_data).execute()
                
                if result.data:
                    logger.info(f"✅ Archivo {filename} subido exitosamente")
                    return result.data[0]
            
            return None
            
        except Exception as e:
            logger.error(f"❌ Error subiendo archivo {filename}: {e}")
            return None
    
    async def download_file(self, file_id: str) -> Optional[bytes]:
        """
        Descargar archivo desde Supabase Storage
        
        Args:
            file_id: ID del archivo en la tabla archivos
        
        Returns:
            Contenido del archivo en bytes o None si falla
        """
        try:
            # Obtener información del archivo
            file_info = self.supabase.table('archivos').select('*').eq('id', file_id).execute()
            
            if not file_info.data:
                return None
            
            file_data = file_info.data[0]
            storage_path = file_data.get('storage_path')
            
            if not storage_path:
                return None
            
            # Descargar archivo
            response = self.supabase.storage.from_(self.bucket_name).download(storage_path)
            
            return response
            
        except Exception as e:
            logger.error(f"❌ Error descargando archivo {file_id}: {e}")
            return None
    
    async def get_file_url(self, file_id: str, regenerate: bool = False) -> Optional[str]:
        """
        Obtener URL de un archivo (pública o firmada)
        
        Args:
            file_id: ID del archivo
            regenerate: Si True, regenera URL firmada incluso si existe
        
        Returns:
            URL del archivo o None
        """
        try:
            file_info = self.supabase.table('archivos').select('storage_path, url_archivo').eq('id', file_id).execute()
            
            if not file_info.data:
                return None
            
            file_data = file_info.data[0]
            storage_path = file_data.get('storage_path')
            
            if not storage_path:
                # Fallback a URL pública si existe
                return file_data.get('url_archivo')
            
            # Intentar generar URL firmada (válida por 1 hora)
            # Nota: El método puede variar según versión de supabase-py
            try:
                # Intentar método create_signed_url (versiones recientes)
                if hasattr(self.supabase.storage.from_(self.bucket_name), 'create_signed_url'):
                    signed_response = self.supabase.storage.from_(self.bucket_name).create_signed_url(
                        path=storage_path,
                        expires_in=3600  # 1 hora
                    )
                    logger.info(f"🔍 Respuesta de create_signed_url: tipo={type(signed_response)}, valor={signed_response}")
                    # El método puede retornar un dict con 'signedURL' o directamente la URL
                    if signed_response:
                        if isinstance(signed_response, dict):
                            signed_url = signed_response.get('signedURL') or signed_response.get('signedUrl') or signed_response.get('url')
                            if signed_url:
                                logger.info(f"✅ URL firmada generada correctamente: {signed_url[:100]}...")
                                return signed_url
                            else:
                                logger.warning(f"⚠️ Respuesta dict pero sin URL. Keys: {signed_response.keys()}")
                        elif isinstance(signed_response, str):
                            logger.info(f"✅ URL firmada generada correctamente (string): {signed_response[:100]}...")
                            return signed_response
                # Alternativa: usar create_signed_url con parámetros diferentes
                elif hasattr(self.supabase.storage.from_(self.bucket_name), 'get_public_url'):
                    # Si no hay método de signed URL, usar pública
                    pass
            except Exception as e:
                logger.warning(f"⚠️ No se pudo generar URL firmada: {e}")
            
            # Fallback a URL pública
            try:
                public_url = self.supabase.storage.from_(self.bucket_name).get_public_url(storage_path)
                return public_url
            except Exception as e:
                logger.warning(f"⚠️ No se pudo obtener URL pública: {e}")
            
            # Último fallback: URL almacenada
            return file_data.get('url_archivo')
            
        except Exception as e:
            logger.error(f"❌ Error obteniendo URL del archivo {file_id}: {e}")
            return None
    
    async def delete_file(self, file_id: str) -> bool:
        """
        Eliminar archivo de Supabase Storage, OpenAI (si aplica) y base de datos
        
        Args:
            file_id: ID del archivo
        
        Returns:
            True si se eliminó correctamente, False en caso contrario
        """
        try:
            # Obtener información del archivo
            file_info = self.supabase.table('archivos').select('*').eq('id', file_id).execute()
            
            if not file_info.data:
                return False
            
            file_data = file_info.data[0]
            storage_path = file_data.get('storage_path')
            openai_file_id = file_data.get('openai_file_id')
            
            # Eliminar de Supabase Storage
            if storage_path:
                self.supabase.storage.from_(self.bucket_name).remove([storage_path])
                logger.info(f"✅ Archivo eliminado de Supabase Storage: {storage_path}")
            
            # Eliminar de OpenAI si tiene file_id
            if openai_file_id:
                try:
                    from app.services.openai_assistant_service import get_assistant_service
                    assistant_service = get_assistant_service()
                    await assistant_service.delete_file_from_openai(openai_file_id)
                    logger.info(f"✅ Archivo eliminado de OpenAI: {openai_file_id}")
                except Exception as e:
                    logger.warning(f"⚠️ No se pudo eliminar de OpenAI: {e}")
            
            # Marcar como inactivo en base de datos y limpiar openai_file_id
            self.supabase.table('archivos').update({
                'activo': False,
                'openai_file_id': None
            }).eq('id', file_id).execute()
            
            logger.info(f"✅ Archivo {file_id} eliminado exitosamente")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error eliminando archivo {file_id}: {e}")
            return False
    
    def _get_content_type(self, filename: str) -> str:
        """Obtener content type basado en extensión"""
        extension = self._get_extension(filename).lower()
        
        content_types = {
            '.pdf': 'application/pdf',
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.png': 'image/png',
            '.gif': 'image/gif',
            '.doc': 'application/msword',
            '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            '.xls': 'application/vnd.ms-excel',
            '.xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            '.txt': 'text/plain',
            '.zip': 'application/zip'
        }
        
        return content_types.get(extension, 'application/octet-stream')
    
    def _get_extension(self, filename: str) -> str:
        """Obtener extensión del archivo"""
        if '.' in filename:
            return '.' + filename.rsplit('.', 1)[1].lower()
        return ''
    
    def _sanitize_filename(self, filename: str) -> str:
        """
        Sanitizar nombre de archivo para Supabase Storage
        Convierte caracteres especiales y acentos a ASCII seguro
        """
        import re
        import unicodedata
        
        # Separar nombre y extensión
        if '.' in filename:
            name, ext = filename.rsplit('.', 1)
        else:
            name, ext = filename, ''
        
        # Normalizar caracteres Unicode (tildes, ñ, etc.) a ASCII
        # NFD = Normalization Form Canonical Decomposition
        name = unicodedata.normalize('NFD', name)
        # Eliminar marcas diacríticas (tildes)
        name = ''.join(char for char in name if unicodedata.category(char) != 'Mn')
        
        # Reemplazar espacios por guiones bajos
        name = name.replace(' ', '_')
        
        # Eliminar caracteres no válidos (solo permitir letras, números, guiones y guiones bajos)
        name = re.sub(r'[^a-zA-Z0-9_\-]', '', name)
        
        # Limitar longitud del nombre (sin extensión)
        if len(name) > 200:
            name = name[:200]
        
        # Reconstruir filename
        safe_name = f"{name}.{ext}" if ext else name
        
        return safe_name

# Instancia global
_storage_service = None

def get_storage_service() -> StorageService:
    """Obtener instancia del servicio de storage"""
    global _storage_service
    if _storage_service is None:
        _storage_service = StorageService()
    return _storage_service


