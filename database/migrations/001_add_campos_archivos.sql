-- ============================================
-- MIGRACIÓN 001: Agregar campos a tabla archivos
-- Fecha: 2025-01-11
-- Descripción: Agregar campos necesarios para gestión de archivos con clasificación
-- ============================================

-- Agregar campo 'periodo' (YYYY-MM)
ALTER TABLE archivos 
ADD COLUMN IF NOT EXISTS periodo VARCHAR(7);

-- Agregar campo 'categoria' (legal o financiero)
ALTER TABLE archivos 
ADD COLUMN IF NOT EXISTS categoria VARCHAR(50);

-- Agregar campo 'tipo' (categoría principal)
ALTER TABLE archivos 
ADD COLUMN IF NOT EXISTS tipo VARCHAR(50);

-- Agregar campo 'subtipo' (subtipo específico: Estatutos, F29, etc.)
ALTER TABLE archivos 
ADD COLUMN IF NOT EXISTS subtipo VARCHAR(100);

-- Agregar campo 'descripcion_personalizada' (para cuando subtipo = "Otros")
ALTER TABLE archivos 
ADD COLUMN IF NOT EXISTS descripcion_personalizada TEXT;

-- Renombrar 'tipo_archivo' a 'mime_type' para claridad
-- (Si la columna existe, la renombramos)
DO $$ 
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'archivos' AND column_name = 'tipo_archivo'
    ) THEN
        ALTER TABLE archivos RENAME COLUMN tipo_archivo TO mime_type;
    END IF;
END $$;

-- Agregar campo opcional 'usuario_subio_id' (para auditoría futura)
ALTER TABLE archivos 
ADD COLUMN IF NOT EXISTS usuario_subio_id UUID REFERENCES usuarios(id) ON DELETE SET NULL;

-- Agregar campo opcional 'fecha_documento' (si el documento tiene fecha específica)
ALTER TABLE archivos 
ADD COLUMN IF NOT EXISTS fecha_documento DATE;

-- ============================================
-- ÍNDICES PARA BÚSQUEDAS OPTIMIZADAS
-- ============================================

-- Índice para búsquedas por empresa + categoría + tipo + subtipo + periodo
CREATE INDEX IF NOT EXISTS idx_archivos_empresa_categoria_tipo_periodo 
ON archivos(empresa_id, categoria, tipo, subtipo, periodo) 
WHERE activo = true;

-- Índice para búsquedas por chat_id (ya existe, pero verificamos)
CREATE INDEX IF NOT EXISTS idx_archivos_chat_id 
ON archivos(chat_id) 
WHERE activo = true;

-- Índice para búsquedas por periodo
CREATE INDEX IF NOT EXISTS idx_archivos_periodo 
ON archivos(periodo) 
WHERE activo = true AND periodo IS NOT NULL;

-- Índice para búsquedas por categoria y subtipo
CREATE INDEX IF NOT EXISTS idx_archivos_categoria_subtipo 
ON archivos(categoria, subtipo) 
WHERE activo = true;

-- ============================================
-- COMENTARIOS EN COLUMNAS (Documentación)
-- ============================================

COMMENT ON COLUMN archivos.periodo IS 'Periodo del archivo en formato YYYY-MM (ej: 2025-01)';
COMMENT ON COLUMN archivos.categoria IS 'Categoría principal: legal o financiero';
COMMENT ON COLUMN archivos.tipo IS 'Tipo de archivo (categoría principal)';
COMMENT ON COLUMN archivos.subtipo IS 'Subtipo específico: Estatutos empresa, F29, F22, etc.';
COMMENT ON COLUMN archivos.descripcion_personalizada IS 'Descripción personalizada cuando subtipo es "Otros"';
COMMENT ON COLUMN archivos.mime_type IS 'Tipo MIME del archivo (application/pdf, image/jpeg, etc.)';
COMMENT ON COLUMN archivos.usuario_subio_id IS 'ID del usuario que subió el archivo (para auditoría)';
COMMENT ON COLUMN archivos.fecha_documento IS 'Fecha específica del documento (si difiere del periodo)';


