"""
🤖 Asesor IA Handler (ACA_QA)
Analista de Consultas Q&A financiero-contable
"""

import logging
from datetime import datetime
from typing import Optional, Dict, Any, List
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from app.security.auth import security
from app.security.company_guard import get_company_guard, NoCompanySelectedError, CompanyNotAuthorizedError
from app.database.supabase import supabase
from app.services.session_manager import get_session_manager
from app.services.ai_service import get_ai_service
from app.services.openai_assistant_service import get_assistant_service
from app.config import Config

logger = logging.getLogger(__name__)

# System Prompt para ACA_QA
SYSTEM_PROMPT_ACA_QA = """Eres ACA_QA, un Analista de Consultas para un bot financiero-contable. Tu trabajo es responder preguntas y, si la solicitud implica acciones, riesgo o falta información, preparar un ticket para revisión humana.

Objetivo principal:
• Responder preguntas con información verificada y específica de la empresa seleccionada.
• Nunca ejecutar acciones críticas ni modificar datos contables.
• Mantener trazabilidad: justificar respuestas con IDs / referencias internas cuando existan.

Reglas duras (no romper):

1. Scope por empresa obligatorio
   • Solo puedes usar datos de una empresa activa (company_id) por respuesta.
   • Si el usuario pide "la otra empresa", debes pedir selección explícita.

2. Modo / Proceso
   • Estás siempre en el proceso: qa.
   • No puedes mezclar procesos (pagos, cierre, clasificar, etc.).
   • Si el usuario pide algo fuera de Q&A, ofrece: (a) crear ticket o (b) volver al menú principal.

3. Acciones prohibidas
   • Prohibido: pagar, transferir, cerrar períodos, emitir documentos tributarios, borrar o modificar registros contables definitivos.
   • Si la solicitud requiere algo de eso: escala a humano con ticket.

4. Calidad de respuesta
   • Si respondes: entrega respuesta breve + bullets + (si existe) IDs o referencias.
   • Si no estás seguro o faltan datos: pregunta solo lo mínimo o crea ticket.

Política de escalamiento (ticket):
Crea ticket cuando:
• la solicitud sea ambigua, compleja o requiera decisiones humanas,
• involucre dinero/impacto legal/tributario,
• requiera acciones fuera del scope de Q&A."""


def escape_markdown(text: str) -> str:
    """Escapar caracteres especiales para Markdown"""
    if not text:
        return text
    return text.replace('_', '\\_').replace('*', '\\*').replace('[', '\\[').replace(']', '\\]').replace('`', '\\`')


