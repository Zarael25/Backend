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
    # ---------------- Configuración base ----------------
    queryset = Usuario.objects.all()
    serializer_class = UsuarioSerializer
    permission_classes = [IsAuthenticated]  # Solo usuarios autenticados pueden acceder

    # ---------------- Queryset personalizado ----------------
    def get_queryset(self):
        """
        Devuelve todos los usuarios, excepto los administradores.
        Esto evita que los admins aparezcan en listados generales.
        """
        return Usuario.objects.exclude(tipo_usuario='admin')

    # ---------------- Listar usuarios ----------------
    def list(self, request, *args, **kwargs):
        """
        Sobrescribe la lista de usuarios:
        - Solo un usuario con tipo_usuario='admin' puede acceder.
        - Los demás reciben un error 403.
        """
        if request.user.tipo_usuario != 'admin':
            return Response(
                {"error": "Acceso denegado. Solo administradores pueden ver la lista de usuarios."},
                status=status.HTTP_403_FORBIDDEN
            )
        return super().list(request, *args, **kwargs)
    
    # ---------------- Editar perfil ----------------
    @action(detail=False, methods=['patch'], url_path='editar-perfil')
    def editar_perfil(self, request):
        """
        Permite que el usuario autenticado edite su propio perfil.
           Restricción: no se pueden modificar campos de administración
           (estado, suscripción, tipo_usuario, suspendido_contador, suspendido_hasta).
        """
        usuario = request.user
        datos = request.data

        # Campos que sí se permiten editar
        campos_permitidos = ['username', 'correo', 'nombre', 'password']
        for campo in campos_permitidos:
            if campo in datos:
                if campo == 'password':
                    usuario.set_password(datos[campo])  # Encripta la nueva contraseña
                else:
                    setattr(usuario, campo, datos[campo])  # Actualiza el campo permitido

        usuario.save()
        serializer = self.get_serializer(usuario)
        return Response(serializer.data, status=status.HTTP_200_OK)



    


class UsuarioAdminViewSet(viewsets.ModelViewSet):
    # ---------------- Configuración base ----------------
    queryset = Usuario.objects.exclude(tipo_usuario='admin')  # No se listan administradores
    serializer_class = UsuarioSerializer
    permission_classes = [IsAuthenticated]  # Solo usuarios autenticados

    # ---------------- Búsqueda de usuarios ----------------
    @action(detail=False, methods=['get'], url_path='buscar')
    def buscar(self, request):
        """
        Permite a un admin buscar usuarios según:
        - nombre
        - username
        - correo
        - estado
        Se usa el parámetro GET ?search=termino
        """
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

    # ---------------- Edición de usuarios por admin ----------------
    @action(detail=True, methods=['patch'], url_path='admin_editar')
    def admin_editar_usuario(self, request, pk=None):
        """
        Permite que un admin edite ciertos campos de un usuario:
        - estado
        - suscripción
        - password (se guarda encriptada)
        """
        try:
            usuario = self.get_object()
            data = request.data
            cambios = {}

            # Actualiza solo los campos enviados
            if 'estado' in data:
                usuario.estado = data['estado']
                cambios['estado'] = data['estado']
            if 'suscripcion' in data:
                usuario.suscripcion = data['suscripcion']
                cambios['suscripcion'] = data['suscripcion']
            if 'password' in data:
                usuario.set_password(data['password'])  # Encripta contraseña
                cambios['password'] = '***'  # No mostrar valor real

            usuario.save()
            return Response(
                {"mensaje": "Usuario actualizado correctamente.", "cambios": cambios},
                status=status.HTTP_200_OK
            )

        except Usuario.DoesNotExist:
            return Response({"error": "Usuario no encontrado."}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            import traceback
            traceback.print_exc()  # Útil para depuración en consola
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)






class UsuarioTicketViewSet(viewsets.ModelViewSet):
    # ---------------- Configuración base ----------------
    queryset = UsuarioTicket.objects.all()                 # Todos los registros usuario-ticket
    serializer_class = UsuarioTicketSerializer             # Serializador asociado
    permission_classes = [IsAuthenticated]                 # Solo usuarios autenticados
    
    # Nota: por ahora no tiene métodos extra ni acciones personalizadas.
    # - GET /usuario_tickets/ → lista todos los registros
    # - POST /usuario_tickets/ → crea una relación usuario-ticket
    # - GET /usuario_tickets/{id}/ → obtiene un registro en particular
    # - PATCH/PUT /usuario_tickets/{id}/ → actualiza un registro
    # - DELETE /usuario_tickets/{id}/ → elimina un registro


