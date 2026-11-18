"""Settings comunes a todos los entornos.

Los valores sensibles vienen SIEMPRE de variables de entorno (ver `.env.example`).
Cada entorno (`dev`, `test`, `prod`) importa este módulo y ajusta lo propio.
"""

import os
from pathlib import Path

import environ
from botocore.config import Config as BotoConfig
from django.core.exceptions import ImproperlyConfigured

BASE_DIR = Path(__file__).resolve().parent.parent.parent

env = environ.Env()

# El .env local solo completa variables que no estén ya definidas en el entorno.
# Los tests lo desactivan con DJANGO_READ_DOT_ENV=0 para no depender del .env de cada uno.
if os.environ.get("DJANGO_READ_DOT_ENV", "1") == "1" and (BASE_DIR / ".env").exists():
    env.read_env(BASE_DIR / ".env")


# --- Aplicaciones --------------------------------------------------------------

INSTALLED_APPS = [
    "apps.core.admin_config.IkiAdminConfig",  # admin con 2FA obligatorio (core/admin_site.py)
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "storages",
    "django_otp",
    "django_otp.plugins.otp_totp",
    "axes",
    "apps.core",
    "apps.projects",
    "apps.services",
    "apps.contact",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "apps.core.middleware.PermissionsPolicyMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django_otp.middleware.OTPMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    # Siempre al final: bloquea los intentos de login después del límite.
    "axes.middleware.AxesMiddleware",
]

ROOT_URLCONF = "config.urls"
WSGI_APPLICATION = "config.wsgi.application"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "apps.core.context_processors.site_settings",
            ],
        },
    },
]


# --- Base de datos -------------------------------------------------------------
# Supabase: usar el pooler en modo *session* (puerto 5432) o la conexión directa.
# El modo *transaction* (6543) requiere DB_DISABLE_SERVER_SIDE_CURSORS=True.

# Vacía o ausente → SQLite local (solo útil en desarrollo; prod exige DATABASE_URL).
DATABASES = {
    "default": environ.Env.db_url_config(
        env("DATABASE_URL", default="") or f"sqlite:///{BASE_DIR / 'db.sqlite3'}"
    ),
}
DATABASES["default"]["CONN_MAX_AGE"] = env.int("DB_CONN_MAX_AGE", default=60)
DATABASES["default"]["CONN_HEALTH_CHECKS"] = True
DATABASES["default"]["DISABLE_SERVER_SIDE_CURSORS"] = env.bool(
    "DB_DISABLE_SERVER_SIDE_CURSORS", default=False
)

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"


# --- Autenticación -------------------------------------------------------------

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
        "OPTIONS": {"min_length": 12},
    },
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

AUTHENTICATION_BACKENDS = [
    "axes.backends.AxesStandaloneBackend",  # primero: corta el login si está bloqueado
    "django.contrib.auth.backends.ModelBackend",
]

# 2FA (TOTP) obligatorio para entrar al admin. Solo se puede apagar en desarrollo/tests;
# en producción el arranque falla si ADMIN_REQUIRE_2FA=False.
ADMIN_REQUIRE_2FA = env.bool("ADMIN_REQUIRE_2FA", default=True)
OTP_TOTP_ISSUER = "IKI Web"

# django-axes: 5 intentos fallidos por usuario + IP → bloqueo de 1 hora.
AXES_FAILURE_LIMIT = 5
AXES_COOLOFF_TIME = 1  # horas
AXES_LOCKOUT_PARAMETERS = [["username", "ip_address"]]
AXES_RESET_ON_SUCCESS = True
AXES_DISABLE_ACCESS_LOG = True  # no guardar un registro de cada login exitoso (datos mínimos)
AXES_LOCKOUT_TEMPLATE = "axes_locked.html"
# Detrás de un proxy (hosting) hay que configurar AXES_CLIENT_IP_CALLABLE para tomar la IP real.

# Sesión del admin: 12 horas.
SESSION_COOKIE_AGE = 12 * 60 * 60

# Ruta del admin: nunca /admin/. Debe terminar en "/".
ADMIN_URL = env("ADMIN_URL", default="gestion-iki/")
if not ADMIN_URL.endswith("/") or ADMIN_URL.startswith("/"):
    raise ImproperlyConfigured("ADMIN_URL debe tener la forma 'algo/' (sin barra inicial).")


# --- Internacionalización ------------------------------------------------------

LANGUAGE_CODE = "es-ar"
TIME_ZONE = "America/Argentina/Buenos_Aires"
USE_I18N = True
USE_TZ = True


# --- Archivos estáticos y media ------------------------------------------------

STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_DIRS = [BASE_DIR / "static"]

MEDIA_URL = "media/"
MEDIA_ROOT = BASE_DIR / "media"

