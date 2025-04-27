from django.db import models


# TABLA USUARIO
class Usuario(models.Model):
    
    ESTADO_CHOICES = [
        ('activo', 'Activo'),
        ('suspendido', 'Suspendido'),
    ]
    
    SUSCRIPCION_CHOICES = [
        ('free', 'Free'),
        ('pro', 'Pro'),
    ]
    
    usuario_id = models.AutoField(primary_key=True)
    username = models.CharField(max_length=50, unique=True)
    password = models.CharField(max_length=255)
    nombre = models.CharField(max_length=100)
    correo = models.EmailField(max_length=100, unique=True)
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='activo')
    suscripcion = models.CharField(max_length=10, choices=SUSCRIPCION_CHOICES, default='free')

    def __str__(self):
        return self.username



# TABLA ADMIN
class Admin(models.Model):
    PERMISOS_CHOICES = [
        ('lectura', 'Lectura'),
        ('escritura', 'Escritura'),
        ('administrador', 'Administrador'),
    ]
    
    admin_id = models.AutoField(primary_key=True)
    username = models.CharField(max_length=50, unique=True)
    password = models.CharField(max_length=255)
    nombre = models.CharField(max_length=100)
    permisos = models.CharField(max_length=50, choices=PERMISOS_CHOICES)
    estado = models.CharField(max_length=20, choices=[('activo', 'Activo'), ('inactivo', 'Inactivo')], default='activo')

    def __str__(self):
        return self.username
    


class UsuarioTicket(models.Model):
    usuario = models.ForeignKey('usuarios.Usuario', on_delete=models.RESTRICT)
    ticket = models.ForeignKey('negocios.Ticket', on_delete=models.RESTRICT)

    class Meta:
        unique_together = ['usuario', 'ticket']
    
    def __str__(self):
        return f"Usuario {self.usuario.username} - Ticket {self.ticket.ticket_id}"
