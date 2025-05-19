from rest_framework import viewsets, status
from rest_framework.response import Response
from .models import Usuario, UsuarioTicket
from .serializers import UsuarioSerializer, UsuarioTicketSerializer
from . import services
from rest_framework.decorators import action

class UsuarioViewSet(viewsets.ModelViewSet):
    queryset = Usuario.objects.all()
    serializer_class = UsuarioSerializer
""""
class AdminViewSet(viewsets.ModelViewSet):
    queryset = Admin.objects.all()
    serializer_class = AdminSerializer
"""
class UsuarioTicketViewSet(viewsets.ModelViewSet):
    queryset = UsuarioTicket.objects.all()
    serializer_class = UsuarioTicketSerializer


# ViewSet para el registro personalizado de usuarios
class RegistroUsuarioViewSet(viewsets.ViewSet):
    def create(self, request):
        try:
            serializer = UsuarioSerializer(data=request.data)
            if serializer.is_valid():
                usuario = serializer.save()
                return Response(UsuarioSerializer(usuario).data, status=status.HTTP_201_CREATED)
            else:
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"error": f"Error inesperado: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


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



from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .services import obtener_datos_usuario
from .serializers import UsuarioSerializer

class PerfilUsuarioViewSet(viewsets.ViewSet):
    """
    ViewSet para obtener los datos del usuario autenticado.
    """
    permission_classes = [IsAuthenticated]

    def list(self, request):
        usuario = obtener_datos_usuario(request.user)
        serializer = UsuarioSerializer(usuario)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
