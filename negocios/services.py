from .models import Negocio

def obtener_negocios_por_usuario(usuario):
    """
    Devuelve todos los negocios pertenecientes al usuario autenticado.
    """
    return Negocio.objects.filter(usuario=usuario)
