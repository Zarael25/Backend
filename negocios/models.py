from django.db import models


# TABLA NEGOCIO
class Negocio(models.Model):
    ESTADO_CHOICES = [
        ('en_revision', 'En Revisión'),
        ('verificado', 'Verificado'),
        ('rechazado', 'Rechazado'),
        ('oculto', 'Oculto'),
    ]
    
    CATEGORIA_CHOICES = [
        ('salud', 'Salud'),
        ('financiera', 'Financiera'),
        ('educacion', 'Educación'),
        ('tecnologia', 'Tecnología'),
        ('restaurantes', 'Restaurantes'),
        ('otros', 'Otros'),
    ]
    
    negocio_id = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=100)
    direccion = models.CharField(max_length=255)
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='en_revision')
    categoria = models.CharField(max_length=50, choices=CATEGORIA_CHOICES)
    doc_respaldo = models.BinaryField(null=True)
    num_referencia = models.CharField(max_length=50, unique=True)
    detalle = models.TextField()
    usuario = models.ForeignKey('usuarios.Usuario', on_delete=models.RESTRICT)

    def __str__(self):
        return self.nombre



#TABLA ATENCION

class FilaAtencion(models.Model):
    fila_atencion_id = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=100)
    cantidad_tickets = models.IntegerField()
    visible = models.BooleanField(default=True)
    periodo_atencion = models.DurationField(null=True, blank=True)
    apertura = models.TimeField()
    finalizacion = models.TimeField()
    numero_ticket_actual = models.IntegerField(default=0)
    permitir_cancelacion = models.BooleanField(default=False)
    negocio = models.ForeignKey(Negocio, on_delete=models.RESTRICT)

    def __str__(self):
        return self.nombre


#TABLA TICKET


class Ticket(models.Model):
    ESTADO_CHOICES = [
        ('pendiente', 'Pendiente'),
        ('activo', 'Activo'),
        ('finalizado', 'Finalizado'),
        ('cancelado', 'Cancelado'),
    ]
    
    ticket_id = models.AutoField(primary_key=True)
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES)
    fecha_hora_registro = models.DateTimeField(auto_now_add=True)
    fecha_hora_atencion = models.DateTimeField(null=True, blank=True)
    posicion = models.IntegerField(default=0)
    fila_atencion = models.ForeignKey(FilaAtencion, on_delete=models.RESTRICT)
    

    def __str__(self):
        return f"Ticket {self.ticket_id}"
