import hashlib

from django.conf import settings
from django.core.cache import cache

WINDOW_SECONDS = 60 * 60


def _key(request):
    # La IP no se guarda en claro ni en la caché: solo un hash con la SECRET_KEY.
    ip = request.META.get("REMOTE_ADDR", "")
    digest = hashlib.sha256(f"{settings.SECRET_KEY}:{ip}".encode()).hexdigest()[:32]
    return f"contact-rl:{digest}"


def is_limited(request):
    return cache.get(_key(request), 0) >= settings.CONTACT_RATE_LIMIT


def register_hit(request):
    key = _key(request)
    if not cache.add(key, 1, WINDOW_SECONDS):
        try:
            cache.incr(key)
        except ValueError:  # expiró entre add() e incr()
            cache.add(key, 1, WINDOW_SECONDS)
