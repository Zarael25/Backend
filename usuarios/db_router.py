from usuarios.middleware import get_current_request

class RoleBasedRouter:
    def db_for_read(self, model, **hints):
        request = get_current_request()
        if request:
            if request.path.startswith("/apiadmin/"):
                return "admin"
            elif request.path.startswith("/api/"):
                return "publico"
        return "default"

    def db_for_write(self, model, **hints):
        request = get_current_request()
        if request and request.path.startswith("/apiadmin/"):
            return "admin"
        return "default"