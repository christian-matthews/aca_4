from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from app.security.auth import security
from app.database.supabase import supabase
from app.decorators.conversation_logging import log_production_conversation, log_unauthorized_access
from datetime import datetime
import json
import logging

logger = logging.getLogger(__name__)

def escape_markdown(text):
    """Escapar caracteres especiales para Markdown"""
    if not text:
        return text
    return text.replace('_', '\\_').replace('*', '\\*').replace('[', '\\[').replace(']', '\\]').replace('`', '\\`')

class ProductionHandlers:
    """Manejadores para el bot de producción"""
    
    @staticmethod
    @log_production_conversation
    async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Comando de inicio para el bot de producción"""
        chat_id = update.effective_chat.id
        
        # ✅ Cancelar cualquier proceso en curso (subida o descarga)
        from app.services.session_manager import get_session_manager
        session_manager = get_session_manager()
        session = session_manager.get_session(chat_id)
        if session:
            session_manager.clear_session(chat_id)
        
        # Validar usuario
        validation = security.validate_user(chat_id)
        
        if not validation['valid']:
            # Registrar usuario no autorizado antes de responder
            await ProductionHandlers._handle_unauthorized_user(update, context)
            return
        
        user_data = validation['user_data']
        
        # El logging ahora es automático con el decorador
        await ProductionHandlers._show_main_menu(update.message, user_data)
    
    @staticmethod
    async def _show_main_menu(message_or_query, user_data):
        """Mostrar menú principal (Pendientes, CxC & CxP, Agendar en FASE 2)"""
        # ✅ Asegurar que no haya sesiones activas al mostrar el menú principal
        chat_id = message_or_query.chat.id if hasattr(message_or_query, 'chat') else message_or_query.message.chat.id
        from app.services.session_manager import get_session_manager
        session_manager = get_session_manager()
        session = session_manager.get_session(chat_id)
        if session:
            session_manager.clear_session(chat_id)
        
        keyboard = [
            [
                InlineKeyboardButton("📊 Información", callback_data="informacion"),
                InlineKeyboardButton("📈 Reporte CFO", callback_data="reporte_cfo")
            ],
            [
                InlineKeyboardButton("🤖 Asesor IA", callback_data="asesor_ia"),
                InlineKeyboardButton("ℹ️ Ayuda", callback_data="ayuda")
            ],
            [InlineKeyboardButton("🚪 Salir", callback_data="salir")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        text = f"👋 **Bienvenido {escape_markdown(user_data.get('nombre', 'Usuario'))}**\n\nSelecciona una opción del menú:"
        
        # Si es un CallbackQuery, usar edit_message_text
        if hasattr(message_or_query, 'edit_message_text'):
            await message_or_query.edit_message_text(
                text,
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )
        # Si es un Message, usar reply_text
        else:
            await message_or_query.reply_text(
                text,
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )
    
    @staticmethod
    async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Manejar callbacks del bot de producción"""
        query = update.callback_query
        await query.answer()
        
        chat_id = update.effective_chat.id
        callback_data = query.data
        
        # ✅ Log detallado para debugging
        import logging
        logger = logging.getLogger(__name__)
        logger.info(f"🔍 ProductionHandlers.handle_callback: callback_data='{callback_data}' para chat_id={chat_id}")
        
        # Validar usuario en cada callback
        validation = security.validate_user(chat_id)
        
        if not validation['valid']:
            await query.edit_message_text(validation['message'])
            return
        
        user_data = validation['user_data']
        
        # Manejar diferentes opciones
        # ✅ IMPORTANTE: Verificar callbacks de descarga PRIMERO (antes de otros callbacks específicos)
        if callback_data.startswith("download_"):
            # ✅ Manejar callbacks de descarga de archivos
            logger.info(f"📥 Callback de descarga detectado: '{callback_data}', enrutando a FileDownloadHandler")
            from app.bots.handlers.file_download_handler import FileDownloadHandler
            try:
                await FileDownloadHandler.handle_download_callback(update, context)
                logger.info(f"✅ FileDownloadHandler.handle_download_callback completado para '{callback_data}'")
            except Exception as e:
                logger.error(f"❌ Error en FileDownloadHandler.handle_download_callback: {e}", exc_info=True)
                await query.edit_message_text(
                    f"❌ Error procesando solicitud: {str(e)}\n\nPor favor, intenta nuevamente.",
                    reply_markup=InlineKeyboardMarkup([[
                        InlineKeyboardButton("🔙 Volver al Menú", callback_data="back_main")
                    ]])
                )
            return  # ✅ CRÍTICO: Retornar después de manejar callback de descarga
        
        # ✅ Manejar callbacks de subida de archivos
        if callback_data.startswith("upload_"):
            logger.info(f"📤 Callback de subida detectado: '{callback_data}', enrutando a FileUploadHandler")
            from app.bots.handlers.file_upload_handler import FileUploadHandler
            try:
                await FileUploadHandler.handle_upload_callback(update, context)
                logger.info(f"✅ FileUploadHandler.handle_upload_callback completado para '{callback_data}'")
            except Exception as e:
                logger.error(f"❌ Error en FileUploadHandler.handle_upload_callback: {e}", exc_info=True)
                await query.edit_message_text(
                    f"❌ Error procesando solicitud: {str(e)}\n\nPor favor, intenta nuevamente.",
                    reply_markup=InlineKeyboardMarkup([[
                        InlineKeyboardButton("🔙 Volver al Menú", callback_data="back_main")
                    ]])
                )
            return  # ✅ CRÍTICO: Retornar después de manejar callback de subida
        
        elif callback_data == "informacion":
            logger.info(f"📊 Usuario presionó 'Información', creando sesión de descarga")
            # ✅ Conectar con sistema de descarga de archivos
            from app.bots.handlers.file_download_handler import FileDownloadHandler
            from app.services.session_manager import get_session_manager
            
            session_manager = get_session_manager()
            # Crear sesión de descarga
            session_manager.create_session(
                chat_id=chat_id,
                intent='descargar_archivo',
                estado='esperando_categoria',
                data={}
            )
            logger.info(f"✅ Sesión creada, mostrando categorías")
            # Mostrar menú de categorías
            await FileDownloadHandler._ask_categoria(query)
        # FASE 2: elif callback_data == "pendientes":
        #     await ProductionHandlers._handle_pendientes(query, user_data)
        # FASE 2: elif callback_data == "cxc_cxp":
        #     await ProductionHandlers._handle_cxc_cxp(query, user_data)
        elif callback_data == "asesor_ia":
            await ProductionHandlers._handle_asesor_ia(query, user_data)
        elif callback_data == "reporte_cfo":
            await ProductionHandlers._handle_reporte_cfo(query, user_data)
        elif callback_data == "ayuda":
            await ProductionHandlers._handle_ayuda(query, user_data)
        elif callback_data == "salir":
            await ProductionHandlers._handle_salir(query)
        elif callback_data == "back_main":
            await ProductionHandlers._show_main_menu(query, user_data)
        elif callback_data == "reportes":
            await ProductionHandlers._handle_reportes(query, user_data)
        elif callback_data == "info_compania":
            await ProductionHandlers._handle_info_compania(query, user_data)
        elif callback_data.startswith("mes_"):
            await ProductionHandlers._handle_mes_reporte(query, user_data)
        elif callback_data.startswith("categoria_"):
            # ❌ Eliminado: Ya no se usa este handler
            # El flujo de descarga maneja las categorías directamente
            await query.edit_message_text("❌ Esta opción ya no está disponible. Usa '📊 Información' para descargar archivos.")
    
    @staticmethod
    async def _handle_informacion(query, user_data):
        """Manejar opción de información - menú principal"""
        try:
            text = "📊 **Información de la Empresa**\n\n"
            text += "Selecciona el tipo de información que necesitas:"
            
            keyboard = [
                [
                    InlineKeyboardButton("📈 Reportes", callback_data="reportes"),
                    InlineKeyboardButton("🏢 Información Compañía", callback_data="info_compania")
                ],
                [InlineKeyboardButton("🔙 Volver al Menú", callback_data="back_main")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Error manejando información: {e}")
            await query.edit_message_text("Error mostrando información.")
    
    @staticmethod
    async def _handle_reportes(query, user_data):
        """Manejar opción de reportes - mostrar meses del año actual"""
        try:
            from datetime import datetime
            current_year = datetime.now().year
            current_month = datetime.now().month
            
            text = f"📈 **Reportes {current_year}**\n\n"
            text += "Selecciona el mes del reporte que necesitas:"
            
            # Crear botones para los meses del año actual
            months = [
                ("Enero", 1), ("Febrero", 2), ("Marzo", 3), ("Abril", 4),
                ("Mayo", 5), ("Junio", 6), ("Julio", 7), ("Agosto", 8),
                ("Septiembre", 9), ("Octubre", 10), ("Noviembre", 11), ("Diciembre", 12)
            ]
            
            keyboard = []
            row = []
            for month_name, month_num in months:
                # Marcar el mes actual
                if month_num == current_month:
                    month_name = f"📍 {month_name}"
                
                row.append(InlineKeyboardButton(
                    month_name, 
                    callback_data=f"mes_{current_year}_{month_num:02d}"
                ))
                
                if len(row) == 3:  # 3 botones por fila
                    keyboard.append(row)
                    row = []
            
            if row:  # Agregar la última fila si no está completa
                keyboard.append(row)
            
            keyboard.append([InlineKeyboardButton("🔙 Volver", callback_data="informacion")])
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Error manejando reportes: {e}")
            await query.edit_message_text("Error mostrando reportes.")
    
    @staticmethod
    async def _handle_info_compania(query, user_data):
        """Manejar opción de información de la compañía"""
        try:
            text = "🏢 **Información de la Compañía**\n\n"
            text += "Selecciona la categoría de información:"
            
            keyboard = [
                [
                    InlineKeyboardButton("⚖️ Legal", callback_data="categoria_legal"),
                    InlineKeyboardButton("💰 Financiera", callback_data="categoria_financiera")
                ],
                [
                    InlineKeyboardButton("📊 Tributaria", callback_data="categoria_tributaria"),
                    InlineKeyboardButton("📁 Carpeta Tributaria", callback_data="categoria_carpeta")
                ],
                [InlineKeyboardButton("🔙 Volver", callback_data="informacion")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Error manejando información de compañía: {e}")
            await query.edit_message_text("Error mostrando información de compañía.")
    
    @staticmethod
    async def _handle_mes_reporte(query, user_data):
        """Manejar selección de mes para reportes"""
        try:
            # Extraer año y mes del callback_data (formato: mes_2024_01)
            _, year, month = query.data.split('_')
            month_name = {
                '01': 'Enero', '02': 'Febrero', '03': 'Marzo', '04': 'Abril',
                '05': 'Mayo', '06': 'Junio', '07': 'Julio', '08': 'Agosto',
                '09': 'Septiembre', '10': 'Octubre', '11': 'Noviembre', '12': 'Diciembre'
            }[month]
            
            text = f"📈 **Reporte {month_name} {year}**\n\n"
            text += f"Empresa: **{user_data.get('empresa_nombre', 'N/A')}**\n"
            text += f"Período: {month_name} {year}\n\n"
            
            # Obtener reportes reales de la base de datos
            reportes = supabase.get_reportes_mensuales(
                empresa_id=user_data['empresa_id'],
                anio=int(year),
                mes=int(month)
            )
            
            if reportes:
                text += "📄 **Reportes disponibles:**\n"
                for reporte in reportes:
                    text += f"• **{reporte.get('titulo', 'Sin título')}**\n"
                    if reporte.get('descripcion'):
                        text += f"  {reporte['descripcion']}\n"
                    if reporte.get('comentarios'):
                        text += f"  📝 {reporte['comentarios']}\n"
                    text += f"  📊 Estado: {reporte.get('estado', 'borrador')}\n\n"
                
                # Obtener archivos adjuntos
                for reporte in reportes:
                    archivos = supabase.get_archivos_reporte(reporte['id'])
                    if archivos:
                        text += f"📎 **Archivos de {reporte.get('titulo', 'reporte')}:**\n"
                        for archivo in archivos:
                            text += f"• {archivo.get('nombre_archivo', 'Sin nombre')}\n"
                        text += "\n"
            else:
                text += "📄 **No hay reportes disponibles para este período.**\n\n"
                text += "Puedes crear un nuevo reporte o adjuntar documentos.\n\n"
            
            keyboard = [
                [
                    InlineKeyboardButton("📄 Crear Reporte", callback_data=f"crear_reporte_{year}_{month}"),
                    InlineKeyboardButton("📎 Adjuntar Archivo", callback_data=f"adjuntar_{year}_{month}")
                ],
                [
                    InlineKeyboardButton("📝 Agregar Comentario", callback_data=f"comentario_{year}_{month}"),
                    InlineKeyboardButton("📊 Ver Datos", callback_data=f"datos_{year}_{month}")
                ],
                [InlineKeyboardButton("🔙 Volver a Reportes", callback_data="reportes")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Error manejando mes de reporte: {e}")
            await query.edit_message_text("Error mostrando reporte del mes.")
    
    @staticmethod
    async def _handle_categoria_info(query, user_data):
        """Manejar categorías de información de la compañía"""
        try:
            categoria = query.data.split('_')[1]  # legal, financiera, tributaria, carpeta
            
            categorias = {
                'legal': {
                    'title': '⚖️ **Información Legal**',
                    'icon': '⚖️',
                    'content': [
                        '• Estatutos de la empresa',
                        '• Registro mercantil',
                        '• Licencias comerciales',
                        '• Contratos vigentes',
                        '• Propiedad intelectual'
                    ]
                },
                'financiera': {
                    'title': '💰 **Información Financiera**',
                    'icon': '💰',
                    'content': [
                        '• Estados financieros',
                        '• Presupuestos',
                        '• Flujos de caja',
                        '• Análisis de ratios',
                        '• Proyecciones financieras'
                    ]
                },
                'tributaria': {
                    'title': '📊 **Información Tributaria**',
                    'icon': '📊',
                    'content': [
                        '• Declaraciones de impuestos',
                        '• Certificados tributarios',
                        '• Retenciones en la fuente',
                        '• IVA y otros impuestos',
                        '• Resoluciones fiscales'
                    ]
                },
                'carpeta': {
                    'title': '📁 **Carpeta Tributaria**',
                    'icon': '📁',
                    'content': [
                        '• Documentos de constitución',
                        '• Registros contables',
                        '• Comprobantes de pago',
                        '• Certificados bancarios',
                        '• Documentos de respaldo'
                    ]
                }
            }
            
            cat_info = categorias.get(categoria, {
                'title': '📋 **Información**',
                'icon': '📋',
                'content': ['Información no disponible']
            })
            
            text = f"{cat_info['title']}\n\n"
            text += f"Empresa: **{user_data.get('empresa_nombre', 'N/A')}**\n\n"
            
            # Obtener información real de la base de datos
            info_compania = supabase.get_info_compania(
                empresa_id=user_data['empresa_id'],
                categoria=categoria
            )
            
            if info_compania:
                text += "📋 **Información disponible:**\n"
                for info in info_compania:
                    text += f"• **{info.get('titulo', 'Sin título')}**\n"
                    if info.get('descripcion'):
                        text += f"  {info['descripcion']}\n"
                    if info.get('contenido'):
                        text += f"  {info['contenido']}\n"
                    text += "\n"
                
                # Obtener archivos adjuntos
                for info in info_compania:
                    archivos = supabase.get_archivos_info_compania(info['id'])
                    if archivos:
                        text += f"📎 **Archivos de {info.get('titulo', 'información')}:**\n"
                        for archivo in archivos:
                            text += f"• {archivo.get('nombre_archivo', 'Sin nombre')}\n"
                        text += "\n"
            else:
                text += "📋 **No hay información disponible en esta categoría.**\n\n"
                text += "Puedes agregar nueva información o adjuntar documentos.\n\n"
            
            keyboard = [
                [
                    InlineKeyboardButton("📝 Agregar Info", callback_data=f"add_{categoria}"),
                    InlineKeyboardButton("📎 Adjuntar Archivo", callback_data=f"attach_{categoria}")
                ],
                [
                    InlineKeyboardButton("📄 Ver Documentos", callback_data=f"docs_{categoria}"),
                    InlineKeyboardButton("📊 Exportar", callback_data=f"export_{categoria}")
                ],
                [InlineKeyboardButton("🔙 Volver", callback_data="info_compania")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Error manejando categoría de información: {e}")
            await query.edit_message_text("Error mostrando información de la categoría.")
    
    @staticmethod
    async def _handle_pendientes(query, user_data):
        """Manejar opción de pendientes"""
        try:
            # Obtener pendientes de la empresa
            pendientes = supabase.get_empresa_data(user_data['empresa_id'], 'pendientes')
            
            text = "⏳ **Pendientes**\n\n"
            
            if pendientes:
                for pendiente in pendientes:
                    text += f"• **{pendiente.get('titulo', 'Sin título')}**\n"
                    text += f"  📅 Fecha: {pendiente.get('fecha_limite', 'Sin fecha')}\n"
                    text += f"  📝 {pendiente.get('descripcion', 'Sin descripción')}\n"
                    text += f"  🏷️ Tipo: {pendiente.get('tipo', 'General')}\n\n"
            else:
                text += "No hay pendientes registrados.\n"
            
            text += "\n*En desarrollo*"
            
            keyboard = [[InlineKeyboardButton("🔙 Volver al Menú", callback_data="back_main")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Error manejando pendientes: {e}")
            await query.edit_message_text("Error obteniendo pendientes.")
    
    @staticmethod
    async def _handle_cxc_cxp(query, user_data):
        """Manejar opción de CxC y CxP"""
        try:
            # Obtener datos de CxC y CxP de la empresa
            cxc_data = supabase.get_empresa_data(user_data['empresa_id'], 'cuentas_cobrar')
            cxp_data = supabase.get_empresa_data(user_data['empresa_id'], 'cuentas_pagar')
            
            text = "💰 **Cuentas por Cobrar y Pagar**\n\n"
            
            # CxC
            text += "📈 **Cuentas por Cobrar:**\n"
            if cxc_data:
                total_cxc = sum(item.get('monto', 0) for item in cxc_data)
                text += f"Total: ${total_cxc:,.0f}\n"
                for cxc in cxc_data[:3]:  # Mostrar solo los primeros 3
                    text += f"• {cxc.get('cliente', 'Sin cliente')}: ${cxc.get('monto', 0):,.0f}\n"
                if len(cxc_data) > 3:
                    text += f"... y {len(cxc_data) - 3} más\n"
            else:
                text += "No hay cuentas por cobrar.\n"
            
            text += "\n📉 **Cuentas por Pagar:**\n"
            if cxp_data:
                total_cxp = sum(item.get('monto', 0) for item in cxp_data)
                text += f"Total: ${total_cxp:,.0f}\n"
                for cxp in cxp_data[:3]:  # Mostrar solo los primeros 3
                    text += f"• {cxp.get('proveedor', 'Sin proveedor')}: ${cxp.get('monto', 0):,.0f}\n"
                if len(cxp_data) > 3:
                    text += f"... y {len(cxp_data) - 3} más\n"
            else:
                text += "No hay cuentas por pagar.\n"
            
            text += "\n*En desarrollo*"
            
            keyboard = [[InlineKeyboardButton("🔙 Volver al Menú", callback_data="back_main")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Error manejando CxC/CxP: {e}")
            await query.edit_message_text("Error obteniendo datos de cuentas.")
    
    @staticmethod
    async def _handle_asesor_ia(query, user_data):
        """Manejar opción de Asesor IA"""
        text = (
            "🤖 **Asesor IA**\n\n"
            "El asesor de inteligencia artificial está en desarrollo.\n\n"
            "Próximamente podrás:\n"
            "• Hacer preguntas sobre tus datos\n"
            "• Obtener análisis automáticos\n"
            "• Recibir recomendaciones\n"
            "• Generar reportes inteligentes\n\n"
            "*En desarrollo*"
        )
        
        keyboard = [[InlineKeyboardButton("🔙 Volver al Menú", callback_data="back_main")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')
    
    @staticmethod
    async def _handle_agendar(query, user_data):
        """Manejar opción de agendar (simplificado)"""
        text = (
            "📅 **Sistema de Agendamiento**\n\n"
            "El sistema de agendamiento está en desarrollo.\n\n"
            "Próximamente podrás:\n"
            "• Crear citas y reuniones\n"
            "• Ver tu calendario\n"
            "• Recibir recordatorios\n"
            "• Integrar con sistemas de calendario\n\n"
            "*En desarrollo*"
        )
        
        keyboard = [[InlineKeyboardButton("🔙 Volver al Menú", callback_data="back_main")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')
    
    @staticmethod
    async def _handle_reporte_cfo(query, user_data):
        """Manejar opción de Reporte CFO - Muestra reporte mensual como JSON formateado"""
        try:
            chat_id = query.from_user.id
            empresa_id = user_data.get('empresa_id')
            
            # Obtener reporte del mes actual o más reciente
            ahora = datetime.now()
            anio_actual = ahora.year
            mes_actual = ahora.month
            
            # Intentar obtener reporte del mes actual (devuelve lista)
            reportes_mes_actual = supabase.get_reportes_mensuales(empresa_id=empresa_id, anio=anio_actual, mes=mes_actual)
            reporte = reportes_mes_actual[0] if reportes_mes_actual else None
            
            # Si no hay del mes actual, buscar el más reciente
            if not reporte:
                todos_reportes = supabase.get_reportes_mensuales(empresa_id=empresa_id)
                if todos_reportes:
                    # Ordenar por fecha más reciente
                    reportes_ordenados = sorted(
                        todos_reportes,
                        key=lambda x: (x.get('anio', 0), x.get('mes', 0)),
                        reverse=True
                    )
                    reporte = reportes_ordenados[0] if reportes_ordenados else None
                else:
                    reporte = None
            
            meses_nombres = {
                1: 'Enero', 2: 'Febrero', 3: 'Marzo', 4: 'Abril',
                5: 'Mayo', 6: 'Junio', 7: 'Julio', 8: 'Agosto',
                9: 'Septiembre', 10: 'Octubre', 11: 'Noviembre', 12: 'Diciembre'
            }
            
            text = "📈 **Reporte CFO**\n\n"
            
            if reporte:
                anio = reporte.get('anio', 'N/A')
                mes = reporte.get('mes', 'N/A')
                mes_nombre = meses_nombres.get(mes, f'Mes {mes}') if isinstance(mes, int) else mes
                titulo = reporte.get('titulo', 'Reporte CFO')
                estado = reporte.get('estado', 'borrador')
                contenido = reporte.get('contenido', {})
                descripcion = reporte.get('descripcion', '')
                comentarios = reporte.get('comentarios', '')
                
                # Encabezado del reporte
                text += f"📅 **Período:** {mes_nombre} {anio}\n"
                text += f"📊 **Estado:** {estado.title()}\n"
                if descripcion:
                    text += f"📝 **Descripción:** {escape_markdown(descripcion)}\n"
                text += "\n"
                
                # Mostrar contenido JSON formateado
                if contenido and isinstance(contenido, dict) and contenido:
                    text += "```json\n"
                    # Formatear JSON de manera legible
                    json_str = json.dumps(contenido, indent=2, ensure_ascii=False)
                    text += json_str
                    text += "\n```\n\n"
                else:
                    text += "📄 *No hay datos estructurados en este reporte.*\n\n"
                
                # Comentarios adicionales si existen
                if comentarios:
                    text += f"💬 **Comentarios:**\n{escape_markdown(comentarios)}\n\n"
                
                text += "💡 *Este reporte se genera mensualmente con datos estructurados.*"
            else:
                text += "📭 **No hay reporte CFO disponible**\n\n"
                text += f"Período actual: {meses_nombres.get(mes_actual, mes_actual)} {anio_actual}\n\n"
                text += "El reporte CFO se genera mensualmente con datos estructurados en formato JSON."
            
            keyboard = [
                [InlineKeyboardButton("🔙 Volver al Menú", callback_data="back_main")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Error manejando reporte CFO: {e}")
            await query.edit_message_text(
                "❌ Error obteniendo reporte CFO. Intenta nuevamente.",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Volver al Menú", callback_data="back_main")]])
            )
    
    @staticmethod
    async def _handle_salir(query):
        """Manejar opción de salir"""
        chat_id = query.message.chat.id
        
        # ✅ Cancelar cualquier proceso en curso (subida o descarga)
        from app.services.session_manager import get_session_manager
        session_manager = get_session_manager()
        session = session_manager.get_session(chat_id)
        if session:
            session_manager.clear_session(chat_id)
        
        text = (
            "👋 **¡Hasta luego!**\n\n"
            "Gracias por usar nuestro sistema.\n"
            "Para volver a usar el bot, envía /start"
        )
        
        await query.edit_message_text(text, parse_mode='Markdown')
    
    @staticmethod
    @log_production_conversation
    async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Manejar mensajes de texto del bot de producción"""
        chat_id = update.effective_chat.id
        message_text = update.message.text
        
        # Validar usuario
        validation = security.validate_user(chat_id)
        
        if not validation['valid']:
            # Registrar usuario no autorizado antes de responder
            await ProductionHandlers._handle_unauthorized_user(update, context)
            return
        
        # ✅ Verificar si hay una sesión activa de descarga o subida
        from app.services.session_manager import get_session_manager
        import logging
        logger = logging.getLogger(__name__)
        
        session_manager = get_session_manager()
        session = session_manager.get_session(chat_id)
        
        if session:
            intent = session.get('intent')
            estado = session.get('estado')
            logger.info(f"🔍 ProductionHandlers.handle_message: sesión encontrada - intent={intent}, estado={estado}")
            # Si hay sesión activa de descarga o subida, dejar que los handlers específicos la manejen
            if intent in ['descargar_archivo', 'subir_archivo']:
                logger.info(f"✅ Dejando que handler específico maneje el mensaje (intent={intent})")
                return  # No hacer nada, dejar que los handlers específicos procesen el mensaje
        else:
            logger.info(f"🔍 ProductionHandlers.handle_message: no hay sesión activa, mostrando menú principal")
        
        user_data = validation['user_data']
        
        # El logging ahora es automático con el decorador
        # Mostrar menú principal solo si no hay sesión activa
        await ProductionHandlers._show_main_menu(update.message, user_data)
    
    @staticmethod
    @log_unauthorized_access()
    async def _handle_unauthorized_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Manejar usuarios no autorizados - REGISTRO AUTOMÁTICO"""
        # El decorador @log_unauthorized_access() se encarga de:
        # 1. Registrar usuario en usuarios_detalle 
        # 2. Registrar intento en intentos_acceso_negado
        # 3. Enviar mensaje explicativo
        # 4. NO ejecutar lógica adicional (return None)
        pass
    
    @staticmethod
    async def _handle_ayuda(query, user_data):
        """Manejar opción de ayuda"""
        text = (
            "ℹ️ *Ayuda del Sistema*\n\n"
            "*Funcionalidades disponibles:*\n\n"
            "📊 *Reportes*: Ver reportes financieros\n"
            "⏳ *Pendientes*: Gestionar tareas pendientes\n"
            "💰 *CxC & CxP*: Ver cuentas por cobrar y pagar\n"
            "🤖 *Asesor IA*: Asesoría inteligente (en desarrollo)\n"
            "📅 *Agendar*: Sistema de citas (en desarrollo)\n\n"
            "*Comandos útiles:*\n"
            "• /start - Mostrar menú principal\n"
            "• /ayuda - Mostrar esta ayuda\n\n"
            "*Soporte:*\n"
            "Si necesitas ayuda, contacta al administrador o usa el botón de abajo."
        )
        
        keyboard = [
            [InlineKeyboardButton("🤖 Ir a @WingmanBOD", url="https://t.me/WingmanBOD")],
            [InlineKeyboardButton("🔙 Volver al Menú", callback_data="back_main")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown') 