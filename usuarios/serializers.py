from rest_framework import serializers
from .models import Usuario, UsuarioTicket

class UsuarioSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)  # Para que no se exponga al leer

    class Meta:
        model = Usuario
        fields = '__all__'

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

    class Meta:
        model = UsuarioTicket
        fields = [
            'ticket_id', 
            'nombre', 'correo',
            'estado', 'fecha_hora_registro', 'fecha_hora_atencion', 'posicion',
            'fila_nombre', 'negocio_nombre',
        ]
