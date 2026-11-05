import os
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent

# Entorno mínimo y válido de producción. Valores falsos, solo para los tests.
PROD_ENV = {
    "DJANGO_SETTINGS_MODULE": "config.settings.prod",
    "DJANGO_READ_DOT_ENV": "0",
    "SECRET_KEY": "x" * 20 + "-clave-de-prueba-larga-no-real-" + "y" * 20,
    "ALLOWED_HOSTS": "iki.example",
    "CSRF_TRUSTED_ORIGINS": "https://iki.example",
    "ADMIN_URL": "panel-prueba/",
    "DATABASE_URL": "postgres://iki@localhost:5432/iki",
}

# Variables que podrían venir del entorno del desarrollador y alterar el resultado.
_ISOLATED = {
    "DEBUG",
    "MEDIA_STORAGE",
    "SUPABASE_URL",
    "SUPABASE_S3_ACCESS_KEY_ID",
    "SUPABASE_S3_SECRET_ACCESS_KEY",
    "SUPABASE_STORAGE_REGION",
}


def run_django(code: str, **env_overrides: str | None) -> subprocess.CompletedProcess:
    """Ejecuta `code` en un proceso nuevo con settings de prod, aislado del entorno actual.

    Un override con valor None elimina esa variable del entorno.
    """
    env = {k: v for k, v in os.environ.items() if k not in PROD_ENV and k not in _ISOLATED}
    env.update(PROD_ENV)
    for key, value in env_overrides.items():
        if value is None:
            env.pop(key, None)
        else:
            env[key] = value
    script = f"import django\ndjango.setup()\n{code}"
    return subprocess.run(
        [sys.executable, "-c", script], cwd=ROOT, env=env, capture_output=True, text=True
    )


@pytest.fixture
def django_proc():
    return run_django
