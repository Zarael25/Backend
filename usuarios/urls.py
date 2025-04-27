from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import UsuarioViewSet, AdminViewSet, UsuarioTicketViewSet

router = DefaultRouter()
router.register(r'usuarios', UsuarioViewSet)
router.register(r'admins', AdminViewSet)
router.register(r'usuario_tickets', UsuarioTicketViewSet)

urlpatterns = [
    path('', include(router.urls)),
    
]