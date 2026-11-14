from django.contrib.admin.apps import AdminConfig


class IkiAdminConfig(AdminConfig):
    """Reemplaza el admin por defecto por IkiAdminSite (2FA obligatorio)."""

    default_site = "apps.core.admin_site.IkiAdminSite"
