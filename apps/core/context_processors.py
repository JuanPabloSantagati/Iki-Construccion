import logging

from django.db import DatabaseError
from django.utils.functional import SimpleLazyObject

from .models import SiteSettings

logger = logging.getLogger(__name__)


def _site_settings():
    # Solo lectura: si todavía no se cargó la configuración, no la crea en un GET.
    try:
        return SiteSettings.objects.filter(pk=1).first() or SiteSettings()
    except DatabaseError:
        # Sin base, el sitio (y sus páginas de error) se muestran sin datos de contacto.
        logger.exception("No se pudo leer SiteSettings")
        return SiteSettings()


def _footer_services():
    from apps.services.models import Service

    try:
        return list(Service.objects.published().only("title", "slug"))
    except DatabaseError:
        logger.exception("No se pudieron leer los servicios del footer")
        return []


def site_settings(request):
    """`site` y `footer_services` en todos los templates; se consultan solo si se usan."""
    return {
        "site": SimpleLazyObject(_site_settings),
        "footer_services": SimpleLazyObject(_footer_services),
    }
