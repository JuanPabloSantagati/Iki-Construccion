import mimetypes

from django.apps import AppConfig
from django.db.models.signals import post_migrate


def _after_migrate(sender, using, **kwargs):
    from .roles import sync_groups
    from .security import secure_public_schema

    secure_public_schema(using)
    sync_groups(using=using)


class CoreConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.core"
    verbose_name = "Sitio"

    def ready(self):
        # Python en Windows no siempre conoce .webp: sin esto, django-storages sube las
        # imágenes como application/octet-stream y el bucket (limitado a image/webp) las rechaza.
        mimetypes.add_type("image/webp", ".webp")
        # Una sola vez por migrate (todas las tablas ya existen cuando se emite).
        post_migrate.connect(_after_migrate, sender=self, dispatch_uid="iki-after-migrate")
