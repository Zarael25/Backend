from django.core.management.base import BaseCommand
from negocios.models import Ticket

class Command(BaseCommand):
    help = 'Finaliza tickets activos con fecha_hora_atencion nula'

    def handle(self, *args, **kwargs):
        tickets_null = Ticket.objects.filter(
            estado='activo',
            fecha_hora_atencion__isnull=True
        )
        cantidad = tickets_null.count()
        tickets_null.update(estado='finalizado')

        self.stdout.write(f'Tickets finalizados con fecha_hora_atencion nula: {cantidad}')