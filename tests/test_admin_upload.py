import pytest
from django.urls import reverse

from apps.projects.models import Project, ProjectImage, ProjectType
from tests.factories import jpeg_bytes, upload

pytestmark = pytest.mark.django_db


@pytest.fixture
def project():
    project_type = ProjectType.objects.create(name="Vivienda", slug="vivienda")
    return Project.objects.create(
        title="Casa LL",
        slug="casa-ll",
        category=Project.Category.OBRA,
        project_type=project_type,
        location="Baradero",
    )


def upload_url(project):
    return reverse("admin:projects_project_upload_images", args=[project.pk])


def jpeg(name, size=(800, 600)):
    return upload(jpeg_bytes(size=size, with_gps=False), name)


def test_la_ficha_ofrece_subir_imagenes(admin_client, project):
    url = reverse("admin:projects_project_change", args=[project.pk])
    assert upload_url(project) in admin_client.get(url).content.decode()


def test_proyecto_nuevo_pide_guardar_antes(admin_client):
    response = admin_client.get(reverse("admin:projects_project_add"))
    assert "Guardá el proyecto" in response.content.decode()


def test_pagina_de_subida_carga_con_input_multiple(admin_client, project):
    response = admin_client.get(upload_url(project))
    assert response.status_code == 200
    assert "multiple" in response.content.decode()


def test_sube_varias_imagenes_con_orden_consecutivo(admin_client, project):
    data = {"files": [jpeg("a.jpg"), jpeg("b.jpg")]}
    response = admin_client.post(upload_url(project), data)
    assert response.status_code == 302
    assert [i.order for i in project.images.all()] == [1, 2]


def test_el_orden_continua_despues_de_las_existentes(admin_client, project):
    ProjectImage.from_upload(project, jpeg("x.jpg"), order=5)
    admin_client.post(upload_url(project), {"files": [jpeg("a.jpg")]})
    assert [i.order for i in project.images.all()] == [5, 6]


def test_archivo_invalido_se_informa_y_los_validos_se_guardan(admin_client, project):
    data = {"files": [jpeg("ok.jpg"), upload(b"no soy una imagen", "malo.jpg")]}
    response = admin_client.post(upload_url(project), data, follow=True)
    assert project.images.count() == 1
    texts = [str(m) for m in response.context["messages"]]
    assert any("malo.jpg" in t for t in texts)
    assert any("Imágenes subidas: 1" in t for t in texts)


def test_sin_archivos_vuelve_a_mostrar_el_formulario(admin_client, project):
    response = admin_client.post(upload_url(project), {})
    assert response.status_code == 200
    assert project.images.count() == 0


def test_tope_de_imagenes_por_subida(admin_client, project):
    files = [jpeg(f"{i}.jpg", size=(50, 50)) for i in range(21)]
    response = admin_client.post(upload_url(project), {"files": files})
    assert response.status_code == 200
    assert project.images.count() == 0
    assert "Máximo 20" in response.content.decode()


def test_anonimo_va_al_login(client, project):
    response = client.post(upload_url(project), {"files": [jpeg("a.jpg")]})
    assert response.status_code == 302
    assert "login" in response.url
    assert project.images.count() == 0


def test_staff_sin_permisos_no_puede_subir(client, django_user_model, project):
    user = django_user_model.objects.create_user("editor", password="x" * 20, is_staff=True)
    client.force_login(user)
    response = client.post(upload_url(project), {"files": [jpeg("a.jpg")]})
    assert response.status_code == 403
    assert project.images.count() == 0


def test_proyecto_inexistente_da_404(admin_client, project):
    url = reverse("admin:projects_project_upload_images", args=[project.pk + 999])
    assert admin_client.get(url).status_code == 404
