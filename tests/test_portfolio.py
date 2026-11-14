"""Etapa C: grilla de proyectos con filtros HTMX y ficha de proyecto."""

import pytest

from apps.core.models import SiteSettings
from apps.projects.models import Project, ProjectFact, ProjectImage, ProjectType
from apps.services.models import Service
from tests.factories import jpeg_bytes, upload

pytestmark = pytest.mark.django_db

LIST_URL = "/proyectos/"
HTMX = {"HTTP_HX_REQUEST": "true"}


@pytest.fixture
def vivienda():
    return ProjectType.objects.create(name="Vivienda", slug="vivienda")


@pytest.fixture
def comercial():
    return ProjectType.objects.create(name="Local comercial", slug="local-comercial")


def make_project(project_type, slug, *, status=Project.Status.PUBLISHED, **kwargs):
    defaults = {
        "title": slug.replace("-", " ").title(),
        "category": Project.Category.OBRA,
        "location": "Baradero",
    }
    defaults.update(kwargs)
    return Project.objects.create(slug=slug, project_type=project_type, status=status, **defaults)


def add_image(project, **kwargs):
    return ProjectImage.from_upload(
        project, upload(jpeg_bytes(size=(800, 600), with_gps=False)), **kwargs
    )


# --- Grilla -------------------------------------------------------------------


def test_la_grilla_muestra_solo_publicados(client, vivienda):
    make_project(vivienda, "casa-publicada")
    make_project(vivienda, "casa-borrador", status=Project.Status.DRAFT)
    body = client.get(LIST_URL).content.decode()
    assert "Casa Publicada" in body
    assert "Casa Borrador" not in body


def test_grilla_vacia_muestra_mensaje(client):
    response = client.get(LIST_URL)
    assert response.status_code == 200
    assert "Todavía no hay proyectos publicados" in response.content.decode()


def test_filtro_por_categoria(client, vivienda):
    make_project(vivienda, "una-obra", category=Project.Category.OBRA)
    make_project(vivienda, "un-render", category=Project.Category.RENDER)
    body = client.get(LIST_URL, {"categoria": "render"}).content.decode()
    assert "Un Render" in body
    assert "Una Obra" not in body


def test_filtro_por_tipo(client, vivienda, comercial):
    make_project(vivienda, "casa-a")
    make_project(comercial, "local-b")
    body = client.get(LIST_URL, {"tipo": "local-comercial"}).content.decode()
    assert "Local B" in body
    assert "Casa A" not in body


def test_filtros_combinados(client, vivienda, comercial):
    make_project(vivienda, "casa-obra", category=Project.Category.OBRA)
    make_project(vivienda, "casa-render", category=Project.Category.RENDER)
    make_project(comercial, "local-render", category=Project.Category.RENDER)
    body = client.get(LIST_URL, {"categoria": "render", "tipo": "vivienda"}).content.decode()
    assert "Casa Render" in body
    assert "Casa Obra" not in body
    assert "Local Render" not in body


@pytest.mark.parametrize("params", [{"categoria": "<script>"}, {"tipo": "no-existe"}])
def test_filtros_invalidos_se_ignoran(client, vivienda, params):
    make_project(vivienda, "casa-a")
    response = client.get(LIST_URL, params)
    body = response.content.decode()
    assert response.status_code == 200
    assert "Casa A" in body
    assert "<script>" not in body


def test_solo_se_ofrecen_tipos_con_proyectos_publicados(client, vivienda, comercial):
    make_project(vivienda, "casa-a")
    make_project(comercial, "local-borrador", status=Project.Status.DRAFT)
    body = client.get(LIST_URL).content.decode()
    assert "tipo=vivienda" in body
    assert "tipo=local-comercial" not in body


def test_htmx_filtro_devuelve_solo_el_fragmento(client, vivienda):
    make_project(vivienda, "casa-a")
    response = client.get(LIST_URL, {"categoria": "obra"}, HTTP_HX_TARGET="project-results", **HTMX)
    body = response.content.decode()
    assert 'id="project-results"' in body
    assert "<html" not in body
    assert "HX-Request" in response.headers["Vary"]


def test_htmx_restaurar_historial_devuelve_pagina_completa(client):
    response = client.get(LIST_URL, HTTP_HX_HISTORY_RESTORE_REQUEST="true", **HTMX)
    assert "<html" in response.content.decode()


def test_paginacion_con_ver_mas(client, vivienda):
    for i in range(14):
        make_project(vivienda, f"casa-{i:02d}", year=2000 + i)
    first = client.get(LIST_URL).content.decode()
    assert first.count("<article") == 12
    assert "Ver más proyectos" in first

    second = client.get(LIST_URL, {"pagina": 2}, HTTP_HX_TARGET="load-more", **HTMX)
    body = second.content.decode()
    assert body.count("<article") == 2
    assert "Ver más proyectos" not in body
    assert "<html" not in body


