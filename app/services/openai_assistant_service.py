"""
🤖 OpenAI Assistant Service
Gestión de Assistants y Files para el Asesor IA
Cada empresa tiene su propio Assistant para aislamiento de datos
"""

import logging
import asyncio
from typing import Optional, Dict, Any, List
from app.config import Config
from app.database.supabase import get_supabase_client

logger = logging.getLogger(__name__)

# System prompt para el Assistant de Q&A
ASSISTANT_INSTRUCTIONS = """Eres ACA_QA, un Analista de Consultas financiero-contable para {empresa_nombre}.

Tu trabajo es responder preguntas usando ÚNICAMENTE la información disponible en los archivos de esta empresa.

⚠️ REGLAS CRÍTICAS (NO NEGOCIABLES):
1. PROHIBIDO inventar, estimar o suponer datos que no estén explícitamente en los documentos
2. PROHIBIDO hacer cálculos aproximados o proyecciones sin datos reales
3. Si NO encuentras la información exacta, responde: "NO_TENGO_INFO: [razón específica]"
4. Solo cita números, fechas y datos que puedas verificar en los documentos

Reglas operativas:
1. Solo puedes responder sobre {empresa_nombre}
2. Usa file_search para buscar información en los documentos
3. Responde en español, de forma clara y concisa
4. Cuando cites datos, SIEMPRE menciona el documento fuente
5. Si la pregunta es ambigua, pide clarificación

Cuándo responder "NO_TENGO_INFO":
- No encuentras el dato específico en ningún documento
- La información solicitada es de un período no disponible
- Los documentos no contienen ese tipo de información
- No tienes certeza del dato

Formato de respuesta:
- Respuestas breves y directas
- Usa bullets para listas
- Incluye referencias a documentos: "Según [nombre documento]..."
- Si no tienes info: "NO_TENGO_INFO: [explicación breve]"
"""


