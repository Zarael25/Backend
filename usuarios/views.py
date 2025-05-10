from rest_framework import viewsets, status
from rest_framework.response import Response
from .models import Usuario, Admin, UsuarioTicket
from .serializers import UsuarioSerializer, AdminSerializer, UsuarioTicketSerializer
from . import services
from rest_framework.decorators import action

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
        


# ViewSet para el inicio de sesión personalizado de usuarios
class LoginUsuarioViewSet(viewsets.ViewSet):
    """
    ViewSet para iniciar sesión con username y contraseña.
    """
    def create(self, request):
        try:
            username = request.data.get("username")
            password = request.data.get("password")

            if not username or not password:
                return Response({"error": "Username y contraseña son obligatorios."}, status=status.HTTP_400_BAD_REQUEST)

            token_data = services.login_usuario(username, password)
            return Response(token_data, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_401_UNAUTHORIZED)
        

class LogoutUsuarioViewSet(viewsets.ViewSet):
    """
    ViewSet para cerrar sesión (logout) de usuario.
    """
    
    @action(detail=False, methods=['post'], url_path='logout')
    def logout(self, request):
        refresh_token = request.data.get('refresh')
        
        if not refresh_token:
            return Response({'error': 'Se requiere token de refresh'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            # Llamamos al servicio para cerrar sesión
            resultado = services.logout_usuario(refresh_token)
            return Response(resultado, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