def test_la_grilla_no_hace_consultas_por_proyecto(client, vivienda, django_assert_max_num_queries):
    for i in range(6):
        add_image(make_project(vivienda, f"casa-{i}"), is_cover=True)
    with django_assert_max_num_queries(8):
        client.get(LIST_URL)


def test_tarjeta_usa_la_portada(client, vivienda):
    project = make_project(vivienda, "casa-a")
    add_image(project, order=0)
    cover = add_image(project, order=1, is_cover=True)
    body = client.get(LIST_URL).content.decode()
    assert cover.medium.url in body


# --- Ficha --------------------------------------------------------------------


@pytest.fixture
def project(vivienda):
    project = make_project(
        vivienda,
        "casa-ll",
        title="Casa LL",
        location="Baradero, Buenos Aires",
        area_m2=330,
        year=2023,
        summary="Una casa entre árboles.",
        description="<p>Patio interno.</p><script>alert(1)</script>",
    )
    ProjectFact.objects.create(project=project, label="Dormitorios", value="3")
    return project


def test_ficha_muestra_titulo_metadatos_y_datos(client, project):
    response = client.get(project.get_absolute_url())
    body = response.content.decode()
    assert response.status_code == 200
    assert "Casa LL" in body
    assert "Baradero, Buenos Aires · 330 m² · 2023 · Vivienda" in body
    assert "Dormitorios" in body
    assert "Todos los proyectos" in body


def test_ficha_sanitiza_la_descripcion(client, project):
    # Aunque el dato se haya guardado sin pasar por save() (ej: update masivo).
    Project.objects.filter(pk=project.pk).update(
        description='<p>Ok</p><img src=x onerror="alert(1)"><script>alert(2)</script>'
    )
    body = client.get(project.get_absolute_url()).content.decode()
    assert "<p>Ok</p>" in body
    assert "onerror" not in body
    assert "<script>alert" not in body


def test_descripcion_en_texto_plano_respeta_parrafos(client, project):
    Project.objects.filter(pk=project.pk).update(description="Primer párrafo.\n\nSegundo & último.")
    body = client.get(project.get_absolute_url()).content.decode()
    assert "<p>Primer párrafo.</p>" in body
    assert "<p>Segundo &amp; último.</p>" in body


def test_borrador_da_404_al_publico(client, vivienda):
    draft = make_project(vivienda, "casa-borrador", status=Project.Status.DRAFT)
    assert client.get(draft.get_absolute_url()).status_code == 404


def test_staff_puede_previsualizar_borrador(admin_client, vivienda):
    draft = make_project(vivienda, "casa-borrador", status=Project.Status.DRAFT)
    response = admin_client.get(draft.get_absolute_url())
    body = response.content.decode()
    assert response.status_code == 200
    assert "Borrador: solo lo ve el equipo" in body
    assert 'name="robots" content="noindex"' in body


def test_ficha_muestra_solo_servicios_publicados(client, project):
    project.services.add(
        Service.objects.create(title="Dirección de obra", slug="direccion", is_published=True),
        Service.objects.create(title="Servicio oculto", slug="oculto", is_published=False),
    )
    body = client.get(project.get_absolute_url()).content.decode()
    assert "Dirección de obra" in body
    assert "Servicio oculto" not in body


def test_galeria_con_lightbox(client, project):
    images = [add_image(project, order=i) for i in range(3)]
    body = client.get(project.get_absolute_url()).content.decode()
    assert body.count("data-lightbox ") == 3
    assert images[0].large.url in body
    assert "js/lightbox.js" in body
    assert 'id="lightbox"' in body


def test_ficha_sin_imagenes_no_rompe(client, project):
    body = client.get(project.get_absolute_url()).content.decode()
    assert 'id="lightbox"' not in body


def test_relacionados_excluyen_al_propio_y_a_borradores(client, project, vivienda):
    make_project(vivienda, "casa-hermana", title="Casa Hermana")
    make_project(vivienda, "casa-oculta", title="Casa Oculta", status=Project.Status.DRAFT)
    body = client.get(project.get_absolute_url()).content.decode()
    assert "Otros proyectos" in body
    assert "Casa Hermana" in body
    assert "Casa Oculta" not in body
    assert body.count('href="/proyectos/casa-ll/"') == 0


def test_cta_whatsapp_y_telefono(client, project):
    SiteSettings.objects.create(whatsapp="5493329000000", phone="+54 3329 40-0000")
    body = client.get(project.get_absolute_url()).content.decode()
    assert "https://wa.me/5493329000000?text=Hola%20IKI%2C%20vi%20el%20proyecto" in body
    assert 'href="tel:+543329400000"' in body


def test_cta_sin_datos_de_contacto_no_muestra_botones(client, project):
    body = client.get(project.get_absolute_url()).content.decode()
    assert "wa.me" not in body
    assert "tel:" not in body
    assert "¿Te gustó este proyecto?" in body
