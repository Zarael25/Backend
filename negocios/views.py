from rest_framework import viewsets

from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status
from rest_framework.exceptions import PermissionDenied

from .models import Negocio, Atencion, Ticket
from .serializers import NegocioSerializer, AtencionSerializer, TicketSerializer
from .services import obtener_negocios_por_usuario

class NegocioViewSet(viewsets.ModelViewSet):
    queryset = Negocio.objects.all() 
    serializer_class = NegocioSerializer
    permission_classes = [IsAuthenticated]  # Protege todas las operaciones del ViewSet

    def get_queryset(self):
        if self.request.user.is_staff:
            return Negocio.objects.all()
        return Negocio.objects.filter(usuario=self.request.user)


    def perform_create(self, serializer):
        usuario = self.request.user

        # Si el usuario no es admin y tiene suscripción free, se limita a 1 negocio
        if not usuario.is_staff and usuario.suscripcion == "free":
            tiene_negocio = Negocio.objects.filter(usuario=usuario).exists()
            if tiene_negocio:
                raise PermissionDenied("Los usuarios con suscripción free solo pueden registrar un negocio.")

        serializer.save(usuario=usuario)




    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated], url_path='mis_negocios')
    def mis_negocios(self, request):
        negocios = obtener_negocios_por_usuario(request.user)
        serializer = self.get_serializer(negocios, many=True)
        return Response(serializer.data)
    
    
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



class AtencionViewSet(viewsets.ModelViewSet):
    queryset = Atencion.objects.all()
    serializer_class = AtencionSerializer

class TicketViewSet(viewsets.ModelViewSet):
    queryset = Ticket.objects.all()
    serializer_class = TicketSerializer
