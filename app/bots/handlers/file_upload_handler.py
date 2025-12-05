"""
📤 Handler de Subida de Archivos
Maneja el flujo conversacional para subir archivos al sistema
Reportes financieros se suben también a OpenAI para el Asesor IA
"""

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from app.security.auth import security
from app.database.supabase import supabase
from app.services.session_manager import get_session_manager
from app.services.storage_service import get_storage_service
from app.services.ai_service import get_ai_service
from app.services.conversation_logger import get_conversation_logger
from app.services.openai_assistant_service import get_assistant_service
from app.utils.file_types import (
    get_botones_categorias,
    get_botones_subtipos,
    get_categoria_nombre,
    get_subtipo_nombre,
    requiere_descripcion,
    validar_categoria,
    validar_subtipo
)
from app.decorators.conversation_logging import log_production_conversation
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

# Subtipos que se suben a OpenAI para el Asesor IA (solo reportes financieros)
SUBTIPOS_PARA_OPENAI = [
    'reporte_mensual',
    'estados_financieros'
]

# Extensiones de archivo que se suben a OpenAI
EXTENSIONES_OPENAI = ['.pdf']


def escape_markdown(text):
    """Escapar caracteres especiales para Markdown"""
    if not text:
        return text
    return text.replace('_', '\\_').replace('*', '\\*').replace('[', '\\[').replace(']', '\\]').replace('`', '\\`')

