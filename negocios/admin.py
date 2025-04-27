from django.contrib import admin

from .models import Negocio, Atencion, Ticket

admin.site.register(Negocio)
admin.site.register(Atencion)
admin.site.register(Ticket)