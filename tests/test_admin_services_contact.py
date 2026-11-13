import pytest
from django.urls import reverse
from django.utils import timezone

from apps.contact.models import Inquiry
from apps.services.models import Service

pytestmark = pytest.mark.django_db


@pytest.fixture
def inquiry():
    return Inquiry.objects.create(
        name="Ana",
        email="ana@iki.example",
        message="Hola",
        consent=True,
        consent_at=timezone.now(),
    )


@pytest.mark.parametrize(
    "name",
    [
        "admin:services_service_changelist",
        "admin:services_service_add",
        "admin:contact_inquiry_changelist",
    ],
)
def test_paginas_cargan(admin_client, name):
    assert admin_client.get(reverse(name)).status_code == 200


def test_servicio_con_pasos_se_crea_desde_el_admin(admin_client):
    data = {
        "title": "Dirección de obra",
        "slug": "direccion-de-obra",
        "summary": "",
        "description": "",
        "order": 0,
        "is_published": "on",
        "steps-TOTAL_FORMS": "1",
        "steps-INITIAL_FORMS": "0",
        "steps-MIN_NUM_FORMS": "0",
        "steps-MAX_NUM_FORMS": "1000",
        "steps-0-title": "Anteproyecto",
        "steps-0-description": "",
        "steps-0-order": "1",
    }
    response = admin_client.post(reverse("admin:services_service_add"), data)
    assert response.status_code == 302
    assert Service.objects.get().steps.get().title == "Anteproyecto"


def test_las_consultas_no_se_cargan_a_mano(admin_client):
    assert admin_client.get(reverse("admin:contact_inquiry_add")).status_code == 403


def test_consulta_se_ve_en_el_admin(admin_client, inquiry):
    url = reverse("admin:contact_inquiry_change", args=[inquiry.pk])
    assert admin_client.get(url).status_code == 200


def test_solo_el_estado_de_la_consulta_es_editable(admin_client, inquiry):
    url = reverse("admin:contact_inquiry_change", args=[inquiry.pk])
    response = admin_client.post(url, {"status": "answered", "name": "Otro nombre"})
    assert response.status_code == 302
    inquiry.refresh_from_db()
    assert inquiry.status == Inquiry.Status.ANSWERED
    assert inquiry.name == "Ana"
