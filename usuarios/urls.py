from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import UsuarioViewSet, AdminViewSet, UsuarioTicketViewSet, RegistroUsuarioViewSet

router = DefaultRouter()
router.register(r'usuarios', UsuarioViewSet)
router.register(r'admins', AdminViewSet)
router.register(r'usuario_tickets', UsuarioTicketViewSet)

# Registrar la ruta para el registro de usuarios
router.register(r'registro', RegistroUsuarioViewSet, basename='registro')


urlpatterns = [
    path('', include(router.urls)),
    
]