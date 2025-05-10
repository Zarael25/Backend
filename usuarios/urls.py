from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import UsuarioViewSet, AdminViewSet, UsuarioTicketViewSet, RegistroUsuarioViewSet, LoginUsuarioViewSet

router = DefaultRouter()
router.register(r'usuarios', UsuarioViewSet)
router.register(r'admins', AdminViewSet)
router.register(r'usuario_tickets', UsuarioTicketViewSet)


router.register(r'registro', RegistroUsuarioViewSet, basename='registro')
router.register(r'login', LoginUsuarioViewSet, basename='login-usuario')

urlpatterns = [
    path('', include(router.urls)),
    
]