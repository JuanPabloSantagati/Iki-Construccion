import pytest
from django.urls import reverse

from apps.core.models import SiteSettings, TeamMember
from tests.factories import jpeg_bytes, upload

pytestmark = pytest.mark.django_db


@pytest.mark.parametrize(
    "name",
    [
        "admin:core_zone_changelist",
        "admin:core_zone_add",
        "admin:core_teammember_changelist",
        "admin:core_teammember_add",
    ],
)
def test_paginas_cargan(admin_client, name):
    assert admin_client.get(reverse(name)).status_code == 200


def test_listado_de_site_settings_lleva_al_unico_registro(admin_client):
    response = admin_client.get(reverse("admin:core_sitesettings_changelist"))
    assert response.status_code == 302
    assert response.url == reverse("admin:core_sitesettings_change", args=[1])
    assert admin_client.get(response.url).status_code == 200


def test_site_settings_no_se_agrega_ni_se_borra(admin_client):
    SiteSettings.load()
    assert admin_client.get(reverse("admin:core_sitesettings_add")).status_code == 403
    delete_url = reverse("admin:core_sitesettings_delete", args=[1])
    assert admin_client.get(delete_url).status_code == 403


def test_site_settings_se_edita(admin_client):
    SiteSettings.load()
    data = {
        "whatsapp": "5493329000000",
        "phone": "",
        "email": "hola@iki.example",
        "address": "",
        "instagram": "",
        "facebook": "",
    }
    response = admin_client.post(reverse("admin:core_sitesettings_change", args=[1]), data)
    assert response.status_code == 302
    assert SiteSettings.load().whatsapp == "5493329000000"


def test_alta_de_integrante_con_foto(admin_client):
    data = {
        "name": "Ana",
        "role": "Arquitecta",
        "bio": "",
        "order": 0,
        "new_photo": upload(jpeg_bytes(size=(1600, 1200)), "yo.jpg"),
    }
    response = admin_client.post(reverse("admin:core_teammember_add"), data)
    assert response.status_code == 302
    member = TeamMember.objects.get()
    assert member.photo.name.startswith("team/")
    assert member.photo.name.endswith("_medium.webp")


def test_foto_invalida_no_crea_al_integrante(admin_client):
    data = {
        "name": "Ana",
        "role": "Arquitecta",
        "bio": "",
        "order": 0,
        "new_photo": upload(b"no soy una imagen", "yo.jpg"),
    }
    response = admin_client.post(reverse("admin:core_teammember_add"), data)
    assert response.status_code == 200
    assert TeamMember.objects.count() == 0
    assert "imagen válida" in response.content.decode()
