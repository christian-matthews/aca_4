-- ============================================
-- MIGRACIÓN 004: Sistema de Roles y Permisos
-- 3 niveles: super_admin, gestor, usuario
-- ============================================

-- Actualizar tabla usuarios_empresas para soportar roles por empresa
-- (Ya existe el campo 'rol', solo necesitamos asegurar valores válidos)

-- Crear constraint para validar roles válidos
DO $$ 
BEGIN
    -- Eliminar constraint si existe
    IF EXISTS (
        SELECT 1 FROM pg_constraint 
        WHERE conname = 'usuarios_empresas_rol_check'
    ) THEN
        ALTER TABLE usuarios_empresas DROP CONSTRAINT usuarios_empresas_rol_check;
    END IF;
    
    -- Crear constraint con los 3 roles válidos
    ALTER TABLE usuarios_empresas 
    ADD CONSTRAINT usuarios_empresas_rol_check 
    CHECK (rol IN ('super_admin', 'gestor', 'usuario'));
END $$;

-- Actualizar tabla usuarios para soportar super_admin
DO $$ 
BEGIN
    -- Eliminar constraint si existe
    IF EXISTS (
        SELECT 1 FROM pg_constraint 
        WHERE conname = 'usuarios_rol_check'
    ) THEN
        ALTER TABLE usuarios DROP CONSTRAINT usuarios_rol_check;
    END IF;
    
    -- Crear constraint con los 3 roles válidos
    ALTER TABLE usuarios 
    ADD CONSTRAINT usuarios_rol_check 
    CHECK (rol IN ('super_admin', 'gestor', 'usuario', 'admin', 'user'));
    -- Mantener 'admin' y 'user' para compatibilidad
END $$;

-- Comentarios
COMMENT ON COLUMN usuarios_empresas.rol IS 'Rol del usuario en esta empresa: super_admin (todos los permisos), gestor (asignar empresas, subir/bajar archivos), usuario (solo bajar archivos)';
COMMENT ON COLUMN usuarios.rol IS 'Rol global del usuario: super_admin, gestor, usuario, admin (legacy), user (legacy)';








