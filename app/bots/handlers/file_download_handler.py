"""
📥 Handler de Descarga de Archivos
Maneja el flujo conversacional para descargar archivos usando IA y flujo estructurado
"""

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from app.security.auth import security
from app.database.supabase import supabase
from app.services.session_manager import get_session_manager
from app.services.storage_service import get_storage_service
from app.services.ai_service import get_ai_service
from app.services.conversation_logger import get_conversation_logger
from app.utils.file_types import (
    get_botones_categorias,
    get_botones_subtipos,
    get_categoria_nombre,
    get_subtipo_nombre,
    validar_categoria,
    validar_subtipo
)
from app.decorators.conversation_logging import log_production_conversation
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

def escape_markdown(text):
    """Escapar caracteres especiales para Markdown"""
    if not text:
        return text
    return text.replace('_', '\\_').replace('*', '\\*').replace('[', '\\[').replace(']', '\\]').replace('`', '\\`')

class FileDownloadHandler:
    """Manejador de descarga de archivos"""
    
    @staticmethod
    @log_production_conversation
    async def handle_download_request(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Manejar solicitud de descarga (mensaje de texto)"""
        chat_id = update.effective_chat.id
        mensaje = update.message.text
        
        # Validar usuario
        validation = security.validate_user(chat_id)
        if not validation['valid']:
            await update.message.reply_text(validation['message'])
            return
        
        user_data = validation['user_data']
        
        # Obtener empresas del usuario
        empresas = await FileDownloadHandler._get_user_empresas(chat_id)
        if not empresas:
            await update.message.reply_text(
                "❌ No tienes empresas asignadas. Contacta al administrador."
            )
            return
        
        # Obtener contexto
        conversation_logger = get_conversation_logger()
        historial = await conversation_logger.get_user_conversation_history(chat_id, limit=5)
        
        # Obtener o crear sesión activa
        session_manager = get_session_manager()
        sesion_activa = session_manager.get_session(chat_id)
        
        if not sesion_activa or sesion_activa.get('intent') != 'descargar_archivo':
            session_manager.create_session(
                chat_id=chat_id,
                intent='descargar_archivo',
                estado='procesando_ia',
                data={}
            )
            sesion_activa = session_manager.get_session(chat_id)
        
        # Intentar extraer intención con IA
        ai_service = get_ai_service()
        intent = await ai_service.extract_file_intent(
            mensaje, empresas, historial, sesion_activa
        )
        
        # Si solo tiene 1 empresa, asignarla automáticamente
        if len(empresas) == 1:
            intent['empresa'] = None
            intent['empresa_id'] = empresas[0]['id']
            intent['empresa_nombre'] = empresas[0]['nombre']
        
        # Decidir flujo según confianza y campos extraídos
        if intent.get('confianza', 0) >= 0.75 and all([
            intent.get('categoria'),
            intent.get('subtipo'),
            intent.get('periodo')
        ]):
            # Flujo directo con IA
            if len(empresas) > 1 and not intent.get('empresa'):
                # Tiene múltiples pero no especificó → preguntar empresa
                await FileDownloadHandler._ask_empresa(update.message, empresas, intent)
            else:
                # Responder directo
                await FileDownloadHandler._process_direct_download(
                    update.message, intent, empresas, user_data
                )
        else:
            # Flujo estructurado (completar campos faltantes)
            await FileDownloadHandler._process_structured_download(
                update.message, intent, empresas, sesion_activa, user_data
            )
    
    @staticmethod
    async def _get_user_empresas(chat_id: int) -> list:
        """Obtener empresas asignadas al usuario (sistema multi-empresa)"""
        try:
            # ✅ Usar el método correcto que maneja multi-empresa desde usuarios_empresas
            return supabase.get_user_empresas(chat_id)
        except Exception as e:
            logger.error(f"Error obteniendo empresas del usuario {chat_id}: {e}")
            return []
    
    @staticmethod
    async def _ask_empresa(message_or_query, empresas: list, intent: dict):
        """Preguntar al usuario qué empresa"""
        session_manager = get_session_manager()
        chat_id = message_or_query.chat.id if hasattr(message_or_query, 'chat') else message_or_query.message.chat.id
        
        # ✅ Obtener datos existentes de la sesión y actualizarlos (no sobreescribir)
        session = session_manager.get_session(chat_id)
        session_data = session.get('data', {}) if session else {}
        
        # Solo actualizar si el intent tiene valores no-None
        if intent.get('categoria'):
            session_data['categoria'] = intent.get('categoria')
        if intent.get('subtipo'):
            session_data['subtipo'] = intent.get('subtipo')
        if intent.get('periodo'):
            session_data['periodo'] = intent.get('periodo')
        
        # Guardar datos actualizados en sesión
        session_manager.update_session(
            chat_id=chat_id,
            estado='esperando_empresa',
            data=session_data
        )
        
        text = "🏢 **¿De qué empresa quieres los archivos?**\n\nSelecciona una opción:"
        
        from app.utils.file_types import organizar_botones_en_columnas
        
        # Crear botones de empresas
        botones_empresas = []
        for empresa in empresas:
            botones_empresas.append(InlineKeyboardButton(
                f"🏢 {escape_markdown(empresa['nombre'])}",
                callback_data=f"download_empresa_{empresa['id']}"
            ))
        
        # Organizar en 2 columnas
        keyboard = organizar_botones_en_columnas(botones_empresas, columnas=2)
        
        keyboard.append([InlineKeyboardButton("❌ Cancelar", callback_data="download_cancelar")])
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        # Detectar si es Message o CallbackQuery
        if hasattr(message_or_query, 'edit_message_text'):
            await message_or_query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')
        else:
            await message_or_query.reply_text(text, reply_markup=reply_markup, parse_mode='Markdown')
    
    @staticmethod
    async def _process_direct_download(message_or_query, intent: dict, empresas: list, user_data: dict):
        """Procesar descarga directa (IA extrajo todo)"""
        chat_id = message_or_query.chat.id if hasattr(message_or_query, 'chat') else message_or_query.message.chat.id
        
        logger.info(f"⚡ DESCARGA DIRECTA - chat_id: {chat_id}")
        logger.info(f"⚡ Intent recibido de IA: {intent}")
        
        # Determinar empresa_id
        empresa_id = intent.get('empresa_id')
        if not empresa_id:
            # Buscar por nombre
            empresa_nombre = intent.get('empresa')
            if empresa_nombre:
                for emp in empresas:
                    if emp['nombre'].lower() == empresa_nombre.lower():
                        empresa_id = emp['id']
                        logger.info(f"⚡ Empresa encontrada por nombre: {empresa_nombre} -> ID: {empresa_id}")
                        break
        
        if not empresa_id and len(empresas) == 1:
            empresa_id = empresas[0]['id']
            logger.info(f"⚡ Auto-asignada única empresa: {empresa_id}")
        
        if not empresa_id:
            logger.error(f"❌ No se pudo determinar empresa_id")
            text = "❌ No se pudo determinar la empresa."
            if hasattr(message_or_query, 'edit_message_text'):
                await message_or_query.edit_message_text(text)
            else:
                await message_or_query.reply_text(text)
            return
        
        logger.info(f"⚡ Llamando a _buscar_archivos con:")
        logger.info(f"  • empresa_id: {empresa_id}")
        logger.info(f"  • categoria: {intent.get('categoria')}")
        logger.info(f"  • subtipo: {intent.get('subtipo')}")
        logger.info(f"  • periodo: {intent.get('periodo')}")
        
        # Buscar archivos
        archivos = await FileDownloadHandler._buscar_archivos(
            empresa_id=empresa_id,
            categoria=intent.get('categoria'),
            subtipo=intent.get('subtipo'),
            periodo=intent.get('periodo')
        )
        
        logger.info(f"⚡ Archivos recibidos: {len(archivos)}")
        
        # Responder con resultados
        await FileDownloadHandler._responder_con_archivos(
            message_or_query, archivos, intent, empresas
        )
        
        # ✅ Solo limpiar sesión si hay 1 archivo (descarga directa completada)
        # No limpiar si hay múltiples archivos (usuario debe seleccionar)
        if archivos and len(archivos) == 1:
            logger.info(f"⚡ Limpiando sesión después de descarga directa de 1 archivo")
            session_manager = get_session_manager()
            session_manager.clear_session(chat_id)
        elif archivos and len(archivos) > 1:
            logger.info(f"⚡ Sesión mantenida para selección de {len(archivos)} archivos")
    
    @staticmethod
    async def _process_structured_download(
        message, intent: dict, empresas: list, sesion_activa: dict, user_data: dict
    ):
        """Procesar descarga con flujo estructurado (completar campos faltantes)"""
        chat_id = message.chat.id
        session_manager = get_session_manager()
        session_data = sesion_activa.get('data', {}) if sesion_activa else {}
        
        # Actualizar sesión con datos extraídos por IA (si hay)
        if intent.get('categoria'):
            session_data['categoria'] = intent['categoria']
        if intent.get('subtipo'):
            session_data['subtipo'] = intent['subtipo']
        if intent.get('periodo'):
            session_data['periodo'] = intent['periodo']
        if intent.get('empresa'):
            session_data['empresa'] = intent['empresa']
        
        # Determinar qué falta
        falta_categoria = not session_data.get('categoria')
        falta_subtipo = not session_data.get('subtipo')
        falta_periodo = not session_data.get('periodo')
        falta_empresa = len(empresas) > 1 and not session_data.get('empresa_id')
        
        # Actualizar sesión
        session_manager.update_session(chat_id=chat_id, data=session_data)
        
        # ✅ Preguntar por lo que falta (ORDEN MODIFICADO: empresa al final)
        # 1. Categoría -> 2. Subtipo -> 3. Período -> 4. Empresa (solo si tiene múltiples) -> 5. Finalizar
        if falta_categoria:
            session_manager.update_session(chat_id=chat_id, estado='esperando_categoria')
            await FileDownloadHandler._ask_categoria(message)
        elif falta_subtipo:
            categoria = session_data['categoria']
            session_manager.update_session(chat_id=chat_id, estado='esperando_subtipo')
            await FileDownloadHandler._ask_subtipo(message, categoria)
        elif falta_periodo:
            session_manager.update_session(chat_id=chat_id, estado='esperando_periodo')
            await FileDownloadHandler._ask_periodo(message)
        elif falta_empresa:
            # ✅ Preguntar empresa al FINAL, solo si tiene múltiples empresas
            await FileDownloadHandler._ask_empresa(message, empresas, intent)
        else:
            # Ya tenemos todo, procesar descarga
            await FileDownloadHandler._finalizar_descarga(message, session_data, empresas)
    
    @staticmethod
    async def _ask_categoria(message_or_query):
        """Preguntar categoría del archivo"""
        logger.info(f"📁 _ask_categoria llamado")
        try:
            text = "📁 **¿Qué categoría de archivo necesitas?**\n\nSelecciona una opción:"
            
            from app.utils.file_types import organizar_botones_en_columnas
            botones_raw = get_botones_categorias()
            logger.info(f"📁 Botones raw obtenidos: {len(botones_raw)} categorías")
            
            botones_telegram = []
            for btn in botones_raw:
                callback_final = f"download_{btn['callback_data']}"
                botones_telegram.append(InlineKeyboardButton(btn['text'], callback_data=callback_final))
                logger.debug(f"  • Botón: {btn['text']} → {callback_final}")
            
            keyboard = organizar_botones_en_columnas(botones_telegram, columnas=2)
            
            keyboard.append([InlineKeyboardButton("❌ Cancelar", callback_data="download_cancelar")])
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            logger.info(f"📁 Enviando mensaje con {len(keyboard)} filas de botones")
            # Detectar si es Message o CallbackQuery
            if hasattr(message_or_query, 'edit_message_text'):
                await message_or_query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')
                logger.info(f"✅ Mensaje editado correctamente en _ask_categoria")
            else:
                await message_or_query.reply_text(text, reply_markup=reply_markup, parse_mode='Markdown')
                logger.info(f"✅ Mensaje enviado correctamente en _ask_categoria")
        except Exception as e:
            logger.error(f"❌ Error en _ask_categoria: {e}", exc_info=True)
            raise
    
    @staticmethod
    async def _ask_subtipo(message_or_query, categoria: str):
        """Preguntar subtipo del archivo"""
        logger.info(f"📋 _ask_subtipo llamado con categoría: '{categoria}'")
        try:
            text = f"📁 **{get_categoria_nombre(categoria)}**\n\nSelecciona el tipo específico:"
            
            from app.utils.file_types import organizar_botones_en_columnas
            botones_raw = get_botones_subtipos(categoria)
            logger.info(f"📋 Subtipos encontrados: {len(botones_raw)} para categoría '{categoria}'")
            
            botones_telegram = []
            for boton in botones_raw:
                callback_data = f"download_subtipo_{categoria}_{boton['callback_data'].replace(f'subtipo_{categoria}_', '')}"
                botones_telegram.append(InlineKeyboardButton(
                    boton['text'],
                    callback_data=callback_data
                ))
                logger.debug(f"  • Botón: {boton['text']} → {callback_data}")
            
            keyboard = organizar_botones_en_columnas(botones_telegram, columnas=2)
            
            keyboard.append([InlineKeyboardButton("🔙 Volver", callback_data="download_back_categoria")])
            keyboard.append([InlineKeyboardButton("❌ Cancelar", callback_data="download_cancelar")])
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            logger.info(f"📋 Enviando mensaje con {len(keyboard)} filas de botones")
            # Detectar si es Message o CallbackQuery
            if hasattr(message_or_query, 'edit_message_text'):
                await message_or_query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')
                logger.info(f"✅ Mensaje editado correctamente")
            else:
                await message_or_query.reply_text(text, reply_markup=reply_markup, parse_mode='Markdown')
                logger.info(f"✅ Mensaje enviado correctamente")
        except Exception as e:
            logger.error(f"❌ Error en _ask_subtipo: {e}", exc_info=True)
            raise
    
    @staticmethod
    async def _ask_periodo(message_or_query):
        """Preguntar período del archivo"""
        current_month = datetime.now().strftime("%Y-%m")
        last_month = (datetime.now().replace(day=1) - timedelta(days=1)).strftime("%Y-%m")
        
        text = "📅 **¿Para qué período necesitas los archivos?**\n\nSelecciona una opción:"
        
        keyboard = [
            [InlineKeyboardButton(f"🟢 Mes actual ({current_month})", callback_data="download_periodo_actual")],
            [InlineKeyboardButton(f"🟡 Mes anterior ({last_month})", callback_data="download_periodo_anterior")],
            [InlineKeyboardButton("📅 Otro mes", callback_data="download_periodo_otro")],
            [InlineKeyboardButton("❌ Cancelar", callback_data="download_cancelar")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        # Detectar si es Message o CallbackQuery
        if hasattr(message_or_query, 'edit_message_text'):
            await message_or_query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')
        else:
            await message_or_query.reply_text(text, reply_markup=reply_markup, parse_mode='Markdown')
    
    @staticmethod
    async def _buscar_archivos(
        empresa_id: str,
        categoria: str,
        subtipo: str,
        periodo: str
    ) -> list:
        """Buscar archivos en Supabase"""
        try:
            logger.info(f"🔍 BUSCAR ARCHIVOS - Parámetros recibidos:")
            logger.info(f"  • empresa_id: {empresa_id}")
            logger.info(f"  • categoria: {categoria}")
            logger.info(f"  • subtipo: {subtipo}")
            logger.info(f"  • periodo: {periodo}")
            
            query = supabase.table('archivos')\
                .select('*')\
                .eq('empresa_id', empresa_id)\
                .eq('activo', True)
            
            if categoria:
                query = query.eq('categoria', categoria)
                logger.info(f"  ✓ Filtro categoria aplicado: {categoria}")
            if subtipo:
                query = query.eq('subtipo', subtipo)
                logger.info(f"  ✓ Filtro subtipo aplicado: {subtipo}")
            if periodo:
                query = query.eq('periodo', periodo)
                logger.info(f"  ✓ Filtro periodo aplicado: {periodo}")
            
            result = query.order('created_at', desc=True).execute()
            
            logger.info(f"🔍 RESULTADOS: {len(result.data) if result.data else 0} archivo(s) encontrado(s)")
            if result.data:
                for idx, archivo in enumerate(result.data, 1):
                    logger.info(f"  Archivo {idx}: {archivo.get('nombre_original', 'Sin nombre')} - Período: {archivo.get('periodo', 'N/A')}")
            
            return result.data if result.data else []
            
        except Exception as e:
            logger.error(f"Error buscando archivos: {e}")
            return []
    
    @staticmethod
    async def _responder_con_archivos(message_or_query, archivos: list, intent: dict, empresas: list):
        """Responder al usuario con los archivos encontrados"""
        logger.info(f"📤 _responder_con_archivos llamado con {len(archivos)} archivo(s)")
        
        if not archivos:
            categoria_nombre = get_categoria_nombre(intent.get('categoria', ''))
            subtipo_nombre = get_subtipo_nombre(
                intent.get('categoria', ''),
                intent.get('subtipo', '')
            )
            periodo = intent.get('periodo', 'N/A')
            empresa_nombre = intent.get('empresa_nombre', 'N/A')
            
            text = (
                f"❌ **No se encontraron archivos**\n\n"
                f"📂 **Categoría:** {categoria_nombre}\n"
                f"📄 **Tipo:** {subtipo_nombre}\n"
                f"📅 **Período:** {periodo}\n"
                f"🏢 **Empresa:** {escape_markdown(empresa_nombre)}\n\n"
                f"¿Quieres buscar en otro período?"
            )
            
            # ✅ Agregar botones inline
            keyboard = [
                [InlineKeyboardButton("✅ Sí, buscar otro período", callback_data="download_buscar_otro_periodo")],
                [InlineKeyboardButton("🔙 Volver al menú", callback_data="download_volver_menu")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            # Detectar si es Message o CallbackQuery
            if hasattr(message_or_query, 'edit_message_text'):
                await message_or_query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')
            else:
                await message_or_query.reply_text(text, reply_markup=reply_markup, parse_mode='Markdown')
            
            # ✅ Mantener sesión activa para permitir buscar otro período
            chat_id = message_or_query.chat.id if hasattr(message_or_query, 'chat') else message_or_query.message.chat.id
            session_manager = get_session_manager()
            session = session_manager.get_session(chat_id)
            if session:
                # Actualizar estado para permitir buscar otro período
                session_manager.update_session(
                    chat_id=chat_id,
                    estado='sin_archivos',
                    data=session.get('data', {})
                )
            return
        
        # ✅ CRÍTICO: Si hay solo 1 archivo, mostrarlo DIRECTAMENTE sin menú
        if len(archivos) == 1:
            logger.info(f"✅ Solo 1 archivo encontrado, mostrando directamente (sin botón 'descargar todos')")
            archivo = archivos[0]
            categoria_nombre = get_categoria_nombre(intent.get('categoria') or archivo.get('categoria', ''))
            subtipo_nombre = get_subtipo_nombre(
                intent.get('categoria') or archivo.get('categoria', ''),
                intent.get('subtipo') or archivo.get('subtipo', '')
            )
            periodo = intent.get('periodo') or archivo.get('periodo', 'N/A')
            empresa_nombre = intent.get('empresa_nombre', 'N/A')
            
            storage_service = get_storage_service()
            archivo_id = archivo.get('id')
            nombre = escape_markdown(archivo.get('nombre_original', archivo.get('nombre_archivo', 'Sin nombre')))
            
            # Regenerar URL firmada
            url = await storage_service.get_file_url(archivo_id, regenerate=True) if archivo_id else archivo.get('url_archivo', '')
            
            logger.info(f"📄 Mostrando archivo único: {nombre}, URL generada: {url is not None}")
            
            text = (
                f"✅ **Archivo encontrado**\n\n"
                f"📂 **Categoría:** {categoria_nombre}\n"
                f"📄 **Tipo:** {subtipo_nombre}\n"
                f"📅 **Período:** {periodo}\n"
                f"🏢 **Empresa:** {escape_markdown(empresa_nombre)}\n\n"
            )
            
            # ✅ Usar botón inline para descarga (más robusto que Markdown)
            if url:
                keyboard = [[InlineKeyboardButton("📥 Descargar archivo", url=url)]]
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                # Texto sin el enlace (se usa el botón)
                text += f"📎 **Archivo:** {nombre}"
                
                # Detectar si es Message o CallbackQuery
                if hasattr(message_or_query, 'edit_message_text'):
                    await message_or_query.edit_message_text(
                        text, 
                        reply_markup=reply_markup,
                        parse_mode='Markdown'
                    )
                else:
                    await message_or_query.reply_text(
                        text,
                        reply_markup=reply_markup, 
                        parse_mode='Markdown'
                    )
            else:
                text += f"📎 **Archivo:** {nombre}\n⚠️ Error al generar URL de descarga"
                if hasattr(message_or_query, 'edit_message_text'):
                    await message_or_query.edit_message_text(text, parse_mode='Markdown')
                else:
                    await message_or_query.reply_text(text, parse_mode='Markdown')
            return
        
        # Si hay múltiples archivos (más de 1), mostrar menú de selección
        logger.info(f"📋 Múltiples archivos encontrados ({len(archivos)}), mostrando menú de selección")
        await FileDownloadHandler._mostrar_menu_seleccion_archivos(
            message_or_query, archivos, intent
        )
    
    @staticmethod
    async def _mostrar_menu_seleccion_archivos(message_or_query, archivos: list, intent: dict):
        """Mostrar menú para seleccionar archivo(s) cuando hay múltiples"""
        logger.info(f"📋 _mostrar_menu_seleccion_archivos - {len(archivos)} archivos")
        logger.info(f"📋 Intent recibido: {intent}")
        
        # Listar todos los archivos que se van a mostrar
        for idx, archivo in enumerate(archivos, 1):
            logger.info(f"   {idx}. {archivo.get('nombre_original', 'Sin nombre')} - Período: {archivo.get('periodo')} - ID: {archivo.get('id')}")
        
        categoria_nombre = get_categoria_nombre(intent.get('categoria', ''))
        subtipo_nombre = get_subtipo_nombre(
            intent.get('categoria', ''),
            intent.get('subtipo', '')
        )
        periodo = intent.get('periodo', 'N/A')
        empresa_nombre = intent.get('empresa_nombre', 'N/A')
        
        text = (
            f"✅ **Encontré {len(archivos)} archivo(s)**\n\n"
            f"📂 **Categoría:** {categoria_nombre}\n"
            f"📄 **Tipo:** {subtipo_nombre}\n"
            f"📅 **Período:** {periodo}\n"
            f"🏢 **Empresa:** {escape_markdown(empresa_nombre)}\n\n"
            f"Selecciona el archivo que deseas descargar:"
        )
        
        # ✅ Guardar IDs de archivos Y datos del intent en la sesión para acceso posterior
        from app.services.session_manager import get_session_manager
        session_manager = get_session_manager()
        chat_id = message_or_query.chat.id if hasattr(message_or_query, 'chat') else message_or_query.message.chat.id
        session = session_manager.get_session(chat_id)
        
        # Preparar datos de sesión
        session_data = session.get('data', {}) if session else {}
        session_data['archivos_encontrados'] = [archivo.get('id') for archivo in archivos]
        # ✅ CRÍTICO: Guardar también los datos del intent para que estén disponibles después
        session_data['categoria'] = intent.get('categoria')
        session_data['subtipo'] = intent.get('subtipo')
        session_data['periodo'] = intent.get('periodo')
        session_data['empresa_nombre'] = intent.get('empresa_nombre')
        session_data['empresa_id'] = intent.get('empresa_id')
        
        if session:
            # ✅ IMPORTANTE: Actualizar sesión manteniendo el intent existente
            session_manager.update_session(
                chat_id=chat_id,
                estado='seleccionando_archivo', 
                data=session_data
            )
            logger.info(f"✅ Sesión actualizada con {len(archivos)} archivos y datos del intent")
        else:
            # Crear sesión si no existe (fallback)
            session_manager.create_session(
                chat_id=chat_id,
                intent='descargar_archivo',
                estado='seleccionando_archivo',
                data=session_data
            )
            logger.info(f"✅ Sesión creada con {len(archivos)} archivos y datos del intent")
        
        logger.info(f"✅ Session data guardado: categoria={session_data.get('categoria')}, subtipo={session_data.get('subtipo')}, periodo={session_data.get('periodo')}")
        
        # ✅ Crear botones individuales (máximo 10 archivos)
        from app.utils.file_types import organizar_botones_en_columnas
        keyboard = []
        
        # Botones individuales (máximo 10)
        botones_archivos = []
        max_mostrar = min(len(archivos), 10)
        
        for i, archivo in enumerate(archivos[:max_mostrar], 1):
            nombre = archivo.get('nombre_original', archivo.get('nombre_archivo', f'Archivo {i}'))
            # Truncar nombre si es muy largo
            if len(nombre) > 30:
                nombre = nombre[:27] + "..."
            botones_archivos.append(InlineKeyboardButton(
                f"{i}. {nombre}",
                callback_data=f"download_file_{archivo.get('id')}"
            ))
        
        # Organizar en 2 columnas
        keyboard.extend(organizar_botones_en_columnas(botones_archivos, columnas=2))
        
        # Si hay más de 10 archivos, mostrar aviso
        if len(archivos) > 10:
            keyboard.append([InlineKeyboardButton(
                f"⚠️ Solo se muestran los primeros 10 de {len(archivos)}",
                callback_data="download_info_limite"
            )])
        
        keyboard.append([InlineKeyboardButton("❌ Cancelar", callback_data="download_cancelar")])
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        # Detectar si es Message o CallbackQuery
        if hasattr(message_or_query, 'edit_message_text'):
            await message_or_query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')
        else:
            await message_or_query.reply_text(text, reply_markup=reply_markup, parse_mode='Markdown')
    
    @staticmethod
    async def _finalizar_descarga(message_or_query, session_data: dict, empresas: list):
        """Finalizar descarga con datos completos de la sesión"""
        chat_id = message_or_query.chat.id if hasattr(message_or_query, 'chat') else message_or_query.message.chat.id
        
        logger.info(f"📦 FINALIZAR DESCARGA - chat_id: {chat_id}")
        logger.info(f"📦 Session data completo: {session_data}")
        
        # Determinar empresa_id
        empresa_id = session_data.get('empresa_id')
        if not empresa_id and len(empresas) == 1:
            empresa_id = empresas[0]['id']
            logger.info(f"📦 Auto-asignado empresa_id: {empresa_id}")
        
        if not empresa_id:
            logger.error(f"❌ No se pudo determinar empresa_id")
            text = "❌ No se pudo determinar la empresa."
            if hasattr(message_or_query, 'edit_message_text'):
                await message_or_query.edit_message_text(text)
            else:
                await message_or_query.reply_text(text)
            return
        
        logger.info(f"📦 Llamando a _buscar_archivos con:")
        logger.info(f"  • empresa_id: {empresa_id}")
        logger.info(f"  • categoria: {session_data.get('categoria')}")
        logger.info(f"  • subtipo: {session_data.get('subtipo')}")
        logger.info(f"  • periodo: {session_data.get('periodo')}")
        
        # Buscar archivos
        archivos = await FileDownloadHandler._buscar_archivos(
            empresa_id=empresa_id,
            categoria=session_data.get('categoria'),
            subtipo=session_data.get('subtipo'),
            periodo=session_data.get('periodo')
        )
        
        logger.info(f"📦 Archivos recibidos de _buscar_archivos: {len(archivos)}")
        
        # Construir intent para respuesta con datos completos
        intent = {
            'categoria': session_data.get('categoria'),
            'subtipo': session_data.get('subtipo'),
            'periodo': session_data.get('periodo'),
            'empresa_id': empresa_id,
            'empresa_nombre': session_data.get('empresa_nombre') or (empresas[0]['nombre'] if empresas else 'N/A')
        }
        
        logger.info(f"📦 Intent construido para respuesta:")
        logger.info(f"  • categoria: {intent.get('categoria')}")
        logger.info(f"  • subtipo: {intent.get('subtipo')}")
        logger.info(f"  • periodo: {intent.get('periodo')}")
        logger.info(f"  • empresa_id: {intent.get('empresa_id')}")
        logger.info(f"  • empresa_nombre: {intent.get('empresa_nombre')}")
        
        # Responder con archivos
        await FileDownloadHandler._responder_con_archivos(message_or_query, archivos, intent, empresas)
        
        # ✅ CRÍTICO: NO limpiar sesión aquí si hay múltiples archivos
        # La sesión se limpia cuando el usuario selecciona un archivo o cancela
        # Solo limpiar si hay UN SOLO archivo (descarga directa completada)
        if archivos and len(archivos) == 1:
            logger.info(f"🧹 Limpiando sesión después de descarga directa de 1 archivo")
            session_manager = get_session_manager()
            session_manager.clear_session(chat_id)
        elif archivos and len(archivos) > 1:
            logger.info(f"📋 Sesión mantenida para selección de archivos múltiples ({len(archivos)} archivos)")
    
    @staticmethod
    async def handle_download_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Manejar callbacks del flujo de descarga"""
        query = update.callback_query
        await query.answer()
        
        chat_id = update.effective_chat.id
        
        # Validar usuario
        validation = security.validate_user(chat_id)
        if not validation['valid']:
            await query.edit_message_text(validation['message'])
            return
        
        user_data = validation['user_data']
        session_manager = get_session_manager()
        session = session_manager.get_session(chat_id)
        
        logger.info(f"🔍 handle_download_callback - chat_id: {chat_id}")
        logger.info(f"🔍 Sesión encontrada: {session is not None}")
        if session:
            logger.info(f"🔍 Intent de sesión: {session.get('intent')}")
            logger.info(f"🔍 Estado de sesión: {session.get('estado')}")
            logger.info(f"🔍 Datos de sesión: {session.get('data', {})}")
        
        if not session or session.get('intent') != 'descargar_archivo':
            logger.error(f"❌ No hay sesión válida - sesión: {session is not None}, intent: {session.get('intent') if session else 'N/A'}")
            await query.edit_message_text("❌ No hay una descarga en proceso.")
            return
        
        callback_data = query.data
        logger.info(f"🔍 Callback recibido en handle_download_callback: '{callback_data}'")
        
        # Cancelar
        if callback_data == "download_cancelar":
            logger.info(f"❌ Usuario canceló descarga para chat_id={chat_id}")
            session_manager.clear_session(chat_id)
            from app.bots.handlers.production_handlers import ProductionHandlers
            # ✅ security ya está importado al inicio del archivo
            validation = security.validate_user(chat_id)
            if validation['valid']:
                user_data = validation['user_data']
                await query.edit_message_text("❌ Descarga cancelada.")
                # Mostrar menú principal después de cancelar
                await ProductionHandlers._show_main_menu(query.message, user_data)
            else:
                await query.edit_message_text("❌ Descarga cancelada.")
            return
        
        # Buscar otro período (cuando no se encontraron archivos)
        if callback_data == "download_buscar_otro_periodo":
            session_manager.update_session(
                chat_id=chat_id,
                estado='esperando_periodo',
                data=session.get('data', {})  # Mantener categoría y subtipo
            )
            await FileDownloadHandler._ask_periodo(query)
            return
        
        # Volver al menú principal (cuando no se encontraron archivos)
        if callback_data == "download_volver_menu":
            session_manager.clear_session(chat_id)
            from app.bots.handlers.production_handlers import ProductionHandlers
            # ✅ security ya está importado al inicio del archivo
            validation = security.validate_user(chat_id)
            if validation['valid']:
                user_data = validation['user_data']
                # Enviar mensaje nuevo con el menú principal
                await query.message.reply_text("🔙 Volviendo al menú principal...")
                await ProductionHandlers._show_main_menu(query.message, user_data)
                # Eliminar mensaje anterior
                await query.edit_message_text("✅ Sesión cancelada")
            else:
                await query.edit_message_text("❌ Error al volver al menú.")
            return
        
        # Descargar archivo individual
        if callback_data.startswith("download_file_"):
            archivo_id = callback_data.replace("download_file_", "")
            await FileDownloadHandler._enviar_archivo_individual(query, archivo_id)
            return
        
        # Info sobre límite de archivos (solo mensaje informativo)
        if callback_data == "download_info_limite":
            await query.answer(
                "ℹ️ Solo se muestran los primeros 10 archivos. "
                "Usa filtros más específicos para reducir resultados.",
                show_alert=True
            )
            return
        
        # Volver a categoría
        if callback_data == "download_back_categoria":
            session_manager.update_session(
                chat_id=chat_id,
                estado='esperando_categoria',
                data={}  # Limpiar subtipo
            )
            await FileDownloadHandler._ask_categoria(query)
            return
        
        # Seleccionar categoría (debe ir ANTES de empresa para evitar conflictos)
        if callback_data.startswith("download_categoria_"):
            categoria = callback_data.replace("download_categoria_", "")
            logger.info(f"📁 Categoría seleccionada: '{categoria}' para chat_id={chat_id}")
            
            if not validar_categoria(categoria):
                logger.warning(f"⚠️ Categoría inválida: '{categoria}'")
                await query.edit_message_text("❌ Categoría inválida.")
                return
            
            logger.info(f"✅ Categoría válida, actualizando sesión y mostrando subtipos")
            session_data = session.get('data', {})
            session_data['categoria'] = categoria
            session_manager.update_session(
                chat_id=chat_id,
                estado='esperando_subtipo',
                data=session_data
            )
            logger.info(f"📋 Sesión actualizada. Llamando a _ask_subtipo con categoría: '{categoria}'")
            try:
                # Asegurar que query esté disponible
                if not query:
                    logger.error(f"❌ Query es None")
                    return
                logger.info(f"📋 Query disponible, editando mensaje...")
                await FileDownloadHandler._ask_subtipo(query, categoria)
                logger.info(f"✅ _ask_subtipo ejecutado correctamente para chat_id={chat_id}")
            except Exception as e:
                logger.error(f"❌ Error en _ask_subtipo para chat_id={chat_id}: {e}", exc_info=True)
                try:
                    await query.edit_message_text(
                        f"❌ Error al mostrar subtipos: {str(e)}\n\n"
                        f"Por favor, intenta nuevamente o presiona Cancelar.",
                        reply_markup=InlineKeyboardMarkup([[
                            InlineKeyboardButton("❌ Cancelar", callback_data="download_cancelar")
                        ]])
                    )
                except Exception as e2:
                    logger.error(f"❌ Error al mostrar mensaje de error: {e2}", exc_info=True)
            return  # ✅ Agregar return para evitar que continúe
        
        # Seleccionar empresa
        elif callback_data.startswith("download_empresa_"):
            empresa_id = callback_data.replace("download_empresa_", "")
            empresa = supabase.table('empresas').select('*').eq('id', empresa_id).execute()
            
            if empresa.data:
                # ✅ Obtener datos actuales de la sesión (ya contiene categoria, subtipo, periodo)
                session_data = session.get('data', {})
                logger.info(f"🏢 Datos de sesión ANTES de agregar empresa: {session_data}")
                
                # Agregar empresa a los datos existentes
                session_data['empresa_id'] = empresa_id
                session_data['empresa_nombre'] = empresa.data[0]['nombre']
                
                logger.info(f"🏢 Datos de sesión DESPUÉS de agregar empresa: {session_data}")
                
                session_manager.update_session(
                    chat_id=chat_id,
                    estado='procesando',
                    data=session_data
                )
                
                # Continuar con descarga
                empresas = await FileDownloadHandler._get_user_empresas(chat_id)
                await FileDownloadHandler._finalizar_descarga(query, session_data, empresas)
            else:
                await query.edit_message_text("❌ Empresa no encontrada.")
                return
        
        # Seleccionar subtipo
        elif callback_data.startswith("download_subtipo_"):
            parts = callback_data.replace("download_subtipo_", "").split("_", 1)
            if len(parts) != 2:
                await query.edit_message_text("❌ Subtipo inválido.")
                return
            
            categoria = parts[0]
            subtipo = parts[1]
            
            if not validar_subtipo(categoria, subtipo):
                await query.edit_message_text("❌ Subtipo inválido.")
                return
            
            session_data = session.get('data', {})
            session_data['subtipo'] = subtipo
            
            session_manager.update_session(
                chat_id=chat_id,
                estado='esperando_periodo',
                data=session_data
            )
            await FileDownloadHandler._ask_periodo(query)
        
        # Seleccionar período
        elif callback_data.startswith("download_periodo_"):
            periodo = callback_data.replace("download_periodo_", "")
            
            if periodo == "actual":
                periodo = datetime.now().strftime("%Y-%m")
            elif periodo == "anterior":
                mes_anterior = datetime.now().replace(day=1) - timedelta(days=1)
                periodo = mes_anterior.strftime("%Y-%m")
            elif periodo == "otro":
                session_manager.update_session(
                    chat_id=chat_id,
                    estado='esperando_periodo_texto_ia'  # ✅ Estado para análisis con IA
                )
                await query.edit_message_text(
                    "📅 **¿Qué período necesitas?**\n\n"
                    "Puedes escribir:\n"
                    "• 'mayo 2024'\n"
                    "• 'marzo del año pasado'\n"
                    "• '2024-05'\n"
                    "• 'el mes pasado'\n"
                    "• O cualquier fecha que necesites",
                    parse_mode='Markdown'
                )
                return
            
            # Validar formato
            try:
                datetime.strptime(periodo, "%Y-%m")
            except ValueError:
                await query.edit_message_text("❌ Formato de período inválido. Usa AAAA-MM")
                return
            
            session_data = session.get('data', {})
            session_data['periodo'] = periodo
            
            # ✅ Verificar si necesita preguntar por empresa
            empresas = await FileDownloadHandler._get_user_empresas(chat_id)
            logger.info(f"🏢 Usuario tiene {len(empresas)} empresa(s)")
            logger.info(f"📋 session_data actual: empresa_id={session_data.get('empresa_id')}, categoria={session_data.get('categoria')}, subtipo={session_data.get('subtipo')}, periodo={periodo}")
            
            if len(empresas) > 1 and not session_data.get('empresa_id'):
                # Usuario tiene múltiples empresas y no ha seleccionado una
                logger.info(f"✅ Usuario tiene {len(empresas)} empresas, preguntando cuál seleccionar")
                session_manager.update_session(
                    chat_id=chat_id,
                    estado='esperando_empresa',
                    data=session_data
                )
                # ✅ Pasar session_data como intent para mantener categoría, subtipo, período
                intent_para_empresa = {
                    'categoria': session_data.get('categoria'),
                    'subtipo': session_data.get('subtipo'),
                    'periodo': session_data.get('periodo')
                }
                await FileDownloadHandler._ask_empresa(query, empresas, intent_para_empresa)
                return  # ✅ CRÍTICO: No continuar después de preguntar empresa
            else:
                # Usuario tiene solo una empresa o ya seleccionó una
                logger.info(f"✅ Usuario tiene 1 empresa o ya seleccionó: auto-asignando")
                if not session_data.get('empresa_id') and len(empresas) == 1:
                    session_data['empresa_id'] = empresas[0]['id']
                    session_data['empresa_nombre'] = empresas[0]['nombre']
                    logger.info(f"✅ Auto-asignado empresa_id: {empresas[0]['id']} ({empresas[0]['nombre']})")
                
                session_manager.update_session(
                    chat_id=chat_id,
                    estado='listo',
                    data=session_data
                )
                # Finalizar descarga
                await FileDownloadHandler._finalizar_descarga(query, session_data, empresas)
                return
    
    @staticmethod
    async def _enviar_archivo_individual(query, archivo_id: str):
        """Enviar un archivo individual al usuario"""
        try:
            storage_service = get_storage_service()
            url = await storage_service.get_file_url(archivo_id, regenerate=True)
            
            if not url:
                await query.answer("❌ No se pudo obtener el archivo", show_alert=True)
                return
            
            # Obtener información del archivo para mostrar nombre
            from app.database.supabase import supabase
            file_info = supabase.table('archivos').select('nombre_original, nombre_archivo').eq('id', archivo_id).execute()
            
            nombre = "Archivo"
            if file_info.data:
                nombre = file_info.data[0].get('nombre_original') or file_info.data[0].get('nombre_archivo', 'Archivo')
            
            # ✅ Usar botón inline para descarga (más robusto)
            text = f"✅ **Archivo listo para descargar**\n\n📄 **{escape_markdown(nombre)}**"
            keyboard = [[InlineKeyboardButton("📥 Descargar archivo", url=url)]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')
            
            # Limpiar sesión
            session_manager = get_session_manager()
            session_manager.clear_session(query.message.chat.id)
            
        except Exception as e:
            logger.error(f"Error enviando archivo individual: {e}")
            await query.answer("❌ Error al obtener el archivo", show_alert=True)
    
    @staticmethod
    async def _enviar_todos_los_archivos(query, session: dict):
        """Enviar todos los archivos encontrados al usuario"""
        try:
            session_data = session.get('data', {})
            archivos_ids = session_data.get('archivos_encontrados', [])
            
            if not archivos_ids:
                await query.answer("❌ No hay archivos para descargar", show_alert=True)
                return
            
            storage_service = get_storage_service()
            from app.database.supabase import supabase
            
            text = "✅ **Archivos listos para descargar**\n\n"
            text += "Haz clic en cada botón para descargar:\n\n"
            
            # ✅ Crear botones inline para cada archivo (máximo 8 para no saturar)
            keyboard = []
            archivos_encontrados = 0
            
            # Obtener información de todos los archivos
            for idx, archivo_id in enumerate(archivos_ids[:8], 1):  # Máximo 8 archivos
                try:
                    url = await storage_service.get_file_url(archivo_id, regenerate=True)
                    if url:
                        file_info = supabase.table('archivos').select('nombre_original, nombre_archivo').eq('id', archivo_id).execute()
                        nombre = "Archivo"
                        if file_info.data:
                            nombre = file_info.data[0].get('nombre_original') or file_info.data[0].get('nombre_archivo', 'Archivo')
                        
                        # Truncar nombre si es muy largo
                        if len(nombre) > 35:
                            nombre_boton = nombre[:32] + "..."
                        else:
                            nombre_boton = nombre
                        
                        # Agregar botón
                        keyboard.append([InlineKeyboardButton(f"📥 {idx}. {nombre_boton}", url=url)])
                        text += f"{idx}. {escape_markdown(nombre)}\n"
                        archivos_encontrados += 1
                except Exception as e:
                    logger.warning(f"Error obteniendo archivo {archivo_id}: {e}")
                    continue
            
            if archivos_encontrados == 0:
                await query.answer("❌ No se pudieron obtener los archivos", show_alert=True)
                return
            
            if len(archivos_ids) > 8:
                text += f"\n⚠️ Mostrando primeros 8 de {len(archivos_ids)} archivos"
            
            text += f"\n\n✅ {archivos_encontrados} archivo(s) disponible(s)"
            
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')
            
            # Limpiar sesión
            session_manager = get_session_manager()
            session_manager.clear_session(query.message.chat.id)
            
        except Exception as e:
            logger.error(f"Error enviando todos los archivos: {e}")
            await query.answer("❌ Error al obtener los archivos", show_alert=True)
    
    @staticmethod
    async def handle_text_during_download(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Manejar texto durante el flujo de descarga"""
        chat_id = update.effective_chat.id
        message_text = update.message.text.strip()
        
        logger.info(f"🔍 FileDownloadHandler.handle_text_during_download llamado: chat_id={chat_id}, texto='{message_text}'")
        
        session_manager = get_session_manager()
        session = session_manager.get_session(chat_id)
        
        if not session:
            logger.info(f"⚠️ No hay sesión activa para chat_id={chat_id}")
            return  # No es una sesión de descarga, dejar que otro handler lo procese
        
        if session.get('intent') != 'descargar_archivo':
            logger.info(f"⚠️ Sesión con intent diferente: {session.get('intent')}")
            return  # No es una sesión de descarga, dejar que otro handler lo procese
        
        estado = session.get('estado')
        logger.info(f"📝 Procesando texto durante descarga: chat_id={chat_id}, estado={estado}, texto='{message_text}'")
        
        # Procesar período con análisis de IA
        if estado == 'esperando_periodo_texto_ia':
            try:
                # ✅ Usar IA para analizar el texto
                ai_service = get_ai_service()
                conversation_logger = get_conversation_logger()
                historial = await conversation_logger.get_user_conversation_history(chat_id, limit=3)
                
                periodo_result = await ai_service.extract_periodo_from_text(message_text, historial)
                logger.info(f"🔍 Resultado análisis período: {periodo_result}")
                
                if periodo_result and periodo_result.get('periodo'):
                    periodo = periodo_result['periodo']
                    confianza = periodo_result.get('confianza', 0.0)
                    interpretacion = periodo_result.get('interpretacion', '')
                    
                    # Si confianza es alta, usar directamente
                    if confianza >= 0.75:
                        session_data = session.get('data', {})
                        session_data['periodo'] = periodo
                        
                        # ✅ Verificar si necesita preguntar por empresa
                        empresas = await FileDownloadHandler._get_user_empresas(chat_id)
                        logger.info(f"🏢 Usuario tiene {len(empresas)} empresa(s) (IA alta confianza)")
                        
                        if len(empresas) > 1 and not session_data.get('empresa_id'):
                            # Usuario tiene múltiples empresas y no ha seleccionado una
                            logger.info(f"✅ Usuario tiene {len(empresas)} empresas, preguntando cuál seleccionar")
                            session_manager.update_session(
                                chat_id=chat_id,
                                estado='esperando_empresa',
                                data=session_data
                            )
                            intent_para_empresa = {
                                'categoria': session_data.get('categoria'),
                                'subtipo': session_data.get('subtipo'),
                                'periodo': session_data.get('periodo')
                            }
                            await FileDownloadHandler._ask_empresa(update.message, empresas, intent_para_empresa)
                        else:
                            # Usuario tiene solo una empresa o ya seleccionó una
                            if not session_data.get('empresa_id') and len(empresas) == 1:
                                session_data['empresa_id'] = empresas[0]['id']
                                session_data['empresa_nombre'] = empresas[0]['nombre']
                            
                            session_manager.update_session(
                                chat_id=chat_id,
                                estado='listo',
                                data=session_data
                            )
                            
                            await FileDownloadHandler._finalizar_descarga(
                                update.message, session_data, empresas
                            )
                    else:
                        # Confianza baja: confirmar con usuario
                        await update.message.reply_text(
                            f"📅 **¿Te refieres a {periodo}?**\n\n"
                            f"Interpretación: {interpretacion}\n\n"
                            f"Confianza: {confianza:.0%}\n\n"
                            f"Si es correcto, escribe 'sí' o 'correcto'.\n"
                            f"Si no, escribe el período correcto.",
                            parse_mode='Markdown'
                        )
                        # Guardar período propuesto en sesión para confirmación
                        session_data = session.get('data', {})
                        session_data['periodo_propuesto'] = periodo
                        session_manager.update_session(
                            chat_id=chat_id,
                            estado='confirmando_periodo',
                            data=session_data
                        )
                else:
                    # Fallback: intentar formato YYYY-MM
                    try:
                        datetime.strptime(message_text, "%Y-%m")
                        session_data = session.get('data', {})
                        session_data['periodo'] = message_text
                        
                        # ✅ Verificar si necesita preguntar por empresa (igual que en callback)
                        empresas = await FileDownloadHandler._get_user_empresas(chat_id)
                        logger.info(f"🏢 Usuario tiene {len(empresas)} empresa(s)")
                        logger.info(f"📋 session_data: empresa_id={session_data.get('empresa_id')}, categoria={session_data.get('categoria')}, subtipo={session_data.get('subtipo')}, periodo={message_text}")
                        
                        if len(empresas) > 1 and not session_data.get('empresa_id'):
                            # Usuario tiene múltiples empresas y no ha seleccionado una
                            logger.info(f"✅ Usuario tiene {len(empresas)} empresas, preguntando cuál seleccionar")
                            session_manager.update_session(
                                chat_id=chat_id,
                                estado='esperando_empresa',
                                data=session_data
                            )
                            # Pasar session_data como intent para mantener datos
                            intent_para_empresa = {
                                'categoria': session_data.get('categoria'),
                                'subtipo': session_data.get('subtipo'),
                                'periodo': session_data.get('periodo')
                            }
                            await FileDownloadHandler._ask_empresa(update.message, empresas, intent_para_empresa)
                        else:
                            # Usuario tiene solo una empresa o ya seleccionó una
                            logger.info(f"✅ Usuario tiene 1 empresa o ya seleccionó: auto-asignando")
                            if not session_data.get('empresa_id') and len(empresas) == 1:
                                session_data['empresa_id'] = empresas[0]['id']
                                session_data['empresa_nombre'] = empresas[0]['nombre']
                                logger.info(f"✅ Auto-asignado empresa_id: {empresas[0]['id']} ({empresas[0]['nombre']})")
                            
                            session_manager.update_session(
                                chat_id=chat_id,
                                estado='listo',
                                data=session_data
                            )
                            # Finalizar descarga
                            await FileDownloadHandler._finalizar_descarga(
                                update.message, session_data, empresas
                            )
                    except ValueError:
                        await update.message.reply_text(
                            "❌ No pude entender el período. Por favor, escribe:\n"
                            "• Un formato `AAAA-MM` (ejemplo: `2024-05`)\n"
                            "• O una fecha en lenguaje natural (ejemplo: 'mayo 2024' o 'febrero del año pasado')",
                            parse_mode='Markdown'
                        )
            except Exception as e:
                logger.error(f"❌ Error procesando período con IA: {e}", exc_info=True)
                await update.message.reply_text(
                    "❌ Error al procesar el período. Por favor, intenta con formato `AAAA-MM` (ejemplo: `2024-02`).",
                    parse_mode='Markdown'
                )
        
        # Confirmar período propuesto
        elif estado == 'confirmando_periodo':
            texto_lower = message_text.lower().strip()
            if texto_lower in ['sí', 'si', 'correcto', 'ok', 's', 'yes']:
                session_data = session.get('data', {})
                periodo = session_data.get('periodo_propuesto')
                
                if periodo:
                    session_data['periodo'] = periodo
                    session_data.pop('periodo_propuesto', None)
                    
                    # ✅ Verificar si necesita preguntar por empresa
                    empresas = await FileDownloadHandler._get_user_empresas(chat_id)
                    logger.info(f"🏢 Usuario tiene {len(empresas)} empresa(s) (confirmando período)")
                    
                    if len(empresas) > 1 and not session_data.get('empresa_id'):
                        # Usuario tiene múltiples empresas y no ha seleccionado una
                        session_manager.update_session(
                            chat_id=chat_id,
                            estado='esperando_empresa',
                            data=session_data
                        )
                        intent_para_empresa = {
                            'categoria': session_data.get('categoria'),
                            'subtipo': session_data.get('subtipo'),
                            'periodo': session_data.get('periodo')
                        }
                        await FileDownloadHandler._ask_empresa(update.message, empresas, intent_para_empresa)
                    else:
                        # Usuario tiene solo una empresa o ya seleccionó una
                        if not session_data.get('empresa_id') and len(empresas) == 1:
                            session_data['empresa_id'] = empresas[0]['id']
                            session_data['empresa_nombre'] = empresas[0]['nombre']
                        
                        session_manager.update_session(
                            chat_id=chat_id,
                            estado='listo',
                            data=session_data
                        )
                        
                        await FileDownloadHandler._finalizar_descarga(
                            update.message, session_data, empresas
                        )
                else:
                    await update.message.reply_text("❌ Error: No hay período propuesto. Intenta nuevamente.")
            else:
                # Usuario corrigió, intentar analizar nuevamente
                session_manager.update_session(
                    chat_id=chat_id,
                    estado='esperando_periodo_texto_ia'
                )
                # Recursivamente procesar el nuevo texto
                await FileDownloadHandler.handle_text_during_download(update, context)
        
        # Procesar período en formato texto (legacy, mantener compatibilidad)
        elif estado == 'esperando_periodo_texto':
            try:
                datetime.strptime(message_text, "%Y-%m")
                session_data = session.get('data', {})
                session_data['periodo'] = message_text
                
                # ✅ Verificar si necesita preguntar por empresa
                empresas = await FileDownloadHandler._get_user_empresas(chat_id)
                logger.info(f"🏢 Usuario tiene {len(empresas)} empresa(s) (legacy texto)")
                
                if len(empresas) > 1 and not session_data.get('empresa_id'):
                    # Usuario tiene múltiples empresas y no ha seleccionado una
                    session_manager.update_session(
                        chat_id=chat_id,
                        estado='esperando_empresa',
                        data=session_data
                    )
                    intent_para_empresa = {
                        'categoria': session_data.get('categoria'),
                        'subtipo': session_data.get('subtipo'),
                        'periodo': session_data.get('periodo')
                    }
                    await FileDownloadHandler._ask_empresa(update.message, empresas, intent_para_empresa)
                else:
                    # Usuario tiene solo una empresa o ya seleccionó una
                    if not session_data.get('empresa_id') and len(empresas) == 1:
                        session_data['empresa_id'] = empresas[0]['id']
                        session_data['empresa_nombre'] = empresas[0]['nombre']
                    
                    session_manager.update_session(
                        chat_id=chat_id,
                        estado='listo',
                        data=session_data
                    )
                    
                    await FileDownloadHandler._finalizar_descarga(
                        update.message, session_data, empresas
                    )
            except ValueError:
                await update.message.reply_text(
                    "❌ Formato inválido. Usa el formato `AAAA-MM` (ejemplo: `2024-05`)",
                    parse_mode='Markdown'
                )

