from rest_framework import viewsets

from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status
from rest_framework.exceptions import PermissionDenied

from .models import Negocio, FilaAtencion, Ticket
from .serializers import NegocioSerializer, FilaAtencionSerializer, TicketSerializer
from .services import obtener_negocios_por_usuario
from django.db.models import Q

from django.utils import timezone
from datetime import datetime, timedelta

from usuarios.models import UsuarioTicket

class NegocioViewSet(viewsets.ModelViewSet):
    queryset = Negocio.objects.all() 
    serializer_class = NegocioSerializer
    permission_classes = [IsAuthenticated]  # Protege todas las operaciones del ViewSet

    def get_queryset(self):
        # En la ruta base siempre devolvemos todos los negocios
        return Negocio.objects.all()


    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated], url_path='mis_negocios')
    def mis_negocios(self, request):
        # Aquí filtramos solo los negocios del usuario logueado
        negocios = Negocio.objects.filter(usuario=request.user)
        serializer = self.get_serializer(negocios, many=True)
        return Response(serializer.data)


    def perform_create(self, serializer):
        usuario = self.request.user

        # Si el usuario no es admin y tiene suscripción free, se limita a 1 negocio
        if not usuario.is_staff and usuario.suscripcion == "free":
            tiene_negocio = Negocio.objects.filter(usuario=usuario).exists()
            if tiene_negocio:
                raise PermissionDenied("Los usuarios con suscripción free solo pueden registrar un negocio.")

        serializer.save(usuario=usuario)
    
     
    @action(detail=True, methods=['patch'], permission_classes=[IsAuthenticated], url_path='editar-parcial')
    def editar_parcial(self, request, pk=None):
        negocio = self.get_object()
        if negocio.usuario != request.user and not request.user.is_staff:
            return Response({"detail": "No tienes permiso para editar este negocio"}, status=status.HTTP_403_FORBIDDEN)

        campos_permitidos = ['nombre', 'direccion', 'categoria', 'doc_respaldo', 'num_referencia', 'detalle']
        datos = {key: value for key, value in request.data.items() if key in campos_permitidos}

        serializer = self.get_serializer(negocio, data=datos, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)
    
    @action(detail=True, methods=['patch'], permission_classes=[IsAuthenticated], url_path='ocultar')
    def ocultar_negocio(self, request, pk=None):
        negocio = self.get_object()
        if negocio.usuario != request.user and not request.user.is_staff:
            return Response({"detail": "No tienes permiso para ocultar este negocio"}, status=status.HTTP_403_FORBIDDEN)

        negocio.estado = 'oculto'
        negocio.save()
        return Response({"detail": f"Negocio '{negocio.nombre}' ocultado correctamente."}, status=status.HTTP_200_OK)
    

    @action(detail=True, methods=['get'], permission_classes=[IsAuthenticated], url_path='mis_filas')
    def mis_filas(self, request, pk=None):
        negocio = self.get_object()

        # Validar que el usuario sea el dueño del negocio o admin
        if negocio.usuario != request.user and not request.user.is_staff:
            return Response({"detail": "No tienes permiso para ver las filas de este negocio."}, status=status.HTTP_403_FORBIDDEN)

        filas = FilaAtencion.objects.filter(negocio=negocio)
        serializer = FilaAtencionSerializer(filas, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated], url_path='verificados')
    def negocios_verificados(self, request):
        termino = request.query_params.get('search', '').strip()

        negocios_verificados = Negocio.objects.filter(estado='verificado')

        if termino:
            negocios_verificados = negocios_verificados.filter(
                Q(nombre__icontains=termino) |
                Q(categoria__icontains=termino)
            )

        serializer = self.get_serializer(negocios_verificados, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'], permission_classes=[IsAuthenticated], url_path='filas_visibles')
    def filas_visibles(self, request, pk=None):
        negocio = self.get_object()

        filas_visibles = FilaAtencion.objects.filter(negocio=negocio, visible=True)
        serializer = FilaAtencionSerializer(filas_visibles, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    


class FilaAtencionViewSet(viewsets.ModelViewSet):
    queryset = FilaAtencion.objects.all()
    serializer_class = FilaAtencionSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            return FilaAtencion.objects.all()
        return FilaAtencion.objects.filter(negocio__usuario=user)

    def perform_create(self, serializer):
        user = self.request.user
        negocio = serializer.validated_data['negocio']

        # Validar propiedad del negocio
        if not user.is_staff and negocio.usuario != user:
            raise PermissionDenied("No tienes permiso para registrar filas en este negocio.")

        # Limitar la cantidad de filas según suscripción
        if not user.is_staff and user.suscripcion == "free":
            # Verifica si ya tiene una fila creada en este negocio
            existe_fila = FilaAtencion.objects.filter(negocio=negocio).exists()
            if existe_fila:
                raise PermissionDenied("Los usuarios con suscripción free solo pueden registrar una fila por negocio.")

        serializer.save()

    @action(detail=True, methods=['patch'], permission_classes=[IsAuthenticated], url_path='editar-parcial')
    def editar_parcial(self, request, pk=None):
        fila = self.get_object()

        # Solo puede editar el dueño del negocio o admin
        if fila.negocio.usuario != request.user and not request.user.is_staff:
            return Response({"detail": "No tienes permiso para editar esta fila."}, status=status.HTTP_403_FORBIDDEN)

        # Lista de campos que se pueden editar
        campos_permitidos = [
            'nombre', 'cantidad_tickets', 'visible', 'periodo_atencion',
            'apertura', 'finalizacion', 'numero_ticket_actual','permitir_cancelacion'
        ]
        datos = {key: value for key, value in request.data.items() if key in campos_permitidos}

        serializer = self.get_serializer(fila, data=datos, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)
    





class TicketViewSet(viewsets.ModelViewSet):
    queryset = Ticket.objects.all()
    serializer_class = TicketSerializer

    @action(detail=False, methods=['post'], url_path='generar', permission_classes=[IsAuthenticated])
    def generar_ticket(self, request):
        usuario = request.user

        #  Verificar si el usuario está suspendido
        if usuario.esta_suspendido:
            return Response({'error': 'Tu cuenta está suspendida. Intenta más tarde.'}, status=status.HTTP_403_FORBIDDEN)

        fila_id = request.data.get('fila_atencion')
        if not fila_id:
            return Response({'error': 'El campo fila_atencion es obligatorio.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            fila = FilaAtencion.objects.get(fila_atencion_id=fila_id)
        except FilaAtencion.DoesNotExist:
            return Response({'error': 'Fila de atención no encontrada.'}, status=status.HTTP_404_NOT_FOUND)

        #  Verificar si ya tiene un ticket activo en esta fila
        tickets_usuario = UsuarioTicket.objects.filter(
            usuario=usuario,
            ticket__fila_atencion=fila,
            ticket__estado='activo'
        )
        
        if tickets_usuario.exists():
            return Response({'error': 'Ya tienes un ticket activo en esta fila.'}, status=status.HTTP_400_BAD_REQUEST)

        #  Continuar con la lógica actual si no tiene ticket aún
        nueva_posicion = fila.numero_ticket_actual + 1
        if nueva_posicion > fila.cantidad_tickets:
            return Response({'error': 'Se ha alcanzado el límite de tickets para esta fila.'}, status=status.HTTP_400_BAD_REQUEST)

        fecha_hora_atencion = None
        if fila.periodo_atencion and fila.periodo_atencion.total_seconds() > 0:
            hoy = timezone.localtime().date()
            hora_base = datetime.combine(hoy, fila.apertura)
            fecha_hora_atencion = hora_base + (fila.periodo_atencion * (nueva_posicion - 1))

            hora_final = datetime.combine(hoy, fila.finalizacion)
            if fecha_hora_atencion.time() > fila.finalizacion:
                return Response({'error': 'No se puede asignar un ticket porque excede el horario de atención.'}, status=status.HTTP_400_BAD_REQUEST)

        ticket = Ticket.objects.create(
            estado='activo',
            fila_atencion=fila,
            posicion=nueva_posicion,
            fecha_hora_atencion=fecha_hora_atencion
        )

        fila.numero_ticket_actual = nueva_posicion
        fila.save()

        # Asociar el ticket al usuario
        UsuarioTicket.objects.create(usuario=usuario, ticket=ticket)

        serializer = self.get_serializer(ticket)
        return Response(serializer.data, status=status.HTTP_201_CREATED)