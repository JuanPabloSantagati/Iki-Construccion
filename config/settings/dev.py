"""Settings de desarrollo local. Nunca usar en un servidor público."""

from .base import *  # noqa: F403
from .base import env

DEBUG = env.bool("DEBUG", default=True)

# Clave solo para desarrollo: no es secreta ni sirve en producción.
SECRET_KEY = env("SECRET_KEY", default="") or "dev-insecure-solo-para-desarrollo-local"

ALLOWED_HOSTS = env.list("ALLOWED_HOSTS", default=["localhost", "127.0.0.1"])

# Sirve los static desde las carpetas fuente, sin collectstatic.
WHITENOISE_USE_FINDERS = True
WHITENOISE_AUTOREFRESH = True
