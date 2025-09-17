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
    # ---------------- Configuración base ----------------
    queryset = Negocio.objects.all() 
    serializer_class = NegocioSerializer
    permission_classes = [IsAuthenticated]  # Requiere autenticación para todas las operaciones

    def get_queryset(self):
        # En la ruta base devolvemos todos los negocios (sin filtros)
        return Negocio.objects.all()

    # ---------------- Endpoints personalizados ----------------

    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated], url_path='mis_negocios')
    def mis_negocios(self, request):
        # Devuelve solo los negocios del usuario autenticado
        negocios = Negocio.objects.filter(usuario=request.user)
        serializer = self.get_serializer(negocios, many=True)
        return Response(serializer.data)

    def perform_create(self, serializer):
        usuario = self.request.user

        # Restricción: usuarios con suscripción "free" solo pueden crear 1 negocio
        if not usuario.is_staff and usuario.suscripcion == "free":
            tiene_negocio = Negocio.objects.filter(usuario=usuario).exists()
            if tiene_negocio:
                raise PermissionDenied("Los usuarios con suscripción free solo pueden registrar un negocio.")

        serializer.save(usuario=usuario)

    @action(detail=True, methods=['patch'], permission_classes=[IsAuthenticated], url_path='editar-parcial')
    def editar_parcial(self, request, pk=None):
        # Permite edición parcial de ciertos campos
        negocio = self.get_object()
        if negocio.usuario != request.user and not request.user.is_staff:
            return Response({"detail": "No tienes permiso para editar este negocio"}, status=status.HTTP_403_FORBIDDEN)

        # Solo se pueden editar los campos permitidos
        campos_permitidos = ['nombre', 'direccion', 'categoria', 'doc_respaldo', 'num_referencia', 'detalle']
        datos = {key: value for key, value in request.data.items() if key in campos_permitidos}

        serializer = self.get_serializer(negocio, data=datos, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    @action(detail=True, methods=['patch'], permission_classes=[IsAuthenticated], url_path='ocultar')
    def ocultar_negocio(self, request, pk=None):
        # Cambia el estado del negocio a "oculto"
        negocio = self.get_object()
        if negocio.usuario != request.user and not request.user.is_staff:
            return Response({"detail": "No tienes permiso para ocultar este negocio"}, status=status.HTTP_403_FORBIDDEN)

        negocio.estado = 'oculto'
        negocio.save()
        return Response({"detail": f"Negocio '{negocio.nombre}' ocultado correctamente."}, status=status.HTTP_200_OK)

    @action(detail=True, methods=['get'], permission_classes=[IsAuthenticated], url_path='mis_filas')
    def mis_filas(self, request, pk=None):
        # Devuelve todas las filas asociadas a un negocio específico
        negocio = self.get_object()

        # Solo el dueño o admin puede acceder
        if negocio.usuario != request.user and not request.user.is_staff:
            return Response({"detail": "No tienes permiso para ver las filas de este negocio."}, status=status.HTTP_403_FORBIDDEN)

        filas = FilaAtencion.objects.filter(negocio=negocio)
        serializer = FilaAtencionSerializer(filas, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated], url_path='verificados')
    def negocios_verificados(self, request):
        # Lista los negocios en estado "verificado"
        termino = request.query_params.get('search', '').strip()
        negocios_verificados = Negocio.objects.filter(estado='verificado')

        # Permite búsqueda por nombre o categoría
        if termino:
            negocios_verificados = negocios_verificados.filter(
                Q(nombre__icontains=termino) |
                Q(categoria__icontains=termino)
            )

        serializer = self.get_serializer(negocios_verificados, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'], permission_classes=[IsAuthenticated], url_path='filas_visibles')
    def filas_visibles(self, request, pk=None):
        # Devuelve solo las filas visibles de un negocio
        negocio = self.get_object()
        filas_visibles = FilaAtencion.objects.filter(negocio=negocio, visible=True)
        serializer = FilaAtencionSerializer(filas_visibles, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=True, methods=['patch'], permission_classes=[IsAuthenticated], url_path='editar-politicas')
    def editar_politicas(self, request, pk=None):
        # Permite actualizar las políticas del negocio (cancelaciones y reservas)
        negocio = self.get_object()

        # Solo el dueño o un admin puede editarlas
        if negocio.usuario != request.user and not request.user.is_staff:
            return Response({"detail": "No tienes permiso para editar las políticas de este negocio."}, status=status.HTTP_403_FORBIDDEN)

        # Campos que sí pueden modificarse
        campos_permitidos = ['permite_cancelar', 'tiempo_limite_cancelacion', 'maximo_reservas_diarias']
        datos = {key: value for key, value in request.data.items() if key in campos_permitidos}

        serializer = self.get_serializer(negocio, data=datos, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(serializer.data, status=status.HTTP_200_OK)

    



class NegocioAdminViewSet(viewsets.ModelViewSet):
    # ---------------- Configuración base ----------------
    queryset = Negocio.objects.all()
    serializer_class = NegocioSerializer
    permission_classes = [IsAuthenticated]  # Requiere autenticación para todas las operaciones

    # ---------------- Listar y buscar negocios ----------------
    @action(detail=False, methods=['get'], url_path='buscar')
    def listar_negocios_admin(self, request):
        """
        Permite al admin listar todos los negocios.
        Si se pasa un parámetro "search", filtra por nombre, categoría o estado.
        """
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

    # ---------------- Cambiar estado de un negocio ----------------
    @action(detail=True, methods=['patch'], url_path='cambiar_estado')
    def cambiar_estado(self, request, pk=None):
        """
        Permite al admin actualizar el estado de un negocio.
        Solo acepta valores definidos en Negocio.ESTADO_CHOICES.
        """
        negocio = self.get_object()
        nuevo_estado = request.data.get('estado')

        # Validar que el estado enviado sea válido
        if nuevo_estado not in dict(Negocio.ESTADO_CHOICES).keys():
            return Response({'error': 'Estado inválido.'}, status=status.HTTP_400_BAD_REQUEST)

        negocio.estado = nuevo_estado
        negocio.save()
        return Response({'mensaje': f"Estado del negocio cambiado a '{nuevo_estado}'."}, status=status.HTTP_200_OK)

    # ---------------- Descargar documento de respaldo ----------------
    @action(detail=True, methods=['get'], url_path='descargar_doc')
    def descargar_doc_respaldo(self, request, pk=None):
        """
        Permite al admin descargar/ver la URL del documento de respaldo
        asociado a un negocio (si existe).
        """
        negocio = self.get_object()

        # Validar que el negocio tenga documento de respaldo
        if not negocio.doc_respaldo:
            return Response({'error': 'Este negocio no tiene un documento de respaldo.'}, status=status.HTTP_404_NOT_FOUND)

        # Genera la URL absoluta para acceder al documento
        url = request.build_absolute_uri(negocio.doc_respaldo.url)
        return Response({'doc_respaldo_url': url}, status=status.HTTP_200_OK)




    


class FilaAtencionViewSet(viewsets.ModelViewSet):
    # ---------------- Configuración base ----------------
    queryset = FilaAtencion.objects.all()
    serializer_class = FilaAtencionSerializer
    permission_classes = [IsAuthenticated]  # Solo usuarios autenticados

    # ---------------- Filtrado de filas según usuario ----------------
    def get_queryset(self):
        """
        - Si el usuario es admin/staff → puede ver todas las filas.
        - Si es usuario normal → solo puede ver las filas de sus negocios.
        """
        user = self.request.user
        if user.is_staff:
            return FilaAtencion.objects.all()
        return FilaAtencion.objects.filter(negocio__usuario=user)

    # ---------------- Crear fila de atención ----------------
    def perform_create(self, serializer):
        """
        Al crear una fila:
        - Verifica que el usuario sea dueño del negocio (o admin).
        - Aplica limitaciones según suscripción (free → 1 sola fila por negocio).
        """
        user = self.request.user
        negocio = serializer.validated_data['negocio']

        # Validar que el usuario sea propietario del negocio
        if not user.is_staff and negocio.usuario != user:
            raise PermissionDenied("No tienes permiso para registrar filas en este negocio.")

        # Restricción para usuarios con suscripción "free"
        if not user.is_staff and user.suscripcion == "free":
            existe_fila = FilaAtencion.objects.filter(negocio=negocio).exists()
            if existe_fila:
                raise PermissionDenied("Los usuarios con suscripción free solo pueden registrar una fila por negocio.")

        serializer.save()

    # ---------------- Edición parcial de una fila ----------------
    @action(detail=True, methods=['patch'], permission_classes=[IsAuthenticated], url_path='editar-parcial')
    def editar_parcial(self, request, pk=None):
        """
        Permite la edición parcial de ciertos campos de la fila.
        Solo puede hacerlo el dueño del negocio o un admin.
        """
        fila = self.get_object()

        # Validación de permisos
        if fila.negocio.usuario != request.user and not request.user.is_staff:
            return Response({"detail": "No tienes permiso para editar esta fila."}, status=status.HTTP_403_FORBIDDEN)

        # Campos permitidos para edición
        campos_permitidos = [
            'nombre', 'cantidad_tickets', 'visible', 'periodo_atencion',
            'apertura', 'finalizacion', 'numero_ticket_actual'
        ]
        datos = {key: value for key, value in request.data.items() if key in campos_permitidos}

        # Serialización y guardado
        serializer = self.get_serializer(fila, data=datos, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    
    





class TicketViewSet(viewsets.ModelViewSet):
    # ---------------- Configuración base ----------------
    queryset = Ticket.objects.all()
    serializer_class = TicketSerializer
    permission_classes = [IsAuthenticated]

    # ---------------- Generar ticket ----------------
    @action(detail=False, methods=['post'], url_path='generar', permission_classes=[IsAuthenticated])
    def generar_ticket(self, request):
        """
        Genera un nuevo ticket para una fila de atención:
        - Valida que el usuario no esté suspendido.
        - Verifica que la fila exista y esté visible.
        - Controla cantidad de tickets disponibles y horario.
        - Aplica limitaciones de reservas diarias y tickets activos.
        - Crea el ticket, lo asigna al usuario y actualiza contadores.
        """
        usuario = request.user

        # 1. Validar suspensión del usuario
        if usuario.esta_suspendido:
            return Response({'error': 'Tu cuenta está suspendida. Intenta más tarde.'}, status=status.HTTP_403_FORBIDDEN)

        # 2. Validar existencia de fila
        fila_id = request.data.get('fila_atencion')
        if not fila_id:
            return Response({'error': 'El campo fila_atencion es obligatorio.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            fila = FilaAtencion.objects.get(fila_atencion_id=fila_id)
        except FilaAtencion.DoesNotExist:
            return Response({'error': 'Fila de atención no encontrada.'}, status=status.HTTP_404_NOT_FOUND)

        # 3. Validar visibilidad
        if not fila.visible:
            return Response({'error': 'Esta fila no está disponible actualmente.'}, status=status.HTTP_403_FORBIDDEN)

        # 4. Cálculo de fechas posibles (hoy o mañana)
        negocio = fila.negocio
        ahora = timezone.localtime()
        hoy = ahora.date()
        hora_actual = ahora.time()
        posibles_fechas = [hoy + timedelta(days=1)] if hora_actual > fila.finalizacion else [hoy]

        ticket_generado = None
        for fecha in posibles_fechas:
            # 5. Contar tickets existentes
            tickets_existentes = Ticket.objects.filter(
                fila_atencion=fila,
                fecha_hora_atencion__date=fecha
            ).count()

            if tickets_existentes >= fila.cantidad_tickets:
                continue  # No hay cupos para esta fecha

            nueva_posicion = tickets_existentes + 1

            # 6. Calcular fecha/hora de atención
            if fila.periodo_atencion and fila.periodo_atencion.total_seconds() > 0:
                hora_base = datetime.combine(fecha, fila.apertura)
                fecha_hora_atencion = hora_base + (fila.periodo_atencion * (nueva_posicion - 1))

                if fecha_hora_atencion.time() > fila.finalizacion:
                    continue  # Se sale del horario, probamos otra fecha
            else:
                fecha_hora_atencion = datetime.combine(fecha, time(0, 0))

            # 7. Validar que el usuario no tenga ya un ticket activo en esa fila
            ya_tiene = UsuarioTicket.objects.filter(
                usuario=usuario,
                ticket__fila_atencion=fila,
                ticket__estado='activo'
            ).exists()
            if ya_tiene:
                return Response({'error': 'Ya tienes un ticket activo en esta fila.'}, status=status.HTTP_400_BAD_REQUEST)

            # 8. Validar reservas diarias máximas
            if negocio.maximo_reservas_diarias and negocio.maximo_reservas_diarias > 0:
                reserva, _ = ReservaDiariaUsuario.objects.get_or_create(
                    usuario=usuario,
                    negocio=negocio,
                    fecha=fecha,
                    defaults={'cantidad_reservas': 0}
                )
                if reserva.cantidad_reservas >= negocio.maximo_reservas_diarias:
                    return Response({'error': 'Has alcanzado el máximo de reservas diarias permitidas.'}, status=status.HTTP_403_FORBIDDEN)

            # 9. Crear el ticket
            ticket = Ticket.objects.create(
                estado='activo',
                fila_atencion=fila,
                posicion=nueva_posicion,
                fecha_hora_atencion=fecha_hora_atencion
            )

            fila.numero_ticket_actual = nueva_posicion
            fila.save()

            UsuarioTicket.objects.create(usuario=usuario, ticket=ticket)

            # 10. Incrementar contador de reservas
            if negocio.maximo_reservas_diarias and negocio.maximo_reservas_diarias > 0:
                reserva.cantidad_reservas += 1
                reserva.save(update_fields=['cantidad_reservas'])

            ticket_generado = ticket
            break  # Se generó correctamente, salimos del bucle

        # 11. Si no se pudo generar ticket
        if not ticket_generado:
            return Response({'error': 'No hay espacio disponible para hoy ni mañana.'}, status=status.HTTP_400_BAD_REQUEST)

        serializer = self.get_serializer(ticket_generado)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    # ---------------- Listar tickets por fila ----------------
    @action(detail=True, methods=['get'], url_path='por-fila', permission_classes=[IsAuthenticated])
    def listar_tickets_por_fila(self, request, pk=None):
        """
        Lista todos los tickets de una fila específica.
        - Solo el dueño del negocio puede verlos.
        - Permite filtrar por fecha con ?fecha=YYYY-MM-DD
        """
        fila_id = pk
        usuario = request.user

        try:
            fila = FilaAtencion.objects.get(fila_atencion_id=fila_id)
        except FilaAtencion.DoesNotExist:
            return Response({'error': 'Fila no encontrada.'}, status=status.HTTP_404_NOT_FOUND)

        # Solo el dueño del negocio puede ver los tickets
        if fila.negocio.usuario != usuario:
            return Response({'error': 'No tienes permiso para ver los tickets de esta fila.'}, status=status.HTTP_403_FORBIDDEN)

        # Filtrado por fecha (opcional)
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

    # ---------------- Cambiar estado de ticket ----------------
    @action(detail=True, methods=['patch'], url_path='cambiar-estado', permission_classes=[IsAuthenticated])
    def cambiar_estado(self, request, pk=None):
        """
        Cambia el estado de un ticket (solo dueño del negocio).
        Estados permitidos: "finalizado" o "cancelado".
        - Si se cancela: aplica penalización al usuario que sacó el ticket.
        """
        usuario = request.user

        # Validar existencia de ticket
        try:
            ticket = Ticket.objects.get(pk=pk)
        except Ticket.DoesNotExist:
            return Response({"error": "Ticket no encontrado."}, status=status.HTTP_404_NOT_FOUND)

        fila = ticket.fila_atencion
        negocio = fila.negocio

        # Solo el dueño del negocio puede modificarlo
        if negocio.usuario != usuario:
            return Response({"error": "No tienes permiso para modificar este ticket."}, status=status.HTTP_403_FORBIDDEN)

        nuevo_estado = request.data.get('nuevo_estado')

        if nuevo_estado not in ['finalizado', 'cancelado']:
            return Response({"error": "Estado inválido. Solo se permite 'finalizado' o 'cancelado'."}, status=status.HTTP_400_BAD_REQUEST)

        # Penalización si se cancela
        if nuevo_estado == 'cancelado':
            usuario_ticket = UsuarioTicket.objects.filter(ticket=ticket).first()
            if usuario_ticket:
                usuario_a_penalizar = usuario_ticket.usuario

                # Incrementar contador de suspensiones
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

        # Actualizar estado del ticket
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
