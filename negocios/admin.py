from django.contrib import admin

from .models import Negocio, FilaAtencion, Ticket

admin.site.register(Negocio)
admin.site.register(FilaAtencion)
admin.site.register(Ticket)