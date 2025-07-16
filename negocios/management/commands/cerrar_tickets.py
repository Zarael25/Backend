from django.core.management.base import BaseCommand
from django.utils import timezone
from negocios.models import FilaAtencion, Ticket

class Command(BaseCommand):
    help = 'Finaliza tickets vencidos y actualiza correctamente el número de ticket actual por fila'

    def handle(self, *args, **kwargs):
        ahora = timezone.localtime()
        
        # 1. Finalizamos TODOS los tickets vencidos (fecha_hora_atencion en el pasado)
        tickets_vencidos = Ticket.objects.filter(
            estado='activo',
            fecha_hora_atencion__lt=ahora
        )
        total_vencidos = tickets_vencidos.count()
        tickets_vencidos.update(estado='finalizado')
        self.stdout.write(f"Tickets finalizados automáticamente: {total_vencidos}")

        # 2. Procesamos cada fila individualmente
        filas = FilaAtencion.objects.all()
        for fila in filas:
            # Resetear contador primero
            fila.numero_ticket_actual = 0

            # Recontar los tickets activos válidos (los que aún están pendientes en el futuro)
            tickets_futuros = Ticket.objects.filter(
                fila_atencion=fila,
                estado='activo',
                fecha_hora_atencion__gte=ahora
            ).count()

            fila.numero_ticket_actual = tickets_futuros
            fila.save()

            self.stdout.write(f"Fila '{fila.nombre}': contador actualizado a {tickets_futuros}")