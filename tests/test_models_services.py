import pytest
from django.db import IntegrityError, transaction

from apps.services.models import Service, ServiceStep

pytestmark = pytest.mark.django_db


def make_service(**kwargs):
    defaults = {"title": "Dirección de obra", "slug": "direccion-de-obra"}
    return Service.objects.create(**{**defaults, **kwargs})


def test_service_slug_unico():
    make_service()
    with pytest.raises(IntegrityError), transaction.atomic():
        make_service(title="Otro")


def test_service_no_publicado_por_defecto_y_str():
    service = make_service()
    assert service.is_published is False
    assert str(service) == "Dirección de obra"


def test_services_ordenados_por_order():
    make_service(title="B", slug="b", order=2)
    make_service(title="A", slug="a", order=1)
    assert [s.slug for s in Service.objects.all()] == ["a", "b"]


def test_steps_ordenados_y_accesibles_desde_el_servicio():
    service = make_service()
    ServiceStep.objects.create(service=service, title="Obra", order=2)
    ServiceStep.objects.create(service=service, title="Anteproyecto", order=1)
    assert [s.title for s in service.steps.all()] == ["Anteproyecto", "Obra"]


def test_borrar_servicio_borra_sus_pasos():
    service = make_service()
    ServiceStep.objects.create(service=service, title="Anteproyecto")
    service.delete()
    assert ServiceStep.objects.count() == 0
