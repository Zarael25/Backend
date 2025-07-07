from django.contrib import admin

from .models import Negocio, FilaAtencion, Ticket,CancelacionUsuarioNegocio, ReservaDiariaUsuario

admin.site.register(Negocio)
admin.site.register(FilaAtencion)
admin.site.register(Ticket)
admin.site.register(CancelacionUsuarioNegocio)
admin.site.register(ReservaDiariaUsuario)
