from django.contrib import admin
from .models import Usuario, Admin, UsuarioTicket

admin.site.register(Usuario)
admin.site.register(Admin)
admin.site.register(UsuarioTicket)