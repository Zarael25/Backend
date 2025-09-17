from django.db import models


# ---------------- TABLA NEGOCIO ----------------
class Negocio(models.Model):
    # ---------------- Opciones de estado ----------------
    # Define en qué situación se encuentra el negocio dentro del sistema.
    ESTADO_CHOICES = [
        ('en_revision', 'En Revisión'),   # Pendiente de validación por el admin
        ('verificado', 'Verificado'),     # Aprobado y visible
        ('rechazado', 'Rechazado'),       # No aprobado por el admin
        ('oculto', 'Oculto'),             # Aprobado pero no visible públicamente
    ]
    
    # ---------------- Categorías de negocio ----------------
    # Ayuda a clasificar el tipo de negocio para búsquedas y organización.
    CATEGORIA_CHOICES = [
        ('salud', 'Salud'),
        ('financiera', 'Financiera'),
        ('educacion', 'Educación'),
        ('tecnologia', 'Tecnología'),
        ('restaurantes', 'Restaurantes'),
        ('otros', 'Otros'),
    ]
    
    # ---------------- Campos principales ----------------
    negocio_id = models.AutoField(primary_key=True)              # Identificador único del negocio
    nombre = models.CharField(max_length=100)                    # Nombre del negocio
    direccion = models.CharField(max_length=255)                 # Dirección física
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='en_revision')  # Estado actual
    categoria = models.CharField(max_length=50, choices=CATEGORIA_CHOICES)                   # Categoría
    doc_respaldo = models.FileField(upload_to='docs_respaldo/', null=True, blank=True)       # Documentación de respaldo opcional
    num_referencia = models.CharField(max_length=50, unique=True)  # Número único de referencia (ej: NIT, código interno)
    detalle = models.TextField()                                 # Descripción detallada del negocio
    
    # Relación con usuario propietario (un negocio pertenece a un usuario)
    usuario = models.ForeignKey('usuarios.Usuario', on_delete=models.RESTRICT)

    # ---------------- Políticas de cancelación y reservas ----------------
    permite_cancelar = models.BooleanField(default=False)  # Si el negocio permite cancelar reservas
    tiempo_limite_cancelacion = models.PositiveIntegerField(
        default=60,  # Por ejemplo, 60 minutos antes de la atención
        help_text="Tiempo en minutos"
    )
    maximo_reservas_diarias = models.PositiveIntegerField(
        default=0,   # 0 puede interpretarse como 'ilimitado'
        help_text="0 para ilimitado"
    )

    # Representación legible en el admin y en consultas
    def __str__(self):
        return self.nombre



# ---------------- TABLA FILA ATENCIÓN ----------------
class FilaAtencion(models.Model):
    # ---------------- Campos principales ----------------
    fila_atencion_id = models.AutoField(primary_key=True)    # Identificador único de la fila de atención
    nombre = models.CharField(max_length=100)                # Nombre de la fila (ej: "Caja 1", "Consultorio A")
    cantidad_tickets = models.IntegerField()                 # Número total de tickets que puede emitir la fila
    visible = models.BooleanField(default=True)              # Indica si la fila es visible públicamente
    periodo_atencion = models.DurationField(null=True, blank=True)  # Duración estimada de atención por ticket
    apertura = models.TimeField()                            # Hora de apertura de la fila
    finalizacion = models.TimeField()                        # Hora de cierre de la fila
    numero_ticket_actual = models.IntegerField(default=0)    # Número del último ticket atendido
    negocio = models.ForeignKey(Negocio, on_delete=models.RESTRICT)  # Relación con el negocio al que pertenece la fila

    # Representación legible en el admin y consultas
    def __str__(self):
        return self.nombre




# ---------------- TABLA TICKET ----------------
class Ticket(models.Model):
    # ---------------- Estados posibles del ticket ----------------
    ESTADO_CHOICES = [
        ('pendiente', 'Pendiente'),    # Ticket generado pero aún no activo
        ('activo', 'Activo'),          # Ticket en turno de atención
        ('finalizado', 'Finalizado'),  # Ticket ya atendido
        ('cancelado', 'Cancelado'),    # Ticket cancelado por usuario o negocio
    ]
    
    # ---------------- Campos principales ----------------
    ticket_id = models.AutoField(primary_key=True)                   # Identificador único del ticket
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES) # Estado actual del ticket
    fecha_hora_registro = models.DateTimeField(auto_now_add=True)    # Fecha y hora en que se generó el ticket
    fecha_hora_atencion = models.DateTimeField(null=True, blank=True) # Momento en que el ticket fue atendido
    posicion = models.IntegerField(default=0)                        # Posición del ticket dentro de la fila
    fila_atencion = models.ForeignKey(FilaAtencion, on_delete=models.RESTRICT)  # Fila a la que pertenece el ticket

    def __str__(self):
        return f"Ticket {self.ticket_id}"




# ---------------- TABLA CANCELACIÓN POR USUARIO ----------------
class CancelacionUsuarioNegocio(models.Model):
    # Relación entre usuario y negocio para contabilizar cuántas veces canceló
    usuario = models.ForeignKey('usuarios.Usuario', on_delete=models.CASCADE)
    negocio = models.ForeignKey('negocios.Negocio', on_delete=models.CASCADE)
    cantidad_cancelaciones = models.PositiveIntegerField(default=0)  # Número de cancelaciones realizadas

    class Meta:
        # Garantiza que no se creen duplicados (un registro por usuario-negocio)
        unique_together = ('usuario', 'negocio')

    def __str__(self):
        return f"Cancelaciones de {self.usuario} en {self.negocio}: {self.cantidad_cancelaciones}"


# ---------------- TABLA RESERVAS DIARIAS POR USUARIO ----------------
class ReservaDiariaUsuario(models.Model):
    # Relación usuario-negocio para limitar o controlar reservas diarias
    usuario = models.ForeignKey('usuarios.Usuario', on_delete=models.CASCADE)
    negocio = models.ForeignKey('negocios.Negocio', on_delete=models.CASCADE)
    fecha = models.DateField()                                          # Día específico de la reserva
    cantidad_reservas = models.PositiveIntegerField(default=0)          # Número de reservas hechas ese día

    class Meta:
        # Evita duplicados: solo puede existir un registro por usuario-negocio-fecha
        unique_together = ('usuario', 'negocio', 'fecha')

    def __str__(self):
        return f"{self.usuario} - {self.negocio} ({self.fecha})"