from .models import Usuario
from rest_framework.exceptions import AuthenticationFailed
from rest_framework_simplejwt.tokens import RefreshToken


def registrar_usuario(data):
    """
    Servicio para registrar un nuevo usuario.
    El estado y la suscripción se asignan por defecto.
    """
    usuario = Usuario.objects.create(
        username=data['username'],
        password=data['password'],  
        nombre=data['nombre'],
        correo=data['correo']
    )
    return usuario  



def login_usuario(username, password):
    try:
        usuario = Usuario.objects.get(username=username)
    except Usuario.DoesNotExist:
        raise AuthenticationFailed("Credenciales inválidas")

    # Comparar contraseñas en texto plano
    if password != usuario.password:
        raise AuthenticationFailed("Credenciales inválidas")

    if usuario.estado != 'activo':
        raise AuthenticationFailed("El usuario está suspendido")

    # Crear tokens JWT
    refresh = RefreshToken.for_user(usuario)

    return {
        'refresh': str(refresh),
        'access': str(refresh.access_token),
        'usuario_id': usuario.usuario_id,
        'nombre': usuario.nombre,
        'suscripcion': usuario.suscripcion,
    }

