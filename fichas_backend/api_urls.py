# fichas_backend/api_urls.py

from django.urls import path, include
from rest_framework.routers import DefaultRouter

from usuarios.views import (
    UsuarioViewSet, UsuarioTicketViewSet, RegistroUsuarioViewSet,
    LoginUsuarioViewSet, LogoutUsuarioViewSet, PerfilUsuarioViewSet
)
from negocios.views import NegocioViewSet, AtencionViewSet, TicketViewSet
from rest_framework_simplejwt.views import TokenRefreshView

router = DefaultRouter()

# Usuarios
router.register(r'usuarios', UsuarioViewSet)
router.register(r'usuario_tickets', UsuarioTicketViewSet)
router.register(r'registro', RegistroUsuarioViewSet, basename='registro')
router.register(r'login', LoginUsuarioViewSet, basename='login')
router.register(r'perfil', PerfilUsuarioViewSet, basename='perfil')

# Negocios
router.register(r'negocios', NegocioViewSet, basename='negocios')
router.register(r'atenciones', AtencionViewSet)
router.register(r'tickets', TicketViewSet)

# Logout personalizado
logout_view = LogoutUsuarioViewSet.as_view({'post': 'logout'})

urlpatterns = [
    path('', include(router.urls)),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('logout/', logout_view, name='logout'),
]