# Límite de subida en memoria; los archivos más grandes van a disco temporal.
DATA_UPLOAD_MAX_MEMORY_SIZE = 5 * 1024 * 1024
FILE_UPLOAD_MAX_MEMORY_SIZE = 5 * 1024 * 1024

# MEDIA_STORAGE=local     → disco (MEDIA_ROOT). Default, sin credenciales.
# MEDIA_STORAGE=supabase  → Supabase Storage vía API S3. Requiere las credenciales S3.
MEDIA_STORAGE = env("MEDIA_STORAGE", default="local")


def _required(name):
    """Variable obligatoria y no vacía (un `VAR=` vacío en el .env no cuenta)."""
    value = env(name, default="")
    if not value:
        raise ImproperlyConfigured(f"Falta la variable de entorno {name}.")
    return value


def _supabase_storage():
    supabase_url = _required("SUPABASE_URL").rstrip("/")
    bucket = env("SUPABASE_STORAGE_BUCKET", default="iki-public")
    return {
        "BACKEND": "storages.backends.s3.S3Storage",
        "OPTIONS": {
            "bucket_name": bucket,
            "endpoint_url": f"{supabase_url}/storage/v1/s3",
            "region_name": _required("SUPABASE_STORAGE_REGION"),
            "access_key": _required("SUPABASE_S3_ACCESS_KEY_ID"),
            "secret_key": _required("SUPABASE_S3_SECRET_ACCESS_KEY"),
            # Las imágenes públicas se sirven desde la URL pública del bucket (solo lectura,
            # sin credenciales). Las subidas las hace únicamente el servidor.
            "custom_domain": f"{supabase_url.removeprefix('https://')}/storage/v1/object/public/{bucket}",
            "querystring_auth": False,
            "default_acl": None,
            "file_overwrite": False,
            "addressing_style": "path",
            "signature_version": "s3v4",
            "object_parameters": {"CacheControl": "public, max-age=31536000, immutable"},
            # boto3 ≥ 1.36 agrega checksums CRC32 por defecto, que Supabase no acepta.
            "client_config": BotoConfig(
                request_checksum_calculation="when_required",
                response_checksum_validation="when_required",
            ),
        },
    }


if MEDIA_STORAGE == "supabase":
    _default_storage = _supabase_storage()
elif MEDIA_STORAGE == "local":
    _default_storage = {"BACKEND": "django.core.files.storage.FileSystemStorage"}
else:
    raise ImproperlyConfigured("MEDIA_STORAGE debe ser 'local' o 'supabase'.")

STORAGES = {
    "default": _default_storage,
    "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"},
}


# --- Email y contacto ------------------------------------------------------------
# EMAIL_URL (SECRETA), ej: smtp+tls://cuenta@gmail.com:CONTRASEÑA_DE_APP@smtp.gmail.com:587
# Vacía → los mails se imprimen en la consola (no se envían).
vars().update(environ.Env.email_url_config(env("EMAIL_URL", default="") or "consolemail://"))
EMAIL_TIMEOUT = 10
DEFAULT_FROM_EMAIL = env("DEFAULT_FROM_EMAIL", default="IKI <no-responder@localhost>")
# A quién le llegan los avisos de consultas nuevas (PRIVADA: no va en el repo).
CONTACT_NOTIFY_EMAIL = env("CONTACT_NOTIFY_EMAIL", default="")
# Anti-spam del formulario: envíos por IP y por hora, y segundos mínimos para completarlo.
CONTACT_RATE_LIMIT = env.int("CONTACT_RATE_LIMIT", default=5)
CONTACT_MIN_SECONDS = 3


# --- Seguridad (valores seguros en todos los entornos) -------------------------

SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_REFERRER_POLICY = "strict-origin-when-cross-origin"
SECURE_CROSS_ORIGIN_OPENER_POLICY = "same-origin"
X_FRAME_OPTIONS = "DENY"

SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = "Lax"
# HTMX toma el token del template (hx-headers), no de la cookie: puede ser HttpOnly.
CSRF_COOKIE_HTTPONLY = True
CSRF_COOKIE_SAMESITE = "Lax"

PERMISSIONS_POLICY = (
    "accelerometer=(), camera=(), geolocation=(), gyroscope=(), magnetometer=(), "
    "microphone=(), payment=(), usb=(), browsing-topics=()"
)


# --- Logging -------------------------------------------------------------------
# Nunca loguear datos personales (consultas, emails, teléfonos) ni secretos.

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "simple": {"format": "{asctime} {levelname} {name} {message}", "style": "{"},
    },
    "handlers": {
        "console": {"class": "logging.StreamHandler", "formatter": "simple"},
    },
    "root": {"handlers": ["console"], "level": "INFO"},
    "loggers": {
        "django.security": {"handlers": ["console"], "level": "WARNING", "propagate": False},
        "security": {"handlers": ["console"], "level": "INFO", "propagate": False},
    },
}
