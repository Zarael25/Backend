from rest_framework import serializers
from .models import Usuario, UsuarioTicket, LogUsuario
from datetime import timedelta
from django.utils import timezone
from rest_framework import serializers
from .models import Usuario, UsuarioTicket, LogUsuario
from datetime import timedelta
from django.utils import timezone

# ---------------- Serializer Usuario ----------------
class UsuarioSerializer(serializers.ModelSerializer):
    # write_only → la contraseña se recibe en requests pero no se devuelve en responses
    password = serializers.CharField(write_only=True)

    class Meta:
        model = Usuario
        exclude = ['groups', 'user_permissions']  # Excluimos campos internos de Django
        # fields = '__all__'  # (alternativa si se quieren incluir todos los campos)

    def create(self, validated_data):
        """
        Crea un nuevo usuario con contraseña encriptada.
        """
        password = validated_data.pop('password')
        usuario = Usuario(**validated_data)
        usuario.set_password(password)  # Encripta la contraseña
        usuario.save()
        return usuario

    def update(self, instance, validated_data):
        """
        Actualiza un usuario.
        Si se incluye 'password', se encripta antes de guardar.
        """
        password = validated_data.pop('password', None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        if password:
            instance.set_password(password)
        instance.save()
        return instance


# ---------------- Serializer UsuarioTicket ----------------
class UsuarioTicketSerializer(serializers.ModelSerializer):
    """
    Serializa la relación Usuario ↔ Ticket (modelo intermedio).
    """
    class Meta:
        model = UsuarioTicket
        fields = '__all__'


# ---------------- Serializer Detallado UsuarioTicket ----------------
class UsuarioTicketDetalleSerializer(serializers.ModelSerializer):
    """
    Serializador extendido que incluye:
    - Info básica del ticket
    - Info del usuario dueño
    - Info de la fila y negocio
    - Cálculo de tiempo restante para cancelar
    """

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

    # Campo calculado: minutos restantes para cancelar
    minutos_restantes_cancelacion = serializers.SerializerMethodField()

    class Meta:
        model = UsuarioTicket
        fields = [
            'ticket_id',
            'nombre', 'correo',
            'estado', 'fecha_hora_registro', 'fecha_hora_atencion', 'posicion',
            'fila_nombre', 'negocio_nombre', 'permitir_cancelacion',
            'minutos_restantes_cancelacion',
        ]

    def get_minutos_restantes_cancelacion(self, obj):
        """
        Calcula cuántos minutos quedan para cancelar el ticket.
        - Si el negocio no permite cancelar → retorna 0.
        - Si ya venció el tiempo de cancelación → retorna 0.
        - Si aún se puede cancelar → retorna los minutos restantes.
        """
        negocio = obj.ticket.fila_atencion.negocio

        if not negocio.permite_cancelar:
            return 0

        tiempo_limite = negocio.tiempo_limite_cancelacion or 0
        fecha_limite = obj.ticket.fecha_hora_registro + timedelta(minutes=tiempo_limite)
        ahora = timezone.now()

        minutos_restantes = (fecha_limite - ahora).total_seconds() / 60
        return int(minutos_restantes) if minutos_restantes > 0 else 0


# ---------------- Serializer LogUsuario ----------------
class LogUsuarioSerializer(serializers.ModelSerializer):
    """
    Serializador de logs de usuario (acciones realizadas por cada usuario).
    """
    class Meta:
        model = LogUsuario
        fields = '__all__'
