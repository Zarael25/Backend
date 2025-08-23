from usuarios.middleware import get_current_request

class SafeRoleBasedRouter:
    """
    Router que selecciona la base de datos según la URL del request.
    - /apiadmin/ → admin
    - /api/login/ → admin
    - /api/ → publico
    """
    def db_for_read(self, model, **hints):
        request = get_current_request()
        if request:
            if request.path.startswith("/apiadmin/"):
                return "admin"
            elif request.path.startswith("/api/login/"):
                return "admin"
            elif request.path.startswith("/api/"):
                return "publico"
        # operaciones internas (migrations, shell) usan default
        return "default"

    def db_for_write(self, model, **hints):
        request = get_current_request()
        if request:
            if request.path.startswith("/apiadmin/"):
                return "admin"
            elif request.path.startswith("/api/login/"):
                return "admin"
            elif request.path.startswith("/api/"):
                return "publico"
        return "default"
