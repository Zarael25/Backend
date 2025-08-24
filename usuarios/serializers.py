from rest_framework import serializers
from .models import Usuario, UsuarioTicket, LogUsuario
from datetime import timedelta
from django.utils import timezone
class UsuarioSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)  # Para que no se exponga al leer

    class Meta:
        model = Usuario
        exclude = ['groups', 'user_permissions']
        #fields = '__all__'

    def create(self, validated_data):
        password = validated_data.pop('password')
        usuario = Usuario(**validated_data)
        usuario.set_password(password)  # Encripta la contraseña
        usuario.save()
        return usuario

    def update(self, instance, validated_data):
        password = validated_data.pop('password', None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        if password:
            instance.set_password(password)
        instance.save()
        return instance


class UsuarioTicketSerializer(serializers.ModelSerializer):
    class Meta:
        model = UsuarioTicket
        fields = '__all__'



class UsuarioTicketDetalleSerializer(serializers.ModelSerializer):
    # ID del ticket
    ticket_id = serializers.IntegerField(source='ticket.ticket_id', read_only=True)

    # Datos del usuario
    nombre = serializers.CharField(source='usuario.nombre', read_only=True)
    correo = serializers.EmailField(source='usuario.correo', read_only=True)

    # Datos del ticket
    estado = serializers.CharField(source='ticket.estado', read_only=True)
    fecha_hora_registro = serializers.DateTimeField(source='ticket.fecha_hora_registro', read_only=True)
    fecha_hora_atencion = serializers.DateTimeField(source='ticket.fecha_hora_atencion', read_only=True)
    posicion = serializers.IntegerField(source='ticket.posicion', read_only=True)

    # Datos de la fila
    fila_nombre = serializers.CharField(source='ticket.fila_atencion.nombre', read_only=True)

    # Datos del negocio
    negocio_nombre = serializers.CharField(source='ticket.fila_atencion.negocio.nombre', read_only=True)
    permitir_cancelacion = serializers.BooleanField(source='ticket.fila_atencion.negocio.permite_cancelar', read_only=True)

    # Campo calculado: hasta qué hora se puede cancelar el ticket
    minutos_restantes_cancelacion = serializers.SerializerMethodField()

    class Meta:
        model = UsuarioTicket
        fields = [
            'ticket_id', 
            'nombre', 'correo',
            'estado', 'fecha_hora_registro', 'fecha_hora_atencion', 'posicion',
            'fila_nombre', 'negocio_nombre','permitir_cancelacion',
            'minutos_restantes_cancelacion',

        ]


    def get_minutos_restantes_cancelacion(self, obj):
        negocio = obj.ticket.fila_atencion.negocio
        
        if not negocio.permite_cancelar:
            return 0  # no permite cancelar, 0 minutos restantes
        
        tiempo_limite = negocio.tiempo_limite_cancelacion or 0
        fecha_limite = obj.ticket.fecha_hora_registro + timedelta(minutes=tiempo_limite)
        ahora = timezone.now()

        minutos_restantes = (fecha_limite - ahora).total_seconds() / 60

        if minutos_restantes <= 0:
            return 0
        
        return int(minutos_restantes)
    


class LogUsuarioSerializer(serializers.ModelSerializer):
    class Meta:
        model = LogUsuario
        fields = '__all__'