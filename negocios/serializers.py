from rest_framework import serializers
from .models import Negocio, FilaAtencion, Ticket
from usuarios.models import UsuarioTicket

class NegocioSerializer(serializers.ModelSerializer):
    class Meta:
        model = Negocio
        fields = '__all__'
        read_only_fields = ['usuario']

class FilaAtencionSerializer(serializers.ModelSerializer):
    class Meta:
        model = FilaAtencion
        fields = '__all__'

class TicketSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ticket
        fields = '__all__'

class TicketConUsuarioSerializer(serializers.ModelSerializer):
    nombre_usuario = serializers.SerializerMethodField()

    class Meta:
        model = Ticket
        fields = '__all__'  # o una lista exacta si prefieres

    def get_nombre_usuario(self, obj):
        usuario_ticket = UsuarioTicket.objects.filter(ticket=obj).first()
        if usuario_ticket:
            return usuario_ticket.usuario.nombre #or usuario_ticket.usuario.username
        return None