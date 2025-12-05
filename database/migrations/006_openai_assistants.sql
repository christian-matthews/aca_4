-- ============================================
-- MIGRACIÓN 006: OpenAI Assistants para PDFs
-- Soporte para Asesor IA con File Search
-- ============================================

-- Agregar columna para Assistant ID en empresas
-- Cada empresa tiene su propio Assistant para aislamiento de datos
ALTER TABLE empresas 
ADD COLUMN IF NOT EXISTS openai_assistant_id TEXT DEFAULT NULL;

-- Agregar columna para File ID en archivos
-- Los PDFs subidos a OpenAI tienen un file_id único
ALTER TABLE archivos 
ADD COLUMN IF NOT EXISTS openai_file_id TEXT DEFAULT NULL;

-- Índices para búsqueda eficiente
CREATE INDEX IF NOT EXISTS idx_empresas_openai_assistant 
ON empresas(openai_assistant_id) WHERE openai_assistant_id IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_archivos_openai_file 
ON archivos(openai_file_id) WHERE openai_file_id IS NOT NULL;

-- Comentarios
COMMENT ON COLUMN empresas.openai_assistant_id IS 'ID del Assistant de OpenAI para esta empresa (aislamiento de datos)';
COMMENT ON COLUMN archivos.openai_file_id IS 'ID del archivo en OpenAI Files API (para PDFs procesados)';

