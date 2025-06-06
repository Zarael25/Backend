from rest_framework import serializers
from .models import Negocio, FilaAtencion, Ticket

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


