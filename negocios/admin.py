from django.contrib import admin

from .models import Negocio, FilaAtencion, Ticket,CancelacionUsuarioNegocio, ReservaDiariaUsuario

# ---------------- Registro de modelos en el panel de administración ----------------
# Esto permite gestionarlos (CRUD) directamente desde el admin de Django.

admin.site.register(Negocio)                   # Gestión de negocios
admin.site.register(FilaAtencion)              # Filas de atención de cada negocio
admin.site.register(Ticket)                    # Tickets generados dentro de una fila
admin.site.register(CancelacionUsuarioNegocio) # Cancelaciones realizadas por usuarios en negocios
admin.site.register(ReservaDiariaUsuario)      # Reservas diarias que realiza un usuario