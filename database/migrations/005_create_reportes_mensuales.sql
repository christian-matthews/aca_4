-- ============================================
-- 📊 TABLA: reportes_mensuales
-- Reportes CFO fabricados mes a mes
-- ============================================

CREATE TABLE IF NOT EXISTS reportes_mensuales (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    empresa_id UUID REFERENCES empresas(id) ON DELETE CASCADE NOT NULL,
    anio INTEGER NOT NULL,
    mes INTEGER NOT NULL CHECK (mes >= 1 AND mes <= 12),
    tipo_reporte VARCHAR(50) DEFAULT 'cfo',
    titulo VARCHAR(255) NOT NULL,
    descripcion TEXT,
    comentarios TEXT,
    estado VARCHAR(20) DEFAULT 'borrador' CHECK (estado IN ('borrador', 'finalizado', 'publicado')),
    contenido JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    created_by UUID REFERENCES usuarios(id) ON DELETE SET NULL,
    UNIQUE(empresa_id, anio, mes, tipo_reporte)
);

-- Índices para búsquedas rápidas
CREATE INDEX IF NOT EXISTS idx_reportes_mensuales_empresa ON reportes_mensuales(empresa_id);
CREATE INDEX IF NOT EXISTS idx_reportes_mensuales_periodo ON reportes_mensuales(anio, mes);
CREATE INDEX IF NOT EXISTS idx_reportes_mensuales_estado ON reportes_mensuales(estado);
CREATE INDEX IF NOT EXISTS idx_reportes_mensuales_empresa_periodo ON reportes_mensuales(empresa_id, anio, mes DESC);

-- Función para actualizar updated_at automáticamente
CREATE OR REPLACE FUNCTION update_reportes_mensuales_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger para actualizar updated_at
DROP TRIGGER IF EXISTS trigger_update_reportes_mensuales_updated_at ON reportes_mensuales;
CREATE TRIGGER trigger_update_reportes_mensuales_updated_at
    BEFORE UPDATE ON reportes_mensuales
    FOR EACH ROW
    EXECUTE FUNCTION update_reportes_mensuales_updated_at();









