from .models import Negocio

def obtener_negocios_por_usuario(usuario):
    """
    Devuelve todos los negocios pertenecientes al usuario autenticado.
    
    Parámetros:
        usuario (Usuario): instancia del usuario autenticado.
    
    Retorna:
        QuerySet[Negocio]: lista de negocios asociados a ese usuario.
    """
    return Negocio.objects.filter(usuario=usuario)