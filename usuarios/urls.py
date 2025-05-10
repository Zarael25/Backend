from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import UsuarioViewSet, AdminViewSet, UsuarioTicketViewSet, RegistroUsuarioViewSet, LoginUsuarioViewSet, LogoutUsuarioViewSet
from rest_framework_simplejwt.views import TokenRefreshView

router = DefaultRouter()
router.register(r'usuarios', UsuarioViewSet)
router.register(r'admins', AdminViewSet)
router.register(r'usuario_tickets', UsuarioTicketViewSet)


router.register(r'registro', RegistroUsuarioViewSet, basename='registro')
router.register(r'login', LoginUsuarioViewSet, basename='login-usuario')

logout_view = LogoutUsuarioViewSet.as_view({'post': 'logout'})

urlpatterns = [
    path('', include(router.urls)),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('logout/', logout_view, name='logout-usuario'),
]