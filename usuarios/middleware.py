import threading

_thread_locals = threading.local()

def get_current_request():
    """Devuelve el request actual o None si aún no existe."""
    return getattr(_thread_locals, "request", None)

class RequestMiddleware:
    """Middleware que guarda el request actual en una variable global por thread."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        _thread_locals.request = request
        response = self.get_response(request)
        return response