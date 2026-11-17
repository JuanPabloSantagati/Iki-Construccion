import json
import re

import pytest
from django.test import override_settings

from apps.core.models import SiteSettings
from apps.projects.models import Project, ProjectType
from apps.services.models import Service
from tests.test_portfolio import add_image, make_project

pytestmark = pytest.mark.django_db


@pytest.fixture
def project():
    kind = ProjectType.objects.create(name="Vivienda", slug="vivienda")
    return make_project(kind, "casa-ll", title="Casa LL")


def test_sitemap_lista_solo_publicados(client, project):
    kind = project.project_type
    make_project(kind, "borrador", status=Project.Status.DRAFT)
    Service.objects.create(slug="renders", title="Renders", is_published=True)
    Service.objects.create(slug="oculto", title="Oculto", is_published=False)
    body = client.get("/sitemap.xml").content.decode()
    assert "/proyectos/casa-ll/" in body
    assert "/servicios/renders/" in body
    assert "borrador" not in body
    assert "oculto" not in body
    assert "<loc>http://testserver/estudio/</loc>" in body


def test_robots_apunta_al_sitemap_y_no_revela_el_admin(client, settings):
    body = client.get("/robots.txt").content.decode()
    assert "Sitemap: http://testserver/sitemap.xml" in body
    assert "Disallow: /contacto/gracias/" in body
    assert settings.ADMIN_URL not in body


def test_security_txt_requiere_email(client):
    assert client.get("/.well-known/security.txt").status_code == 404
    SiteSettings.objects.create(email="hola@iki.example")
    body = client.get("/.well-known/security.txt").content.decode()
    assert "Contact: mailto:hola@iki.example" in body
    assert "Expires: " in body


def test_canonical_ignora_los_filtros(client, project):
    body = client.get("/proyectos/?categoria=obra").content.decode()
    assert '<link rel="canonical" href="http://testserver/proyectos/">' in body


def test_open_graph_de_proyecto_con_portada(client, project):
    add_image(project, is_cover=True)
    body = client.get(project.get_absolute_url()).content.decode()
    assert '<meta property="og:type" content="article">' in body
    assert '<meta property="og:title" content="Casa LL">' in body
    assert re.search(r'<meta property="og:image" content="http://testserver/', body)


def test_json_ld_de_la_home_es_valido_y_escapado(client):
    SiteSettings.objects.create(phone="+54 3329 40-0000", instagram="https://instagram.com/iki")
    body = client.get("/").content.decode()
    match = re.search(r'<script type="application/ld\+json">(.*?)</script>', body, re.S)
    data = json.loads(match.group(1))
    assert data["@type"] == "HomeAndConstructionBusiness"
    assert data["telephone"] == "+54 3329 40-0000"
    assert data["sameAs"] == ["https://instagram.com/iki"]


def test_json_ld_no_deja_cerrar_el_script(client):
    SiteSettings.objects.create(phone="</script><b>x")
    body = client.get("/").content.decode()
    assert "</script><b>" not in body


def test_csp_en_el_sitio_publico_y_no_en_el_admin(client, settings):
    csp = client.get("/").headers["Content-Security-Policy"]
    assert "default-src 'self'" in csp
    assert "frame-ancestors 'none'" in csp
    assert "script-src" not in csp  # cae en default-src 'self': sin inline
    assert "Content-Security-Policy" not in client.get(f"/{settings.ADMIN_URL}login/").headers


@override_settings(CSP_REPORT_ONLY=True, CSP_IMG_HOST="https://abc.supabase.co")
def test_csp_report_only_y_host_de_imagenes(client):
    response = client.get("/")
    assert "Content-Security-Policy" not in response.headers
    assert "https://abc.supabase.co" in response.headers["Content-Security-Policy-Report-Only"]
