-- =====================================
-- Archivo: roles_permisos.sql
-- Proyecto: Fichas Virtuales
-- Descripción: Creación de roles y permisos en PostgreSQL
-- Ejecutable en cualquier entorno
-- =====================================

-- ============================
-- 1. Crear roles con login y contraseña segura
-- ============================
CREATE ROLE acceso_publico LOGIN PASSWORD 'PblC_Acc3s0!2025';
CREATE ROLE acceso_admin LOGIN PASSWORD 'Adm1n_Syst3m#2025!';
CREATE ROLE solo_lectura LOGIN PASSWORD 'Read0nly_Aud1t$25';

-- ============================
-- 2. Revocar permisos por defecto
-- ============================
REVOKE ALL ON ALL TABLES IN SCHEMA public FROM PUBLIC;

-- ============================
-- 3. Asignar permisos a cada rol
-- ============================

-- ------- acceso_publico: API pública -------
GRANT CONNECT ON DATABASE fichadb TO acceso_publico;
GRANT USAGE ON SCHEMA public TO acceso_publico;

-- Solo puede ver negocios, filas y tickets
GRANT SELECT ON negocios_negocio, negocios_filaatencion, negocios_ticket TO acceso_publico;

-- No se puede insertar usuarios directamente por SQL (se hace vía Django)
-- GRANT INSERT ON usuarios_usuario TO acceso_publico; -- opcional si quieres probar inserts desde SQL

-- ------- acceso_admin: Panel administrativo -------
GRANT CONNECT ON DATABASE fichadb TO acceso_admin;
GRANT USAGE ON SCHEMA public TO acceso_admin;

-- Acceso total a todas las tablas y secuencias
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO acceso_admin;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO acceso_admin;

-- ------- solo_lectura: Auditoría / Reportes -------
GRANT CONNECT ON DATABASE fichadb TO solo_lectura;
GRANT USAGE ON SCHEMA public TO solo_lectura;

-- Solo lectura en todas las tablas
GRANT SELECT ON ALL TABLES IN SCHEMA public TO solo_lectura;

-- ============================
-- 4. Notas
-- ============================
-- Este archivo puede ejecutarse así:
-- psql -U postgres -d fichadb -f roles_permisos.sql
-- Asegúrate de reemplazar las contraseñas por algo seguro en producción.
