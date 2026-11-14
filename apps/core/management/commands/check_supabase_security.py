from django.core.management.base import BaseCommand, CommandError
from django.db import connection

from apps.core.security import api_role_grants, tables_without_rls


class Command(BaseCommand):
    help = "Verifica RLS en todas las tablas de public y que anon/authenticated no tengan permisos."

    def handle(self, *args, **options):
        if connection.vendor != "postgresql":
            raise CommandError("Solo aplica a PostgreSQL (Supabase).")
        with connection.cursor() as cursor:
            missing = tables_without_rls(cursor)
            grants = api_role_grants(cursor)
        for table in missing:
            self.stderr.write(f"Sin RLS: public.{table}")
        for grantee, table, privilege in grants:
            self.stderr.write(f"Permiso de {grantee}: {privilege} en public.{table}")
        if missing or grants:
            raise CommandError("La base NO está protegida. Corré `manage.py migrate` de nuevo.")
        self.stdout.write(
            self.style.SUCCESS("OK: RLS en todas las tablas y sin permisos para la API.")
        )