class FileUploadHandler:
    """Manejador de subida de archivos"""
    
    @staticmethod
    @log_production_conversation
    async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Manejar cuando el usuario envía un documento"""
        chat_id = update.effective_chat.id
        
        # Validar usuario
        validation = security.validate_user(chat_id)
        if not validation['valid']:
            await update.message.reply_text(validation['message'])
            return
        
        user_data = validation['user_data']
        document = update.message.document
        
        # Obtener información del archivo
        file_info = await context.bot.get_file(document.file_id)
        filename = document.file_name or f"archivo_{document.file_id}"
        
        # Verificar si hay sesión activa
        session_manager = get_session_manager()
        session = session_manager.get_session(chat_id)
        
        # Si hay sesión activa y es de subida, actualizar con archivo
        if session and session.get('intent') == 'subir_archivo':
            # Ya hay una subida en proceso, ignorar este archivo
            await update.message.reply_text(
                "⚠️ Ya tienes una subida en proceso. Completa o cancela la actual primero."
            )
            return
        
        # Iniciar nuevo flujo de subida
        # Paso 1: Identificar empresa
        empresas = await FileUploadHandler._get_user_empresas(chat_id)
        
        if not empresas:
            await update.message.reply_text(
                "❌ No tienes empresas asignadas. Contacta al administrador."
            )
            return
        
        # Si solo hay 1 empresa, asignarla automáticamente
        if len(empresas) == 1:
            empresa = empresas[0]
            # Crear sesión con empresa ya asignada
            session_data = {
                'empresa_id': empresa['id'],
                'empresa_nombre': empresa['nombre'],
                'nombre_original_archivo': filename,
                'file_id': document.file_id
            }
            
            session_manager.create_session(
                chat_id=chat_id,
                intent='subir_archivo',
                estado='esperando_categoria',
                data=session_data
            )
            
            # Preguntar por categoría
            await FileUploadHandler._ask_categoria(update.message, user_data)
        else:
            # Múltiples empresas: preguntar cuál
            session_data = {
                'nombre_original_archivo': filename,
                'file_id': document.file_id
            }
            
            session_manager.create_session(
                chat_id=chat_id,
                intent='subir_archivo',
                estado='esperando_empresa',
                data=session_data
            )
            
            await FileUploadHandler._ask_empresa(update.message, empresas)
    
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
    async def _ask_empresa(message, empresas: list):
        """Preguntar al usuario qué empresa"""
        text = "🏢 **¿De qué empresa es este archivo?**\n\nSelecciona una opción:"
        
        from app.utils.file_types import organizar_botones_en_columnas
        
        # Crear botones de empresas
        botones_empresas = []
        for empresa in empresas:
            botones_empresas.append(InlineKeyboardButton(
                f"🏢 {escape_markdown(empresa['nombre'])}",
                callback_data=f"upload_empresa_{empresa['id']}"
            ))
        
        # Organizar en 2 columnas
        keyboard = organizar_botones_en_columnas(botones_empresas, columnas=2)
        
        keyboard.append([InlineKeyboardButton("❌ Cancelar", callback_data="upload_cancelar")])
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await message.reply_text(text, reply_markup=reply_markup, parse_mode='Markdown')
    
    @staticmethod
    async def _ask_categoria(message_or_query, user_data):
        """Preguntar categoría del archivo"""
        text = "📁 **¿Qué tipo de archivo es?**\n\nSelecciona la categoría:"
        
        # Crear botones en 2 columnas
        botones = get_botones_categorias()
        keyboard = []
        row = []
        for boton in botones:
            row.append(InlineKeyboardButton(
                boton['text'],
                callback_data=f"upload_{boton['callback_data']}"
            ))
            if len(row) == 2:
                keyboard.append(row)
                row = []
        if row:
            keyboard.append(row)
        
        keyboard.append([InlineKeyboardButton("❌ Cancelar", callback_data="upload_cancelar")])
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        if hasattr(message_or_query, 'edit_message_text'):
            await message_or_query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')
        else:
            await message_or_query.reply_text(text, reply_markup=reply_markup, parse_mode='Markdown')
    
    @staticmethod
    async def handle_upload_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Manejar callbacks del flujo de subida"""
        query = update.callback_query
        await query.answer()
        
        chat_id = update.effective_chat.id
        callback_data = query.data
        logger.info(f"🔍 Callback recibido en handle_upload_callback: '{callback_data}' para chat_id={chat_id}")
        
        # Validar usuario
        validation = security.validate_user(chat_id)
        if not validation['valid']:
            await query.edit_message_text(validation['message'])
            return
        
        user_data = validation['user_data']
        session_manager = get_session_manager()
        session = session_manager.get_session(chat_id)
        
        if not session or session.get('intent') != 'subir_archivo':
            logger.info(f"⚠️ No hay sesión de subida activa para chat_id={chat_id}")
            await query.edit_message_text("❌ No hay una subida en proceso. Envía un archivo para comenzar.")
            return
        
        logger.info(f"📤 Sesión de subida encontrada, estado actual: {session.get('estado')}")
        
        # Cancelar
        if callback_data == "upload_cancelar":
            session_manager.clear_session(chat_id)
            await query.edit_message_text("❌ Subida cancelada.")
            return
        
        # Volver a categoría
        if callback_data == "upload_back_categoria":
            session_manager.update_session(
                chat_id=chat_id,
                estado='esperando_categoria',
                data={}  # Limpiar subtipo
            )
            await FileUploadHandler._ask_categoria(query, user_data)
            return
        
        # Seleccionar empresa
        if callback_data.startswith("upload_empresa_"):
            empresa_id = callback_data.replace("upload_empresa_", "")
            empresa = supabase.table('empresas').select('*').eq('id', empresa_id).execute()
            
            if empresa.data:
                session_manager.update_session(
                    chat_id=chat_id,
                    estado='esperando_categoria',
                    data={
                        'empresa_id': empresa_id,
                        'empresa_nombre': empresa.data[0]['nombre']
                    }
                )
                await FileUploadHandler._ask_categoria(query, user_data)
            else:
                await query.edit_message_text("❌ Empresa no encontrada.")
            return
        
        # Seleccionar categoría
        if callback_data.startswith("upload_categoria_"):
            categoria = callback_data.replace("upload_categoria_", "")
            
            if not validar_categoria(categoria):
                await query.edit_message_text("❌ Categoría inválida.")
                return
            
            session_manager.update_session(
                chat_id=chat_id,
                estado='esperando_subtipo',
                data={'categoria': categoria}
            )
            await FileUploadHandler._ask_subtipo(query, categoria, user_data)
            return
        
        # Seleccionar subtipo
        if callback_data.startswith("upload_subtipo_"):
            # Formato: upload_subtipo_legal_estatutos_empresa
            parts = callback_data.replace("upload_subtipo_", "").split("_", 1)
            if len(parts) != 2:
                await query.edit_message_text("❌ Subtipo inválido.")
                return
            
            categoria = parts[0]
            subtipo = parts[1]
            
            if not validar_subtipo(categoria, subtipo):
                await query.edit_message_text("❌ Subtipo inválido.")
                return
            
            session_data = {'subtipo': subtipo}
            
            # Si requiere descripción, pedirla
            if requiere_descripcion(categoria, subtipo):
                session_manager.update_session(
                    chat_id=chat_id,
                    estado='esperando_descripcion',
                    data=session_data
                )
                await FileUploadHandler._ask_descripcion(query, categoria, subtipo, user_data)
            else:
                # Continuar con período
                session_manager.update_session(
                    chat_id=chat_id,
                    estado='esperando_periodo',
                    data=session_data
                )
                await FileUploadHandler._ask_periodo(query, user_data)
            return
        
        # Seleccionar período
        if callback_data.startswith("upload_periodo_"):
            periodo = callback_data.replace("upload_periodo_", "")
            
            if periodo == "actual":
                periodo = datetime.now().strftime("%Y-%m")
            elif periodo == "anterior":
                # Mes anterior (mismo método que en descarga)
                mes_anterior = datetime.now().replace(day=1) - timedelta(days=1)
                periodo = mes_anterior.strftime("%Y-%m")
            elif periodo == "otro":
                session_manager.update_session(
                    chat_id=chat_id,
                    estado='esperando_periodo_texto_ia'  # ✅ Estado para análisis con IA
                )
                await query.edit_message_text(
                    "📅 **¿Para qué período es este archivo?**\n\n"
                    "Puedes escribir:\n"
                    "• 'mayo 2024'\n"
                    "• 'marzo del año pasado'\n"
                    "• '2024-05'\n"
                    "• 'el mes pasado'\n"
                    "• O cualquier fecha que necesites",
                    parse_mode='Markdown'
                )
                return
            
            # Validar formato YYYY-MM
            try:
                datetime.strptime(periodo, "%Y-%m")
            except ValueError:
                await query.edit_message_text("❌ Formato de período inválido. Usa AAAA-MM")
                return
            
            session_manager.update_session(
                chat_id=chat_id,
                estado='listo_para_subir',
                data={'periodo': periodo}
            )
            
            # Proceder con la subida
            await FileUploadHandler._process_upload(chat_id, query, user_data, context)
            return
    
    @staticmethod
    async def _ask_subtipo(query, categoria: str, user_data):
        """Preguntar subtipo del archivo"""
        text = f"📁 **{get_categoria_nombre(categoria)}**\n\nSelecciona el tipo específico:"
        
        # Crear botones en 2 columnas
        botones = get_botones_subtipos(categoria)
        keyboard = []
        row = []
        for boton in botones:
            row.append(InlineKeyboardButton(
                boton['text'],
                callback_data=f"upload_subtipo_{categoria}_{boton['callback_data'].replace(f'subtipo_{categoria}_', '')}"
            ))
            if len(row) == 2:
                keyboard.append(row)
                row = []
        if row:
            keyboard.append(row)
        
        keyboard.append([
            InlineKeyboardButton("🔙 Volver", callback_data="upload_back_categoria"),
            InlineKeyboardButton("❌ Cancelar", callback_data="upload_cancelar")
        ])
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')
    
    @staticmethod
    async def _ask_descripcion(query, categoria: str, subtipo: str, user_data):
        """Preguntar descripción personalizada"""
        text = (
            f"📝 **Descripción del archivo**\n\n"
            f"Categoría: {get_categoria_nombre(categoria)}\n"
            f"Tipo: {get_subtipo_nombre(categoria, subtipo)}\n\n"
            f"Escribe una descripción para identificar este archivo y presiona **Enviar** para continuar:"
        )
        
        keyboard = [[InlineKeyboardButton("❌ Cancelar", callback_data="upload_cancelar")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')
    
    @staticmethod
    async def _ask_periodo(message_or_query, user_data):
        """Preguntar período del archivo"""
        current_month = datetime.now().strftime("%Y-%m")
        last_month = (datetime.now().replace(day=1) - timedelta(days=1)).strftime("%Y-%m")
        
        text = "📅 **¿Para qué período es este archivo?**\n\nSelecciona una opción:"
        
        keyboard = [
            [
                InlineKeyboardButton(f"🟢 Actual ({current_month})", callback_data="upload_periodo_actual"),
                InlineKeyboardButton(f"🟡 Anterior ({last_month})", callback_data="upload_periodo_anterior")
            ],
            [
                InlineKeyboardButton("📅 Otro mes", callback_data="upload_periodo_otro"),
                InlineKeyboardButton("❌ Cancelar", callback_data="upload_cancelar")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        if hasattr(message_or_query, 'edit_message_text'):
            await message_or_query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')
        else:
            await message_or_query.reply_text(text, reply_markup=reply_markup, parse_mode='Markdown')
    
    @staticmethod
    async def handle_text_during_upload(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Manejar texto durante el flujo de subida"""
        chat_id = update.effective_chat.id
        message_text = update.message.text.strip()
        
        session_manager = get_session_manager()
        session = session_manager.get_session(chat_id)
        
        if not session or session.get('intent') != 'subir_archivo':
            # No hay subida en proceso, ignorar
            return
        
        estado = session.get('estado')
        
        # Procesar período con análisis de IA
        if estado == 'esperando_periodo_texto_ia':
            # ✅ Usar IA para analizar el texto
            ai_service = get_ai_service()
            conversation_logger = get_conversation_logger()
            historial = await conversation_logger.get_user_conversation_history(chat_id, limit=3)
            
            periodo_result = await ai_service.extract_periodo_from_text(message_text, historial)
            
            if periodo_result and periodo_result.get('periodo'):
                periodo = periodo_result['periodo']
                confianza = periodo_result.get('confianza', 0.0)
                interpretacion = periodo_result.get('interpretacion', '')
                
                # Si confianza es alta, usar directamente
                if confianza >= 0.75:
                    session_data = session.get('data', {})
                    session_data['periodo'] = periodo
                    
                    session_manager.update_session(
                        chat_id=chat_id,
                        estado='listo_para_subir',
                        data=session_data
                    )
                    
                    validation = security.validate_user(chat_id)
                    user_data = validation.get('user_data', {})
                    
                    await FileUploadHandler._process_upload(chat_id, update.message, user_data, context)
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
                        estado='confirmando_periodo_upload',
                        data=session_data
                    )
            else:
                # Fallback: intentar formato YYYY-MM
                try:
                    datetime.strptime(message_text, "%Y-%m")
                    session_data = session.get('data', {})
                    session_data['periodo'] = message_text
                    
                    session_manager.update_session(
                        chat_id=chat_id,
                        estado='listo_para_subir',
                        data=session_data
                    )
                    
                    validation = security.validate_user(chat_id)
                    user_data = validation.get('user_data', {})
                    
                    await FileUploadHandler._process_upload(chat_id, update.message, user_data, context)
                except ValueError:
                    await update.message.reply_text(
                        "❌ No pude entender el período. Por favor, escribe:\n"
                        "• Un formato `AAAA-MM` (ejemplo: `2024-05`)\n"
                        "• O una fecha en lenguaje natural (ejemplo: 'mayo 2024')",
                        parse_mode='Markdown'
                    )
        
        # Confirmar período propuesto en subida
        elif estado == 'confirmando_periodo_upload':
            texto_lower = message_text.lower().strip()
            if texto_lower in ['sí', 'si', 'correcto', 'ok', 's', 'yes']:
                session_data = session.get('data', {})
                periodo = session_data.get('periodo_propuesto')
                
                if periodo:
                    session_data['periodo'] = periodo
                    session_data.pop('periodo_propuesto', None)
                    
                    session_manager.update_session(
                        chat_id=chat_id,
                        estado='listo_para_subir',
                        data=session_data
                    )
                    
                    validation = security.validate_user(chat_id)
                    user_data = validation.get('user_data', {})
                    
                    await FileUploadHandler._process_upload(chat_id, update.message, user_data, context)
                else:
                    await update.message.reply_text("❌ Error: No hay período propuesto. Intenta nuevamente.")
            else:
                # Usuario corrigió, intentar analizar nuevamente
                session_manager.update_session(
                    chat_id=chat_id,
                    estado='esperando_periodo_texto_ia'
                )
                # Recursivamente procesar el nuevo texto
                await FileUploadHandler.handle_text_during_upload(update, context)
        
        # Procesar período en formato texto (legacy, mantener compatibilidad)
        elif estado == 'esperando_periodo_texto':
            try:
                # Validar formato YYYY-MM
                datetime.strptime(message_text, "%Y-%m")
                session_manager.update_session(
                    chat_id=chat_id,
                    estado='listo_para_subir',
                    data={'periodo': message_text}
                )
                
                validation = security.validate_user(chat_id)
                user_data = validation.get('user_data', {})
                
                await FileUploadHandler._process_upload(chat_id, update.message, user_data, context)
            except ValueError:
                await update.message.reply_text(
                    "❌ Formato inválido. Usa el formato `AAAA-MM` (ejemplo: `2024-05`)",
                    parse_mode='Markdown'
                )
        
        # Procesar descripción personalizada
        elif estado == 'esperando_descripcion':
            # Validar que la descripción no esté vacía
            if not message_text or len(message_text.strip()) < 3:
                await update.message.reply_text(
                    "❌ La descripción debe tener al menos 3 caracteres. Por favor, escribe una descripción más detallada:",
                    parse_mode='Markdown'
                )
                return
            
            # Guardar descripción y continuar con período
            session_manager.update_session(
                chat_id=chat_id,
                estado='esperando_periodo',
                data={'descripcion_personalizada': message_text.strip()}
            )
            
            # Confirmar descripción recibida
            await update.message.reply_text(
                f"✅ Descripción guardada: **{escape_markdown(message_text.strip())}**\n\nAhora necesito el período del archivo:",
                parse_mode='Markdown'
            )
            
            validation = security.validate_user(chat_id)
            user_data = validation.get('user_data', {})
            
            # Continuar con período
            await FileUploadHandler._ask_periodo(update.message, user_data)
    
    @staticmethod
    async def _process_upload(chat_id: int, message_or_query, user_data, context: ContextTypes.DEFAULT_TYPE):
        """Procesar la subida del archivo"""
        session_manager = get_session_manager()
        session = session_manager.get_session(chat_id)
        
        if not session:
            text = "❌ Sesión expirada. Por favor, envía el archivo nuevamente."
            if hasattr(message_or_query, 'edit_message_text'):
                await message_or_query.edit_message_text(text)
            else:
                await message_or_query.reply_text(text)
            return
        
        session_data = session.get('data', {})
        
        # Validar que tenemos todos los datos necesarios
        required_fields = ['empresa_id', 'categoria', 'subtipo', 'periodo', 'file_id', 'nombre_original_archivo']
        missing_fields = [field for field in required_fields if not session_data.get(field)]
        
        if missing_fields:
            text = f"❌ Faltan datos: {', '.join(missing_fields)}"
            if hasattr(message_or_query, 'edit_message_text'):
                await message_or_query.edit_message_text(text)
            else:
                await message_or_query.reply_text(text)
            return
        
        # Mostrar mensaje de procesamiento
        text = "⏳ **Subiendo archivo...**\n\nPor favor espera."
        is_callback = hasattr(message_or_query, 'edit_message_text')
        
        if is_callback:
            await message_or_query.edit_message_text(text, parse_mode='Markdown')
        else:
            processing_msg = await message_or_query.reply_text(text, parse_mode='Markdown')
        
        try:
            # Descargar archivo desde Telegram
            file_id = session_data['file_id']
            file_info = await context.bot.get_file(file_id)
            file_bytes = await file_info.download_as_bytearray()
            
            # Subir a Supabase Storage
            storage_service = get_storage_service()
            archivo_result = await storage_service.upload_file(
                file_bytes=bytes(file_bytes),
                filename=session_data['nombre_original_archivo'],
                chat_id=chat_id,
                empresa_id=session_data['empresa_id'],
                categoria=session_data['categoria'],
                tipo=session_data['categoria'],  # tipo = categoria
                subtipo=session_data['subtipo'],
                periodo=session_data['periodo'],
                descripcion_personalizada=session_data.get('descripcion_personalizada'),
                usuario_subio_id=user_data.get('id')
            )
            
            if archivo_result:
                # Mensaje de confirmación base
                categoria_nombre = get_categoria_nombre(session_data['categoria'])
                subtipo_nombre = get_subtipo_nombre(session_data['categoria'], session_data['subtipo'])
                empresa_nombre = session_data.get('empresa_nombre', 'N/A')
                periodo = session_data['periodo']
                filename = session_data['nombre_original_archivo']
                subtipo = session_data['subtipo']
                empresa_id = session_data['empresa_id']
                
                # Verificar si es un reporte PDF que debe subirse a OpenAI
                openai_uploaded = False
                extension = '.' + filename.split('.')[-1].lower() if '.' in filename else ''
                
                if subtipo in SUBTIPOS_PARA_OPENAI and extension in EXTENSIONES_OPENAI:
                    logger.info(f"📤 Subiendo reporte a OpenAI: {filename} (subtipo: {subtipo})")
                    
                    try:
                        assistant_service = get_assistant_service()
                        archivo_id = archivo_result.get('id')
                        
                        # Subir a OpenAI y asociar al Assistant de la empresa
                        openai_file_id = await assistant_service.upload_file_to_openai(
                            file_bytes=bytes(file_bytes),
                            filename=filename,
                            empresa_id=empresa_id,
                            archivo_id=archivo_id
                        )
                        
                        if openai_file_id:
                            openai_uploaded = True
                            logger.info(f"✅ Reporte subido a OpenAI: {openai_file_id}")
                        else:
                            logger.warning(f"⚠️ No se pudo subir a OpenAI: {filename}")
                    except Exception as e:
                        logger.error(f"❌ Error subiendo a OpenAI: {e}")
                
                # Limpiar sesión
                session_manager.clear_session(chat_id)
                
                text = (
                    f"✅ **Archivo subido exitosamente**\n\n"
                    f"📁 **Archivo:** {escape_markdown(filename)}\n"
                    f"🏢 **Empresa:** {escape_markdown(empresa_nombre)}\n"
                    f"📂 **Categoría:** {categoria_nombre}\n"
                    f"📄 **Tipo:** {subtipo_nombre}\n"
                    f"📅 **Período:** {periodo}\n"
                )
                
                if session_data.get('descripcion_personalizada'):
                    text += f"📝 **Descripción:** {escape_markdown(session_data['descripcion_personalizada'])}\n"
                
                # Indicar si se subió a OpenAI
                if openai_uploaded:
                    text += f"\n🤖 _Disponible para consultas con Asesor IA_"
                
                # Botón para volver al menú principal
                keyboard = [[InlineKeyboardButton("🔙 Volver al menú", callback_data="back_main")]]
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                # Enviar mensaje de confirmación con botón
                if is_callback:
                    await message_or_query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')
                else:
                    # Si es desde texto, editar el mensaje de "procesando" o enviar uno nuevo
                    try:
                        await processing_msg.edit_text(text, reply_markup=reply_markup, parse_mode='Markdown')
                    except:
                        await message_or_query.reply_text(text, reply_markup=reply_markup, parse_mode='Markdown')
            else:
                error_text = "❌ Error al subir el archivo. Por favor, intenta nuevamente."
                if is_callback:
                    await message_or_query.edit_message_text(error_text)
                else:
                    await message_or_query.reply_text(error_text)
        
        except Exception as e:
            logger.error(f"Error procesando subida para chat_id {chat_id}: {e}", exc_info=True)
            error_text = "❌ Error al procesar el archivo. Por favor, intenta nuevamente."
            if is_callback:
                await message_or_query.edit_message_text(error_text)
            else:
                await message_or_query.reply_text(error_text)

