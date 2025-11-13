-- ============================================
-- MIGRACIÓN 002: Crear tabla sesiones_conversacion
-- Fecha: 2025-01-11
-- Descripción: Tabla para manejar sesiones conversacionales de archivos
-- ============================================

-- Tabla para manejar sesiones conversacionales
CREATE TABLE IF NOT EXISTS sesiones_conversacion (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    chat_id BIGINT NOT NULL,
    estado VARCHAR(50) NOT NULL, -- 'idle', 'esperando_empresa', 'esperando_categoria', 'esperando_subtipo', 'esperando_descripcion', 'esperando_periodo', 'finalizado'
    intent VARCHAR(50), -- 'subir_archivo', 'descargar_archivo'
    data JSONB DEFAULT '{}'::jsonb, -- Datos temporales de la sesión
    archivo_temp_id UUID, -- ID temporal del archivo si está en proceso de subida
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    expires_at TIMESTAMPTZ DEFAULT NOW() + INTERVAL '1 hour' -- Expiración automática (1 hora)
);

-- Índice para búsquedas rápidas por chat_id
CREATE INDEX IF NOT EXISTS idx_sesiones_chat_id 
ON sesiones_conversacion(chat_id);

-- Índice para limpieza de sesiones expiradas
CREATE INDEX IF NOT EXISTS idx_sesiones_expires_at 
ON sesiones_conversacion(expires_at);

-- Índice para búsquedas por estado
CREATE INDEX IF NOT EXISTS idx_sesiones_estado 
ON sesiones_conversacion(estado);

-- Índice compuesto para búsquedas por chat_id y estado (sesiones activas)
CREATE INDEX IF NOT EXISTS idx_sesiones_chat_estado 
ON sesiones_conversacion(chat_id, estado);

-- ============================================
-- FUNCIÓN PARA LIMPIAR SESIONES EXPIRADAS
-- ============================================

-- Función para limpiar sesiones expiradas
CREATE OR REPLACE FUNCTION limpiar_sesiones_expiradas()
RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    DELETE FROM sesiones_conversacion 
    WHERE expires_at < NOW();
    
    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql;

-- ============================================
-- COMENTARIOS EN COLUMNAS (Documentación)
-- ============================================

COMMENT ON TABLE sesiones_conversacion IS 'Tabla para manejar sesiones conversacionales de subida/descarga de archivos';
COMMENT ON COLUMN sesiones_conversacion.chat_id IS 'ID del chat de Telegram del usuario';
COMMENT ON COLUMN sesiones_conversacion.estado IS 'Estado actual de la sesión: idle, esperando_empresa, esperando_categoria, esperando_subtipo, esperando_descripcion, esperando_periodo, finalizado';
COMMENT ON COLUMN sesiones_conversacion.intent IS 'Intención de la sesión: subir_archivo o descargar_archivo';
COMMENT ON COLUMN sesiones_conversacion.data IS 'Datos temporales de la sesión en formato JSON (empresa_id, tipo, periodo, etc.)';
COMMENT ON COLUMN sesiones_conversacion.archivo_temp_id IS 'ID temporal del archivo si está en proceso de subida';
COMMENT ON COLUMN sesiones_conversacion.expires_at IS 'Fecha y hora de expiración de la sesión (1 hora desde última actualización)';

