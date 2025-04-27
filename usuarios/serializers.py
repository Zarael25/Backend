from rest_framework import serializers
from .models import Usuario, Admin, UsuarioTicket
#from negocios.models import Ticket  # si lo necesitas para UsuarioTicket

class UsuarioSerializer(serializers.ModelSerializer):
    class Meta:
        model = Usuario
        fields = '__all__'

class AdminSerializer(serializers.ModelSerializer):
    class Meta:
        model = Admin
        fields = '__all__'

class UsuarioTicketSerializer(serializers.ModelSerializer):
    class Meta:
        model = UsuarioTicket
        fields = '__all__'