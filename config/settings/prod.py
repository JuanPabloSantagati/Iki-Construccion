"""Settings de producción.

El arranque FALLA (ImproperlyConfigured) si falta una variable obligatoria,
si DEBUG=True o si la configuración es insegura. Mejor no arrancar que arrancar mal.
"""

import tempfile
from pathlib import Path

from django.core.exceptions import ImproperlyConfigured

from .base import *  # noqa: F403
from .base import ADMIN_URL, DATABASES, STORAGES, env

if env.bool("DEBUG", default=False):
    raise ImproperlyConfigured("DEBUG=True no está permitido en producción.")
DEBUG = False

SECRET_KEY = env("SECRET_KEY", default="")
if not SECRET_KEY:
    raise ImproperlyConfigured("Falta la variable de entorno SECRET_KEY.")
if len(SECRET_KEY) < 50 or SECRET_KEY.startswith(("django-insecure", "dev-insecure", "test-")):
    raise ImproperlyConfigured("SECRET_KEY de producción inválida: generá una nueva y larga.")

if not env.bool("ADMIN_REQUIRE_2FA", default=True):
    raise ImproperlyConfigured("ADMIN_REQUIRE_2FA=False no está permitido en producción.")

# Obligatoria en prod: el default de base.py (público en el repo) no debe llegar a producción.
if not env("ADMIN_URL", default=""):
    raise ImproperlyConfigured("Falta la variable de entorno ADMIN_URL.")
if ADMIN_URL.strip("/").lower() in {"admin", "administrador", "login", "wp-admin"}:
    raise ImproperlyConfigured("ADMIN_URL es demasiado predecible.")

# Sin esto los mails de consultas nuevas irían a la consola y nadie se enteraría.
for _name in ("EMAIL_URL", "CONTACT_NOTIFY_EMAIL"):
    if not env(_name, default=""):
        raise ImproperlyConfigured(f"Falta la variable de entorno {_name}.")

if not env("DATABASE_URL", default=""):
    raise ImproperlyConfigured("DATABASE_URL es obligatoria en producción.")
DATABASES["default"].setdefault("OPTIONS", {})["sslmode"] = "require"

ALLOWED_HOSTS = env.list("ALLOWED_HOSTS", default=[])
CSRF_TRUSTED_ORIGINS = env.list("CSRF_TRUSTED_ORIGINS", default=[])
if not ALLOWED_HOSTS or "*" in ALLOWED_HOSTS:
    raise ImproperlyConfigured("ALLOWED_HOSTS debe listar los dominios reales (sin '*').")
if not CSRF_TRUSTED_ORIGINS:
    raise ImproperlyConfigured("Falta la variable de entorno CSRF_TRUSTED_ORIGINS.")


# --- Caché ---------------------------------------------------------------------
# El límite de envíos del formulario cuenta en la caché: con la de memoria (por proceso) cada
# worker de gunicorn llevaría su propia cuenta. En disco la comparten todos los de un servidor.
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.filebased.FileBasedCache",
        "LOCATION": env("CACHE_DIR", default=str(Path(tempfile.gettempdir()) / "iki-cache")),
    }
}


# --- HTTPS ---------------------------------------------------------------------

SECURE_SSL_REDIRECT = True
# Solo activar detrás de un proxy que reescriba X-Forwarded-Proto (Render, Railway, etc.).
# Sin proxy, aceptar este header permitiría a un cliente falsear HTTPS.
if env.bool("TRUST_PROXY_SSL_HEADER", default=False):
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

SECURE_HSTS_SECONDS = env.int("SECURE_HSTS_SECONDS", default=31536000)
SECURE_HSTS_INCLUDE_SUBDOMAINS = env.bool("SECURE_HSTS_INCLUDE_SUBDOMAINS", default=True)
SECURE_HSTS_PRELOAD = env.bool("SECURE_HSTS_PRELOAD", default=True)

SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True


# --- Estáticos -----------------------------------------------------------------

STORAGES["staticfiles"] = {
    "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
}
