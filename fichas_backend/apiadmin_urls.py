from django.urls import path, include
from rest_framework.routers import DefaultRouter
from usuarios.views import LoginAdminViewSet, UsuarioAdminViewSet
from negocios.views import NegocioAdminViewSet
from rest_framework_simplejwt.views import TokenRefreshView

router = DefaultRouter()

# Endpoints que solo un administrador puede usar
router.register(r'adminlogin', LoginAdminViewSet, basename='login_admin')
router.register(r'usuarios', UsuarioAdminViewSet, basename='usuarios_admin')  
router.register(r'negocios', NegocioAdminViewSet, basename='negocios_admin')

urlpatterns = [
    path('', include(router.urls)),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
]

