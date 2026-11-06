"""Settings para pytest. Usa DATABASE_URL si está definida (Postgres en CI), si no SQLite."""

import tempfile

from .base import *  # noqa: F403
from .base import env

DEBUG = False
SECRET_KEY = "test-insecure-solo-para-tests"  # noqa: S105
ALLOWED_HOSTS = ["testserver", "localhost"]

# Hash rápido: solo afecta a los tests.
PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]

EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"

# Los tests nunca suben archivos a Supabase.
MEDIA_ROOT = tempfile.mkdtemp(prefix="iki-test-media-")
STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"},
}

ADMIN_URL = env("ADMIN_URL", default="gestion-test/")

# Sirve los static desde las carpetas fuente, sin collectstatic.
WHITENOISE_USE_FINDERS = True
WHITENOISE_AUTOREFRESH = True
