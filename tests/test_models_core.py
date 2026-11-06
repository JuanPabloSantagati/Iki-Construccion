import pytest
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction

from apps.core.models import SiteSettings, TeamMember, Zone

pytestmark = pytest.mark.django_db


def test_site_settings_es_singleton():
    SiteSettings.objects.create(email="a@iki.example")
    SiteSettings(email="b@iki.example").save()
    assert SiteSettings.objects.count() == 1
    assert SiteSettings.load().email == "b@iki.example"


def test_site_settings_load_crea_el_registro():
    assert SiteSettings.objects.count() == 0
    assert SiteSettings.load().pk == 1
    assert SiteSettings.objects.count() == 1


@pytest.mark.parametrize("value", ["abc", "123", "+5493329000000", "1" * 16])
def test_whatsapp_invalido(value):
    with pytest.raises(ValidationError):
        SiteSettings(whatsapp=value).clean_fields()


def test_whatsapp_valido_y_vacio():
    SiteSettings(whatsapp="5493329000000").clean_fields()
    SiteSettings(whatsapp="").clean_fields()


def test_zone_slug_unico():
    Zone.objects.create(name="Baradero", slug="baradero")
    with pytest.raises(IntegrityError), transaction.atomic():
        Zone.objects.create(name="Otra", slug="baradero")


def test_zone_no_publicada_por_defecto():
    zone = Zone.objects.create(name="San Pedro", slug="san-pedro")
    assert zone.is_published is False
    assert str(zone) == "San Pedro"


def test_team_member_ordenado_por_order_y_nombre():
    TeamMember.objects.create(name="Zoe", role="Arquitecta", order=1)
    TeamMember.objects.create(name="Ana", role="Arquitecta", order=1)
    TeamMember.objects.create(name="Beto", role="Maestro mayor de obras", order=0)
    assert [m.name for m in TeamMember.objects.all()] == ["Beto", "Ana", "Zoe"]
