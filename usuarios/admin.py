from django.contrib import admin
from .models import Usuario, UsuarioTicket, LogUsuario

admin.site.register(Usuario)
admin.site.register(UsuarioTicket)

@admin.register(LogUsuario)
class LogUsuarioAdmin(admin.ModelAdmin):
    list_display = ('usuario', 'tipo_accion', 'fecha_hora', 'ruta_acceso', 'origen_conexion')
    list_filter = ('tipo_accion', 'origen_conexion', 'fecha_hora')
    search_fields = ('usuario__username', 'ruta_acceso', 'tipo_accion')
    ordering = ('-fecha_hora',)