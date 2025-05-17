from .models import Usuario
from rest_framework.exceptions import AuthenticationFailed
from rest_framework_simplejwt.tokens import RefreshToken


def registrar_usuario(data):
    usuario = Usuario(
        username=data['username'],
        nombre=data['nombre'],
        correo=data['correo']
    )
    usuario.set_password(data['password'])  # Encripta la contraseña
    usuario.save()
    return usuario



def login_usuario(username, password):
    try:
        usuario = Usuario.objects.get(username=username)
    except Usuario.DoesNotExist:
        raise AuthenticationFailed("Credenciales inválidas")

    if not usuario.check_password(password):
        raise AuthenticationFailed("Credenciales inválidas")

    if usuario.estado != 'activo':
        raise AuthenticationFailed("El usuario está suspendido")

    refresh = RefreshToken.for_user(usuario)

    return {
        'refresh': str(refresh),
        'access': str(refresh.access_token),
        'usuario_id': usuario.usuario_id,
        'nombre': usuario.nombre,
        'suscripcion': usuario.suscripcion,
    }



def logout_usuario(refresh_token_str):
    """
    El backend no almacena tokens. El logout consiste en que el cliente elimine el token.
    """
    # Podés agregar lógica de validación si querés asegurarte que el token es válido
    try:
        token = RefreshToken(refresh_token_str)
        return {"mensaje": "Logout exitoso. El cliente debe eliminar el token."}
    except Exception:
        raise AuthenticationFailed("Token inválido o expirado.")