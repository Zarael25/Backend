from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import NegocioViewSet, AtencionViewSet, TicketViewSet

router = DefaultRouter()
router.register(r'negocios', NegocioViewSet)
router.register(r'atenciones', AtencionViewSet)
router.register(r'tickets', TicketViewSet)

urlpatterns = [
    path('', include(router.urls)),
]