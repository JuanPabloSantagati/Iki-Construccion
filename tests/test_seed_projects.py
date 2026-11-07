from io import StringIO

import pytest
from django.core.management import call_command
from django.core.management.base import CommandError

from apps.core.models import SiteSettings, Zone
from apps.projects.models import Project, ProjectType
from apps.services.models import Service, ServiceStep

pytestmark = pytest.mark.django_db


@pytest.fixture
def debug_on(settings):
    settings.DEBUG = True


def seed(*args):
    out = StringIO()
    call_command("seed_projects", *args, stdout=out)
    return out.getvalue()


def test_carga_los_datos_de_referencia(debug_on):
    seed()
    assert ProjectType.objects.count() == 5
    assert Zone.objects.count() == 4
    assert Service.objects.count() == 5
    assert ServiceStep.objects.count() == 20
    assert SiteSettings.load().address == "Baradero, Buenos Aires"


def test_no_inventa_proyectos_ni_datos_de_contacto(debug_on):
    seed()
    assert Project.objects.count() == 0
    site = SiteSettings.load()
    assert (site.whatsapp, site.phone, site.email) == ("", "", "")


def test_nada_queda_publicado(debug_on):
    seed()
    assert not Service.objects.filter(is_published=True).exists()
    assert not Zone.objects.filter(is_published=True).exists()


def test_es_idempotente(debug_on):
    seed()
    out = seed()
    assert ProjectType.objects.count() == 5
    assert Zone.objects.count() == 4
    assert Service.objects.count() == 5
    assert ServiceStep.objects.count() == 20
    assert "Nada nuevo" in out


def test_no_pisa_lo_editado_en_el_admin(debug_on):
    seed()
    service = Service.objects.get(slug="construccion")
    service.title = "Obra llave en mano"
    service.is_published = True
    service.save()
    service.steps.all().delete()
    SiteSettings.objects.filter(pk=1).update(address="Otra calle 123")
    seed()
    service.refresh_from_db()
    assert (service.title, service.is_published) == ("Obra llave en mano", True)
    assert service.steps.count() == 0
    assert SiteSettings.load().address == "Otra calle 123"


def test_se_niega_con_debug_apagado():
    with pytest.raises(CommandError, match="DEBUG"):
        seed()
    assert ProjectType.objects.count() == 0


def test_force_permite_correr_con_debug_apagado():
    seed("--force")
    assert ProjectType.objects.count() == 5
