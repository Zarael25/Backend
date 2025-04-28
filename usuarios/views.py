from rest_framework import viewsets, status
from rest_framework.response import Response
from .models import Usuario, Admin, UsuarioTicket
from .serializers import UsuarioSerializer, AdminSerializer, UsuarioTicketSerializer
from . import services

class UsuarioViewSet(viewsets.ModelViewSet):
    queryset = Usuario.objects.all()
    serializer_class = UsuarioSerializer

class AdminViewSet(viewsets.ModelViewSet):
    queryset = Admin.objects.all()
    serializer_class = AdminSerializer

class UsuarioTicketViewSet(viewsets.ModelViewSet):
    queryset = UsuarioTicket.objects.all()
    serializer_class = UsuarioTicketSerializer


# ViewSet para el registro personalizado de usuarios
class RegistroUsuarioViewSet(viewsets.ViewSet):
    """
    ViewSet para registrar un nuevo usuario.
    """
    def create(self, request):
        try:
            # Llamamos al servicio para registrar el usuario
            usuario = services.registrar_usuario(request.data)  # No se desempaqueta
            
            # Usamos el serializador para devolver los datos del nuevo usuario
            serializer = UsuarioSerializer(usuario)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        
        except Exception as e:
            # En caso de error, se devuelve una respuesta con el mensaje del error
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        