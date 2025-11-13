-- ============================================
-- 🗄️ SCHEMA COMPLETO PARA ACA 4.0
-- Sistema de Bots de Telegram con Supabase
-- ============================================

-- Habilitar extensión UUID si no existe
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ============================================
-- TABLAS CRÍTICAS (Esenciales)
-- ============================================

-- 1. TABLA: empresas
CREATE TABLE IF NOT EXISTS empresas (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    rut VARCHAR(20) UNIQUE NOT NULL,
    nombre VARCHAR(255) NOT NULL,
    activo BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 2. TABLA: usuarios
CREATE TABLE IF NOT EXISTS usuarios (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    chat_id BIGINT UNIQUE NOT NULL,
    empresa_id UUID REFERENCES empresas(id) ON DELETE SET NULL,
    nombre VARCHAR(255) NOT NULL,
    rol VARCHAR(50) DEFAULT 'user',
    activo BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 3. TABLA: conversaciones
CREATE TABLE IF NOT EXISTS conversaciones (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    chat_id BIGINT NOT NULL,
    empresa_id UUID REFERENCES empresas(id) ON DELETE SET NULL,
    mensaje TEXT NOT NULL,
    respuesta TEXT,
    usuario_nombre VARCHAR(255),
    usuario_username VARCHAR(255),
    bot_tipo VARCHAR(20) DEFAULT 'production',
    comando VARCHAR(100),
    parametros JSONB,
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 4. TABLA: usuarios_detalle
CREATE TABLE IF NOT EXISTS usuarios_detalle (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    chat_id BIGINT UNIQUE NOT NULL,
    user_id BIGINT,
    first_name VARCHAR(255),
    last_name VARCHAR(255),
    username VARCHAR(255),
    language_code VARCHAR(10),
    is_bot BOOLEAN DEFAULT false,
    is_premium BOOLEAN DEFAULT false,
    phone_number VARCHAR(20),
    empresa_id UUID REFERENCES empresas(id) ON DELETE SET NULL,
    tipo_acceso VARCHAR(20) DEFAULT 'no_autorizado',
    intentos_acceso INTEGER DEFAULT 0,
    primera_interaccion TIMESTAMPTZ DEFAULT NOW(),
    ultima_interaccion TIMESTAMPTZ DEFAULT NOW(),
    total_mensajes INTEGER DEFAULT 0,
    ultima_actividad TEXT,
    bloqueado_razon TEXT,
    notas_admin TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 5. TABLA: intentos_acceso_negado
CREATE TABLE IF NOT EXISTS intentos_acceso_negado (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    chat_id BIGINT NOT NULL,
    user_id BIGINT,
    first_name VARCHAR(255),
    last_name VARCHAR(255),
    username VARCHAR(255),
    mensaje_enviado TEXT,
    accion_intentada VARCHAR(100),
    bot_tipo VARCHAR(20),
    ip_address INET,
    timestamp TIMESTAMPTZ DEFAULT NOW(),
    bloqueado BOOLEAN DEFAULT false
);

-- ============================================
-- TABLAS OPCIONALES (Recomendadas)
-- ============================================

-- 6. TABLA: security_logs
CREATE TABLE IF NOT EXISTS security_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    chat_id BIGINT NOT NULL,
    event_type VARCHAR(100) NOT NULL,
    description TEXT,
    timestamp TIMESTAMPTZ DEFAULT NOW()
);

-- 7. TABLA: bot_analytics
CREATE TABLE IF NOT EXISTS bot_analytics (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    fecha DATE NOT NULL,
    bot_tipo VARCHAR(20) NOT NULL,
    total_mensajes INTEGER DEFAULT 0,
    usuarios_unicos INTEGER DEFAULT 0,
    usuarios_nuevos INTEGER DEFAULT 0,
    comandos_ejecutados INTEGER DEFAULT 0,
    errores_count INTEGER DEFAULT 0,
    tiempo_promedio_respuesta_ms INTEGER,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(fecha, bot_tipo)
);

-- ============================================
-- TABLA STORAGE (FASE 2)
-- ============================================

-- 8. TABLA: archivos
CREATE TABLE IF NOT EXISTS archivos (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    chat_id BIGINT NOT NULL,
    empresa_id UUID REFERENCES empresas(id) ON DELETE SET NULL,
    nombre_archivo VARCHAR(255) NOT NULL,
    nombre_original VARCHAR(255),
    tipo_archivo VARCHAR(100),
    extension VARCHAR(10),
    tamaño_bytes BIGINT,
    url_archivo TEXT NOT NULL,
    storage_provider VARCHAR(50) DEFAULT 'supabase',
    storage_path TEXT,
    descripcion TEXT,
    metadata JSONB DEFAULT '{}'::jsonb,
    activo BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================
-- ÍNDICES PARA PERFORMANCE
-- ============================================

-- Índices para empresas
CREATE INDEX IF NOT EXISTS idx_empresas_rut ON empresas(rut);
CREATE INDEX IF NOT EXISTS idx_empresas_activo ON empresas(activo);

-- Índices para usuarios
CREATE INDEX IF NOT EXISTS idx_usuarios_chat_id ON usuarios(chat_id);
CREATE INDEX IF NOT EXISTS idx_usuarios_empresa_id ON usuarios(empresa_id);
CREATE INDEX IF NOT EXISTS idx_usuarios_activo ON usuarios(activo);

-- Índices para conversaciones
CREATE INDEX IF NOT EXISTS idx_conversaciones_chat_id ON conversaciones(chat_id);
CREATE INDEX IF NOT EXISTS idx_conversaciones_empresa_id ON conversaciones(empresa_id);
CREATE INDEX IF NOT EXISTS idx_conversaciones_bot_tipo ON conversaciones(bot_tipo);
CREATE INDEX IF NOT EXISTS idx_conversaciones_created_at ON conversaciones(created_at);

-- Índices para usuarios_detalle
CREATE INDEX IF NOT EXISTS idx_usuarios_detalle_chat_id ON usuarios_detalle(chat_id);
CREATE INDEX IF NOT EXISTS idx_usuarios_detalle_tipo_acceso ON usuarios_detalle(tipo_acceso);
CREATE INDEX IF NOT EXISTS idx_usuarios_detalle_ultima_interaccion ON usuarios_detalle(ultima_interaccion);

-- Índices para intentos_acceso_negado
CREATE INDEX IF NOT EXISTS idx_intentos_acceso_chat_id ON intentos_acceso_negado(chat_id);
CREATE INDEX IF NOT EXISTS idx_intentos_acceso_timestamp ON intentos_acceso_negado(timestamp);

-- Índices para archivos
CREATE INDEX IF NOT EXISTS idx_archivos_chat_id ON archivos(chat_id);
CREATE INDEX IF NOT EXISTS idx_archivos_empresa_id ON archivos(empresa_id);
CREATE INDEX IF NOT EXISTS idx_archivos_activo ON archivos(activo);

-- Índices para bot_analytics
CREATE INDEX IF NOT EXISTS idx_bot_analytics_fecha_bot ON bot_analytics(fecha, bot_tipo);

-- ============================================
-- FUNCIÓN SQL CRÍTICA
-- ============================================

-- Función: log_conversacion_simple
CREATE OR REPLACE FUNCTION log_conversacion_simple(
    p_chat_id BIGINT,
    p_mensaje TEXT,
    p_user_id BIGINT DEFAULT NULL,
    p_respuesta TEXT DEFAULT NULL,
    p_first_name VARCHAR(255) DEFAULT NULL,
    p_last_name VARCHAR(255) DEFAULT NULL,
    p_username VARCHAR(255) DEFAULT NULL,
    p_bot_tipo VARCHAR(20) DEFAULT 'production',
    p_tiene_acceso BOOLEAN DEFAULT false
) RETURNS UUID AS $$
DECLARE
    conversacion_id UUID;
    empresa_uuid UUID;
    usuario_nombre VARCHAR(255);
BEGIN
    -- Construir nombre completo
    usuario_nombre := TRIM(COALESCE(p_first_name, '') || ' ' || COALESCE(p_last_name, ''));
    IF usuario_nombre = '' THEN
        usuario_nombre := COALESCE(p_username, 'Usuario Desconocido');
    END IF;
    
    -- 1. Registrar/actualizar usuario en tabla detalle
    INSERT INTO usuarios_detalle (
        chat_id, user_id, first_name, last_name, username, 
        ultima_interaccion, total_mensajes, intentos_acceso, 
        ultima_actividad, tipo_acceso
    ) VALUES (
        p_chat_id, p_user_id, p_first_name, p_last_name, p_username,
        NOW(), 1, 
        CASE WHEN NOT p_tiene_acceso THEN 1 ELSE 0 END,
        p_mensaje,
        CASE WHEN p_tiene_acceso THEN 'autorizado' ELSE 'no_autorizado' END
    )
    ON CONFLICT (chat_id) 
    DO UPDATE SET 
        user_id = COALESCE(EXCLUDED.user_id, usuarios_detalle.user_id),
        first_name = COALESCE(EXCLUDED.first_name, usuarios_detalle.first_name),
        last_name = COALESCE(EXCLUDED.last_name, usuarios_detalle.last_name),
        username = COALESCE(EXCLUDED.username, usuarios_detalle.username),
        ultima_interaccion = NOW(),
        total_mensajes = usuarios_detalle.total_mensajes + 1,
        intentos_acceso = CASE 
            WHEN NOT p_tiene_acceso THEN usuarios_detalle.intentos_acceso + 1 
            ELSE usuarios_detalle.intentos_acceso 
        END,
        ultima_actividad = p_mensaje,
        updated_at = NOW();
    
    -- 2. Si no tiene acceso, registrar intento no autorizado
    IF NOT p_tiene_acceso THEN
        INSERT INTO intentos_acceso_negado (
            chat_id, user_id, first_name, last_name, username,
            mensaje_enviado, bot_tipo
        ) VALUES (
            p_chat_id, p_user_id, p_first_name, p_last_name, p_username,
            p_mensaje, p_bot_tipo
        );
    END IF;
    
    -- 3. Buscar empresa si tiene acceso
    IF p_tiene_acceso THEN
        SELECT empresa_id INTO empresa_uuid 
        FROM usuarios 
        WHERE chat_id = p_chat_id 
        LIMIT 1;
    END IF;
    
    -- 4. Registrar conversación
    INSERT INTO conversaciones (
        chat_id, empresa_id, mensaje, respuesta, usuario_nombre, 
        usuario_username, bot_tipo, metadata
    ) VALUES (
        p_chat_id, empresa_uuid, p_mensaje, p_respuesta, usuario_nombre,
        p_username, p_bot_tipo, 
        jsonb_build_object(
            'tiene_acceso', p_tiene_acceso,
            'user_id', p_user_id,
            'timestamp', NOW()
        )
    ) RETURNING id INTO conversacion_id;
    
    RETURN conversacion_id;
END;
$$ LANGUAGE plpgsql;

-- ============================================
-- VISTAS ÚTILES
-- ============================================

-- Vista: vista_conversaciones_recientes
CREATE OR REPLACE VIEW vista_conversaciones_recientes AS
SELECT 
    c.id,
    c.chat_id,
    c.usuario_nombre,
    c.usuario_username,
    COALESCE(e.nombre, 'Usuario No Registrado') as empresa_nombre,
    c.mensaje,
    c.respuesta,
    c.bot_tipo,
    c.created_at,
    CASE 
        WHEN c.empresa_id IS NOT NULL THEN 'Autorizado'
        ELSE 'No Autorizado'
    END as estado_usuario
FROM conversaciones c
LEFT JOIN empresas e ON c.empresa_id = e.id
ORDER BY c.created_at DESC
LIMIT 1000;

-- Vista: vista_usuarios_sin_acceso
CREATE OR REPLACE VIEW vista_usuarios_sin_acceso AS
SELECT 
    ud.chat_id,
    ud.user_id,
    ud.first_name,
    ud.last_name,
    ud.username,
    ud.intentos_acceso,
    ud.total_mensajes,
    ud.primera_interaccion,
    ud.ultima_interaccion,
    ud.tipo_acceso
FROM usuarios_detalle ud
WHERE ud.tipo_acceso IN ('no_autorizado', 'bloqueado')
ORDER BY ud.ultima_interaccion DESC;

-- ============================================
-- COMENTARIOS Y DOCUMENTACIÓN
-- ============================================

COMMENT ON TABLE empresas IS 'Tabla principal de empresas registradas';
COMMENT ON TABLE usuarios IS 'Usuarios autorizados del sistema vinculados a empresas';
COMMENT ON TABLE conversaciones IS 'Registro de todas las conversaciones con los bots';
COMMENT ON TABLE usuarios_detalle IS 'Información detallada de todos los usuarios (autorizados y no autorizados)';
COMMENT ON TABLE intentos_acceso_negado IS 'Registro de intentos de acceso no autorizados';
COMMENT ON TABLE security_logs IS 'Logs de eventos de seguridad';
COMMENT ON TABLE bot_analytics IS 'Estadísticas diarias de uso de bots';
COMMENT ON TABLE archivos IS 'Archivos subidos desde bots (FASE 2 - Storage)';

COMMENT ON FUNCTION log_conversacion_simple IS 'Función optimizada para registrar conversaciones y actualizar usuarios_detalle';

-- ============================================
-- MENSAJE DE COMPLETADO
-- ============================================

DO $$
BEGIN
    RAISE NOTICE '✅ SCHEMA ACA 4.0 CREADO EXITOSAMENTE';
    RAISE NOTICE '📊 Tablas creadas: empresas, usuarios, conversaciones, usuarios_detalle, intentos_acceso_negado, security_logs, bot_analytics, archivos';
    RAISE NOTICE '🔍 Vistas creadas: vista_conversaciones_recientes, vista_usuarios_sin_acceso';
    RAISE NOTICE '⚡ Función creada: log_conversacion_simple()';
    RAISE NOTICE '📈 Índices creados para optimización';
END $$;


