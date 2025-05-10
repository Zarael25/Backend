from .models import Usuario



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

