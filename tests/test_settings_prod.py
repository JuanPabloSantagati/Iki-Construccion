"""El arranque en producción tiene que FALLAR ante una configuración insegura."""

import pytest

from .conftest import ROOT


def test_prod_arranca_con_configuracion_valida(django_proc):
    result = django_proc("from django.conf import settings; print(settings.DEBUG)")
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == "False"


def test_prod_falla_sin_secret_key(django_proc):
    result = django_proc("", SECRET_KEY=None)
    assert result.returncode != 0
    assert "SECRET_KEY" in result.stderr


@pytest.mark.parametrize(
    "value", ["corta", "dev-insecure-" + "a" * 60, "django-insecure-" + "a" * 60]
)
def test_prod_falla_con_secret_key_debil(django_proc, value):
    result = django_proc("", SECRET_KEY=value)
    assert result.returncode != 0
    assert "SECRET_KEY" in result.stderr


def test_prod_falla_con_debug_true(django_proc):
    result = django_proc("", DEBUG="True")
    assert result.returncode != 0
    assert "DEBUG" in result.stderr


@pytest.mark.parametrize("value", [None, "admin/"])
def test_prod_falla_con_admin_url_ausente_o_predecible(django_proc, value):
    result = django_proc("", ADMIN_URL=value)
    assert result.returncode != 0
    assert "ADMIN_URL" in result.stderr


@pytest.mark.parametrize("value", [None, "", "*"])
def test_prod_falla_sin_allowed_hosts_explicitos(django_proc, value):
    result = django_proc("", ALLOWED_HOSTS=value)
    assert result.returncode != 0
    assert "ALLOWED_HOSTS" in result.stderr


def test_prod_falla_sin_database_url(django_proc):
    result = django_proc("", DATABASE_URL=None)
    assert result.returncode != 0
    assert "DATABASE_URL" in result.stderr


def test_prod_activa_https_y_cookies_seguras(django_proc):
    code = (
        "from django.conf import settings as s; "
        "print(s.SECURE_SSL_REDIRECT, s.SESSION_COOKIE_SECURE, s.CSRF_COOKIE_SECURE, "
        "s.SECURE_HSTS_SECONDS >= 31536000)"
    )
    result = django_proc(code)
    assert result.returncode == 0, result.stderr
    assert result.stdout.split() == ["True", "True", "True", "True"]


def test_check_deploy_sin_warnings(django_proc):
    code = (
        "from django.core.management import call_command; "
        "call_command('check', deploy=True, fail_level='WARNING')"
    )
    result = django_proc(code)
    assert result.returncode == 0, result.stderr + result.stdout


def test_manage_py_usa_dev_y_wsgi_usa_prod():
    assert "config.settings.dev" in (ROOT / "manage.py").read_text()
    assert "config.settings.prod" in (ROOT / "config" / "wsgi.py").read_text()
    assert "config.settings.prod" in (ROOT / "config" / "asgi.py").read_text()