class AdvisorHandler:
    """Manejador del Asesor IA (ACA_QA)"""
    
    # Palabras clave que indican acciones prohibidas
    FORBIDDEN_ACTIONS = [
        "pagar", "pago", "transferir", "transferencia",
        "cerrar período", "cerrar periodo", "cierre contable",
        "emitir factura", "emitir boleta", "facturar",
        "borrar", "eliminar", "modificar registro",
        "anular", "reversar", "cerrar mes"
    ]
    
    # Palabras clave para solicitar ticket (más flexibles)
    TICKET_KEYWORDS = [
        "ticket", "humano", "persona real", "agente",
        "escalar", "soporte", "administrador", "admin",
        "ayuda humana", "hablar con alguien"
    ]
    
    @staticmethod
    async def handle_advisor_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Iniciar el Asesor IA desde el menú principal"""
        query = update.callback_query
        if query:
            await query.answer()
        
        chat_id = update.effective_chat.id
        
        # Validar usuario
        validation = security.validate_user(chat_id)
        if not validation['valid']:
            message = query.message if query else update.message
            await message.reply_text(validation['message'])
            return
        
        user_data = validation['user_data']
        company_guard = get_company_guard()
        session_manager = get_session_manager()
        
        # Limpiar sesión anterior si existe
        session_manager.clear_session(chat_id)
        
        # Resolver empresa
        empresas = company_guard.get_allowed_companies(chat_id)
        
        if not empresas:
            text = "❌ No tienes empresas asignadas. Contacta al administrador."
            if query:
                await query.edit_message_text(text)
            else:
                await update.message.reply_text(text)
            return
        
        if len(empresas) == 1:
            # Auto-seleccionar única empresa
            empresa = empresas[0]
            logger.info(f"✅ Auto-seleccionada empresa {empresa['nombre']} para usuario {chat_id}")
            
            # Crear sesión con empresa seleccionada
            session_manager.create_session(
                chat_id=chat_id,
                intent='asesor_ia',
                estado='activo',
                data={
                    'selected_company_id': empresa['id'],
                    'selected_company_name': empresa['nombre'],
                    'company_locked': True,
                    'qa_history': []
                }
            )
            
            # Mostrar interfaz del asesor
            await AdvisorHandler._show_advisor_interface(query or update.message, empresa)
        else:
            # Múltiples empresas: pedir selección
            await AdvisorHandler._ask_company_selection(query or update.message, empresas)
    
    @staticmethod
    async def _ask_company_selection(message_or_query, empresas: List[Dict[str, Any]]):
        """Mostrar lista de empresas para selección en 2 columnas"""
        text = "🏢 **¿Sobre qué empresa deseas consultar?**\n\nSelecciona una opción:"
        
        # Crear botones en 2 columnas
        keyboard = []
        row = []
        for i, empresa in enumerate(empresas):
            row.append(InlineKeyboardButton(
                f"🏢 {empresa['nombre'][:20]}",  # Truncar nombre si es largo
                callback_data=f"advisor_empresa_{empresa['id']}"
            ))
            if len(row) == 2:  # 2 columnas
                keyboard.append(row)
                row = []
        
        # Agregar última fila si quedó incompleta
        if row:
            keyboard.append(row)
        
        keyboard.append([InlineKeyboardButton("🔙 Volver", callback_data="back_main")])
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        if hasattr(message_or_query, 'edit_message_text'):
            await message_or_query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')
        else:
            await message_or_query.reply_text(text, reply_markup=reply_markup, parse_mode='Markdown')
    
    @staticmethod
    async def _show_advisor_interface(message_or_query, empresa: Dict[str, Any]):
        """Mostrar interfaz del Asesor IA"""
        text = (
            f"🤖 **Asesor IA - {escape_markdown(empresa['nombre'])}**\n\n"
            f"Soy tu asistente IA financiero-contable. Puedo ayudarte con:\n\n"
            f"• 📊 Consultas sobre reportes financieros\n"
            f"• 📋 Datos de la empresa - _en desarrollo_\n\n"
            f"**¿Qué información necesitas?**"
        )
        
        keyboard = [
            [
                InlineKeyboardButton("🔄 Cambiar empresa", callback_data="advisor_change_company"),
                InlineKeyboardButton("🔙 Menú principal", callback_data="back_main")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        if hasattr(message_or_query, 'edit_message_text'):
            await message_or_query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')
        else:
            await message_or_query.reply_text(text, reply_markup=reply_markup, parse_mode='Markdown')
    
    @staticmethod
    async def handle_advisor_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Manejar callbacks del Asesor IA"""
        query = update.callback_query
        await query.answer()
        
        chat_id = update.effective_chat.id
        callback_data = query.data
        
        logger.info(f"🤖 Advisor callback: {callback_data} para chat_id={chat_id}")
        
        # Validar usuario
        validation = security.validate_user(chat_id)
        if not validation['valid']:
            await query.edit_message_text(validation['message'])
            return
        
        session_manager = get_session_manager()
        company_guard = get_company_guard()
        
        # Selección de empresa
        if callback_data.startswith("advisor_empresa_"):
            empresa_id = callback_data.replace("advisor_empresa_", "")
            
            # Validar acceso
            if not company_guard.validate_access(chat_id, empresa_id):
                await query.edit_message_text("❌ No tienes acceso a esta empresa.")
                return
            
            # Obtener info de empresa
            empresa_info = company_guard._get_empresa_info(empresa_id)
            if not empresa_info:
                await query.edit_message_text("❌ Empresa no encontrada.")
                return
            
            # Crear sesión con empresa seleccionada
            session_manager.create_session(
                chat_id=chat_id,
                intent='asesor_ia',
                estado='activo',
                data={
                    'selected_company_id': empresa_id,
                    'selected_company_name': empresa_info['nombre'],
                    'company_locked': True,
                    'qa_history': []
                }
            )
            
            logger.info(f"✅ Empresa {empresa_info['nombre']} seleccionada para Asesor IA")
            await AdvisorHandler._show_advisor_interface(query, empresa_info)
            return
        
        # Cambiar empresa
        if callback_data == "advisor_change_company":
            empresas = company_guard.get_allowed_companies(chat_id)
            if len(empresas) <= 1:
                await query.answer("Solo tienes acceso a una empresa.", show_alert=True)
                return
            
            # Limpiar sesión actual
            session_manager.clear_session(chat_id)
            await AdvisorHandler._ask_company_selection(query, empresas)
            return
        
        # Continuar con empresa actual (después de detectar intento de cambio)
        if callback_data == "advisor_continue":
            session = session_manager.get_session(chat_id)
            if session and session.get('intent') == 'asesor_ia':
                session_data = session.get('data', {})
                empresa_info = {
                    'id': session_data.get('selected_company_id'),
                    'nombre': session_data.get('selected_company_name', 'N/A')
                }
                await AdvisorHandler._show_advisor_interface(query, empresa_info)
            else:
                await query.edit_message_text("❌ No hay sesión activa.")
            return
        
        # Crear ticket desde botón
        if callback_data == "advisor_create_ticket":
            session = session_manager.get_session(chat_id)
            if session and session.get('intent') == 'asesor_ia':
                session_data = session.get('data', {})
                qa_history = session_data.get('qa_history', [])
                
                # Obtener última pregunta del historial
                ultima_pregunta = qa_history[-1].get('pregunta', 'Consulta no especificada') if qa_history else 'Consulta no especificada'
                
                await AdvisorHandler._escalate_to_admin_from_callback(
                    query, chat_id, ultima_pregunta, session_data, 
                    "Usuario solicitó ayuda - La IA no pudo responder"
                )
            else:
                await query.edit_message_text("❌ No hay sesión activa.")
            return
    
    @staticmethod
    async def _handle_quick_query(query, chat_id: int, pregunta: str):
        """Manejar consulta rápida predefinida"""
        session_manager = get_session_manager()
        session = session_manager.get_session(chat_id)
        
        if not session or session.get('intent') != 'asesor_ia':
            await query.edit_message_text("❌ No hay sesión activa del Asesor IA.")
            return
        
        session_data = session.get('data', {})
        empresa_id = session_data.get('selected_company_id')
        empresa_nombre = session_data.get('selected_company_name', 'N/A')
        
        if not empresa_id:
            await query.edit_message_text("❌ No hay empresa seleccionada.")
            return
        
        # Mostrar "pensando..."
        await query.edit_message_text(
            f"🤖 **Asesor IA - {escape_markdown(empresa_nombre)}**\n\n"
            f"💭 Procesando tu consulta...",
            parse_mode='Markdown'
        )
        
        # Procesar pregunta
        response = await AdvisorHandler._process_question(chat_id, pregunta, session_data)
        
        keyboard = [
            [
                InlineKeyboardButton("🔄 Cambiar empresa", callback_data="advisor_change_company"),
                InlineKeyboardButton("🔙 Menú principal", callback_data="back_main")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        text = (
            f"🤖 **Asesor IA - {escape_markdown(empresa_nombre)}**\n\n"
            f"❓ **Tu consulta:** {escape_markdown(pregunta)}\n\n"
            f"📝 **Respuesta:**\n{response}\n\n"
            f"_Escribe otra pregunta o usa los botones._"
        )
        
        await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')
    
    @staticmethod
    async def handle_advisor_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Manejar mensajes de texto durante sesión de Asesor IA"""
        chat_id = update.effective_chat.id
        message_text = update.message.text.strip()
        
        logger.info(f"🤖 Advisor message: '{message_text[:50]}...' para chat_id={chat_id}")
        
        session_manager = get_session_manager()
        session = session_manager.get_session(chat_id)
        
        if not session or session.get('intent') != 'asesor_ia':
            logger.info(f"⚠️ No hay sesión de asesor activa para {chat_id}")
            return False  # No es una sesión de asesor, dejar que otro handler lo procese
        
        session_data = session.get('data', {})
        empresa_id = session_data.get('selected_company_id')
        empresa_nombre = session_data.get('selected_company_name', 'N/A')
        
        if not empresa_id:
            await update.message.reply_text("❌ No hay empresa seleccionada. Usa /start para comenzar.")
            return True
        
        company_guard = get_company_guard()
        
        # Detectar intento de cambio de empresa
        if company_guard.detect_company_change_attempt(message_text):
            empresas = company_guard.get_allowed_companies(chat_id)
            
            if len(empresas) <= 1:
                await update.message.reply_text(
                    f"ℹ️ Solo tienes acceso a **{escape_markdown(empresa_nombre)}**.\n\n"
                    f"¿En qué más puedo ayudarte?",
                    parse_mode='Markdown'
                )
            else:
                keyboard = [
                    [
                        InlineKeyboardButton("🔄 Cambiar empresa", callback_data="advisor_change_company"),
                        InlineKeyboardButton("❌ Continuar", callback_data="advisor_continue")
                    ]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                await update.message.reply_text(
                    f"⚠️ Estás consultando **{escape_markdown(empresa_nombre)}**.\n\n"
                    f"Para consultar otra empresa, usa el botón 'Cambiar empresa'.",
                    reply_markup=reply_markup,
                    parse_mode='Markdown'
                )
            return True
        
        # Detectar acciones prohibidas
        if AdvisorHandler._detect_forbidden_action(message_text):
            await AdvisorHandler._escalate_to_admin(update, chat_id, message_text, session_data, "Acción prohibida detectada")
            return True
        
        # Detectar solicitud explícita de ticket
        if AdvisorHandler._detect_ticket_request(message_text):
            await AdvisorHandler._escalate_to_admin(update, chat_id, message_text, session_data, "Solicitud de asistencia humana")
            return True
        
        # Mostrar "pensando..."
        thinking_msg = await update.message.reply_text(
            f"💭 Procesando tu consulta sobre **{escape_markdown(empresa_nombre)}**...",
            parse_mode='Markdown'
        )
        
        # Procesar pregunta con PolicyGate
        try:
            response = await AdvisorHandler._process_question(chat_id, message_text, session_data)
            
            # Detectar si la IA no pudo responder
            needs_ticket = False
            if "NO_TENGO_INFO" in response:
                needs_ticket = True
                # Limpiar el marcador de la respuesta
                response = response.replace("NO_TENGO_INFO:", "⚠️ **No encontré esa información:**")
            
            # Crear keyboard con opción de ticket si es necesario
            if needs_ticket:
                keyboard = [
                    [InlineKeyboardButton("🎫 Crear ticket de ayuda", callback_data="advisor_create_ticket")],
                    [
                        InlineKeyboardButton("🔄 Cambiar empresa", callback_data="advisor_change_company"),
                        InlineKeyboardButton("🔙 Menú principal", callback_data="back_main")
                    ]
                ]
                response += "\n\n💡 _Si necesitas esta información, puedo crear un ticket para el equipo._"
            else:
                keyboard = [
                    [
                        InlineKeyboardButton("🔄 Cambiar empresa", callback_data="advisor_change_company"),
                        InlineKeyboardButton("🔙 Menú principal", callback_data="back_main")
                    ]
                ]
            
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await thinking_msg.edit_text(
                f"🤖 **Asesor IA - {escape_markdown(empresa_nombre)}**\n\n"
                f"📝 {response}\n\n"
                f"_Escribe otra pregunta o usa los botones._",
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )
            
            # Actualizar historial en sesión
            qa_history = session_data.get('qa_history', [])
            qa_history.append({
                'pregunta': message_text[:200],
                'timestamp': datetime.now().isoformat()
            })
            # Mantener solo últimas 10 interacciones
            if len(qa_history) > 10:
                qa_history = qa_history[-10:]
            
            session_manager.update_session(
                chat_id=chat_id,
                data={'qa_history': qa_history}
            )
            
        except NoCompanySelectedError:
            await thinking_msg.edit_text("❌ No hay empresa seleccionada. Usa /start para comenzar.")
        except CompanyNotAuthorizedError:
            await thinking_msg.edit_text("❌ No tienes acceso a esta empresa.")
        except Exception as e:
            logger.error(f"❌ Error procesando pregunta: {e}", exc_info=True)
            await thinking_msg.edit_text(
                "❌ Error procesando tu consulta. Por favor, intenta de nuevo."
            )
        
        return True
    
    @staticmethod
    async def _process_question(
        chat_id: int, 
        pregunta: str, 
        session_data: Dict[str, Any]
    ) -> str:
        """
        Procesar pregunta con PolicyGate y AI.
        Usa OpenAI Assistants si hay PDFs procesados, sino usa método tradicional.
        
        Args:
            chat_id: Chat ID del usuario
            pregunta: Pregunta del usuario
            session_data: Datos de sesión
            
        Returns:
            Respuesta del asistente
        """
        company_guard = get_company_guard()
        assistant_service = get_assistant_service()
        
        # PolicyGate: Validar empresa
        empresa_id = company_guard.require_company(chat_id, session_data)
        empresa_nombre = session_data.get('selected_company_name', 'N/A')
        
        logger.info(f"🔍 Procesando pregunta para empresa {empresa_id}: '{pregunta[:50]}...'")
        
        try:
            # Verificar si la empresa tiene PDFs procesados en OpenAI
            archivos_openai = await assistant_service.get_assistant_files_count(empresa_id)
            
            if archivos_openai > 0:
                # Usar OpenAI Assistants (PDFs procesados)
                logger.info(f"📚 Usando Assistants API ({archivos_openai} PDFs disponibles)")
                
                result = await assistant_service.query_assistant(
                    empresa_id=empresa_id,
                    pregunta=pregunta,
                    chat_id=chat_id
                )
                
                if result.get('exito'):
                    respuesta = result.get('respuesta', 'No pude procesar tu consulta.')
                    fuentes = result.get('fuentes', [])
                    
                    if fuentes:
                        respuesta += f"\n\n📎 _Basado en {len(fuentes)} documento(s)_"
                    
                    return respuesta
                else:
                    # Fallback si falla Assistants
                    logger.warning("⚠️ Assistants API falló, usando método tradicional")
            
            # Método tradicional (metadatos)
            logger.info(f"📋 Usando método tradicional (metadatos)")
            
            ai_service = get_ai_service()
            
            # Detectar contexto temporal
            pregunta_lower = pregunta.lower()
            limit_reportes = 10
            
            if any(palabra in pregunta_lower for palabra in ['año', 'anual', 'todo el año', 'este año', '2024', '2025', 'acumulado']):
                limit_reportes = 50
            elif any(palabra in pregunta_lower for palabra in ['trimestre', 'trimestral', 'últimos meses', 'semestre']):
                limit_reportes = 20
            
            # Obtener reportes financieros
            reportes_financieros = supabase.get_reportes_financieros(
                empresa_id=empresa_id,
                chat_id=chat_id,
                limit=limit_reportes
            )
            
            # Obtener reportes CFO/ejecutivos
            reportes_cfo = supabase.get_reportes_cfo(
                empresa_id=empresa_id,
                chat_id=chat_id,
                limit=limit_reportes
            )
            
            # Obtener historial de conversación
            qa_history = session_data.get('qa_history', [])
            historial = [{'mensaje': q.get('pregunta', '')} for q in qa_history[-5:]]
            
            logger.info(f"📊 Contexto: {len(reportes_financieros)} reportes financieros, {len(reportes_cfo)} reportes CFO")
            
            # Llamar a AI con rol ACA_QA
            result = await ai_service.answer_as_aca_qa(
                pregunta=pregunta,
                empresa_nombre=empresa_nombre,
                reportes_financieros=reportes_financieros,
                reportes_cfo=reportes_cfo,
                historial=historial
            )
            
            respuesta = result.get('respuesta', 'No pude procesar tu consulta.')
            requiere_ticket = result.get('requiere_ticket', False)
            
            if requiere_ticket:
                respuesta += "\n\n🎫 _Esta solicitud ha sido marcada para revisión del equipo._"
            
            # Si no hay PDFs procesados, sugerir procesarlos
            if archivos_openai == 0:
                respuesta += "\n\n💡 _Para respuestas más precisas, los PDFs de esta empresa pueden ser procesados._"
            
            return respuesta
            
        except Exception as e:
            logger.error(f"❌ Error procesando pregunta: {e}")
            return "Lo siento, hubo un error al consultar la información. Por favor, intenta de nuevo."
    
    @staticmethod
    def _detect_forbidden_action(message: str) -> bool:
        """Detectar si el mensaje solicita una acción prohibida"""
        message_lower = message.lower()
        for action in AdvisorHandler.FORBIDDEN_ACTIONS:
            if action in message_lower:
                logger.warning(f"⚠️ Acción prohibida detectada: '{action}'")
                return True
        return False
    
    @staticmethod
    def _detect_ticket_request(message: str) -> bool:
        """Detectar si el usuario solicita crear un ticket o hablar con humano"""
        message_lower = message.lower()
        
        # Detectar palabras clave simples
        for keyword in AdvisorHandler.TICKET_KEYWORDS:
            if keyword in message_lower:
                logger.info(f"🎫 Solicitud de ticket detectada: '{keyword}'")
                return True
        
        # Detectar patrones más complejos
        import re
        patterns = [
            r'crea\w*\s+\w*\s*ticket',  # crea/crear un ticket
            r'genera\w*\s+\w*\s*ticket',  # genera/generar un ticket
            r'abr\w*\s+\w*\s*ticket',  # abre/abrir un ticket
            r'neces\w+\s+ayuda',  # necesito ayuda
            r'quiero\s+hablar',  # quiero hablar
        ]
        
        for pattern in patterns:
            if re.search(pattern, message_lower):
                logger.info(f"🎫 Solicitud de ticket detectada por patrón: '{pattern}'")
                return True
        
        return False
    
    @staticmethod
    def _generate_ticket_id() -> str:
        """Generar ID único para ticket"""
        import uuid
        import time
        # Formato: TKT-YYYYMMDD-XXXX (ej: TKT-20241205-A1B2)
        date_part = datetime.now().strftime('%Y%m%d')
        unique_part = uuid.uuid4().hex[:4].upper()
        return f"TKT-{date_part}-{unique_part}"
    
    @staticmethod
    async def _escalate_to_admin(
        update: Update, 
        chat_id: int, 
        solicitud: str, 
        session_data: Dict[str, Any],
        motivo: str
    ):
        """
        Escalar solicitud al administrador mediante ticket usando bot admin.
        """
        from telegram import Bot
        
        admin_chat_id = getattr(Config, 'ADMIN_CHAT_ID', None)
        # Usar bot de producción para enviar tickets (más confiable)
        bot_token = getattr(Config, 'BOT_PRODUCTION_TOKEN', None)
        
        if not admin_chat_id:
            logger.error("❌ ADMIN_CHAT_ID no configurado")
            await update.message.reply_text(
                "⚠️ Esta solicitud requiere revisión humana, pero no pude crear el ticket.\n"
                "Por favor, contacta directamente al administrador."
            )
            return
        
        if not bot_token:
            logger.error("❌ BOT_PRODUCTION_TOKEN no configurado")
            await update.message.reply_text(
                "⚠️ No pude crear el ticket.\n"
                "Por favor, contacta directamente al administrador."
            )
            return
        
        # Generar ID único del ticket
        ticket_id = AdvisorHandler._generate_ticket_id()
        
        empresa_id = session_data.get('selected_company_id', 'N/A')
        empresa_nombre = session_data.get('selected_company_name', 'N/A')
        
        # Obtener info del usuario
        user = update.effective_user
        username = f"@{user.username}" if user.username else f"ID: {user.id}"
        nombre = user.full_name or "Sin nombre"
        
        # Construir mensaje del ticket para admin
        ticket_text = (
            f"🎫 **TICKET: {ticket_id}**\n\n"
            f"📋 **Consulta:**\n{solicitud[:500]}\n\n"
            f"🏢 **Empresa:** {empresa_nombre}\n"
            f"👤 **Usuario:** {nombre} ({username})\n"
            f"💬 **Chat ID:** `{chat_id}`\n\n"
            f"⚠️ **Motivo:** {motivo}\n"
            f"📅 **Fecha:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
            f"_Para responder, usa el chat ID del usuario._"
        )
        
        try:
            logger.info(f"📤 Intentando enviar ticket {ticket_id} al admin {admin_chat_id}")
            
            # Usar el mismo bot que recibió el mensaje para enviar al admin
            bot = update.get_bot()
            await bot.send_message(
                chat_id=int(admin_chat_id),
                text=ticket_text,
                parse_mode='Markdown'
            )
            
            logger.info(f"✅ Ticket {ticket_id} enviado al admin {admin_chat_id}")
            
            # Confirmar al usuario con el ID del ticket
            await update.message.reply_text(
                f"✅ **Ticket Creado**\n\n"
                f"🎫 **ID:** `{ticket_id}`\n\n"
                f"Tu solicitud ha sido enviada al equipo de soporte.\n\n"
                f"📋 Consulta: _{escape_markdown(solicitud[:80])}..._\n\n"
                f"Guarda el ID del ticket para seguimiento.\n"
                f"Un administrador te contactará pronto.",
                parse_mode='Markdown'
            )
            
        except Exception as e:
            logger.error(f"❌ Error enviando ticket {ticket_id}: {e}", exc_info=True)
            await update.message.reply_text(
                f"⚠️ Error al crear ticket.\n\n"
                f"Detalles: {str(e)[:100]}\n\n"
                f"Por favor, contacta al administrador directamente."
            )
    
    @staticmethod
    async def _escalate_to_admin_from_callback(
        query,
        chat_id: int, 
        solicitud: str, 
        session_data: Dict[str, Any],
        motivo: str
    ):
        """
        Escalar solicitud al administrador mediante ticket (desde callback) usando bot admin.
        """
        from telegram import Bot
        
        admin_chat_id = getattr(Config, 'ADMIN_CHAT_ID', None)
        
        if not admin_chat_id:
            logger.error("❌ ADMIN_CHAT_ID no configurado")
            await query.edit_message_text(
                "⚠️ No pude crear el ticket (ADMIN_CHAT_ID no configurado).\n"
                "Por favor, contacta directamente al administrador."
            )
            return
        
        # Generar ID único del ticket
        ticket_id = AdvisorHandler._generate_ticket_id()
        
        empresa_id = session_data.get('selected_company_id', 'N/A')
        empresa_nombre = session_data.get('selected_company_name', 'N/A')
        
        # Obtener info del usuario
        user = query.from_user
        username = f"@{user.username}" if user.username else f"ID: {user.id}"
        nombre = user.full_name or "Sin nombre"
        
        # Construir mensaje del ticket para admin
        ticket_text = (
            f"🎫 **TICKET: {ticket_id}**\n\n"
            f"📋 **Consulta:**\n{solicitud[:500]}\n\n"
            f"🏢 **Empresa:** {empresa_nombre}\n"
            f"👤 **Usuario:** {nombre} ({username})\n"
            f"💬 **Chat ID:** `{chat_id}`\n\n"
            f"⚠️ **Motivo:** {motivo}\n"
            f"📅 **Fecha:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
            f"_Para responder, usa el chat ID del usuario._"
        )
        
        try:
            logger.info(f"📤 Intentando enviar ticket {ticket_id} al admin {admin_chat_id} (callback)")
            
            # Usar el mismo bot que recibió el mensaje
            bot = query.get_bot()
            await bot.send_message(
                chat_id=int(admin_chat_id),
                text=ticket_text,
                parse_mode='Markdown'
            )
            
            logger.info(f"✅ Ticket {ticket_id} enviado al admin {admin_chat_id}")
            
            # Confirmar al usuario con ID del ticket
            keyboard = [
                [
                    InlineKeyboardButton("🔄 Cambiar empresa", callback_data="advisor_change_company"),
                    InlineKeyboardButton("🔙 Menú principal", callback_data="back_main")
                ]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(
                f"✅ **Ticket Creado**\n\n"
                f"🎫 **ID:** `{ticket_id}`\n\n"
                f"Tu solicitud ha sido enviada al equipo de soporte.\n\n"
                f"📋 Consulta: _{escape_markdown(solicitud[:80])}..._\n\n"
                f"Guarda el ID del ticket para seguimiento.\n"
                f"Un administrador te contactará pronto.\n\n"
                f"_¿Necesitas algo más?_",
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )
            
        except Exception as e:
            logger.error(f"❌ Error enviando ticket {ticket_id}: {e}", exc_info=True)
            await query.edit_message_text(
                f"⚠️ Error al crear ticket.\n\n"
                f"Detalles: {str(e)[:100]}\n\n"
                f"Por favor, contacta al administrador directamente."
            )

