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


def site_settings(request):
    """`site` en todos los templates; la consulta se hace solo si un template la usa."""
    return {"site": SimpleLazyObject(_site_settings)}
