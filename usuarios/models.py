from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager, Group, Permission

# -------------------------------
# MANAGER PERSONALIZADO USUARIO
# -------------------------------
class UsuarioManager(BaseUserManager):
    def create_user(self, username, correo, password=None, **extra_fields):
        if not username:
            raise ValueError('El nombre de usuario es obligatorio.')
        if not correo:
            raise ValueError('El correo electrónico es obligatorio.')
        
        correo = self.normalize_email(correo)
        user = self.model(username=username, correo=correo, **extra_fields)
        user.set_password(password)  # Encripta la contraseña
        user.save(using=self._db)
        return user

    def create_superuser(self, username, correo, password=None, **extra_fields):
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('estado', 'activo')
        extra_fields.setdefault('tipo_usuario', 'admin')  # o como prefieras llamarlo

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser debe tener is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser debe tener is_superuser=True.')

        return self.create_user(username, correo, password, **extra_fields)




# -------------------------------
# MODELO USUARIO
# -------------------------------
class Usuario(AbstractBaseUser, PermissionsMixin):
    ESTADO_CHOICES = [
        ('activo', 'Activo'),
        ('suspendido', 'Suspendido'),
    ]
    
    SUSCRIPCION_CHOICES = [
        ('free', 'Free'),
        ('pro', 'Pro'),
    ]
    
    TIPO_USUARIO_CHOICES = [
        ('usuario', 'Usuario'),
        ('admin', 'Administrador'),
    ]

    usuario_id = models.AutoField(primary_key=True)
    username = models.CharField(max_length=50, unique=True)
    correo = models.EmailField(max_length=100, unique=True)
    nombre = models.CharField(max_length=100)
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='activo')
    suscripcion = models.CharField(max_length=10, choices=SUSCRIPCION_CHOICES, default='free')
    tipo_usuario = models.CharField(max_length=20, choices=TIPO_USUARIO_CHOICES, default='usuario')
    
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)

    groups = models.ManyToManyField(
        Group,
        related_name='usuario_set',
        blank=True
    )
    user_permissions = models.ManyToManyField(
        Permission,
        related_name='usuario_permissions_set',
        blank=True
    )


    objects = UsuarioManager()

    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['correo']

    def __str__(self):
        return self.username

    @property
    def id(self):
        return self.usuario_id
    

""""
# -------------------------------
# MANAGER PERSONALIZADO ADMIN
# -------------------------------
class AdminManager(BaseUserManager):
    def create_user(self, username, nombre, password=None, **extra_fields):
        if not username:
            raise ValueError('El nombre de usuario es obligatorio.')
        
        user = self.model(username=username, nombre=nombre, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, username, nombre, password=None, **extra_fields):
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_active', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser debe tener is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser debe tener is_superuser=True.')
        if extra_fields.get('is_active') is not True:
            raise ValueError('Superuser debe tener is_active=True.')

        return self.create_user(username, nombre, password, **extra_fields)



# -------------------------------
# MODELO ADMIN
# -------------------------------
class Admin(AbstractBaseUser, PermissionsMixin):
    PERMISOS_CHOICES = [
        ('lectura', 'Lectura'),
        ('escritura', 'Escritura'),
        ('administrador', 'Administrador'),
    ]

    ESTADO_CHOICES = [
        ('activo', 'Activo'),
        ('inactivo', 'Inactivo'),
    ]
    
    admin_id = models.AutoField(primary_key=True)
    username = models.CharField(max_length=50, unique=True)
    nombre = models.CharField(max_length=100)
    permisos = models.CharField(max_length=50, choices=PERMISOS_CHOICES)
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='activo')
    
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=True)
    is_superuser = models.BooleanField(default=False)


    groups = models.ManyToManyField(
        Group,
        related_name='admin_set',  # <- diferente a 'usuario_set'
        blank=True
    )
    user_permissions = models.ManyToManyField(
        Permission,
        related_name='admin_permissions_set',  # <- diferente a 'usuario_permissions_set'
        blank=True
    )



    objects = AdminManager()

    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['nombre']

    def __str__(self):
        return self.username

    @property
    def id(self):
        return self.admin_id
"""



# -------------------------------
# MODELO USUARIO-TICKET
# -------------------------------
class UsuarioTicket(models.Model):
    usuario = models.ForeignKey('usuarios.Usuario', on_delete=models.RESTRICT)
    
    ticket = models.ForeignKey('negocios.Ticket', on_delete=models.RESTRICT)

    class Meta:
        unique_together = ['usuario', 'ticket']
        
    
    def __str__(self):
        return f"Usuario {self.usuario.username} - Ticket {self.ticket.ticket_id}"
