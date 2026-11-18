"""Etapa E: formulario de contacto, anti-spam, mails, privacidad y anonimización."""

from datetime import timedelta
from unittest import mock

import pytest
from django.core import mail
from django.core.cache import cache
from django.core.management import call_command
from django.test import Client, override_settings
from django.urls import reverse
from django.utils import timezone

from apps.contact.forms import started_token
from apps.contact.models import Inquiry
from apps.projects.models import Project, ProjectType
from apps.services.models import Service

pytestmark = pytest.mark.django_db

URL = "/contacto/"
HTMX = {"HTTP_HX_REQUEST": "true"}


@pytest.fixture(autouse=True)
def _clear_rate_limit():
    cache.clear()
    yield
    cache.clear()


def data(**overrides):
    values = {
        "name": "Ana Pérez",
        "email": "ana@iki.example",
        "phone": "+54 3329 40-0000",
        "location": "Baradero",
        "approx_area": "120",
        "message": "Quiero construir una casa.",
        "consent": "on",
        "started": started_token(),
        "website": "",
    }
    values.update(overrides)
    return {k: v for k, v in values.items() if v is not None}


# --- Página -------------------------------------------------------------------


def test_pagina_de_contacto(client):
    response = client.get(URL)
    body = response.content.decode()
    assert response.status_code == 200
    assert "Iniciar proyecto" in body
    assert 'hx-post="/contacto/"' in body
    assert "csrfmiddlewaretoken" in body
    assert reverse("core:privacy") in body


def test_precarga_servicio_y_proyecto_publicados(client):
    service = Service.objects.create(title="Renders", slug="renders", is_published=True)
    tipo = ProjectType.objects.create(name="Vivienda", slug="vivienda")
    Project.objects.create(
        title="Obra JJ",
        slug="obra-jj",
        project_type=tipo,
        location="Baradero",
        category=Project.Category.OBRA,
        status=Project.Status.PUBLISHED,
    )
    body = client.get(URL, {"servicio": "renders", "proyecto": "obra-jj"}).content.decode()
    assert f'<option value="{service.pk}" selected>' in body
    assert "Me interesa un proyecto como «Obra JJ»" in body


def test_select_solo_ofrece_servicios_publicados(client):
    Service.objects.create(title="Renders", slug="renders", is_published=True)
    Service.objects.create(title="Oculto", slug="oculto", is_published=False)
    body = client.get(URL).content.decode()
    assert "Renders" in body
    assert "Oculto" not in body


# --- Envío --------------------------------------------------------------------


def test_envio_valido_guarda_y_avisa_por_mail(client):
    response = client.post(URL, data())
    assert response.status_code == 302
    assert response.headers["Location"] == reverse("contact:thanks")
    inquiry = Inquiry.objects.get()
    assert inquiry.name == "Ana Pérez"
    assert inquiry.approx_area == 120
    assert inquiry.consent is True and inquiry.consent_at is not None
    assert len(mail.outbox) == 1
    sent = mail.outbox[0]
    assert sent.to == ["avisos@iki.example"]
    assert sent.reply_to == ["ana@iki.example"]
    assert sent.subject == "Nueva consulta web: Ana Pérez"
    assert "Quiero construir una casa." in sent.body


def test_envio_htmx_devuelve_el_mensaje_de_exito(client):
    response = client.post(URL, data(), **HTMX)
    body = response.content.decode()
    assert response.status_code == 200
    assert "Ya recibimos tu consulta" in body
    assert "<html" not in body


def test_errores_htmx_se_muestran_en_el_formulario(client):
    response = client.post(URL, data(phone=""), **HTMX)
    body = response.content.decode()
    assert response.status_code == 200
    assert "<form" in body and "<html" not in body
    assert not Inquiry.objects.exists()


def test_sin_consentimiento_no_se_guarda(client):
    response = client.post(URL, data(consent=None))
    assert response.status_code == 200
    assert "tenés que aceptar la política de privacidad" in response.content.decode()
    assert not Inquiry.objects.exists()


@pytest.mark.parametrize(
    "field,value",
    [
        ("email", "no-es-un-mail"),
        ("phone", "llamame"),
        ("approx_area", "999999"),
        ("message", "x" * 3001),
        ("message", ""),
        ("name", ""),
    ],
)
def test_validacion_de_campos(client, field, value):
    client.post(URL, data(**{field: value}))
    assert not Inquiry.objects.exists()


