-- ============================================
-- MIGRACIÓN 003: Tabla usuarios_empresas
-- Soporte para multiempresa (múltiples empresas por usuario)
-- ============================================

-- Tabla intermedia para relación muchos a muchos entre usuarios y empresas
CREATE TABLE IF NOT EXISTS usuarios_empresas (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    usuario_id UUID NOT NULL REFERENCES usuarios(id) ON DELETE CASCADE,
    empresa_id UUID NOT NULL REFERENCES empresas(id) ON DELETE CASCADE,
    rol VARCHAR(50) DEFAULT 'user',
    activo BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(usuario_id, empresa_id)
);

-- Índices para performance
CREATE INDEX IF NOT EXISTS idx_usuarios_empresas_usuario ON usuarios_empresas(usuario_id);
CREATE INDEX IF NOT EXISTS idx_usuarios_empresas_empresa ON usuarios_empresas(empresa_id);
CREATE INDEX IF NOT EXISTS idx_usuarios_empresas_activo ON usuarios_empresas(activo);

-- Comentarios
COMMENT ON TABLE usuarios_empresas IS 'Relación muchos a muchos entre usuarios y empresas (multiempresa)';
COMMENT ON COLUMN usuarios_empresas.usuario_id IS 'ID del usuario';
COMMENT ON COLUMN usuarios_empresas.empresa_id IS 'ID de la empresa';
COMMENT ON COLUMN usuarios_empresas.rol IS 'Rol del usuario en esta empresa específica';
COMMENT ON COLUMN usuarios_empresas.activo IS 'Si la relación está activa';

-- Función para migrar datos existentes
-- Esta función migra el empresa_id actual de usuarios a la nueva tabla
CREATE OR REPLACE FUNCTION migrar_empresas_existentes()
RETURNS void AS $$
BEGIN
    -- Insertar relaciones basadas en empresa_id existente en usuarios
    INSERT INTO usuarios_empresas (usuario_id, empresa_id, rol, activo)
    SELECT 
        id as usuario_id,
        empresa_id,
        rol,
        activo
    FROM usuarios
    WHERE empresa_id IS NOT NULL
    ON CONFLICT (usuario_id, empresa_id) DO NOTHING;
    
    RAISE NOTICE 'Migración de empresas existentes completada';
END;
$$ LANGUAGE plpgsql;

-- Ejecutar migración automáticamente
SELECT migrar_empresas_existentes();









