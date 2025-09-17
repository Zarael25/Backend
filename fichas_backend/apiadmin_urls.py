from django.urls import path, include
from rest_framework.routers import DefaultRouter
from usuarios.views import LoginAdminViewSet, UsuarioAdminViewSet
from negocios.views import NegocioAdminViewSet
from rest_framework_simplejwt.views import TokenRefreshView

router = DefaultRouter()

# ---------------- Endpoints exclusivos para ADMIN ----------------
router.register(r'adminlogin', LoginAdminViewSet, basename='login_admin')     # Login de administradores
router.register(r'usuarios', UsuarioAdminViewSet, basename='usuarios_admin')  # Gestión de usuarios (solo admin)
router.register(r'negocios', NegocioAdminViewSet, basename='negocios_admin')  # Gestión de negocios (solo admin)

# ---------------- URL patterns finales ----------------
urlpatterns = [
    path('', include(router.urls)),                          # Rutas generadas por el router
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),  # Refrescar tokens JWT
]