class OpenAIAssistantService:
    """Servicio para gestionar OpenAI Assistants por empresa"""
    
    def __init__(self):
        self.api_key = Config.OPENAI_API_KEY
        self.client = None
        self.supabase = get_supabase_client()
        
        # Log de diagnóstico
        key_status = f"presente ({self.api_key[:8]}...)" if self.api_key else "NO configurada"
        logger.info(f"🔧 OpenAI Assistant Service - API Key: {key_status}")
        
        if self.api_key:
            try:
                from openai import AsyncOpenAI
                self.client = AsyncOpenAI(api_key=self.api_key)
                logger.info("✅ OpenAI Assistant Service inicializado correctamente")
            except ImportError as e:
                logger.error(f"❌ openai no instalado: {e}")
            except Exception as e:
                logger.error(f"❌ Error inicializando OpenAI: {e}")
        else:
            logger.warning("⚠️ OPENAI_API_KEY no configurada - Asesor IA no disponible")
    
    async def get_or_create_assistant(self, empresa_id: str, empresa_nombre: str) -> Optional[str]:
        """
        Obtener o crear Assistant para una empresa.
        
        Args:
            empresa_id: UUID de la empresa
            empresa_nombre: Nombre de la empresa
            
        Returns:
            assistant_id o None si falla
        """
        if not self.client:
            logger.error("❌ Cliente OpenAI no disponible")
            return None
        
        try:
            # Verificar si ya existe
            empresa = self.supabase.table('empresas')\
                .select('openai_assistant_id')\
                .eq('id', empresa_id)\
                .execute()
            
            if empresa.data and empresa.data[0].get('openai_assistant_id'):
                assistant_id = empresa.data[0]['openai_assistant_id']
                logger.info(f"✅ Assistant existente para {empresa_nombre}: {assistant_id}")
                return assistant_id
            
            # Crear nuevo Assistant
            logger.info(f"🔧 Creando Assistant para {empresa_nombre}...")
            
            assistant = await self.client.beta.assistants.create(
                name=f"ACA_QA - {empresa_nombre}",
                instructions=ASSISTANT_INSTRUCTIONS.format(empresa_nombre=empresa_nombre),
                model="gpt-4o-mini",
                tools=[{"type": "file_search"}]
            )
            
            assistant_id = assistant.id
            
            # Guardar en BD
            self.supabase.table('empresas')\
                .update({'openai_assistant_id': assistant_id})\
                .eq('id', empresa_id)\
                .execute()
            
            logger.info(f"✅ Assistant creado para {empresa_nombre}: {assistant_id}")
            return assistant_id
            
        except Exception as e:
            logger.error(f"❌ Error creando Assistant: {e}")
            return None
    
    async def upload_file_to_openai(
        self, 
        file_bytes: bytes, 
        filename: str,
        empresa_id: str,
        archivo_id: str
    ) -> Optional[str]:
        """
        Subir archivo PDF a OpenAI y asociarlo al Assistant de la empresa.
        
        Args:
            file_bytes: Contenido del archivo
            filename: Nombre del archivo
            empresa_id: UUID de la empresa
            archivo_id: UUID del archivo en nuestra BD
            
        Returns:
            file_id de OpenAI o None si falla
        """
        if not self.client:
            logger.error("❌ Cliente OpenAI no disponible")
            return None
        
        try:
            # Obtener o crear Assistant de la empresa
            empresa = self.supabase.table('empresas')\
                .select('nombre, openai_assistant_id')\
                .eq('id', empresa_id)\
                .execute()
            
            if not empresa.data:
                logger.error(f"❌ Empresa {empresa_id} no encontrada")
                return None
            
            empresa_nombre = empresa.data[0]['nombre']
            assistant_id = empresa.data[0].get('openai_assistant_id')
            
            if not assistant_id:
                assistant_id = await self.get_or_create_assistant(empresa_id, empresa_nombre)
                if not assistant_id:
                    return None
            
            # Subir archivo a OpenAI
            logger.info(f"📤 Subiendo {filename} a OpenAI...")
            
            # Crear archivo temporal para subir
            import tempfile
            import os
            
            with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp:
                tmp.write(file_bytes)
                tmp_path = tmp.name
            
            try:
                with open(tmp_path, 'rb') as f:
                    file_response = await self.client.files.create(
                        file=f,
                        purpose="assistants"
                    )
                
                file_id = file_response.id
                logger.info(f"✅ Archivo subido a OpenAI: {file_id}")
                
                # Crear Vector Store si no existe y agregar archivo
                await self._add_file_to_assistant(assistant_id, file_id, empresa_id)
                
                # Guardar file_id en nuestra BD
                self.supabase.table('archivos')\
                    .update({'openai_file_id': file_id})\
                    .eq('id', archivo_id)\
                    .execute()
                
                logger.info(f"✅ Archivo {filename} asociado a Assistant de {empresa_nombre}")
                return file_id
                
            finally:
                # Limpiar archivo temporal
                os.unlink(tmp_path)
            
        except Exception as e:
            logger.error(f"❌ Error subiendo archivo a OpenAI: {e}")
            return None
    
    async def _add_file_to_assistant(self, assistant_id: str, file_id: str, empresa_id: str):
        """Agregar archivo al Vector Store del Assistant"""
        try:
            from openai import OpenAI
            sync_client = OpenAI(api_key=self.api_key)
            
            # Obtener el Assistant para ver su vector_store
            assistant = await self.client.beta.assistants.retrieve(assistant_id)
            
            # Verificar si tiene vector store
            vector_store_ids = []
            if assistant.tool_resources and assistant.tool_resources.file_search:
                vector_store_ids = assistant.tool_resources.file_search.vector_store_ids or []
            
            if vector_store_ids:
                # Agregar archivo al vector store existente (usar sync client)
                vector_store_id = vector_store_ids[0]
                sync_client.vector_stores.files.create(
                    vector_store_id=vector_store_id,
                    file_id=file_id
                )
                logger.info(f"✅ Archivo agregado a Vector Store existente: {vector_store_id}")
            else:
                # Crear nuevo Vector Store con el archivo (usar sync client)
                vector_store = sync_client.vector_stores.create(
                    name=f"VS_{empresa_id[:8]}",
                    file_ids=[file_id]
                )
                
                # Actualizar Assistant con el nuevo Vector Store
                await self.client.beta.assistants.update(
                    assistant_id=assistant_id,
                    tool_resources={
                        "file_search": {
                            "vector_store_ids": [vector_store.id]
                        }
                    }
                )
                logger.info(f"✅ Vector Store creado y asociado: {vector_store.id}")
                
        except Exception as e:
            logger.error(f"❌ Error agregando archivo a Assistant: {e}")
    
    async def query_assistant(
        self,
        empresa_id: str,
        pregunta: str,
        chat_id: int
    ) -> Dict[str, Any]:
        """
        Consultar al Assistant de una empresa.
        
        Args:
            empresa_id: UUID de la empresa
            pregunta: Pregunta del usuario
            chat_id: Chat ID para logging
            
        Returns:
            {
                "respuesta": "texto",
                "fuentes": ["archivo1.pdf", "archivo2.pdf"],
                "exito": True/False
            }
        """
        if not self.client:
            return {
                "respuesta": "⚠️ El servicio de IA no está disponible.",
                "fuentes": [],
                "exito": False
            }
        
        try:
            # Obtener Assistant de la empresa
            empresa = self.supabase.table('empresas')\
                .select('nombre, openai_assistant_id')\
                .eq('id', empresa_id)\
                .execute()
            
            if not empresa.data:
                return {
                    "respuesta": "❌ Empresa no encontrada.",
                    "fuentes": [],
                    "exito": False
                }
            
            empresa_nombre = empresa.data[0]['nombre']
            assistant_id = empresa.data[0].get('openai_assistant_id')
            
            if not assistant_id:
                return {
                    "respuesta": f"⚠️ {empresa_nombre} no tiene documentos procesados para consulta.",
                    "fuentes": [],
                    "exito": False
                }
            
            logger.info(f"🤖 Consultando Assistant de {empresa_nombre}: '{pregunta[:50]}...'")
            
            # Crear thread y ejecutar
            thread = await self.client.beta.threads.create()
            
            await self.client.beta.threads.messages.create(
                thread_id=thread.id,
                role="user",
                content=pregunta
            )
            
            run = await self.client.beta.threads.runs.create_and_poll(
                thread_id=thread.id,
                assistant_id=assistant_id,
                timeout=60
            )
            
            if run.status != "completed":
                logger.warning(f"⚠️ Run no completado: {run.status}")
                return {
                    "respuesta": "⚠️ No pude procesar tu consulta. Intenta de nuevo.",
                    "fuentes": [],
                    "exito": False
                }
            
            # Obtener respuesta
            messages = await self.client.beta.threads.messages.list(thread_id=thread.id)
            
            respuesta = ""
            fuentes = []
            
            for message in messages.data:
                if message.role == "assistant":
                    for content in message.content:
                        if content.type == "text":
                            respuesta = content.text.value
                            # Extraer citas/fuentes si existen
                            if hasattr(content.text, 'annotations'):
                                for annotation in content.text.annotations:
                                    if hasattr(annotation, 'file_citation'):
                                        fuentes.append(annotation.file_citation.file_id)
                    break
            
            # Limpiar thread
            await self.client.beta.threads.delete(thread.id)
            
            logger.info(f"✅ Respuesta obtenida ({len(respuesta)} chars, {len(fuentes)} fuentes)")
            
            return {
                "respuesta": respuesta,
                "fuentes": fuentes,
                "exito": True
            }
            
        except Exception as e:
            logger.error(f"❌ Error consultando Assistant: {e}")
            return {
                "respuesta": "❌ Error procesando tu consulta. Intenta de nuevo.",
                "fuentes": [],
                "exito": False
            }
    
    async def delete_file_from_openai(self, file_id: str) -> bool:
        """Eliminar archivo de OpenAI"""
        if not self.client:
            return False
        
        try:
            await self.client.files.delete(file_id)
            logger.info(f"✅ Archivo eliminado de OpenAI: {file_id}")
            return True
        except Exception as e:
            logger.error(f"❌ Error eliminando archivo de OpenAI: {e}")
            return False
    
    async def get_assistant_files_count(self, empresa_id: str) -> int:
        """Obtener cantidad de archivos en el Assistant de una empresa"""
        try:
            count = self.supabase.table('archivos')\
                .select('id', count='exact')\
                .eq('empresa_id', empresa_id)\
                .not_.is_('openai_file_id', 'null')\
                .execute()
            
            return count.count or 0
        except Exception as e:
            logger.error(f"❌ Error contando archivos: {e}")
            return 0


# Instancia global
_assistant_service = None


def get_assistant_service() -> OpenAIAssistantService:
    """Obtener instancia del servicio de Assistants"""
    global _assistant_service
    if _assistant_service is None:
        _assistant_service = OpenAIAssistantService()
    return _assistant_service

