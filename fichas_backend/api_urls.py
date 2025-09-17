from django.urls import path, include
from rest_framework.routers import DefaultRouter

from usuarios.views import (
    UsuarioViewSet, UsuarioTicketViewSet, RegistroUsuarioViewSet,
    LoginUsuarioViewSet, LogoutUsuarioViewSet, PerfilUsuarioViewSet,
    LoginAdminViewSet
)
from negocios.views import NegocioViewSet, FilaAtencionViewSet, TicketViewSet
from rest_framework_simplejwt.views import TokenRefreshView



# Router por defecto de DRF: permite generar automáticamente las rutas
# para los ViewSets registrados.
router = DefaultRouter()

# ---------------- Rutas para USUARIOS ----------------
router.register(r'usuarios', UsuarioViewSet)                     # CRUD de usuarios
router.register(r'usuario_tickets', UsuarioTicketViewSet)        # Tickets generados por usuarios
router.register(r'registro', RegistroUsuarioViewSet, basename='registro')  # Registro de nuevos usuarios
router.register(r'login', LoginUsuarioViewSet, basename='login')           # Login de usuarios
router.register(r'perfil', PerfilUsuarioViewSet, basename='perfil')        # Perfil del usuario autenticado

# ---------------- Rutas para NEGOCIOS ----------------
router.register(r'negocios', NegocioViewSet, basename='negocios')  # CRUD de negocios
router.register(r'filas', FilaAtencionViewSet)                     # Filas de atención de cada negocio
router.register(r'tickets', TicketViewSet)                         # Tickets disponibles en una fila

# ---------------- Logout personalizado ----------------
# Se define como vista aparte porque no encaja directamente con router.register
logout_view = LogoutUsuarioViewSet.as_view({'post': 'logout'})

# ---------------- URL patterns finales ----------------
urlpatterns = [
    path('', include(router.urls)),                          # Todas las rutas del router
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),  # Refrescar tokens JWT
    path('logout/', logout_view, name='logout'),             # Logout de usuario
]