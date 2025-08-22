-- =====================================
-- Archivo: roles_permisos.sql
-- Proyecto: Fichas Virtuales
-- Descripción: Creación de roles y permisos en PostgreSQL
-- Ejecutable en cualquier entorno
-- =====================================

-- ============================
-- 1. Crear roles con login y contraseña segura
-- ============================
CREATE ROLE acceso_publico LOGIN PASSWORD 'Publico123!';
CREATE ROLE acceso_admin LOGIN PASSWORD 'Admin123!';
CREATE ROLE solo_lectura LOGIN PASSWORD 'Lectura123!';


-- ============================
-- 2. Revocar permisos por defecto
-- ============================
REVOKE ALL ON ALL TABLES IN SCHEMA public FROM PUBLIC;


-- ------- acceso_publico: API pública -------
GRANT CONNECT ON DATABASE fichadbrender TO acceso_publico;
GRANT USAGE ON SCHEMA public TO acceso_publico;

-- Solo puede ver negocios, filas y tickets
GRANT SELECT ON negocios_negocio, negocios_filaatencion TO acceso_publico;




-- ------- acceso_admin: Panel administrativo -------
GRANT CONNECT ON DATABASE fichadbrender TO acceso_admin;
GRANT USAGE ON SCHEMA public TO acceso_admin;

-- Acceso total a todas las tablas y secuencias
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO acceso_admin;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO acceso_admin;



-- ------- solo_lectura: Auditoría / Reportes -------
GRANT CONNECT ON DATABASE fichadbrender TO solo_lectura;
GRANT USAGE ON SCHEMA public TO solo_lectura;

-- Solo lectura en todas las tablas
GRANT SELECT ON ALL TABLES IN SCHEMA public TO solo_lectura;


