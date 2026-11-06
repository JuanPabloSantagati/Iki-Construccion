import pytest
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction

from apps.core.models import Zone
from apps.projects.models import Project, ProjectFact, ProjectImage, ProjectType
from apps.services.models import Service
from tests.factories import jpeg_bytes, upload

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


def new_image(project, **kwargs):
    return ProjectImage.from_upload(project, upload(jpeg_bytes(size=(800, 600))), **kwargs)


def test_from_upload_guarda_los_tres_tamanos(project_type):
    image = new_image(make_project(project_type))
    for label in ("thumb", "medium", "large"):
        field = getattr(image, label)
        assert field.name.startswith("projects/")
        assert field.name.endswith(f"_{label}.webp")
        assert field.storage.exists(field.name)


def test_from_upload_rechaza_archivos_que_no_son_imagen(project_type):
    project = make_project(project_type)
    with pytest.raises(ValidationError):
        ProjectImage.from_upload(project, upload(b"no soy una imagen"))
    assert ProjectImage.objects.count() == 0


def test_alt_se_autogenera_con_proyecto_y_ubicacion(project_type):
    image = new_image(make_project(project_type))
    assert image.alt == "Casa LL, Baradero"


def test_alt_manual_se_respeta(project_type):
    image = new_image(make_project(project_type), alt="Fachada norte")
    assert image.alt == "Fachada norte"


def test_una_sola_portada_por_proyecto(project_type):
    project = make_project(project_type)
    new_image(project, is_cover=True)
    with pytest.raises(IntegrityError), transaction.atomic():
        new_image(project, is_cover=True)


def test_dos_proyectos_pueden_tener_portada_cada_uno(project_type):
    new_image(make_project(project_type), is_cover=True)
    other = make_project(project_type, title="Casa MM", slug="casa-mm")
    new_image(other, is_cover=True)
    assert ProjectImage.objects.filter(is_cover=True).count() == 2


def test_imagenes_ordenadas(project_type):
    project = make_project(project_type)
    second = new_image(project, order=2)
    first = new_image(project, order=1)
    assert list(project.images.all()) == [first, second]


def test_borrar_la_imagen_borra_sus_archivos(project_type, django_capture_on_commit_callbacks):
    image = new_image(make_project(project_type))
    fields = [getattr(image, label) for label in ("thumb", "medium", "large")]
    names = [f.name for f in fields]
    with django_capture_on_commit_callbacks(execute=True):
        image.delete()
    assert not any(fields[0].storage.exists(name) for name in names)


def test_borrar_el_proyecto_borra_los_archivos_de_sus_imagenes(
    project_type, django_capture_on_commit_callbacks
):
    project = make_project(project_type)
    image = new_image(project)
    storage = image.thumb.storage
    names = [getattr(image, label).name for label in ("thumb", "medium", "large")]
    with django_capture_on_commit_callbacks(execute=True):
        project.delete()
    assert not any(storage.exists(name) for name in names)