@pytest.mark.parametrize("field", ["name", "location"])
def test_rechaza_saltos_de_linea_header_injection(client, field):
    client.post(URL, data(**{field: "Ana\r\nBcc: victima@example.com"}))
    assert not Inquiry.objects.exists()
    assert mail.outbox == []


def test_csrf_obligatorio():
    response = Client(enforce_csrf_checks=True).post(URL, data())
    assert response.status_code == 403
    assert not Inquiry.objects.exists()


def test_formulario_vencido_o_manipulado(client):
    response = client.post(URL, data(started="1234:firma-falsa"))
    assert "El formulario venció" in response.content.decode()
    assert not Inquiry.objects.exists()


def test_falla_del_mail_no_pierde_la_consulta(client):
    with mock.patch("django.core.mail.EmailMessage.send", side_effect=OSError("smtp caído")):
        response = client.post(URL, data())
    assert response.status_code == 302
    assert Inquiry.objects.count() == 1


@override_settings(CONTACT_NOTIFY_EMAIL="")
def test_sin_destinatario_guarda_igual(client):
    client.post(URL, data())
    assert Inquiry.objects.count() == 1
    assert mail.outbox == []


# --- Anti-spam ----------------------------------------------------------------


def test_honeypot_descarta_en_silencio(client):
    response = client.post(URL, data(website="http://spam.example"))
    assert response.status_code == 302  # el bot cree que funcionó
    assert not Inquiry.objects.exists()
    assert mail.outbox == []


@override_settings(CONTACT_MIN_SECONDS=60)
def test_envio_demasiado_rapido_se_descarta(client):
    response = client.post(URL, data())
    assert response.status_code == 302
    assert not Inquiry.objects.exists()


@override_settings(CONTACT_RATE_LIMIT=2)
def test_limite_de_envios_por_ip(client):
    for _ in range(2):
        assert client.post(URL, data()).status_code == 302
    response = client.post(URL, data())
    assert response.status_code == 429
    assert "Probá de nuevo más tarde" in response.content.decode()
    assert Inquiry.objects.count() == 2


@override_settings(CONTACT_RATE_LIMIT=1)
def test_limite_es_por_ip(client):
    assert client.post(URL, data(), REMOTE_ADDR="10.0.0.1").status_code == 302
    assert client.post(URL, data(), REMOTE_ADDR="10.0.0.2").status_code == 302
    assert client.post(URL, data(), REMOTE_ADDR="10.0.0.1").status_code == 429


@override_settings(CONTACT_RATE_LIMIT=1)
def test_limite_con_htmx_muestra_el_error(client):
    client.post(URL, data(), **HTMX)
    response = client.post(URL, data(), **HTMX)
    assert response.status_code == 200
    assert "Probá de nuevo más tarde" in response.content.decode()


def test_no_guarda_la_ip_en_claro_en_la_cache(client):
    client.post(URL, data(), REMOTE_ADDR="203.0.113.7")
    keys = list(cache._cache.keys())  # LocMemCache en tests
    assert keys and all("203.0.113.7" not in key for key in keys)


# --- Privacidad y anonimización -----------------------------------------------


def test_pagina_de_privacidad(client):
    body = client.get(reverse("core:privacy")).content.decode()
    assert "Política de privacidad" in body
    assert "Ley N° 25.326" in body


def make_inquiry(days_ago):
    inquiry = Inquiry.objects.create(
        name="Ana",
        email="ana@iki.example",
        phone="123456",
        location="Baradero",
        message="Hola",
        consent=True,
        consent_at=timezone.now(),
    )
    Inquiry.objects.filter(pk=inquiry.pk).update(
        created_at=timezone.now() - timedelta(days=days_ago)
    )
    return inquiry


def test_purge_anonimiza_las_viejas():
    old, recent = make_inquiry(800), make_inquiry(10)
    call_command("purge_inquiries")
    old.refresh_from_db()
    recent.refresh_from_db()
    assert (old.name, old.phone, old.message, old.location) == ("(anonimizada)", "", "", "")
    assert old.anonymized_at is not None
    assert recent.name == "Ana"


def test_purge_delete_borra():
    make_inquiry(800)
    call_command("purge_inquiries", "--delete")
    assert not Inquiry.objects.exists()


def test_purge_dry_run_no_toca_nada(capsys):
    make_inquiry(800)
    call_command("purge_inquiries", "--dry-run")
    assert Inquiry.objects.get().name == "Ana"
    assert "Consultas para anonimizar: 1" in capsys.readouterr().out
