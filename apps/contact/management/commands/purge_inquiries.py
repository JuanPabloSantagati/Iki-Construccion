from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.contact.models import Inquiry

ANONYMIZED = {
    "name": "(anonimizada)",
    "email": "anonimizada@iki.invalid",
    "phone": "",
    "location": "",
    "message": "",
}


class Command(BaseCommand):
    help = (
        "Ley 25.326: anonimiza (o borra con --delete) las consultas más viejas que --days. "
        "Pensado para correr periódicamente (ej: una vez por mes)."
    )

    def add_arguments(self, parser):
        parser.add_argument("--days", type=int, default=730, help="Antigüedad en días (730).")
        parser.add_argument("--delete", action="store_true", help="Borra en vez de anonimizar.")
        parser.add_argument("--dry-run", action="store_true", help="Solo informa cuántas son.")

    def handle(self, *args, days, delete, dry_run, **options):
        cutoff = timezone.now() - timedelta(days=days)
        old = Inquiry.objects.filter(created_at__lt=cutoff)
        if not delete:
            old = old.filter(anonymized_at__isnull=True)
        count = old.count()
        action, done = ("borrar", "borradas") if delete else ("anonimizar", "anonimizadas")
        if dry_run:
            self.stdout.write(f"Consultas para {action}: {count} (anteriores a {cutoff:%d/%m/%Y}).")
            return
        if delete:
            old.delete()
        else:
            old.update(**ANONYMIZED, anonymized_at=timezone.now())
        self.stdout.write(self.style.SUCCESS(f"Consultas {done}: {count}."))
