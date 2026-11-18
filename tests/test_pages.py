"""Etapa D: home, estudio y servicios."""

import pytest
from django.urls import reverse

from apps.core.models import SiteSettings, TeamMember
from apps.projects.models import Project, ProjectImage, ProjectType
from apps.services.models import Service, ServiceStep
from tests.factories import jpeg_bytes, upload

pytestmark = pytest.mark.django_db


@pytest.fixture
def vivienda():
    return ProjectType.objects.create(name="Vivienda", slug="vivienda")


def make_project(project_type, slug, *, published=True, **kwargs):
    status = Project.Status.PUBLISHED if published else Project.Status.DRAFT
    defaults = {
        "title": slug.replace("-", " ").title(),
        "category": Project.Category.OBRA,
        "location": "Baradero",
    }
    defaults.update(kwargs)
    return Project.objects.create(slug=slug, project_type=project_type, status=status, **defaults)


def make_service(slug, *, published=True, **kwargs):
    defaults = {"title": slug.replace("-", " ").title(), "summary": f"Resumen de {slug}"}
    defaults.update(kwargs)
    return Service.objects.create(slug=slug, is_published=published, **defaults)


# --- Home ---------------------------------------------------------------------


def test_home_hero_usa_el_proyecto_destacado(client, vivienda):
    make_project(vivienda, "casa-nueva", year=2025)
    destacado = make_project(vivienda, "casa-destacada", year=2020, is_featured=True)
    ProjectImage.from_upload(destacado, upload(jpeg_bytes(size=(800, 600), with_gps=False)))
    body = client.get("/").content.decode()
    hero = body.split('id="servicios"')[0]
    assert "Casa Destacada" in hero
    assert 'fetchpriority="high"' in hero


def test_home_sin_destacado_usa_el_ultimo_publicado(client, vivienda):
    make_project(vivienda, "casa-vieja", year=2019)
    make_project(vivienda, "casa-nueva", year=2025)
    body = client.get("/").content.decode()
    assert body.index("Casa Nueva") < body.index("Casa Vieja")


def test_home_muestra_hasta_tres_proyectos_recientes(client, vivienda):
    for i in range(6):
        make_project(vivienda, f"casa-{i}", year=2010 + i)
    make_project(vivienda, "casa-borrador", published=False, year=2030)
    body = client.get("/").content.decode()
    recientes = body.split('id="ultimos"')[1]
    assert recientes.count("<article") == 3
    assert "Casa Borrador" not in body


def test_home_muestra_solo_servicios_publicados(client):
    make_service("renders")
    make_service("oculto", published=False)
    body = client.get("/").content.decode()
    assert "Renders" in body
    assert "Oculto" not in body


def test_home_vacia_no_rompe(client):
    response = client.get("/")
    assert response.status_code == 200
    assert "La elegancia de lo esencial" in response.content.decode()


# --- Estudio ------------------------------------------------------------------


def test_estudio_muestra_el_equipo(client):
    TeamMember.objects.create(name="Ana Pérez", role="Arquitecta", order=1)
    response = client.get(reverse("core:studio"))
    body = response.content.decode()
    assert response.status_code == 200
    assert "Ana Pérez" in body
    assert "Arquitecta" in body


def test_estudio_sin_equipo_oculta_la_seccion(client):
    body = client.get(reverse("core:studio")).content.decode()
    assert 'id="equipo"' not in body


# --- Servicios ----------------------------------------------------------------


def test_indice_de_servicios_solo_publicados_y_en_orden(client):
    make_service("segundo", order=2)
    make_service("primero", order=1)
    make_service("borrador", published=False)
    body = client.get(reverse("services:list")).content.decode()
    assert body.index("Primero") < body.index("Segundo")
    assert "Borrador" not in body


def test_detalle_de_servicio_con_proceso(client):
    service = make_service("planos-municipales", title="Planos municipales")
    ServiceStep.objects.create(service=service, title="Relevamiento", order=1)
    ServiceStep.objects.create(service=service, title="Presentación", order=2)
    response = client.get(service.get_absolute_url())
    body = response.content.decode()
    assert response.status_code == 200
    assert body.index("Relevamiento") < body.index("Presentación")
    assert "Planos municipales en Baradero" in body  # <title> para SEO local


def test_descripcion_de_servicio_se_escapa(client):
    service = make_service("renders", description="Línea 1\n\n<script>alert(1)</script>")
    body = client.get(service.get_absolute_url()).content.decode()
    assert "<p>Línea 1</p>" in body
    assert "<script>alert(1)</script>" not in body
    assert "&lt;script&gt;" in body


def test_servicio_borrador_404_para_el_publico(client):
    service = make_service("borrador", published=False)
    assert client.get(service.get_absolute_url()).status_code == 404


def test_staff_previsualiza_servicio_borrador(admin_client):
    service = make_service("borrador", published=False)
    body = admin_client.get(service.get_absolute_url()).content.decode()
    assert "Borrador: solo lo ve el equipo" in body
    assert 'content="noindex"' in body


def test_servicio_muestra_solo_proyectos_publicados_con_ese_servicio(client, vivienda):
    service = make_service("direccion-de-obra")
    con = make_project(vivienda, "casa-con")
    con.services.add(service)
    make_project(vivienda, "casa-sin")
    oculto = make_project(vivienda, "casa-oculta", published=False)
    oculto.services.add(service)
    body = client.get(service.get_absolute_url()).content.decode()
    assert "Casa Con" in body
    assert "Casa Sin" not in body
    assert "Casa Oculta" not in body


def test_servicio_cta_whatsapp(client):
    SiteSettings.objects.create(whatsapp="5493329000000")
    service = make_service("renders", title="Renders")
    body = client.get(service.get_absolute_url()).content.decode()
    assert (
        "https://wa.me/5493329000000?text=Hola%20IKI%2C%20quiero%20consultar%20por%20Renders."
        in body
    )


def test_ficha_de_proyecto_linkea_a_sus_servicios(client, vivienda):
    service = make_service("renders", title="Renders")
    project = make_project(vivienda, "casa-a")
    project.services.add(service)
    body = client.get(project.get_absolute_url()).content.decode()
    assert f'href="{service.get_absolute_url()}"' in body


# --- Navegación ---------------------------------------------------------------


@pytest.mark.parametrize("url", ["/", "/estudio/", "/servicios/", "/proyectos/"])
def test_menu_linkea_a_las_secciones(client, url):
    body = client.get(url).content.decode()
    for href in ('href="/estudio/"', 'href="/servicios/"', 'href="/proyectos/"'):
        assert href in body