class RegistroUsuarioViewSet(viewsets.ViewSet):
    # ---------------- Configuración ----------------
    permission_classes = [AllowAny]  # Cualquiera puede registrarse (sin autenticación)

    # ---------------- Registro de usuario ----------------
    def create(self, request):
        """
        Endpoint para registrar un nuevo usuario.
        - Recibe los datos por POST.
        - Valida con UsuarioSerializer.
        - Si es válido, guarda el usuario y devuelve sus datos.
        - Maneja errores de validación y excepciones inesperadas.
        """
        try:
            # Se valida la data recibida con el serializer
            serializer = UsuarioSerializer(data=request.data)

            if serializer.is_valid():
                # Guarda el nuevo usuario
                usuario = serializer.save()
                return Response(UsuarioSerializer(usuario).data, status=status.HTTP_201_CREATED)
            else:
                # Si hay errores de validación, se devuelven
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            # Captura de errores inesperados (ej: DB, lógica interna, etc.)
            return Response({"error": f"Error inesperado: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)






class LoginUsuarioViewSet(viewsets.ViewSet):
    permission_classes = [AllowAny]  # Cualquiera puede intentar iniciar sesión

    """
    ViewSet para iniciar sesión con username y contraseña.
    Retorna un par de tokens JWT si las credenciales son correctas.
    """

    def create(self, request):
        try:
            # ---------------- Obtener credenciales ----------------
            username = request.data.get("username")
            password = request.data.get("password")

            if not username or not password:
                return Response(
                    {"error": "Username y contraseña son obligatorios."},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # ---------------- Lógica de autenticación ----------------
            # Delegamos el login a un servicio separado (services.login_usuario)
            # que valida credenciales y devuelve los tokens JWT.
            token_data = services.login_usuario(request, username, password)

            return Response(token_data, status=status.HTTP_200_OK)

        # ---------------- Manejo de errores ----------------
        except AuthenticationFailed as e:
            # Credenciales incorrectas → error 401
            return Response({"error": str(e)}, status=status.HTTP_401_UNAUTHORIZED)

        except Exception as e:
            # Errores inesperados → error 500
            return Response({"error": "Error interno del servidor"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        




class LogoutUsuarioViewSet(viewsets.ViewSet):
    """
    ViewSet para cerrar sesión (logout) de usuario.
    Invalida el refresh token proporcionado para que no pueda reutilizarse.
    """
    permission_classes = [IsAuthenticated]  # Solo usuarios autenticados pueden hacer logout

    @action(detail=False, methods=['post'], url_path='logout')
    def logout(self, request):
        # ---------------- Validar refresh token ----------------
        refresh_token = request.data.get('refresh')
        if not refresh_token:
            return Response(
                {'error': 'Se requiere token de refresh'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            # ---------------- Cerrar sesión ----------------
            # Se delega la lógica al servicio logout_usuario,
            # que invalida el token de refresco en la blacklist.
            resultado = services.logout_usuario(refresh_token)
            return Response(resultado, status=status.HTTP_200_OK)

        except Exception as e:
            # ---------------- Manejo de errores ----------------
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)






class PerfilUsuarioViewSet(viewsets.ViewSet):
    """
    ViewSet para obtener los datos del usuario autenticado.
    Solo devuelve la información del usuario que hace la petición.
    """
    permission_classes = [IsAuthenticated]  # Requiere estar autenticado con JWT

    def list(self, request):
        """
        Retorna el perfil del usuario autenticado:
        - Se obtiene el usuario desde request.user
        - Se procesan los datos con la función auxiliar obtener_datos_usuario
        - Se serializa y retorna la información en formato JSON
        """
        usuario = obtener_datos_usuario(request.user)
        serializer = UsuarioSerializer(usuario)
        return Response(serializer.data, status=status.HTTP_200_OK)

    

class UsuarioTicketViewSet(viewsets.ReadOnlyModelViewSet):
    # ---------------- Configuración base ----------------
    queryset = UsuarioTicket.objects.all()
    permission_classes = [IsAuthenticated]  # Solo usuarios autenticados

    # ---------------- Listar tickets propios ----------------
    @action(detail=False, methods=['get'], url_path='mis-tickets')
    def mis_tickets(self, request):
        """
        Devuelve todos los tickets del usuario autenticado.
        """
        usuario = request.user
        tickets = UsuarioTicket.objects.filter(usuario=usuario)
        serializer = UsuarioTicketDetalleSerializer(tickets, many=True)
        return Response(serializer.data)

    # ---------------- Detalle de un ticket propio ----------------
    @action(detail=True, methods=['get'], url_path='detalle')
    def detalle_ticket(self, request, pk=None):
        """
        Devuelve el detalle de un ticket en particular,
        validando que pertenezca al usuario autenticado.
        """
        usuario = request.user
        try:
            usuario_ticket = UsuarioTicket.objects.get(pk=pk, usuario=usuario)
        except UsuarioTicket.DoesNotExist:
            return Response(
                {'error': 'Ticket no encontrado o no pertenece al usuario.'},
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = UsuarioTicketDetalleSerializer(usuario_ticket)
        return Response(serializer.data)
    
    # ---------------- Detalle por ID de ticket ----------------
    @action(detail=False, methods=['get'], url_path=r'detalle-por-ticket/(?P<ticket_id>\d+)')
    def detalle_por_ticket(self, request, ticket_id=None):
        """
        Devuelve el detalle de un ticket buscándolo por ticket_id
        en lugar del id de la relación UsuarioTicket.
        """
        usuario = request.user
        try:
            usuario_ticket = UsuarioTicket.objects.get(ticket__ticket_id=ticket_id, usuario=usuario)
        except UsuarioTicket.DoesNotExist:
            return Response(
                {'error': 'Ticket no encontrado o no pertenece al usuario.'},
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = UsuarioTicketDetalleSerializer(usuario_ticket)
        return Response(serializer.data)
    
    # ---------------- Cancelar ticket ----------------
    @action(detail=True, methods=['post'], url_path='cancelar')
    def cancelar_ticket(self, request, pk=None):
        """
        Permite al usuario cancelar su ticket:
        - Si el negocio no permite cancelaciones → penalización directa.
        - Si cancela fuera de tiempo → penalización directa.
        - Primeras 2 cancelaciones → sin penalización.
        - 3ra cancelación → advertencia.
        - 4ta en adelante → penalización.
        """
        usuario = request.user

        try:
            usuario_ticket = UsuarioTicket.objects.get(ticket__ticket_id=pk, usuario=usuario)
        except UsuarioTicket.DoesNotExist:
            return Response(
                {'error': 'Ticket no encontrado o no pertenece al usuario.'},
                status=status.HTTP_404_NOT_FOUND
            )

        ticket = usuario_ticket.ticket

        # Solo se pueden cancelar tickets activos
        if ticket.estado != 'activo':
            return Response(
                {'error': 'Solo se pueden cancelar tickets con estado activo.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        negocio = ticket.fila_atencion.negocio

        # Caso 1: El negocio no permite cancelaciones
        if not negocio.permite_cancelar:
            return self.aplicar_penalizacion_y_cancelar(usuario, ticket, motivo="Este negocio no permite cancelaciones.")

        # Caso 2: Cancelación fuera del tiempo límite
        fecha_limite_cancelacion = ticket.fecha_hora_registro + timedelta(minutes=negocio.tiempo_limite_cancelacion)
        if timezone.now() > fecha_limite_cancelacion:
            return self.aplicar_penalizacion_y_cancelar(usuario, ticket, motivo="Has cancelado fuera del tiempo permitido.")

        # Caso 3: Cancelaciones permitidas con reglas
        cancelacion_obj, _ = CancelacionUsuarioNegocio.objects.get_or_create(
            usuario=usuario,
            negocio=negocio,
            defaults={'cantidad_cancelaciones': 0}
        )

        if cancelacion_obj.cantidad_cancelaciones >= 3:
            # Penalización directa
            return self.aplicar_penalizacion_y_cancelar(
                usuario, ticket,
                motivo="Has cancelado más de 3 veces en este negocio. Se aplica penalización."
            )
        elif cancelacion_obj.cantidad_cancelaciones == 2:
            # 3ra cancelación → advertencia
            ticket.estado = 'cancelado'
            ticket.save(update_fields=['estado'])
            cancelacion_obj.cantidad_cancelaciones += 1
            cancelacion_obj.save(update_fields=['cantidad_cancelaciones'])

            return Response({
                'mensaje': 'Ticket cancelado correctamente.',
                'advertencia': 'Ya has cancelado 3 veces en este negocio. La próxima se aplicará una penalización.'
            }, status=status.HTTP_200_OK)
        else:
            # Primeras dos cancelaciones → sin castigo
            ticket.estado = 'cancelado'
            ticket.save(update_fields=['estado'])
            cancelacion_obj.cantidad_cancelaciones += 1
            cancelacion_obj.save(update_fields=['cantidad_cancelaciones'])

            return Response({
                'mensaje': f'Ticket cancelado correctamente. Cancelaciones previas en este negocio: {cancelacion_obj.cantidad_cancelaciones}'
            }, status=status.HTTP_200_OK)

    # ---------------- Método auxiliar ----------------
    def aplicar_penalizacion_y_cancelar(self, usuario, ticket, motivo=""):
        """
        Aplica una penalización al usuario (suspensión temporal o permanente)
        y marca el ticket como cancelado.
        """
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
    Retorna un par de tokens JWT si las credenciales son correctas.
    """
    permission_classes = [AllowAny]  # Cualquiera puede intentar iniciar sesión (sin autenticación previa)

    def create(self, request):
        try:
            # ---------------- Obtener credenciales ----------------
            username = request.data.get("username")
            password = request.data.get("password")

            if not username or not password:
                return Response(
                    {"error": "Username y contraseña son obligatorios."},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # ---------------- Autenticación de administrador ----------------
            # Se delega al servicio login_admin, que valida que el usuario tenga
            # credenciales correctas y sea admin.
            token_data = services.login_admin(request, username, password)
            return Response(token_data, status=status.HTTP_200_OK)

        # ---------------- Manejo de errores ----------------
        except AuthenticationFailed as e:
            # Credenciales incorrectas → 401
            return Response({"error": str(e)}, status=status.HTTP_401_UNAUTHORIZED)

        except Exception as e:
            # Errores inesperados → 500
            return Response({"error": "Error interno del servidor"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
