from .models import Usuario
from rest_framework.exceptions import AuthenticationFailed
from rest_framework_simplejwt.tokens import RefreshToken
from usuarios.models import LogUsuario


# ---------------- Registrar nuevo usuario ----------------
def registrar_usuario(data):
    """
    Crea un nuevo usuario en la base de datos.
    - Encripta la contraseña antes de guardarla.
    """
    usuario = Usuario(
        username=data['username'],
        nombre=data['nombre'],
        correo=data['correo']
    )
    usuario.set_password(data['password'])  # Encripta la contraseña
    usuario.save()
    return usuario


# ---------------- Login de usuario normal ----------------
def login_usuario(request, username, password):
    """
    Valida credenciales de un usuario normal y retorna sus tokens JWT.
    - Verifica que el usuario exista y la contraseña sea válida.
    - Rechaza usuarios suspendidos.
    - Registra el log de inicio de sesión.
    """
    try:
        usuario = Usuario.objects.get(username=username)
    except Usuario.DoesNotExist:
        raise AuthenticationFailed("Credenciales inválidas")

    if not usuario.check_password(password):
        raise AuthenticationFailed("Credenciales inválidas")

    if usuario.esta_suspendido:
        raise AuthenticationFailed("El usuario está suspendido, comunicarse con admin@filas.com")

    # Simula que el request tiene al usuario autenticado (para registrar el log)
    request.user = usuario
    registrar_log_usuario(request, "inicio de sesión")

    refresh = RefreshToken.for_user(usuario)

    return {
        'refresh': str(refresh),
        'access': str(refresh.access_token),
        'usuario_id': usuario.usuario_id,
        'nombre': usuario.nombre,
        'suscripcion': usuario.suscripcion,
    }


# ---------------- Logout de usuario ----------------
def logout_usuario(refresh_token_str):
    """
    Simula el cierre de sesión.
    - El backend no almacena tokens: el cliente debe eliminarlos.
    - Aquí solo se valida el token de refresh para asegurar que sea correcto.
    """
    try:
        token = RefreshToken(refresh_token_str)
        return {"mensaje": "Logout exitoso. El cliente debe eliminar el token."}
    except Exception:
        raise AuthenticationFailed("Token inválido o expirado.")


# ---------------- Obtener datos del usuario ----------------
def obtener_datos_usuario(usuario):
    """
    Devuelve los datos del usuario autenticado.
    Se usa en el endpoint de perfil.
    """
    return usuario


# ---------------- Registrar logs de acciones ----------------
def registrar_log_usuario(request, tipo_accion):
    """
    Registra en la tabla LogUsuario:
    - tipo de acción (ej: "inicio de sesión")
    - ruta accedida
    - origen de conexión (web o móvil, según User-Agent)
    """
    user_agent = request.META.get("HTTP_USER_AGENT", "").lower()
    origen = "móvil" if "android" in user_agent or "mobile" in user_agent else "web"

    LogUsuario.objects.create(
        usuario=request.user if request.user.is_authenticated else None,
        tipo_accion=tipo_accion,
        ruta_acceso=request.path,
        origen_conexion=origen
    )


# ---------------- Login de administrador ----------------
def login_admin(request, username, password):
    """
    Valida credenciales de un administrador y retorna tokens JWT.
    - Verifica credenciales
    - Rechaza usuarios suspendidos
    - Rechaza si el usuario no es admin
    - Registra log de inicio de sesión como administrador
    """
    try:
        usuario = Usuario.objects.get(username=username)
    except Usuario.DoesNotExist:
        raise AuthenticationFailed("Credenciales inválidas")

    if not usuario.check_password(password):
        raise AuthenticationFailed("Credenciales inválidas")

    if usuario.esta_suspendido:
        raise AuthenticationFailed("El usuario está suspendido, comunicarse con admin@filas.com")

    if usuario.tipo_usuario != 'admin':
        raise AuthenticationFailed("Acceso denegado: solo administradores pueden iniciar sesión aquí.")

    request.user = usuario
    registrar_log_usuario(request, "inicio de sesión como administrador")

    refresh = RefreshToken.for_user(usuario)

    return {
        'refresh': str(refresh),
        'access': str(refresh.access_token),
        'usuario_id': usuario.usuario_id,
        'nombre': usuario.nombre,
        'suscripcion': usuario.suscripcion,
        'tipo_usuario': usuario.tipo_usuario,
    }