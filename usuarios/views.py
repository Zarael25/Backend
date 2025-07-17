from rest_framework import viewsets, status
from rest_framework.response import Response
from .models import Usuario, UsuarioTicket
from .serializers import UsuarioSerializer, UsuarioTicketSerializer, UsuarioTicketDetalleSerializer
from . import services
from rest_framework.decorators import action
from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .services import obtener_datos_usuario
from django.utils import timezone
from datetime import timedelta
from rest_framework.exceptions import AuthenticationFailed
from negocios.models import CancelacionUsuarioNegocio

class UsuarioViewSet(viewsets.ModelViewSet):
    queryset = Usuario.objects.all()
    serializer_class = UsuarioSerializer

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

            # Ahora solo llamamos al servicio (que maneja errores correctamente)
            token_data = services.login_usuario(request, username, password)
            return Response(token_data, status=status.HTTP_200_OK)

        except AuthenticationFailed as e:
            return Response({"error": str(e)}, status=status.HTTP_401_UNAUTHORIZED)

        except Exception as e:
            return Response({"error": "Error interno del servidor"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        

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





class PerfilUsuarioViewSet(viewsets.ViewSet):
    """
    ViewSet para obtener los datos del usuario autenticado.
    """
    permission_classes = [IsAuthenticated]

    def list(self, request):
        usuario = obtener_datos_usuario(request.user)
        serializer = UsuarioSerializer(usuario)
        return Response(serializer.data, status=status.HTTP_200_OK)
    

class UsuarioTicketViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = UsuarioTicket.objects.all()
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=['get'], url_path='mis-tickets')
    def mis_tickets(self, request):
        usuario = request.user
        tickets = UsuarioTicket.objects.filter(usuario=usuario)
        serializer = UsuarioTicketDetalleSerializer(tickets, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'], url_path='detalle')
    def detalle_ticket(self, request, pk=None):
        usuario = request.user
        try:
            usuario_ticket = UsuarioTicket.objects.get(pk=pk, usuario=usuario)
        except UsuarioTicket.DoesNotExist:
            return Response({'error': 'Ticket no encontrado o no pertenece al usuario.'}, status=status.HTTP_404_NOT_FOUND)

        serializer = UsuarioTicketDetalleSerializer(usuario_ticket)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'], url_path=r'detalle-por-ticket/(?P<ticket_id>\d+)')
    def detalle_por_ticket(self, request, ticket_id=None):
        usuario = request.user
        try:
            usuario_ticket = UsuarioTicket.objects.get(ticket__ticket_id=ticket_id, usuario=usuario)
        except UsuarioTicket.DoesNotExist:
            return Response({'error': 'Ticket no encontrado o no pertenece al usuario.'}, status=status.HTTP_404_NOT_FOUND)

        serializer = UsuarioTicketDetalleSerializer(usuario_ticket)
        return Response(serializer.data)
    

    @action(detail=True, methods=['post'], url_path='cancelar')
    def cancelar_ticket(self, request, pk=None):
        usuario = request.user

        try:
            usuario_ticket = UsuarioTicket.objects.get(ticket__ticket_id=pk, usuario=usuario)
        except UsuarioTicket.DoesNotExist:
            return Response({'error': 'Ticket no encontrado o no pertenece al usuario.'}, status=status.HTTP_404_NOT_FOUND)

        ticket = usuario_ticket.ticket

        if ticket.estado != 'activo':
            return Response({'error': 'Solo se pueden cancelar tickets con estado activo.'}, status=status.HTTP_400_BAD_REQUEST)

        negocio = ticket.fila_atencion.negocio

        # Si el negocio no permite cancelar, aplicar penalización directa
        if not negocio.permite_cancelar:
            return self.aplicar_penalizacion_y_cancelar(usuario, ticket, motivo="Este negocio no permite cancelaciones.")

        # Obtener o crear registro de cancelaciones para este usuario y negocio
        cancelacion_obj, creado = CancelacionUsuarioNegocio.objects.get_or_create(
            usuario=usuario,
            negocio=negocio,
            defaults={'cantidad_cancelaciones': 0}
        )

        # Revisar cantidad de cancelaciones previas
        if cancelacion_obj.cantidad_cancelaciones >= 3:
            # Penalización
            return self.aplicar_penalizacion_y_cancelar(
                usuario, ticket,
                motivo="Has cancelado más de 3 veces en este negocio. Se aplica penalización."
            )
        elif cancelacion_obj.cantidad_cancelaciones == 2:
            # 3era cancelación: solo advertencia
            ticket.estado = 'cancelado'
            ticket.save(update_fields=['estado'])

            # Incrementar contador
            cancelacion_obj.cantidad_cancelaciones += 1
            cancelacion_obj.save(update_fields=['cantidad_cancelaciones'])

            return Response({
                'mensaje': 'Ticket cancelado correctamente.',
                'advertencia': 'Ya has cancelado 3 veces en este negocio. La próxima se aplicará una penalización.'
            }, status=status.HTTP_200_OK)
        else:
            # Primeras dos cancelaciones sin castigo
            ticket.estado = 'cancelado'
            ticket.save(update_fields=['estado'])

            # Incrementar contador
            cancelacion_obj.cantidad_cancelaciones += 1
            cancelacion_obj.save(update_fields=['cantidad_cancelaciones'])

            return Response({
                'mensaje': f'Ticket cancelado correctamente. Cancelaciones previas en este negocio: {cancelacion_obj.cantidad_cancelaciones}'
            }, status=status.HTTP_200_OK)

    def aplicar_penalizacion_y_cancelar(self, usuario, ticket, motivo=""):
        usuario.suspendido_contador += 1

        if usuario.suspendido_contador >= 5:
            usuario.estado = 'suspendido'
            usuario.suspendido_hasta = None
            castigo = "Suspensión permanente"
        else:
            minutos_castigo = usuario.suspendido_contador
            usuario.estado = 'suspendido'
            usuario.suspendido_hasta = timezone.now() + timedelta(minutes=minutos_castigo)
            castigo = f"Suspensión por {minutos_castigo} minutos"

        usuario.save(update_fields=['estado', 'suspendido_contador', 'suspendido_hasta'])

        ticket.estado = 'cancelado'
        ticket.save(update_fields=['estado'])

        return Response({
            'mensaje': f'Ticket cancelado con penalización. Motivo: {motivo}',
            'castigo': castigo
        }, status=status.HTTP_200_OK)



class LoginAdminViewSet(viewsets.ViewSet):
    """
    ViewSet para que los administradores inicien sesión con username y contraseña.
    """
    def create(self, request):
        try:
            username = request.data.get("username")
            password = request.data.get("password")

            if not username or not password:
                return Response({"error": "Username y contraseña son obligatorios."}, status=status.HTTP_400_BAD_REQUEST)

            token_data = services.login_admin(request, username, password)
            return Response(token_data, status=status.HTTP_200_OK)

        except AuthenticationFailed as e:
            return Response({"error": str(e)}, status=status.HTTP_401_UNAUTHORIZED)

        except Exception as e:
            return Response({"error": "Error interno del servidor"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
