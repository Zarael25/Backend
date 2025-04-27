from rest_framework import viewsets, status
from rest_framework.response import Response
from .models import Usuario, Admin, UsuarioTicket
from .serializers import UsuarioSerializer, AdminSerializer, UsuarioTicketSerializer

class UsuarioViewSet(viewsets.ModelViewSet):
    queryset = Usuario.objects.all()
    serializer_class = UsuarioSerializer

class AdminViewSet(viewsets.ModelViewSet):
    queryset = Admin.objects.all()
    serializer_class = AdminSerializer

class UsuarioTicketViewSet(viewsets.ModelViewSet):
    queryset = UsuarioTicket.objects.all()
    serializer_class = UsuarioTicketSerializer
