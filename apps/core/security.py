"""Endurecimiento de la base en Supabase (se aplica solo en PostgreSQL)."""

import logging

from django.db import connections
from psycopg import sql

logger = logging.getLogger("security")

# Roles de la API REST de Supabase. No usamos la API: no deben poder leer nada.
API_ROLES = ("anon", "authenticated")


def tables_without_rls(cursor):
    cursor.execute(
        "SELECT tablename FROM pg_tables WHERE schemaname = 'public' AND NOT rowsecurity "
        "ORDER BY tablename"
    )
    return [row[0] for row in cursor.fetchall()]


def existing_api_roles(cursor):
    cursor.execute("SELECT rolname FROM pg_roles WHERE rolname = ANY(%s)", [list(API_ROLES)])
    return [row[0] for row in cursor.fetchall()]


def api_role_grants(cursor):
    cursor.execute(
        "SELECT grantee, table_name, privilege_type FROM information_schema.role_table_grants "
        "WHERE table_schema = 'public' AND grantee = ANY(%s)",
        [list(API_ROLES)],
    )
    return cursor.fetchall()


def secure_public_schema(using="default"):
    """RLS en todas las tablas de public y sin permisos para los roles de la API.

    El rol con el que se conecta Django es dueño de las tablas, así que RLS no lo afecta.
    """
    connection = connections[using]
    if connection.vendor != "postgresql":
        return
    with connection.cursor() as cursor:
        for table in tables_without_rls(cursor):
            cursor.execute(
                sql.SQL("ALTER TABLE public.{} ENABLE ROW LEVEL SECURITY").format(
                    sql.Identifier(table)
                )
            )
            logger.info("RLS activado en public.%s", table)
        roles = existing_api_roles(cursor)
        if not roles:  # Postgres que no es de Supabase (CI, local)
            return
        role_list = sql.SQL(", ").join(sql.Identifier(role) for role in roles)
        for kind in ("TABLES", "SEQUENCES", "FUNCTIONS"):
            cursor.execute(
                sql.SQL("REVOKE ALL ON ALL {} IN SCHEMA public FROM {}").format(
                    sql.SQL(kind), role_list
                )
            )
            cursor.execute(
                sql.SQL(
                    "ALTER DEFAULT PRIVILEGES IN SCHEMA public REVOKE ALL ON {} FROM {}"
                ).format(sql.SQL(kind), role_list)
            )
