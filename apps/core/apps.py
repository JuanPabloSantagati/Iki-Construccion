import mimetypes

from django.apps import AppConfig


class CoreConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.core"
    verbose_name = "Sitio"

    def ready(self):
        # Python en Windows no siempre conoce .webp: sin esto, django-storages sube las
        # imágenes como application/octet-stream y el bucket (limitado a image/webp) las rechaza.
        mimetypes.add_type("image/webp", ".webp")
