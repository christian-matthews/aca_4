from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from app.security.auth import security
from app.database.supabase import supabase
from app.config import Config
from app.decorators.conversation_logging import log_admin_conversation, log_admin_action, log_unauthorized_access
import logging

logger = logging.getLogger(__name__)

def escape_markdown(text):
    """Escapar caracteres especiales para Markdown"""
    if not text:
        return text
    return text.replace('_', '\\_').replace('*', '\\*').replace('[', '\\[').replace(']', '\\]').replace('`', '\\`')

class AdminHandlers:
    """Manejadores para el bot de administración"""
    
    @staticmethod
    @log_admin_conversation
    async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Comando de inicio para el bot admin"""
        chat_id = update.effective_chat.id
        
        if not security.is_admin(chat_id):
            # Registrar intento no autorizado
            await AdminHandlers._handle_unauthorized_admin(update, context)
            return
        
        keyboard = [
            [
                InlineKeyboardButton("📊 Crear Empresa", callback_data="create_empresa"),
                InlineKeyboardButton("👥 Ver Empresas", callback_data="list_empresas")
            ],
            [
                InlineKeyboardButton("➕ Agregar Usuario", callback_data="add_user"),
                InlineKeyboardButton("📋 Ver Usuarios", callback_data="list_users")
            ],
            [
                InlineKeyboardButton("📈 Estadísticas", callback_data="stats"),
                InlineKeyboardButton("⚙️ Configuración", callback_data="config")
            ],
            [InlineKeyboardButton("🔄 Reiniciar Bots", callback_data="restart_bots")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await AdminHandlers._show_main_menu(update.message)
    
    @staticmethod
    @log_unauthorized_access()
    async def _handle_unauthorized_admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Manejar intentos no autorizados al bot admin"""
        # Crear botón de contacto directo
        keyboard = [
            [InlineKeyboardButton("💬 Contactar a @wingmanbod", url="https://t.me/wingmanbod")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        # El decorador registra automáticamente el intento
        await update.message.reply_text(
            "🚫 **Acceso Denegado**\n\n"
            "No tienes permisos de administrador.\n"
            "Este incidente ha sido registrado.\n\n"
            "📞 Para solicitar acceso presiona el botón:",
            reply_markup=reply_markup
        )
    
    @staticmethod
    @log_admin_action("crear_empresa")
    async def crear_empresa_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Comando para crear empresa (con logging automático)"""
        await update.message.reply_text("🏢 Función de crear empresa en desarrollo...")
    
    @staticmethod
    @log_admin_action("adduser")
    async def adduser_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Comando simplificado para agregar usuario
        Formato: /adduser CHAT_ID NOMBRE ROL RUT_EMPRESA
        """
        chat_id = update.effective_chat.id
        
        if not security.is_admin(chat_id):
            await update.message.reply_text("🚫 No tienes permisos de administrador.")
            return
        
        # Verificar argumentos
        if len(context.args) < 4:
            await update.message.reply_text(
                "❌ *Formato incorrecto*\n\n"
                "Usa: `/adduser CHAT_ID NOMBRE ROL RUT_EMPRESA`\n\n"
                "*Ejemplo*: `/adduser 123456789 \"Juan Perez\" user 76142021-6`\n\n"
                "**Roles disponibles:**\n"
                "• `super_admin` - Todos los permisos\n"
                "• `gestor` - Puede subir y bajar archivos\n"
                "• `user` - Solo puede bajar archivos\n\n"
                "💡 Consejo: El RUT debe incluir guión (ej: 12345678-9)",
                parse_mode='Markdown'
            )
            return
        
        try:
            user_chat_id = int(context.args[0])
            nombre_usuario = " ".join(context.args[1:-2])  # Nombre puede tener espacios
            rol = context.args[-2].lower()
            rut_empresa = context.args[-1]
            
            # Validar rol
            roles_validos = ['super_admin', 'gestor', 'user', 'usuario']
            if rol not in roles_validos:
                await update.message.reply_text(
                    f"❌ *Rol inválido*\n\n"
                    f"Rol recibido: `{rol}`\n\n"
                    "**Roles válidos:**\n"
                    "• `super_admin` - Todos los permisos\n"
                    "• `gestor` - Puede subir y bajar archivos\n"
                    "• `user` - Solo puede bajar archivos",
                    parse_mode='Markdown'
                )
                return
            
            # Normalizar 'usuario' a 'user'
            if rol == 'usuario':
                rol = 'user'
            
            # ✅ Buscar empresa por RUT en lugar de UUID
            empresa = supabase.table('empresas').select('*').eq('rut', rut_empresa).execute()
            if not empresa.data:
                await update.message.reply_text(
                    f"❌ *Empresa no encontrada*\n\n"
                    f"RUT: `{rut_empresa}`\n\n"
                    "Verifica que el RUT esté correcto (con guión)",
                    parse_mode='Markdown'
                )
                return
            
            empresa_id = empresa.data[0]['id']
            empresa_nombre = empresa.data[0]['nombre']
            
            # Verificar si el usuario ya existe
            usuario_existente = supabase.table('usuarios').select('*').eq('chat_id', user_chat_id).execute()
            
            usuario_id = None
            if usuario_existente.data:
                # Actualizar usuario existente
                usuario_id = usuario_existente.data[0]['id']
                resultado = supabase.table('usuarios').update({
                    'empresa_id': empresa_id,
                    'nombre': nombre_usuario,
                    'rol': rol,
                    'activo': True
                }).eq('chat_id', user_chat_id).execute()
                
                mensaje = f"🔄 *Usuario actualizado*\n\n"
            else:
                # Crear nuevo usuario
                resultado = supabase.table('usuarios').insert({
                    'chat_id': user_chat_id,
                    'empresa_id': empresa_id,
                    'nombre': nombre_usuario,
                    'rol': rol,
                    'activo': True
                }).execute()
                
                if resultado.data:
                    usuario_id = resultado.data[0]['id']
                
                mensaje = f"✅ *Usuario creado*\n\n"
            
            # ✅ Asociar usuario a empresa en usuarios_empresas (sistema multi-empresa)
            if usuario_id:
                # Verificar si ya existe relación
                relacion_existente = supabase.table('usuarios_empresas')\
                    .select('*')\
                    .eq('usuario_id', usuario_id)\
                    .eq('empresa_id', empresa_id)\
                    .execute()
                
                if not relacion_existente.data:
                    # Crear relación en usuarios_empresas
                    supabase.table('usuarios_empresas').insert({
                        'usuario_id': usuario_id,
                        'empresa_id': empresa_id,
                        'rol': rol,
                        'activo': True
                    }).execute()
            
            # Mensaje de confirmación
            await update.message.reply_text(
                mensaje +
                f"👤 **Chat ID:** `{user_chat_id}`\n"
                f"🏷️ **Nombre:** {escape_markdown(nombre_usuario)}\n"
                f"🏢 **Empresa:** {escape_markdown(empresa_nombre)} ({rut_empresa})\n"
                f"👔 **Rol:** {rol}\n"
                f"📱 **Estado:** 🟢 Activo\n\n"
                f"🎉 El usuario ya puede usar el bot de producción",
                parse_mode='Markdown'
            )
            
        except ValueError:
            await update.message.reply_text(
                "❌ *Chat ID inválido*\n\n"
                "El Chat ID debe ser un número.\n"
                "Ejemplo: `123456789`",
                parse_mode='Markdown'
            )
        except Exception as e:
            logger.error(f"Error agregando usuario: {e}")
            await update.message.reply_text(
                f"❌ *Error al agregar usuario*\n\n"
                f"Error: {str(e)}"
            )
    
    @staticmethod
    @log_admin_conversation
    async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Manejar callbacks del bot admin con logging"""
        query = update.callback_query
        await query.answer()
        
        if not security.is_admin(query.from_user.id):
            await AdminHandlers._handle_unauthorized_admin(update, context)
            return
        
        data = query.data
        
        if data == "create_empresa":
            await query.edit_message_text("🏢 Función de crear empresa en desarrollo...")
        elif data == "list_empresas":
            await AdminHandlers._list_empresas(query)
        elif data == "add_user":
            await AdminHandlers._start_add_user_flow(query)
        elif data == "list_users":
            await AdminHandlers._list_users(query)
        elif data == "stats":
            await AdminHandlers._show_stats(query)
        elif data == "config":
            await query.edit_message_text("⚙️ Función de configuración en desarrollo...")
        elif data == "restart_bots":
            await query.edit_message_text("🔄 Función de reiniciar bots en desarrollo...")
        elif data == "back_to_menu":
            await AdminHandlers._show_main_menu(query)
        else:
            await query.edit_message_text("❓ Opción no reconocida")
    
    @staticmethod
    async def _show_main_menu(message_or_query):
        """Mostrar menú principal de administración"""
        keyboard = [
            [
                InlineKeyboardButton("📊 Crear Empresa", callback_data="create_empresa"),
                InlineKeyboardButton("👥 Ver Empresas", callback_data="list_empresas")
            ],
            [
                InlineKeyboardButton("📈 Estadísticas", callback_data="stats"),
                InlineKeyboardButton("⚙️ Configuración", callback_data="config")
            ],
            [InlineKeyboardButton("🔄 Reiniciar Bots", callback_data="restart_bots")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        text = "🔧 **Panel de Administración**\n\nBienvenido al sistema de administración. Selecciona una opción:"
        
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
        """Manejar callbacks del bot admin"""
        query = update.callback_query
        await query.answer()
        
        chat_id = update.effective_chat.id
        
        if not security.is_admin(chat_id):
            await query.edit_message_text("No tienes permisos de administrador.")
            return
        
        if query.data == "create_empresa":
            await AdminHandlers._show_create_empresa_form(query)
        elif query.data == "list_empresas":
            await AdminHandlers._show_empresas_list(query)
        elif query.data == "stats":
            await AdminHandlers._show_stats(query)
        elif query.data == "config":
            await AdminHandlers._show_config(query)
        elif query.data == "restart_bots":
            await AdminHandlers._restart_bots(query)
        elif query.data == "back_main":
            await AdminHandlers._show_main_menu(query)
        elif query.data.startswith("empresa_"):
            await AdminHandlers._handle_empresa_action(query)
    
    @staticmethod
    async def _show_create_empresa_form(query):
        """Mostrar formulario para crear empresa"""
        text = (
            "📝 *Crear Nueva Empresa*\n\n"
            "Para crear una nueva empresa, envía el mensaje en el siguiente formato:\n\n"
            "/crear_empresa RUT NOMBRE CHAT_ID\n\n"
            "Ejemplo:\n"
            "/crear_empresa 12345678-9 Empresa Ejemplo 123456789\n\n"
            "Donde:\n"
            "• RUT: RUT de la empresa\n"
            "• NOMBRE: Nombre de la empresa\n"
            "• CHAT_ID: ID del chat del usuario principal"
        )
        
        keyboard = [[InlineKeyboardButton("🔙 Volver al Menú", callback_data="back_main")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')
    
    @staticmethod
    async def _show_empresas_list(query):
        """Mostrar lista de empresas"""
        try:
            response = supabase.client.table('empresas').select('*').eq('activo', True).execute()
            empresas = response.data
            
            if not empresas:
                await query.edit_message_text("No hay empresas registradas.")
                return
            
            text = "🏢 **Empresas Registradas**\n\n"
            keyboard = []
            
            # Crear botones en dos columnas
            for i in range(0, len(empresas), 2):
                row = []
                row.append(InlineKeyboardButton(
                    f"📋 {empresas[i]['nombre'][:15]}", 
                    callback_data=f"empresa_{empresas[i]['id']}"
                ))
                
                # Agregar segunda columna si existe
                if i + 1 < len(empresas):
                    row.append(InlineKeyboardButton(
                        f"📋 {empresas[i+1]['nombre'][:15]}", 
                        callback_data=f"empresa_{empresas[i+1]['id']}"
                    ))
                
                keyboard.append(row)
            
            # Agregar botón volver
            keyboard.append([InlineKeyboardButton("🔙 Volver al Menú", callback_data="back_main")])
            
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Error obteniendo empresas: {e}")
            await query.edit_message_text("Error obteniendo la lista de empresas.")
    
    @staticmethod
    async def _show_stats(query):
        """Mostrar estadísticas del sistema"""
        try:
            # Contar empresas
            empresas_response = supabase.client.table('empresas').select('id', count='exact').eq('activo', True).execute()
            empresas_count = empresas_response.count if hasattr(empresas_response, 'count') else 0
            
            # Contar usuarios
            usuarios_response = supabase.client.table('usuarios').select('id', count='exact').eq('activo', True).execute()
            usuarios_count = usuarios_response.count if hasattr(usuarios_response, 'count') else 0
            
            # Contar conversaciones
            conv_response = supabase.client.table('conversaciones').select('id', count='exact').execute()
            conv_count = conv_response.count if hasattr(conv_response, 'count') else 0
            
            text = (
                "📊 **Estadísticas del Sistema**\n\n"
                f"🏢 **Empresas activas:** {empresas_count}\n"
                f"👥 **Usuarios registrados:** {usuarios_count}\n"
                f"💬 **Conversaciones totales:** {conv_count}\n\n"
                "Última actualización: Ahora"
            )
            
            keyboard = [[InlineKeyboardButton("🔙 Volver al Menú", callback_data="back_main")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Error obteniendo estadísticas: {e}")
            await query.edit_message_text("Error obteniendo estadísticas.")
    
    @staticmethod
    async def _handle_empresa_action(query):
        """Manejar acciones específicas de empresa"""
        empresa_id = query.data.split('_')[1]
        
        try:
            # Obtener datos de la empresa
            empresa_response = supabase.client.table('empresas').select('*').eq('id', empresa_id).execute()
            empresa = empresa_response.data[0] if empresa_response.data else None
            
            if not empresa:
                await query.edit_message_text("Empresa no encontrada.")
                return
            
            # Obtener usuarios de la empresa
            usuarios_response = supabase.client.table('usuarios').select('*').eq('empresa_id', empresa_id).execute()
            usuarios = usuarios_response.data
            
            text = f"🏢 **{empresa['nombre']}**\n\n"
            text += f"**RUT:** {empresa['rut']}\n"
            text += f"**Estado:** {'Activa' if empresa['activo'] else 'Inactiva'}\n\n"
            text += f"**Usuarios ({len(usuarios)}):**\n"
            
            for usuario in usuarios:
                text += f"• {usuario['nombre']} (Chat ID: {usuario['chat_id']})\n"
            
            keyboard = [
                [InlineKeyboardButton("🔙 Volver", callback_data="list_empresas")],
                [InlineKeyboardButton("❌ Desactivar Empresa", callback_data=f"deactivate_{empresa_id}")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Error obteniendo datos de empresa: {e}")
            await query.edit_message_text("Error obteniendo datos de la empresa.")
    
    @staticmethod
    async def crear_empresa_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Comando para crear nueva empresa"""
        chat_id = update.effective_chat.id
        
        if not security.is_admin(chat_id):
            await update.message.reply_text("No tienes permisos de administrador.")
            return
        
        try:
            # Parsear argumentos: /crear_empresa RUT NOMBRE CHAT_ID
            args = context.args
            if len(args) < 3:
                await update.message.reply_text(
                    "Formato incorrecto. Usa:\n"
                    "`/crear_empresa RUT NOMBRE CHAT_ID`"
                )
                return
            
            rut = args[0]
            nombre = ' '.join(args[1:-1])  # Nombre puede tener espacios
            admin_chat_id = int(args[-1])
            
            # Crear empresa
            empresa_id = supabase.create_empresa(rut, nombre, admin_chat_id)
            
            if empresa_id:
                await update.message.reply_text(
                    f"✅ **Empresa creada exitosamente**\n\n"
                    f"**Nombre:** {nombre}\n"
                    f"**RUT:** {rut}\n"
                    f"**ID Empresa:** {empresa_id}\n"
                    f"**Admin Chat ID:** {admin_chat_id}\n\n"
                    "La empresa ya puede usar el bot de producción."
                )
                
                # Log de seguridad
                security.log_security_event(
                    chat_id, 
                    "empresa_creada", 
                    f"Empresa {nombre} (ID: {empresa_id}) creada"
                )
            else:
                await update.message.reply_text("❌ Error creando la empresa. Verifica los datos.")
                
        except ValueError:
            await update.message.reply_text("❌ El CHAT_ID debe ser un número válido.")
        except Exception as e:
            logger.error(f"Error creando empresa: {e}")
            await update.message.reply_text("❌ Error interno creando la empresa.")
    
    @staticmethod
    async def _show_config(query):
        """Mostrar configuración del sistema"""
        try:
            from app.config import Config
            
            text = (
                "⚙️ **Configuración del Sistema**\n\n"
                f"**Entorno:** {Config.ENVIRONMENT}\n"
                f"**Debug:** {'Activado' if Config.DEBUG else 'Desactivado'}\n"
                f"**Admin Chat ID:** {Config.ADMIN_CHAT_ID}\n\n"
                "**Variables configuradas:**\n"
                f"• BOT_ADMIN_TOKEN: {'✅' if Config.BOT_ADMIN_TOKEN else '❌'}\n"
                f"• BOT_PRODUCTION_TOKEN: {'✅' if Config.BOT_PRODUCTION_TOKEN else '❌'}\n"
                f"• SUPABASE_URL: {'✅' if Config.SUPABASE_URL else '❌'}\n"
                f"• SUPABASE_KEY: {'✅' if Config.SUPABASE_KEY else '❌'}\n"
                f"• OPENAI_API_KEY: {'✅' if Config.OPENAI_API_KEY else '❌'}\n"
            )
            
            keyboard = [[InlineKeyboardButton("🔙 Volver al Menú", callback_data="back_main")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Error mostrando configuración: {e}")
            await query.edit_message_text("Error obteniendo configuración.")
    
    @staticmethod
    async def _restart_bots(query):
        """Reiniciar bots"""
        try:
            text = (
                "🔄 **Reiniciando Bots**\n\n"
                "Los bots se están reiniciando...\n"
                "Esto puede tomar unos segundos."
            )
            
            keyboard = [[InlineKeyboardButton("🔙 Volver al Menú", callback_data="back_main")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')
            
            # Aquí podrías agregar la lógica para reiniciar los bots
            logger.info("Reinicio de bots solicitado por admin")
            
        except Exception as e:
            logger.error(f"Error reiniciando bots: {e}")
            await query.edit_message_text("Error reiniciando bots.")
    
    @staticmethod
    async def _list_empresas(query):
        """Listar empresas registradas"""
        try:
            empresas = supabase.table('empresas').select('*').limit(10).execute()
            
            if not empresas.data:
                await query.edit_message_text(
                    "📋 *Lista de Empresas*\n\n❌ No hay empresas registradas",
                    parse_mode='Markdown'
                )
                return
            
            texto = "📋 *Lista de Empresas*\n\n"
            for empresa in empresas.data:
                texto += f"🏢 **{empresa['nombre']}**\n"
                texto += f"📍 RUT: {empresa.get('rut', 'N/A')}\n"
                texto += f"🆔 ID: `{empresa['id']}`\n\n"
            
            keyboard = [[InlineKeyboardButton("🔙 Volver", callback_data="back_to_menu")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(texto, reply_markup=reply_markup, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Error listando empresas: {e}")
            await query.edit_message_text("❌ Error al cargar empresas")
    
    @staticmethod
    async def _start_add_user_flow(query):
        """Iniciar proceso de agregar usuario"""
        await query.edit_message_text(
            "➕ **Agregar Nuevo Usuario**\n\n"
            "**Formato simplificado:**\n"
            "`/adduser CHAT_ID NOMBRE ROL RUT_EMPRESA`\n\n"
            "**Ejemplo:**\n"
            "`/adduser 123456789 Juan Perez user 76142021-6`\n\n"
            "**Parámetros:**\n"
            "• **CHAT_ID:** ID del chat de Telegram del usuario\n"
            "• **NOMBRE:** Nombre del usuario (puede tener espacios)\n"
            "• **ROL:** Rol del usuario (ver abajo)\n"
            "• **RUT_EMPRESA:** RUT de la empresa (con guión)\n\n"
            "**Roles disponibles:**\n"
            "• `super_admin` - Todos los permisos\n"
            "• `gestor` - Puede subir y bajar archivos\n"
            "• `user` - Solo puede bajar archivos\n\n"
            "💡 **Consejo:** Para obtener el Chat ID, ve a conversaciones no autorizadas",
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Volver", callback_data="back_to_menu")]])
        )
    
    @staticmethod  
    async def _list_users(query):
        """Listar usuarios registrados"""
        try:
            usuarios = supabase.table('usuarios').select('*, empresas(nombre)').limit(10).execute()
            
            if not usuarios.data:
                await query.edit_message_text("📋 *Lista de Usuarios*\n\n❌ No hay usuarios registrados", parse_mode='Markdown')
                return
            
            texto = "📋 *Lista de Usuarios*\n\n"
            for usuario in usuarios.data:
                empresa_nombre = usuario.get('empresas', {}).get('nombre', 'Sin empresa') if usuario.get('empresas') else 'Sin empresa'
                estado = "🟢 Activo" if usuario.get('activo') else "🔴 Inactivo"
                
                texto += f"👤 Chat ID: `{usuario['chat_id']}`\n🏢 {empresa_nombre}\n📱 {estado}\n\n"
            
            keyboard = [[InlineKeyboardButton("🔙 Volver", callback_data="back_to_menu")]]
            await query.edit_message_text(texto, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Error listando usuarios: {e}")
            await query.edit_message_text("❌ Error al cargar usuarios")
    
    @staticmethod
    async def _show_stats(query):
        """Mostrar estadísticas del sistema"""
        try:
            from datetime import datetime
            
            empresas_count = supabase.table('empresas').select('id', count='exact').execute()
            usuarios_count = supabase.table('usuarios').select('id', count='exact').execute()
            conversaciones_count = supabase.table('conversaciones').select('id', count='exact').execute()
            
            hoy = datetime.now().date().isoformat()
            conversaciones_hoy = supabase.table('conversaciones').select('id', count='exact').gte('created_at', hoy).execute()
            
            texto = f"📈 *Estadísticas del Sistema*\n\n"
            texto += f"🏢 Empresas: {empresas_count.count}\n"
            texto += f"👥 Usuarios: {usuarios_count.count}\n"
            texto += f"💬 Conversaciones: {conversaciones_count.count}\n"
            texto += f"📅 Hoy: {conversaciones_hoy.count}\n\n"
            texto += f"🕐 Actualizado: {datetime.now().strftime('%H:%M:%S')}"
            
            keyboard = [[InlineKeyboardButton("🔙 Volver", callback_data="back_to_menu")]]
            await query.edit_message_text(texto, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Error estadísticas: {e}")
            await query.edit_message_text("❌ Error al cargar estadísticas") 