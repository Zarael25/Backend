from rest_framework import viewsets

from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status
from rest_framework.exceptions import PermissionDenied

from .models import Negocio, FilaAtencion, Ticket,ReservaDiariaUsuario
from .serializers import NegocioSerializer, FilaAtencionSerializer, TicketSerializer, TicketConUsuarioSerializer
from .services import obtener_negocios_por_usuario
from django.db.models import Q

from django.utils import timezone
from datetime import datetime, time, timedelta

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
    
    @action(detail=True, methods=['patch'], permission_classes=[IsAuthenticated], url_path='editar-politicas')
    def editar_politicas(self, request, pk=None):
        negocio = self.get_object()

        # Solo puede editar el dueño o un admin
        if negocio.usuario != request.user and not request.user.is_staff:
            return Response({"detail": "No tienes permiso para editar las políticas de este negocio."}, status=status.HTTP_403_FORBIDDEN)

        campos_permitidos = ['permite_cancelar', 'tiempo_limite_cancelacion', 'maximo_reservas_diarias']
        datos = {key: value for key, value in request.data.items() if key in campos_permitidos}

        serializer = self.get_serializer(negocio, data=datos, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(serializer.data, status=status.HTTP_200_OK)
    


    
# --- API ADMIN ---
class NegocioAdminViewSet(viewsets.ModelViewSet):
    queryset = Negocio.objects.all()
    serializer_class = NegocioSerializer
    permission_classes = [IsAuthenticated]  # Podrías poner IsAdminUser o un permiso custom

    @action(detail=False, methods=['get'], url_path='buscar')
    def listar_negocios_admin(self, request):
        termino = request.query_params.get('search', '').strip()
        negocios = Negocio.objects.all()
        if termino:
            negocios = negocios.filter(
                Q(nombre__icontains=termino) |
                Q(categoria__icontains=termino) |
                Q(estado__icontains=termino)
            )
        serializer = self.get_serializer(negocios, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['patch'], url_path='cambiar_estado')
    def cambiar_estado(self, request, pk=None):
        negocio = self.get_object()
        nuevo_estado = request.data.get('estado')

        if nuevo_estado not in dict(Negocio.ESTADO_CHOICES).keys():
            return Response({'error': 'Estado inválido.'}, status=status.HTTP_400_BAD_REQUEST)

        negocio.estado = nuevo_estado
        negocio.save()
        return Response({'mensaje': f"Estado del negocio cambiado a '{nuevo_estado}'."}, status=status.HTTP_200_OK)

    @action(detail=True, methods=['get'], url_path='descargar_doc')
    def descargar_doc_respaldo(self, request, pk=None):
        negocio = self.get_object()
        if not negocio.doc_respaldo:
            return Response({'error': 'Este negocio no tiene un documento de respaldo.'}, status=status.HTTP_404_NOT_FOUND)

        url = request.build_absolute_uri(negocio.doc_respaldo.url)
        return Response({'doc_respaldo_url': url}, status=status.HTTP_200_OK)








    


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
            'apertura', 'finalizacion', 'numero_ticket_actual'
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

        if usuario.esta_suspendido:
            return Response({'error': 'Tu cuenta está suspendida. Intenta más tarde.'}, status=status.HTTP_403_FORBIDDEN)

        fila_id = request.data.get('fila_atencion')
        if not fila_id:
            return Response({'error': 'El campo fila_atencion es obligatorio.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            fila = FilaAtencion.objects.get(fila_atencion_id=fila_id)
        except FilaAtencion.DoesNotExist:
            return Response({'error': 'Fila de atención no encontrada.'}, status=status.HTTP_404_NOT_FOUND)

        if not fila.visible:
            return Response({'error': 'Esta fila no está disponible actualmente.'}, status=status.HTTP_403_FORBIDDEN)



        negocio = fila.negocio

        ahora = timezone.localtime()
        hoy = ahora.date()
        hora_actual = ahora.time()

        # Si ya pasó la hora de finalización, solo intentamos mañana
        if hora_actual > fila.finalizacion:
            posibles_fechas = [hoy + timedelta(days=1)]
        else:
            posibles_fechas = [hoy]

        ticket_generado = None
        for fecha in posibles_fechas:
            # Contar cuántos tickets hay ya para esa fecha
            tickets_existentes = Ticket.objects.filter(
                fila_atencion=fila,
                fecha_hora_atencion__date=fecha
            ).count()

            if tickets_existentes >= fila.cantidad_tickets:
                continue  # Ya no hay espacio, probamos el siguiente día

            nueva_posicion = tickets_existentes + 1

            # Calcular fecha_hora_atencion
            if fila.periodo_atencion and fila.periodo_atencion.total_seconds() > 0:
                hora_base = datetime.combine(fecha, fila.apertura)
                fecha_hora_atencion = hora_base + (fila.periodo_atencion * (nueva_posicion - 1))

                # Validamos que no se exceda el horario
                if fecha_hora_atencion.time() > fila.finalizacion:
                    continue  # No se puede asignar esa hora, probamos siguiente día si hay

            else:
                # Si no hay periodo de atención, solo asignamos la fecha con hora 00:00
                fecha_hora_atencion = datetime.combine(fecha, time(0, 0))

            # Verificar si ya tiene un ticket activo en esta fila
            ya_tiene = UsuarioTicket.objects.filter(
                usuario=usuario,
                ticket__fila_atencion=fila,
                ticket__estado='activo'
            ).exists()
            if ya_tiene:
                return Response({'error': 'Ya tienes un ticket activo en esta fila.'}, status=status.HTTP_400_BAD_REQUEST)

            # Verificar reservas diarias
            if negocio.maximo_reservas_diarias and negocio.maximo_reservas_diarias > 0:
                reserva, _ = ReservaDiariaUsuario.objects.get_or_create(
                    usuario=usuario,
                    negocio=negocio,
                    fecha=fecha,
                    defaults={'cantidad_reservas': 0}
                )
                if reserva.cantidad_reservas >= negocio.maximo_reservas_diarias:
                    return Response({'error': 'Has alcanzado el máximo de reservas diarias permitidas.'}, status=status.HTTP_403_FORBIDDEN)

            # Crear el ticket
            ticket = Ticket.objects.create(
                estado='activo',
                fila_atencion=fila,
                posicion=nueva_posicion,
                fecha_hora_atencion=fecha_hora_atencion
            )

            fila.numero_ticket_actual = nueva_posicion
            fila.save()

            UsuarioTicket.objects.create(usuario=usuario, ticket=ticket)

            if negocio.maximo_reservas_diarias and negocio.maximo_reservas_diarias > 0:
                reserva.cantidad_reservas += 1
                reserva.save(update_fields=['cantidad_reservas'])

            ticket_generado = ticket
            break  # Ya se generó, no seguimos buscando fechas

        if not ticket_generado:
            return Response({'error': 'No hay espacio disponible para hoy ni mañana.'}, status=status.HTTP_400_BAD_REQUEST)

        serializer = self.get_serializer(ticket_generado)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    


    @action(detail=True, methods=['get'], url_path='por-fila', permission_classes=[IsAuthenticated])
    def listar_tickets_por_fila(self, request, pk=None):
        fila_id = pk  # Aquí recibes el 21 de /tickets/21/por-fila/
        usuario = request.user

        try:
            fila = FilaAtencion.objects.get(fila_atencion_id=fila_id)
        except FilaAtencion.DoesNotExist:
            return Response({'error': 'Fila no encontrada.'}, status=status.HTTP_404_NOT_FOUND)

        if fila.negocio.usuario != usuario:
            return Response({'error': 'No tienes permiso para ver los tickets de esta fila.'}, status=status.HTTP_403_FORBIDDEN)

        fecha_str = request.query_params.get('fecha', None)
        if fecha_str:
            try:
                fecha_obj = datetime.strptime(fecha_str, '%Y-%m-%d').date()
            except ValueError:
                return Response({'error': 'Formato de fecha inválido. Usa YYYY-MM-DD.'}, status=status.HTTP_400_BAD_REQUEST)

            inicio_dia = datetime.combine(fecha_obj, time.min)
            fin_dia = datetime.combine(fecha_obj, time.max)

            tickets = Ticket.objects.filter(
                fila_atencion=fila,
                fecha_hora_atencion__range=(inicio_dia, fin_dia)
            ).order_by('posicion')
        else:
            tickets = Ticket.objects.filter(fila_atencion=fila).order_by('posicion')

        serializer = TicketConUsuarioSerializer(tickets, many=True)
        return Response(serializer.data)
    

    @action(detail=True, methods=['patch'], url_path='cambiar-estado', permission_classes=[IsAuthenticated])
    def cambiar_estado(self, request, pk=None):
        usuario = request.user

        try:
            ticket = Ticket.objects.get(pk=pk)
        except Ticket.DoesNotExist:
            return Response({"error": "Ticket no encontrado."}, status=status.HTTP_404_NOT_FOUND)

        fila = ticket.fila_atencion
        negocio = fila.negocio

        if negocio.usuario != usuario:
            return Response({"error": "No tienes permiso para modificar este ticket."},
                            status=status.HTTP_403_FORBIDDEN)

        nuevo_estado = request.data.get('nuevo_estado')

        if nuevo_estado not in ['finalizado', 'cancelado']:
            return Response({"error": "Estado inválido. Solo se permite 'finalizado' o 'cancelado'."},
                            status=status.HTTP_400_BAD_REQUEST)

        # Si se cancela, aplicamos penalización al usuario dueño del ticket (asumiendo que es el que sacó el ticket)
        if nuevo_estado == 'cancelado':
            usuario_ticket = UsuarioTicket.objects.filter(ticket=ticket).first()
            if usuario_ticket:
                usuario_a_penalizar = usuario_ticket.usuario

                # Incrementar contador de suspensión
                usuario_a_penalizar.suspendido_contador += 1

                if usuario_a_penalizar.suspendido_contador >= 5:
                    usuario_a_penalizar.estado = 'suspendido'
                    usuario_a_penalizar.suspendido_hasta = None
                    castigo = "Suspensión permanente"
                else:
                    minutos_castigo = usuario_a_penalizar.suspendido_contador
                    usuario_a_penalizar.estado = 'suspendido'
                    usuario_a_penalizar.suspendido_hasta = timezone.now() + timedelta(minutes=minutos_castigo)
                    castigo = f"Suspensión por {minutos_castigo} minutos"

                usuario_a_penalizar.save(update_fields=['estado', 'suspendido_contador', 'suspendido_hasta'])

        ticket.estado = nuevo_estado
        ticket.save()

        serializer = self.get_serializer(ticket)

        if nuevo_estado == 'cancelado':
            return Response({
                'mensaje': 'Ticket cancelado y penalización aplicada.',
                'castigo': castigo,
                'ticket': serializer.data
            }, status=status.HTTP_200_OK)

        return Response(serializer.data, status=status.HTTP_200_OK)
