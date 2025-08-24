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
from django.db.models import Q
from rest_framework.permissions import AllowAny

class UsuarioViewSet(viewsets.ModelViewSet):
    queryset = Usuario.objects.all()
    serializer_class = UsuarioSerializer
    permission_classes = [IsAuthenticated]  # asegúrate que el usuario esté logueado

    def get_queryset(self):
        return Usuario.objects.exclude(tipo_usuario='admin')

    def list(self, request, *args, **kwargs):
        # Verificamos si es admin
        if request.user.tipo_usuario != 'admin':
            return Response({"error": "Acceso denegado. Solo administradores pueden ver la lista de usuarios."},
                            status=status.HTTP_403_FORBIDDEN)
        return super().list(request, *args, **kwargs)
    
    @action(detail=False, methods=['patch'], url_path='editar-perfil')
    def editar_perfil(self, request):
        """
        Permite que el usuario autenticado edite su propio perfil.
        No se pueden modificar campos admin: estado, suscripcion, tipo_usuario, suspendido_contador, suspendido_hasta
        """
        usuario = request.user
        datos = request.data

        campos_permitidos = ['username', 'correo', 'nombre', 'password']
        for campo in campos_permitidos:
            if campo in datos:
                if campo == 'password':
                    usuario.set_password(datos[campo])
                else:
                    setattr(usuario, campo, datos[campo])

        usuario.save()
        serializer = self.get_serializer(usuario)
        return Response(serializer.data, status=status.HTTP_200_OK)



    


class UsuarioAdminViewSet(viewsets.ModelViewSet):
    queryset = Usuario.objects.exclude(tipo_usuario='admin')
    serializer_class = UsuarioSerializer
    permission_classes = [IsAuthenticated]  # Solo usuarios logueados

    # Acción de búsqueda solo disponible en /apiadmin/
    @action(detail=False, methods=['get'], url_path='buscar')
    def buscar(self, request):
        termino = request.query_params.get('search', '').strip()
        queryset = self.get_queryset()

        if termino:
            queryset = queryset.filter(
                Q(nombre__icontains=termino) |
                Q(username__icontains=termino) |
                Q(correo__icontains=termino) | 
                Q(estado__icontains=termino)
            )

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    # Acción de edición solo disponible en /apiadmin/
    @action(detail=True, methods=['patch'], url_path='admin_editar')
    def admin_editar_usuario(self, request, pk=None):
        try:
            usuario = self.get_object()
            data = request.data
            cambios = {}

            # Solo actualiza si se envía ese campo
            if 'estado' in data:
                usuario.estado = data['estado']
                cambios['estado'] = data['estado']
            if 'suscripcion' in data:
                usuario.suscripcion = data['suscripcion']
                cambios['suscripcion'] = data['suscripcion']
            if 'password' in data:
                usuario.set_password(data['password'])
                cambios['password'] = '***'

            usuario.save()
            return Response({"mensaje": "Usuario actualizado correctamente.", "cambios": cambios}, status=status.HTTP_200_OK)

        except Usuario.DoesNotExist:
            return Response({"error": "Usuario no encontrado."}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            import traceback
            traceback.print_exc()
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)













class UsuarioTicketViewSet(viewsets.ModelViewSet):
    queryset = UsuarioTicket.objects.all()
    serializer_class = UsuarioTicketSerializer
    permission_classes = [IsAuthenticated]


# ViewSet para el registro personalizado de usuarios
class RegistroUsuarioViewSet(viewsets.ViewSet):
    permission_classes = [AllowAny]
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
    permission_classes = [AllowAny]
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
    permission_classes = [IsAuthenticated]

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


         # Verificar si aún está en el tiempo permitido de cancelación
        fecha_limite_cancelacion = ticket.fecha_hora_registro + timedelta(minutes=negocio.tiempo_limite_cancelacion)
        tiempo_expirado = timezone.now() > fecha_limite_cancelacion

        if tiempo_expirado:
            # Se permite cancelar, pero con penalización directa
            return self.aplicar_penalizacion_y_cancelar(usuario, ticket, motivo="Has cancelado fuera del tiempo permitido.")


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
    permission_classes = [AllowAny]
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
