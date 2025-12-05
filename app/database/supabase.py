from supabase import create_client, Client
from app.config import Config
import logging

logger = logging.getLogger(__name__)

class SupabaseManager:
    _instance = None
    _client: Client = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(SupabaseManager, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        if self._client is None:
            # ✅ Usar SERVICE_KEY para operaciones de backend (bypasea RLS)
            self._client = create_client(Config.SUPABASE_URL, Config.SUPABASE_SERVICE_KEY)
    
    @property
    def client(self) -> Client:
        return self._client
    
    def table(self, table_name: str):
        """Acceso directo a tablas"""
        return self._client.table(table_name)
    
    def get_user_by_chat_id(self, chat_id: int):
        """Obtener usuario por chat_id con validación de seguridad"""
        try:
            response = self._client.table('usuarios').select('*').eq('chat_id', chat_id).eq('activo', True).execute()
            return response.data[0] if response.data else None
        except Exception as e:
            logger.error(f"Error obteniendo usuario por chat_id {chat_id}: {e}")
            return None
    
    def get_user_empresas(self, chat_id: int):
        """
        Obtener todas las empresas asociadas a un usuario (multiempresa)
        
        Args:
            chat_id: Chat ID del usuario en Telegram
            
        Returns:
            Lista de empresas asociadas al usuario:
            [{'id': 'uuid', 'nombre': 'Nombre', 'rut': '12345678-9', 'rol': 'user'}, ...]
        """
        try:
            # Obtener usuario primero
            user = self.get_user_by_chat_id(chat_id)
            if not user:
                return []
            
            usuario_id = user['id']
            
            # Consultar tabla usuarios_empresas con join a empresas
            response = self._client.table('usuarios_empresas')\
                .select('empresa_id, rol, empresas(id, nombre, rut, activo)')\
                .eq('usuario_id', usuario_id)\
                .eq('activo', True)\
                .execute()
            
            empresas = []
            if response.data:
                for rel in response.data:
                    empresa_info = rel.get('empresas', {}) if rel.get('empresas') else {}
                    # Verificar que la empresa esté activa
                    if empresa_info.get('activo', False):
                        empresas.append({
                            'id': rel['empresa_id'],
                            'nombre': empresa_info.get('nombre', ''),
                            'rut': empresa_info.get('rut', ''),
                            'rol': rel.get('rol', 'user')
                        })
            
            # Si no hay empresas en usuarios_empresas, usar empresa_id legacy (compatibilidad)
            if not empresas and user.get('empresa_id'):
                empresa_legacy = self._client.table('empresas')\
                    .select('*')\
                    .eq('id', user['empresa_id'])\
                    .eq('activo', True)\
                    .execute()
                
                if empresa_legacy.data:
                    empresas.append({
                        'id': empresa_legacy.data[0]['id'],
                        'nombre': empresa_legacy.data[0]['nombre'],
                        'rut': empresa_legacy.data[0].get('rut', ''),
                        'rol': user.get('rol', 'user')
                    })
            
            return empresas
            
        except Exception as e:
            logger.error(f"Error obteniendo empresas del usuario {chat_id}: {e}")
            return []
    
    def user_has_access_to_empresa(self, chat_id: int, empresa_id: str) -> bool:
        """
        Validar si un usuario tiene acceso a una empresa específica
        
        Args:
            chat_id: Chat ID del usuario
            empresa_id: ID de la empresa a validar
            
        Returns:
            True si el usuario tiene acceso, False en caso contrario
        """
        try:
            empresas = self.get_user_empresas(chat_id)
            empresa_ids = [e['id'] for e in empresas]
            return empresa_id in empresa_ids
        except Exception as e:
            logger.error(f"Error validando acceso de usuario {chat_id} a empresa {empresa_id}: {e}")
            return False
    
    def log_conversation(self, chat_id: int, empresa_id: int, mensaje: str, respuesta: str, tipo: str = "user"):
        """Registrar conversación en la base de datos"""
        try:
            data = {
                'chat_id': chat_id,
                'empresa_id': empresa_id,
                'mensaje': mensaje,
                'respuesta': respuesta,
                'tipo': tipo
            }
            self._client.table('conversaciones').insert(data).execute()
        except Exception as e:
            logger.error(f"Error registrando conversación: {e}")
    
    def get_empresa_data(self, empresa_id: int, table_name: str, chat_id: int = None):
        """
        Obtener datos de una empresa específica con validación de seguridad
        
        Args:
            empresa_id: ID de la empresa
            table_name: Nombre de la tabla
            chat_id: Chat ID del usuario (opcional, para validar acceso)
        
        Returns:
            Lista de datos de la empresa
        """
        try:
            # Validar acceso si se proporciona chat_id
            if chat_id and not self.user_has_access_to_empresa(chat_id, empresa_id):
                logger.warning(f"Usuario {chat_id} intentó acceder a empresa {empresa_id} sin permisos")
                return []
            
            response = self._client.table(table_name).select('*').eq('empresa_id', empresa_id).execute()
            return response.data
        except Exception as e:
            logger.error(f"Error obteniendo datos de {table_name} para empresa {empresa_id}: {e}")
            return []
    
    def create_empresa(self, rut: str, nombre: str, admin_chat_id: int):
        """Crear nueva empresa desde el bot admin"""
        try:
            # Crear empresa
            empresa_data = {
                'rut': rut,
                'nombre': nombre,
                'activo': True
            }
            empresa_response = self._client.table('empresas').insert(empresa_data).execute()
            
            if empresa_response.data:
                empresa_id = empresa_response.data[0]['id']
                
                # Crear usuario admin para la empresa
                usuario_data = {
                    'chat_id': admin_chat_id,
                    'empresa_id': empresa_id,
                    'nombre': 'Administrador',
                    'rol': 'admin',
                    'activo': True
                }
                self._client.table('usuarios').insert(usuario_data).execute()
                
                return empresa_id
            return None
        except Exception as e:
            logger.error(f"Error creando empresa: {e}")
            return None

    def get_reportes_mensuales(self, empresa_id, anio=None, mes=None):
        """Obtener reportes mensuales de una empresa"""
        try:
            query = self._client.table('reportes_mensuales').select('*').eq('empresa_id', empresa_id)
            
            if anio:
                query = query.eq('anio', anio)
            if mes:
                query = query.eq('mes', mes)
            
            result = query.order('anio', desc=True).order('mes', desc=True).execute()
            return result.data
        except Exception as e:
            logger.error(f"Error obteniendo reportes mensuales: {e}")
            return []
    
    def get_archivos_reporte(self, reporte_id):
        """Obtener archivos adjuntos de un reporte"""
        try:
            result = self._client.table('archivos_reportes').select('*').eq('reporte_id', reporte_id).execute()
            return result.data
        except Exception as e:
            logger.error(f"Error obteniendo archivos del reporte: {e}")
            return []
    
    def get_comentarios_reporte(self, reporte_id):
        """Obtener comentarios de un reporte"""
        try:
            result = self._client.table('comentarios_reportes').select('*').eq('reporte_id', reporte_id).execute()
            return result.data
        except Exception as e:
            logger.error(f"Error obteniendo comentarios del reporte: {e}")
            return []
    
    def get_info_compania(self, empresa_id, categoria=None):
        """Obtener información de compañía por categoría"""
        try:
            query = self._client.table('info_compania').select('*').eq('empresa_id', empresa_id).eq('estado', 'activo')
            
            if categoria:
                query = query.eq('categoria', categoria)
            
            result = query.execute()
            return result.data
        except Exception as e:
            logger.error(f"Error obteniendo información de compañía: {e}")
            return []
    
    def get_archivos_info_compania(self, info_id):
        """Obtener archivos adjuntos de información de compañía"""
        try:
            result = self._client.table('archivos_info_compania').select('*').eq('info_id', info_id).execute()
            return result.data
        except Exception as e:
            logger.error(f"Error obteniendo archivos de información: {e}")
            return []
    
    def crear_reporte_mensual(self, empresa_id, anio, mes, tipo_reporte, titulo, descripcion=None, comentarios=None):
        """Crear un nuevo reporte mensual"""
        try:
            data = {
                'empresa_id': empresa_id,
                'anio': anio,
                'mes': mes,
                'tipo_reporte': tipo_reporte,
                'titulo': titulo,
                'descripcion': descripcion,
                'comentarios': comentarios,
                'estado': 'borrador'
            }
            
            result = self._client.table('reportes_mensuales').insert(data).execute()
            return result.data[0] if result.data else None
        except Exception as e:
            logger.error(f"Error creando reporte mensual: {e}")
            return None
    
    def agregar_archivo_reporte(self, reporte_id, nombre_archivo, tipo_archivo, url_archivo, descripcion=None):
        """Agregar archivo adjunto a un reporte"""
        try:
            data = {
                'reporte_id': reporte_id,
                'nombre_archivo': nombre_archivo,
                'tipo_archivo': tipo_archivo,
                'url_archivo': url_archivo,
                'descripcion': descripcion
            }
            
            result = self._client.table('archivos_reportes').insert(data).execute()
            return result.data[0] if result.data else None
        except Exception as e:
            logger.error(f"Error agregando archivo al reporte: {e}")
            return None
    
    def agregar_comentario_reporte(self, reporte_id, usuario_id, comentario, tipo_comentario='general'):
        """Agregar comentario a un reporte"""
        try:
            data = {
                'reporte_id': reporte_id,
                'usuario_id': usuario_id,
                'comentario': comentario,
                'tipo_comentario': tipo_comentario
            }
            
            result = self._client.table('comentarios_reportes').insert(data).execute()
            return result.data[0] if result.data else None
        except Exception as e:
            logger.error(f"Error agregando comentario al reporte: {e}")
            return None
    
    def get_reportes_financieros(self, empresa_id: str, periodo: str = None, chat_id: int = None, limit: int = 10):
        """
        Obtener reportes financieros de una empresa
        
        Args:
            empresa_id: UUID de la empresa
            periodo: Periodo en formato YYYY-MM. Si es None, busca los más recientes
            chat_id: Chat ID del usuario (opcional, para validar acceso)
            limit: Número máximo de reportes a retornar
        
        Returns:
            Lista de archivos de reportes financieros con contenido/metadata
        """
        try:
            # Validar acceso si se proporciona chat_id
            if chat_id and not self.user_has_access_to_empresa(chat_id, empresa_id):
                logger.warning(f"Usuario {chat_id} intentó acceder a empresa {empresa_id} sin permisos")
                return []
            
            # Buscar reportes financieros (reportes mensuales, estados financieros, f29, etc.)
            query = self._client.table('archivos')\
                .select('*')\
                .eq('empresa_id', empresa_id)\
                .eq('categoria', 'financiero')\
                .eq('activo', True)
            
            if periodo:
                query = query.eq('periodo', periodo)
            
            # Filtrar por subtipos de reportes financieros relevantes
            query = query.in_('subtipo', ['reporte_mensual', 'estados_financieros', 'f29', 'otros'])
            
            # Ordenar por período más reciente y limitar resultados
            result = query.order('periodo', desc=True).order('created_at', desc=True).limit(limit).execute()
            
            logger.info(f"📊 get_reportes_financieros: {len(result.data)} reportes encontrados para empresa {empresa_id}")
            return result.data
        except Exception as e:
            logger.error(f"Error obteniendo reportes financieros: {e}")
            return []
    
    def get_reportes_cfo(self, empresa_id: str, chat_id: int = None, limit: int = 10):
        """
        Obtener reportes CFO/ejecutivos de una empresa
        
        Args:
            empresa_id: UUID de la empresa
            chat_id: Chat ID del usuario (opcional, para validar acceso)
            limit: Número máximo de reportes
        
        Returns:
            Lista de archivos de reportes CFO/ejecutivos
        """
        try:
            # Validar acceso si se proporciona chat_id
            if chat_id and not self.user_has_access_to_empresa(chat_id, empresa_id):
                logger.warning(f"Usuario {chat_id} intentó acceder a empresa {empresa_id} sin permisos")
                return []
            
            # Buscar archivos ejecutivos/CFO
            query = self._client.table('archivos')\
                .select('*')\
                .eq('empresa_id', empresa_id)\
                .eq('activo', True)
            
            result = query.order('periodo', desc=True).order('created_at', desc=True).limit(50).execute()
            
            # Filtrar en Python para encontrar archivos relacionados con CFO/ejecutivos
            reportes_cfo = []
            keywords = ['cfo', 'performance', 'monthly', 'ejecutivo', 'resumen', 'consolidado', 'dashboard']
            
            for archivo in result.data:
                nombre = (archivo.get('nombre_original') or archivo.get('nombre_archivo') or '').lower()
                descripcion = (archivo.get('descripcion_personalizada') or archivo.get('descripcion') or '').lower()
                subtipo = (archivo.get('subtipo') or '').lower()
                
                for keyword in keywords:
                    if keyword in nombre or keyword in descripcion or keyword in subtipo:
                        reportes_cfo.append(archivo)
                        break
                
                if len(reportes_cfo) >= limit:
                    break
            
            logger.info(f"📈 get_reportes_cfo: {len(reportes_cfo)} reportes CFO/ejecutivos encontrados para empresa {empresa_id}")
            return reportes_cfo
        except Exception as e:
            logger.error(f"Error obteniendo reportes CFO: {e}")
            return []
    
    def get_contenido_archivo(self, archivo_id: str):
        """
        Obtener contenido de un archivo (si está disponible)
        
        Args:
            archivo_id: UUID del archivo
        
        Returns:
            Contenido del archivo o None si no se puede obtener
        """
        try:
            # Obtener metadata del archivo
            archivo = self._client.table('archivos').select('*').eq('id', archivo_id).execute()
            if not archivo.data:
                return None
            
            archivo_data = archivo.data[0]
            # Por ahora retornamos metadata. En el futuro podríamos leer el contenido del archivo
            return {
                'nombre': archivo_data.get('nombre_original') or archivo_data.get('nombre_archivo'),
                'periodo': archivo_data.get('periodo'),
                'subtipo': archivo_data.get('subtipo'),
                'descripcion': archivo_data.get('descripcion_personalizada') or archivo_data.get('descripcion'),
                'metadata': archivo_data.get('metadata', {}),
                'url': archivo_data.get('url_archivo')
            }
        except Exception as e:
            logger.error(f"Error obteniendo contenido de archivo: {e}")
            return None

# Instancia global
supabase = SupabaseManager()

def get_supabase_client() -> SupabaseManager:
    """Obtener instancia del cliente de Supabase"""
    return supabase 