from rest_framework import serializers
from .models import Negocio, FilaAtencion, Ticket
from usuarios.models import UsuarioTicket

# ---------------- Serializer Negocio ----------------
class NegocioSerializer(serializers.ModelSerializer):
    class Meta:
        model = Negocio
        fields = '__all__'             # Incluye todos los campos del modelo
        read_only_fields = ['usuario'] # El campo usuario se asigna automáticamente en el backend

# ---------------- Serializer Fila de Atención ----------------
class FilaAtencionSerializer(serializers.ModelSerializer):
    class Meta:
        model = FilaAtencion
        fields = '__all__'  # Todos los campos de la fila

# ---------------- Serializer Ticket ----------------
class TicketSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ticket
        fields = '__all__'  # Todos los campos del ticket

# ---------------- Serializer Ticket con datos de usuario ----------------
class TicketConUsuarioSerializer(serializers.ModelSerializer):
    # Campo calculado → se obtiene el nombre del usuario asociado al ticket
    nombre_usuario = serializers.SerializerMethodField()

    class Meta:
        model = Ticket
        fields = '__all__'  # Incluye todos los campos del ticket + nombre_usuario

    def get_nombre_usuario(self, obj):
        """
        Retorna el nombre (o username) del usuario que generó este ticket.
        Si no existe relación, devuelve None.
        """
        usuario_ticket = UsuarioTicket.objects.filter(ticket=obj).first()
        if usuario_ticket:
            return usuario_ticket.usuario.nombre  # o .username si prefieres
        return None