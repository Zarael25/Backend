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
REVOKE ALL ON ALL SEQUENCES IN SCHEMA public FROM PUBLIC;

-- ------- acceso_publico: API pública -------
-- Revocar permisos por defecto del rol
REVOKE ALL ON ALL TABLES IN SCHEMA public FROM acceso_publico;
REVOKE ALL ON ALL SEQUENCES IN SCHEMA public FROM acceso_publico;

-- Conexión y uso de esquema
GRANT CONNECT ON DATABASE fichadbrender TO acceso_publico;
GRANT USAGE ON SCHEMA public TO acceso_publico;

-- Lectura de todas las tablas
GRANT SELECT ON ALL TABLES IN SCHEMA public TO acceso_publico;

-- Permisos para secuencias (para INSERT en tablas con AutoField/Serial)
GRANT USAGE, SELECT, UPDATE ON ALL SEQUENCES IN SCHEMA public TO acceso_publico;

-- Escritura limitada: insertar/actualizar ciertos registros
GRANT INSERT, UPDATE ON TABLE usuarios_usuario TO acceso_publico;
GRANT INSERT, UPDATE ON TABLE negocios_negocio TO acceso_publico;
GRANT INSERT, UPDATE ON TABLE negocios_filaatencion TO acceso_publico;
GRANT INSERT ON TABLE negocios_ticket TO acceso_publico;
GRANT INSERT, UPDATE ON TABLE negocios_cancelacionusuarionegocio TO acceso_publico;
GRANT INSERT, UPDATE ON TABLE negocios_reservadiariausuario TO acceso_publico;


--  Permisos completos sobre usuarios_usuario para que login funcione
GRANT SELECT, INSERT, UPDATE, DELETE ON TABLE usuarios_usuario TO acceso_publico;
GRANT USAGE, SELECT, UPDATE ON SEQUENCE usuarios_usuario_usuario_id_seq TO acceso_publico;


-- Revocar permisos no necesarios
REVOKE DELETE ON ALL TABLES IN SCHEMA public FROM acceso_publico;

-- Asegurar que tablas nuevas también permitan lectura/escritura correcta
ALTER DEFAULT PRIVILEGES IN SCHEMA public
GRANT SELECT, INSERT, UPDATE ON TABLES TO acceso_publico;

ALTER DEFAULT PRIVILEGES IN SCHEMA public
GRANT USAGE, SELECT, UPDATE ON SEQUENCES TO acceso_publico;



-- ------- acceso_admin: Panel administrativo -------
-- Conexión y uso de esquema
GRANT CONNECT ON DATABASE fichadbrender TO acceso_admin;
GRANT USAGE ON SCHEMA public TO acceso_admin;

-- Todos los permisos sobre todas las tablas
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO acceso_admin;
GRANT USAGE, SELECT, UPDATE ON ALL SEQUENCES IN SCHEMA public TO acceso_admin;

-- Asegurar que tablas nuevas también permitan acceso completo
ALTER DEFAULT PRIVILEGES IN SCHEMA public
GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO acceso_admin;
ALTER DEFAULT PRIVILEGES IN SCHEMA public
GRANT USAGE, SELECT, UPDATE ON SEQUENCES TO acceso_admin;





-- ------- solo_lectura: Auditoría / Reportes -------
-- Conexión y uso de esquema
GRANT CONNECT ON DATABASE fichadbrender TO solo_lectura;
GRANT USAGE ON SCHEMA public TO solo_lectura;

-- Solo lectura en todas las tablas
GRANT SELECT ON ALL TABLES IN SCHEMA public TO solo_lectura;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO solo_lectura;

-- Revocar permisos innecesarios
REVOKE INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public FROM solo_lectura;

-- Asegurar que tablas nuevas también sean solo lectura
ALTER DEFAULT PRIVILEGES IN SCHEMA public
GRANT SELECT ON TABLES TO solo_lectura;
ALTER DEFAULT PRIVILEGES IN SCHEMA public
GRANT USAGE, SELECT ON SEQUENCES TO solo_lectura;

