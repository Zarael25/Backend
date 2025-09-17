from django.contrib import admin
from .models import Usuario, UsuarioTicket, LogUsuario

# ---------------- Registro simple de modelos ----------------
# Se registran para poder gestionarlos directamente desde el admin de Django.
admin.site.register(Usuario)        # Modelo principal de usuarios
admin.site.register(UsuarioTicket)  # Tickets asociados a usuarios

# ---------------- Registro personalizado con configuración extra ----------------
# Se usa el decorador @admin.register en lugar de admin.site.register
# para añadir opciones de visualización y filtrado al modelo LogUsuario.
@admin.register(LogUsuario)
class LogUsuarioAdmin(admin.ModelAdmin):
    # Columnas que se mostrarán en la tabla de listado del admin
    list_display = ('usuario', 'tipo_accion', 'fecha_hora', 'ruta_acceso', 'origen_conexion')
    
    # Filtros laterales en el panel para segmentar registros
    list_filter = ('tipo_accion', 'origen_conexion', 'fecha_hora')
    
    # Campos habilitados para la barra de búsqueda
    search_fields = ('usuario__username', 'ruta_acceso', 'tipo_accion')
    
    # Orden de los registros (por defecto descendente en la fecha)
    ordering = ('-fecha_hora',)