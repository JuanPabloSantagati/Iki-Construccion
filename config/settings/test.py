"""Settings para pytest. Usa DATABASE_URL si está definida (Postgres en CI), si no SQLite.

Los tests NUNCA leen el .env: así no pueden conectarse a la base ni al Storage de Supabase
que cada uno tiene configurados para desarrollo.
"""

import os
import tempfile

os.environ["DJANGO_READ_DOT_ENV"] = "0"

from .base import *  # noqa: E402, F403
from .base import env  # noqa: E402

DEBUG = False
SECRET_KEY = "test-insecure-solo-para-tests"  # noqa: S105
ALLOWED_HOSTS = ["testserver", "localhost"]

# Hash rápido: solo afecta a los tests.
PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]

EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"
CONTACT_NOTIFY_EMAIL = "avisos@iki.example"
CONTACT_MIN_SECONDS = 0  # los tests envían el formulario al instante

# Los tests nunca suben archivos a Supabase.
MEDIA_ROOT = tempfile.mkdtemp(prefix="iki-test-media-")
STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"},
}

ADMIN_URL = env("ADMIN_URL", default="gestion-test/")

# Los tests de admin usan force_login; los de 2FA lo vuelven a activar con override_settings.
ADMIN_REQUIRE_2FA = False

# Sirve los static desde las carpetas fuente, sin collectstatic.
WHITENOISE_USE_FINDERS = True
WHITENOISE_AUTOREFRESH = True
