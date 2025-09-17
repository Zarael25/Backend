from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager, Group, Permission
from django.utils import timezone
from datetime import timedelta
from django.conf import settings

# ---------------- TABLA MANAGER PERSONALIZADO USUARIO ----------------
class UsuarioManager(BaseUserManager):
    # ---------------- Crear usuario normal ----------------
    def create_user(self, username, correo, password=None, **extra_fields):
        # Validaciones básicas obligatorias
        if not username:
            raise ValueError('El nombre de usuario es obligatorio.')
        if not correo:
            raise ValueError('El correo electrónico es obligatorio.')
        
        # Normaliza el correo (ej: convierte dominio a minúsculas)
        correo = self.normalize_email(correo)

        # Crea la instancia del usuario con los datos recibidos
        user = self.model(username=username, correo=correo, **extra_fields)

        # Encripta la contraseña antes de guardarla en la BD
        user.set_password(password)

        # Guarda el usuario en la base de datos activa (_db)
        user.save(using=self._db)
        return user

    # ---------------- Crear superusuario ----------------
    def create_superuser(self, username, correo, password=None, **extra_fields):
        # Se establecen valores por defecto para un superusuario
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('estado', 'activo')
        extra_fields.setdefault('tipo_usuario', 'admin')  # Rol de administrador

        # Validaciones: deben ser True obligatoriamente
        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser debe tener is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser debe tener is_superuser=True.')

        # Reutiliza create_user para crear el superusuario con privilegios
        return self.create_user(username, correo, password, **extra_fields)




# ---------------- TABLA MODELO USUARIO ----------------
class Usuario(AbstractBaseUser, PermissionsMixin):
    # ---------------- Opciones de estado ----------------
    ESTADO_CHOICES = [
        ('activo', 'Activo'),          # Usuario con acceso normal
        ('suspendido', 'Suspendido'),  # Usuario bloqueado temporalmente
    ]
    
    # ---------------- Tipos de suscripción ----------------
    SUSCRIPCION_CHOICES = [
        ('free', 'Free'),  # Usuario gratuito
        ('pro', 'Pro'),    # Usuario con plan de pago
    ]
    
    # ---------------- Tipos de usuario ----------------
    TIPO_USUARIO_CHOICES = [
        ('usuario', 'Usuario'),          # Usuario normal
        ('admin', 'Administrador'),      # Usuario con rol administrativo
    ]

    # ---------------- Campos principales ----------------
    usuario_id = models.AutoField(primary_key=True)           # Identificador único
    username = models.CharField(max_length=50, unique=True)   # Nombre de usuario único
    correo = models.EmailField(max_length=100, unique=True)   # Correo único
    nombre = models.CharField(max_length=100)                 # Nombre completo
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='activo')  # Estado actual
    suscripcion = models.CharField(max_length=10, choices=SUSCRIPCION_CHOICES, default='free')  # Plan actual
    tipo_usuario = models.CharField(max_length=20, choices=TIPO_USUARIO_CHOICES, default='usuario')  # Rol
    suspendido_contador = models.PositiveIntegerField(default=0)  # Número de veces suspendido
    suspendido_hasta = models.DateTimeField(null=True, blank=True) # Fecha límite de suspensión (si aplica)

    # ---------------- Campos de control Django ----------------
    is_active = models.BooleanField(default=True)     # Indica si puede autenticarse
    is_staff = models.BooleanField(default=False)     # Permite acceso al admin de Django
    is_superuser = models.BooleanField(default=False) # Permite todos los permisos

    # ---------------- Relaciones con grupos y permisos ----------------
    groups = models.ManyToManyField(
        Group,
        related_name='usuario_set',     # Se cambia el related_name para evitar conflictos con el modelo default
        blank=True
    )
    user_permissions = models.ManyToManyField(
        Permission,
        related_name='usuario_permissions_set',  # Idem: nombre distinto para evitar conflictos
        blank=True
    )

    # ---------------- Manager personalizado ----------------
    objects = UsuarioManager()

    # ---------------- Configuración de autenticación ----------------
    USERNAME_FIELD = 'username'   # Campo usado para login
    REQUIRED_FIELDS = ['correo']  # Campos adicionales requeridos al crear superusuarios

    def __str__(self):
        return self.username

    @property
    def id(self):
        """ Alias para devolver usuario_id como 'id' """
        return self.usuario_id
    
    @property
    def esta_suspendido(self):
        """
        Verifica si el usuario está actualmente suspendido por cancelación de tickets.
        - Si la fecha de suspensión aún no expira → sigue suspendido.
        - Si ya pasó la fecha de suspensión → lo reactiva automáticamente.
        """
        if self.estado == 'suspendido':
            if self.suspendido_hasta and timezone.now() < self.suspendido_hasta:
                return True
            elif self.suspendido_hasta and timezone.now() >= self.suspendido_hasta:
                # Reactiva automáticamente al usuario
                self.estado = 'activo'
                self.suspendido_hasta = None
                self.save(update_fields=['estado', 'suspendido_hasta'])
                return False
        return False
    



# ---------------- TABLA USUARIO-TICKET ----------------
class UsuarioTicket(models.Model):
    # Relación con el usuario que generó o posee el ticket
    usuario = models.ForeignKey('usuarios.Usuario', on_delete=models.RESTRICT)
    
    # Relación con el ticket asociado
    ticket = models.ForeignKey('negocios.Ticket', on_delete=models.RESTRICT)

    class Meta:
        # Garantiza que un usuario no tenga duplicado el mismo ticket
        unique_together = ['usuario', 'ticket']
        
    def __str__(self):
        # Representación legible: "Usuario X - Ticket Y"
        return f"Usuario {self.usuario.username} - Ticket {self.ticket.ticket_id}"




# ---------------- TABLA LOG USUARIO ----------------
class LogUsuario(models.Model):
    # ---------------- Campos principales ----------------
    fecha_hora = models.DateTimeField(auto_now_add=True)   # Momento exacto en que ocurrió la acción
    tipo_accion = models.CharField(max_length=100)         # Tipo de acción (ej: "inicio de sesión", "cerrar sesión", "generar ticket")
    ruta_acceso = models.CharField(max_length=255)         # Ruta o endpoint accedido
    origen_conexion = models.CharField(max_length=50)      # Medio de conexión: "web", "móvil", etc.

    # Relación con el usuario que realizó la acción.
    # SET_NULL → si el usuario se elimina, los logs no se pierden (quedan con usuario=None).
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)

    # ---------------- Representación legible ----------------
    def __str__(self):
        return f"{self.usuario} - {self.tipo_accion} - {self.fecha_hora}"