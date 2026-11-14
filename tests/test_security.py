"""Headers de seguridad, admin oculto, CSRF y páginas de error sin filtrar información."""

import pytest
from django.conf import settings
from django.test import Client

# Header y footer leen la configuración del sitio de la base.
pytestmark = pytest.mark.django_db


@pytest.fixture
def response(client):
    return client.get("/")


def test_home_responde(response):
    assert response.status_code == 200
    assert "La elegancia de lo esencial" in response.content.decode()


@pytest.mark.parametrize(
    ("header", "value"),
    [
        ("X-Content-Type-Options", "nosniff"),
        ("X-Frame-Options", "DENY"),
        ("Referrer-Policy", "strict-origin-when-cross-origin"),
        ("Cross-Origin-Opener-Policy", "same-origin"),
    ],
)
def test_headers_de_seguridad(response, header, value):
    assert response.headers[header] == value


def test_permissions_policy(response):
    policy = response.headers["Permissions-Policy"]
    for feature in ("camera=()", "microphone=()", "geolocation=()"):
        assert feature in policy


@pytest.mark.django_db
def test_admin_no_esta_en_ruta_por_defecto(client):
    assert client.get("/admin/").status_code == 404


@pytest.mark.django_db
def test_admin_en_ruta_configurada(client):
    response = client.get(f"/{settings.ADMIN_URL}")
    assert response.status_code == 302
    assert "/login/" in response.headers["Location"]


@pytest.mark.django_db
def test_csrf_activo_en_formularios():
    client = Client(enforce_csrf_checks=True)
    response = client.post(f"/{settings.ADMIN_URL}login/", {"username": "x", "password": "y"})
    assert response.status_code == 403


def test_404_propio_sin_detalles_tecnicos(client):
    response = client.get("/no-existe/")
    body = response.content.decode()
    assert response.status_code == 404
    assert "Página no encontrada" in body
    assert "Traceback" not in body
    assert "urlpatterns" not in body


def test_cookies_httponly():
    assert settings.CSRF_COOKIE_HTTPONLY is True
    assert settings.SESSION_COOKIE_HTTPONLY is True
