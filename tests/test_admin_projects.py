import pytest
from django.urls import reverse

from apps.projects.models import Project, ProjectType

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


@pytest.mark.parametrize(
    "name",
    [
        "admin:projects_project_changelist",
        "admin:projects_project_add",
        "admin:projects_projecttype_changelist",
        "admin:projects_projecttype_add",
    ],
)
def test_paginas_cargan(admin_client, name):
    assert admin_client.get(reverse(name)).status_code == 200


def test_filtros_del_listado_de_proyectos(admin_client, project):
    url = reverse("admin:projects_project_changelist")
    response = admin_client.get(url, {"status__exact": "draft", "category__exact": "obra"})
    assert response.status_code == 200
    assert "Casa LL" in response.content.decode()


def test_ficha_del_proyecto_carga_con_sus_inlines(admin_client, project):
    url = reverse("admin:projects_project_change", args=[project.pk])
    response = admin_client.get(url)
    assert response.status_code == 200
    body = response.content.decode()
    assert "facts-TOTAL_FORMS" in body
    assert "images-TOTAL_FORMS" in body
