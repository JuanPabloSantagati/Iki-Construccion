import pytest
from django.db import IntegrityError, transaction

from apps.core.models import Zone
from apps.projects.models import Project, ProjectFact, ProjectType
from apps.services.models import Service

pytestmark = pytest.mark.django_db


@pytest.fixture
def project_type():
    return ProjectType.objects.create(name="Vivienda", slug="vivienda")


def make_project(project_type, **kwargs):
    defaults = {
        "title": "Casa LL",
        "slug": "casa-ll",
        "category": Project.Category.OBRA,
        "project_type": project_type,
        "location": "Baradero",
    }
    return Project.objects.create(**{**defaults, **kwargs})


def test_project_type_slug_unico(project_type):
    with pytest.raises(IntegrityError), transaction.atomic():
        ProjectType.objects.create(name="Otra", slug="vivienda")


def test_project_nace_en_borrador(project_type):
    project = make_project(project_type)
    assert project.status == Project.Status.DRAFT
    assert project.is_featured is False
    assert str(project) == "Casa LL"


def test_project_slug_unico(project_type):
    make_project(project_type)
    with pytest.raises(IntegrityError), transaction.atomic():
        make_project(project_type, title="Otra")


def test_project_categorias():
    assert [c.value for c in Project.Category] == ["obra", "proyecto", "render"]


def test_descripcion_se_sanitiza_al_guardar(project_type):
    project = make_project(
        project_type,
        description='<p>Hola</p><script>alert(1)</script><a href="javascript:x()">l</a>',
    )
    project.refresh_from_db()
    assert "<script" not in project.description
    assert "javascript" not in project.description
    assert "<p>Hola</p>" in project.description


def test_borrar_zona_no_borra_el_proyecto(project_type):
    zone = Zone.objects.create(name="Baradero", slug="baradero")
    project = make_project(project_type, zone=zone)
    zone.delete()
    project.refresh_from_db()
    assert project.zone is None


def test_no_se_puede_borrar_un_tipo_con_proyectos(project_type):
    make_project(project_type)
    with pytest.raises(IntegrityError), transaction.atomic():
        project_type.delete()


def test_project_servicios_m2m(project_type):
    project = make_project(project_type)
    service = Service.objects.create(title="Dirección de obra", slug="direccion-de-obra")
    project.services.add(service)
    assert list(service.projects.all()) == [project]


def test_facts_ordenados_y_se_borran_con_el_proyecto(project_type):
    project = make_project(project_type)
    ProjectFact.objects.create(project=project, label="Superficie", value="180 m²", order=2)
    ProjectFact.objects.create(project=project, label="Año", value="2024", order=1)
    assert [f.label for f in project.facts.all()] == ["Año", "Superficie"]
    project.delete()
    assert ProjectFact.objects.count() == 0
