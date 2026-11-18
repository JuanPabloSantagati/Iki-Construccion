"""IP real del cliente, también detrás de un proxy (hosting)."""

from django.conf import settings


def get_client_ip(request):
    """Con TRUSTED_PROXY_COUNT=N toma la N-ésima IP desde la derecha de X-Forwarded-For.

    Cada proxy confiable agrega al final la IP que vio; lo que el cliente escriba a la izquierda
    se ignora, así no puede falsear su IP. Con 0 (default, sin proxy) usa REMOTE_ADDR.
    """
    count = settings.TRUSTED_PROXY_COUNT
    if count:
        forwarded = request.META.get("HTTP_X_FORWARDED_FOR", "")
        parts = [part.strip() for part in forwarded.split(",") if part.strip()]
        if len(parts) >= count:
            return parts[-count]
    return request.META.get("REMOTE_ADDR", "")
