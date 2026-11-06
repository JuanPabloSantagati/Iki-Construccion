# Etapa B1 · PR 3 — Admin con subida múltiple — Plan de implementación

> **Para agentes:** SUB-SKILL REQUERIDA: usar superpowers:subagent-driven-development (recomendado)
> o superpowers:executing-plans para implementar este plan tarea por tarea. Los pasos usan
> checkboxes (`- [ ]`).

**Objetivo:** que los socios puedan cargar y administrar todo el contenido desde el admin de
Django: proyectos con datos e imágenes, servicios con pasos, zonas, equipo, datos del sitio y
consultas recibidas.

**Arquitectura:** un `admin.py` por app, sin dependencias nuevas ni JS de terceros. La subida
múltiple es una vista propia colgada de `ProjectAdmin` (`.../subir-imagenes/`) con un
`<input multiple>`; cada archivo pasa por `ProjectImage.from_upload` (el pipeline del PR 2).
El orden es un campo numérico editable. Las imágenes existentes se editan en un inline que no
permite agregar (se agregan solo con la vista de subida).

**Stack:** Django 5.2 admin, pytest-django (`admin_client`), ruff. Spec:
`docs/superpowers/specs/2026-11-06-etapa-b1-modelos-admin-design.md`.

**Convenciones (de `CLAUDE.md`):** código en inglés, textos visibles en español. Commits
convencionales. Cada commit termina con la línea
`Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>` (segundo `-m`).

**Dependencia de rama:** apilado sobre el PR 2 (`feature/etapa-b1-proyectos-imagenes`, PR #5),
que a su vez está sobre el PR 1 (PR #4). El PR se abre contra la rama del PR 2.

**Cambio en código del PR 2 (a anotar en el PR):** al marcar una imagen como portada, la
portada anterior se desmarca sola (`ProjectImage.save`). Sin esto, cambiar de portada desde el
inline daría un error de base de datos según el orden en que se guarden las filas. La
restricción única en la DB se mantiene como red de seguridad.

**Fuera de alcance:** 2FA, django-axes, roles y RLS (etapa B2). Hasta B2 el admin solo debe
usarse en local/dev, nunca expuesto públicamente.

---

## Estructura de archivos

| Archivo | Responsabilidad |
|---|---|
| `apps/projects/models.py` | `ProjectImage.save`: una sola portada por proyecto |
| `apps/core/admin.py` | `SiteSettings` (singleton), `Zone`, `TeamMember` (foto por pipeline) |
| `apps/services/admin.py` | `Service` con inline de pasos |
| `apps/contact/admin.py` | `Inquiry` de solo lectura (salvo el estado) |
| `apps/projects/admin.py` | `ProjectType`, `Project` con inlines y vista de subida |
| `apps/projects/forms.py` | `UploadImagesForm` (campo de archivos múltiples) |
| `templates/admin/projects/project/upload_images.html` | página de subida |
| `tests/test_admin_*.py` | tests del admin |

Comandos desde la raíz del repo, con el venv activo (`source .venv/Scripts/activate`).

---

### Task 0: Rama de trabajo

- [ ] **Step 1: Rama apilada sobre el PR 2**

```bash
git switch feature/etapa-b1-proyectos-imagenes
git switch -c feature/etapa-b1-admin
```

- [ ] **Step 2: Commitear el plan**

```bash
ruff format docs/superpowers/plans/2026-11-06-etapa-b1-pr3-admin.md
git add docs/superpowers/plans/2026-11-06-etapa-b1-pr3-admin.md
git commit -m "docs: plan de implementación del PR 3 de B1" \
  -m "Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>"
```

---

### Task 1: Una sola portada por proyecto

**Files:**
- Modify: `apps/projects/models.py` (`ProjectImage.save`), `tests/test_models_projects.py`

- [ ] **Step 1: Reemplazar el test de la portada por dos tests**

En `tests/test_models_projects.py`, reemplazar la función
`test_una_sola_portada_por_proyecto` completa por:

```python
def test_marcar_nueva_portada_desmarca_la_anterior(project_type):
    project = make_project(project_type)
    first = new_image(project, is_cover=True)
    second = new_image(project, is_cover=True)
    first.refresh_from_db()
    assert (first.is_cover, second.is_cover) == (False, True)


def test_la_db_impide_dos_portadas_aunque_se_salte_save(project_type):
    project = make_project(project_type)
    new_image(project, is_cover=True)
    other = new_image(project)
    with pytest.raises(IntegrityError), transaction.atomic():
        ProjectImage.objects.filter(pk=other.pk).update(is_cover=True)
```

- [ ] **Step 2: Verificar que falla**

Run: `pytest tests/test_models_projects.py -v`
Expected: FAIL en `test_marcar_nueva_portada_desmarca_la_anterior` con `IntegrityError`.

- [ ] **Step 3: Implementar**

En `apps/projects/models.py`, reemplazar el método `save` de `ProjectImage` por:

```python
    def save(self, *args, **kwargs):
        if not self.alt:
            parts = [self.project.title, self.project.location]
            self.alt = ", ".join(part for part in parts if part)[:200]
        with transaction.atomic():
            if self.is_cover:
                # Una sola portada por proyecto: la anterior se desmarca antes de guardar.
                type(self).objects.filter(project=self.project, is_cover=True).exclude(
                    pk=self.pk
                ).update(is_cover=False)
            super().save(*args, **kwargs)
```

- [ ] **Step 4: Verificar que pasa**

Run: `pytest tests/test_models_projects.py -v`
Expected: 19 passed.

- [ ] **Step 5: Commit**

```bash
ruff check . && ruff format --check .
git add apps/projects/models.py tests/test_models_projects.py
git commit -m "feat(projects): al marcar una portada se desmarca la anterior" \
  -m "Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>"
```

---

### Task 2: Admin de `core`

**Files:**
- Modify: `apps/core/admin.py` (hoy vacío)
- Create: `tests/test_admin_core.py`

- [ ] **Step 1: Escribir los tests que fallan**

`tests/test_admin_core.py`:

```python
import pytest
from django.urls import reverse

from apps.core.models import SiteSettings, TeamMember
from tests.factories import jpeg_bytes, upload

pytestmark = pytest.mark.django_db


@pytest.mark.parametrize(
    "name",
    [
        "admin:core_zone_changelist",
        "admin:core_zone_add",
        "admin:core_teammember_changelist",
        "admin:core_teammember_add",
    ],
)
def test_paginas_cargan(admin_client, name):
    assert admin_client.get(reverse(name)).status_code == 200


def test_listado_de_site_settings_lleva_al_unico_registro(admin_client):
    response = admin_client.get(reverse("admin:core_sitesettings_changelist"))
    assert response.status_code == 302
    assert response.url == reverse("admin:core_sitesettings_change", args=[1])
    assert admin_client.get(response.url).status_code == 200


def test_site_settings_no_se_agrega_ni_se_borra(admin_client):
    SiteSettings.load()
    assert admin_client.get(reverse("admin:core_sitesettings_add")).status_code == 403
    delete_url = reverse("admin:core_sitesettings_delete", args=[1])
    assert admin_client.get(delete_url).status_code == 403


def test_site_settings_se_edita(admin_client):
    SiteSettings.load()
    data = {
        "whatsapp": "5493329000000",
        "phone": "",
        "email": "hola@iki.example",
        "address": "",
        "instagram": "",
        "facebook": "",
    }
    response = admin_client.post(reverse("admin:core_sitesettings_change", args=[1]), data)
    assert response.status_code == 302
    assert SiteSettings.load().whatsapp == "5493329000000"


def test_alta_de_integrante_con_foto(admin_client):
    data = {
        "name": "Ana",
        "role": "Arquitecta",
        "bio": "",
        "order": 0,
        "new_photo": upload(jpeg_bytes(size=(1600, 1200)), "yo.jpg"),
    }
    response = admin_client.post(reverse("admin:core_teammember_add"), data)
    assert response.status_code == 302
    member = TeamMember.objects.get()
    assert member.photo.name.startswith("team/")
    assert member.photo.name.endswith("_medium.webp")


def test_foto_invalida_no_crea_al_integrante(admin_client):
    data = {
        "name": "Ana",
        "role": "Arquitecta",
        "bio": "",
        "order": 0,
        "new_photo": upload(b"no soy una imagen", "yo.jpg"),
    }
    response = admin_client.post(reverse("admin:core_teammember_add"), data)
    assert response.status_code == 200
    assert TeamMember.objects.count() == 0
    assert "imagen válida" in response.content.decode()
```

- [ ] **Step 2: Verificar que falla**

Run: `pytest tests/test_admin_core.py -v`
Expected: FAIL (`NoReverseMatch` para `admin:core_zone_changelist`).

- [ ] **Step 3: Implementar**

`apps/core/admin.py`:

```python
from django import forms
from django.contrib import admin
from django.shortcuts import redirect
from django.urls import reverse
from django.utils.html import format_html

from .images import process_image
from .models import SiteSettings, TeamMember, Zone


@admin.register(SiteSettings)
class SiteSettingsAdmin(admin.ModelAdmin):
    """Registro único: el listado lleva directo a su formulario; no se agrega ni se borra."""

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def changelist_view(self, request, extra_context=None):
        obj = SiteSettings.load()
        return redirect(reverse("admin:core_sitesettings_change", args=[obj.pk]))


@admin.register(Zone)
class ZoneAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "is_published")
    list_filter = ("is_published",)
    list_editable = ("is_published",)
    search_fields = ("name",)
    prepopulated_fields = {"slug": ("name",)}


class TeamMemberForm(forms.ModelForm):
    """La foto no se edita como ImageField: se sube por `new_photo` y pasa por el pipeline."""

    new_photo = forms.FileField(label="Foto nueva", required=False)

    class Meta:
        model = TeamMember
        exclude = ("photo",)

    def clean_new_photo(self):
        upload = self.cleaned_data.get("new_photo")
        if upload:
            process_image(upload)  # lanza ValidationError si no es una imagen válida
            upload.seek(0)
        return upload


@admin.register(TeamMember)
class TeamMemberAdmin(admin.ModelAdmin):
    form = TeamMemberForm
    list_display = ("name", "role", "order")
    list_editable = ("order",)
    fields = ("name", "role", "bio", "order", "photo_preview", "new_photo")
    readonly_fields = ("photo_preview",)

    @admin.display(description="Foto actual")
    def photo_preview(self, obj):
        if obj and obj.photo:
            return format_html('<img src="{}" width="120" alt="">', obj.photo.url)
        return "—"

    def save_model(self, request, obj, form, change):
        upload = form.cleaned_data.get("new_photo")
        if upload:
            obj.set_photo(upload)
        super().save_model(request, obj, form, change)
```

- [ ] **Step 4: Verificar que pasa**

Run: `pytest tests/test_admin_core.py -v`
Expected: 9 passed.

- [ ] **Step 5: Commit**

```bash
ruff check . && ruff format --check .
git add apps/core/admin.py tests/test_admin_core.py
git commit -m "feat(core): admin de SiteSettings, Zone y TeamMember" \
  -m "Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>"
```

---

### Task 3: Admin de `services` y `contact`

**Files:**
- Modify: `apps/services/admin.py`, `apps/contact/admin.py` (hoy vacíos)
- Create: `tests/test_admin_services_contact.py`

- [ ] **Step 1: Escribir los tests que fallan**

`tests/test_admin_services_contact.py`:

```python
import pytest
from django.urls import reverse
from django.utils import timezone

from apps.contact.models import Inquiry
from apps.services.models import Service

pytestmark = pytest.mark.django_db


@pytest.fixture
def inquiry():
    return Inquiry.objects.create(
        name="Ana",
        email="ana@iki.example",
        message="Hola",
        consent=True,
        consent_at=timezone.now(),
    )


@pytest.mark.parametrize(
    "name",
    [
        "admin:services_service_changelist",
        "admin:services_service_add",
        "admin:contact_inquiry_changelist",
    ],
)
def test_paginas_cargan(admin_client, name):
    assert admin_client.get(reverse(name)).status_code == 200


def test_servicio_con_pasos_se_crea_desde_el_admin(admin_client):
    data = {
        "title": "Dirección de obra",
        "slug": "direccion-de-obra",
        "summary": "",
        "description": "",
        "order": 0,
        "is_published": "on",
        "steps-TOTAL_FORMS": "1",
        "steps-INITIAL_FORMS": "0",
        "steps-MIN_NUM_FORMS": "0",
        "steps-MAX_NUM_FORMS": "1000",
        "steps-0-title": "Anteproyecto",
        "steps-0-description": "",
        "steps-0-order": "1",
    }
    response = admin_client.post(reverse("admin:services_service_add"), data)
    assert response.status_code == 302
    assert Service.objects.get().steps.get().title == "Anteproyecto"


def test_las_consultas_no_se_cargan_a_mano(admin_client):
    assert admin_client.get(reverse("admin:contact_inquiry_add")).status_code == 403


def test_consulta_se_ve_en_el_admin(admin_client, inquiry):
    url = reverse("admin:contact_inquiry_change", args=[inquiry.pk])
    assert admin_client.get(url).status_code == 200


def test_solo_el_estado_de_la_consulta_es_editable(admin_client, inquiry):
    url = reverse("admin:contact_inquiry_change", args=[inquiry.pk])
    response = admin_client.post(url, {"status": "answered", "name": "Otro nombre"})
    assert response.status_code == 302
    inquiry.refresh_from_db()
    assert inquiry.status == Inquiry.Status.ANSWERED
    assert inquiry.name == "Ana"
```

- [ ] **Step 2: Verificar que falla**

Run: `pytest tests/test_admin_services_contact.py -v`
Expected: FAIL (`NoReverseMatch` para `admin:services_service_changelist`).

- [ ] **Step 3: Implementar**

`apps/services/admin.py`:

```python
from django.contrib import admin

from .models import Service, ServiceStep


class ServiceStepInline(admin.TabularInline):
    model = ServiceStep
    extra = 1


@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ("title", "order", "is_published")
    list_editable = ("order", "is_published")
    list_filter = ("is_published",)
    search_fields = ("title",)
    prepopulated_fields = {"slug": ("title",)}
    inlines = [ServiceStepInline]
```

`apps/contact/admin.py`:

```python
from django.contrib import admin

from .models import Inquiry


@admin.register(Inquiry)
class InquiryAdmin(admin.ModelAdmin):
    """Las consultas llegan por el formulario: acá solo se leen y se cambia el estado."""

    list_display = ("name", "email", "status", "created_at")
    list_filter = ("status",)
    search_fields = ("name", "email")
    date_hierarchy = "created_at"
    fields = (
        "status",
        "name",
        "email",
        "phone",
        "message",
        "consent",
        "consent_at",
        "created_at",
    )
    readonly_fields = (
        "name",
        "email",
        "phone",
        "message",
        "consent",
        "consent_at",
        "created_at",
    )

    def has_add_permission(self, request):
        return False
```

- [ ] **Step 4: Verificar que pasa**

Run: `pytest tests/test_admin_services_contact.py -v`
Expected: 7 passed.

- [ ] **Step 5: Commit**

```bash
ruff check . && ruff format --check .
git add apps/services/admin.py apps/contact/admin.py tests/test_admin_services_contact.py
git commit -m "feat: admin de Service (con pasos) e Inquiry (solo lectura)" \
  -m "Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>"
```

---

### Task 4: Admin de `projects` (sin la subida)

**Files:**
- Modify: `apps/projects/admin.py` (hoy vacío)
- Create: `tests/test_admin_projects.py`

- [ ] **Step 1: Escribir los tests que fallan**

`tests/test_admin_projects.py`:

```python
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
```

- [ ] **Step 2: Verificar que falla**

Run: `pytest tests/test_admin_projects.py -v`
Expected: FAIL (`NoReverseMatch` para `admin:projects_project_changelist`).

- [ ] **Step 3: Implementar**

`apps/projects/admin.py`:

```python
from django.contrib import admin
from django.utils.html import format_html

from .models import Project, ProjectFact, ProjectImage, ProjectType


@admin.register(ProjectType)
class ProjectTypeAdmin(admin.ModelAdmin):
    list_display = ("name", "slug")
    search_fields = ("name",)
    prepopulated_fields = {"slug": ("name",)}


class ProjectFactInline(admin.TabularInline):
    model = ProjectFact
    extra = 1


class ProjectImageInline(admin.TabularInline):
    """Edita alt, orden y portada de imágenes ya subidas. Las nuevas entran por 'Subir imágenes'."""

    model = ProjectImage
    extra = 0
    fields = ("preview", "alt", "order", "is_cover")
    readonly_fields = ("preview",)

    def has_add_permission(self, request, obj=None):
        return False

    @admin.display(description="Imagen")
    def preview(self, obj):
        if obj and obj.pk:
            return format_html('<img src="{}" width="120" alt="">', obj.thumb.url)
        return "—"


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ("title", "category", "project_type", "zone", "year", "status", "is_featured")
    list_editable = ("status", "is_featured")
    list_filter = ("status", "category", "project_type", "zone", "is_featured")
    search_fields = ("title", "location")
    prepopulated_fields = {"slug": ("title",)}
    filter_horizontal = ("services",)
    inlines = [ProjectFactInline, ProjectImageInline]
    fieldsets = (
        (None, {"fields": ("title", "slug", "status", "category", "project_type", "is_featured")}),
        ("Ubicación y datos", {"fields": ("location", "zone", "area_m2", "year")}),
        ("Contenido", {"fields": ("summary", "description", "services")}),
        ("SEO", {"classes": ("collapse",), "fields": ("seo_title", "seo_description")}),
    )
```

- [ ] **Step 4: Verificar que pasa**

Run: `pytest tests/test_admin_projects.py -v`
Expected: 6 passed (4 de páginas, 1 de filtros y 1 de ficha).

- [ ] **Step 5: Commit**

```bash
ruff check . && ruff format --check .
git add apps/projects/admin.py tests/test_admin_projects.py
git commit -m "feat(projects): admin de Project y ProjectType con inlines" \
  -m "Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>"
```

---

### Task 5: Subida múltiple de imágenes

**Files:**
- Create: `apps/projects/forms.py`, `templates/admin/projects/project/upload_images.html`, `tests/test_admin_upload.py`
- Modify: `apps/projects/admin.py`

- [ ] **Step 1: Escribir los tests que fallan**

`tests/test_admin_upload.py`:

```python
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
```

- [ ] **Step 2: Verificar que falla**

Run: `pytest tests/test_admin_upload.py -v`
Expected: FAIL (`NoReverseMatch` para `admin:projects_project_upload_images`).

- [ ] **Step 3: Formulario con archivos múltiples**

`apps/projects/forms.py`:

```python
from django import forms
from django.core.exceptions import ValidationError

MAX_FILES_PER_UPLOAD = 20


class MultipleFileInput(forms.ClearableFileInput):
    allow_multiple_selected = True


class MultipleFileField(forms.FileField):
    """Patrón de la documentación de Django para subir varios archivos con un solo input."""

    def __init__(self, *args, **kwargs):
        kwargs.setdefault("widget", MultipleFileInput())
        super().__init__(*args, **kwargs)

    def clean(self, data, initial=None):
        clean_one = super().clean
        if isinstance(data, list | tuple):
            return [clean_one(item, initial) for item in data]
        return [clean_one(data, initial)]


class UploadImagesForm(forms.Form):
    files = MultipleFileField(label="Imágenes")

    def clean_files(self):
        files = self.cleaned_data["files"]
        if not files:
            raise ValidationError("Elegí al menos una imagen.")
        if len(files) > MAX_FILES_PER_UPLOAD:
            raise ValidationError(f"Máximo {MAX_FILES_PER_UPLOAD} imágenes por vez.")
        return files
```

- [ ] **Step 4: Template de la página de subida**

`templates/admin/projects/project/upload_images.html`:

```django
{% extends "admin/base_site.html" %}

{% block breadcrumbs %}
<div class="breadcrumbs">
  <a href="{% url 'admin:index' %}">Inicio</a> ›
  <a href="{% url 'admin:projects_project_changelist' %}">Proyectos</a> ›
  <a href="{% url 'admin:projects_project_change' project.pk %}">{{ project.title }}</a> ›
  Subir imágenes
</div>
{% endblock %}

{% block content %}
<p>Elegí una o varias fotos (JPEG, PNG o WebP; hasta 10 MB cada una, máximo 20 por vez). Se
optimizan, se les borran los datos de ubicación y se guardan en tres tamaños.</p>
<form method="post" enctype="multipart/form-data">
  {% csrf_token %}
  {{ form.non_field_errors }}
  {{ form.files.errors }}
  {{ form.files }}
  <p><input type="submit" value="Subir imágenes" class="default"></p>
</form>
{% endblock %}
```

- [ ] **Step 5: Vista y enlace en `ProjectAdmin`**

En `apps/projects/admin.py`, reemplazar los imports del tope por:

```python
from django.contrib import admin, messages
from django.core.exceptions import PermissionDenied, ValidationError
from django.db.models import Max
from django.http import Http404
from django.shortcuts import redirect
from django.template.response import TemplateResponse
from django.urls import path, reverse
from django.utils.html import format_html

from .forms import UploadImagesForm
from .models import Project, ProjectFact, ProjectImage, ProjectType
```

En `ProjectAdmin`, agregar `readonly_fields = ("upload_link",)`, agregar al `fieldsets` la
sección de imágenes entre "Contenido" y "SEO":

```python
(("Imágenes", {"fields": ("upload_link",)}),)
```

y agregar estos métodos a la clase:

```python
@admin.display(description="Imágenes nuevas")
def upload_link(self, obj):
    if not obj or not obj.pk:
        return "Guardá el proyecto para poder subir imágenes."
    url = reverse("admin:projects_project_upload_images", args=[obj.pk])
    return format_html('<a class="button" href="{}">Subir imágenes</a>', url)


def get_urls(self):
    custom = [
        path(
            "<path:object_id>/subir-imagenes/",
            self.admin_site.admin_view(self.upload_images_view),
            name="projects_project_upload_images",
        ),
    ]
    return custom + super().get_urls()


def upload_images_view(self, request, object_id):
    project = self.get_object(request, object_id)
    if project is None:
        raise Http404
    if not self.has_change_permission(request, project):
        raise PermissionDenied
    form = UploadImagesForm(request.POST or None, request.FILES or None)
    if request.method == "POST" and form.is_valid():
        next_order = (project.images.aggregate(top=Max("order"))["top"] or 0) + 1
        saved = 0
        for uploaded in form.cleaned_data["files"]:
            try:
                ProjectImage.from_upload(project, uploaded, order=next_order + saved)
            except ValidationError as exc:
                self.message_user(
                    request, f"{uploaded.name}: {' '.join(exc.messages)}", messages.ERROR
                )
            else:
                saved += 1
        if saved:
            self.message_user(request, f"Imágenes subidas: {saved}.", messages.SUCCESS)
        return redirect(reverse("admin:projects_project_change", args=[project.pk]))
    context = {
        **self.admin_site.each_context(request),
        "opts": self.model._meta,
        "project": project,
        "form": form,
        "title": f"Subir imágenes · {project.title}",
    }
    return TemplateResponse(request, "admin/projects/project/upload_images.html", context)
```

- [ ] **Step 6: Verificar que pasa**

Run: `pytest tests/test_admin_upload.py tests/test_admin_projects.py -v`
Expected: 17 passed (11 de subida + 6 de admin de projects).

- [ ] **Step 7: Commit**

```bash
ruff check . && ruff format --check .
git add apps/projects templates/admin tests/test_admin_upload.py
git commit -m "feat(projects): subida múltiple de imágenes desde el admin" \
  -m "Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>"
```

---

### Task 6: Verificación completa y PR

- [ ] **Step 1: Suite completa y lint**

```bash
pytest -q
ruff check . && ruff format --check .
python manage.py makemigrations --check --dry-run
```

Expected: todo en verde (85 previos + 1 + 9 + 7 + 6 + 11 = 119 tests; si el conteo difiere,
reportar la diferencia exacta), `No changes detected`.

- [ ] **Step 2: Chequeo de prod**

```bash
SECRET_KEY=$(python -c "import secrets;print(secrets.token_urlsafe(60))") \
ADMIN_URL=panel-xyz/ DATABASE_URL=postgres://u:p@localhost/db \
ALLOWED_HOSTS=iki.example CSRF_TRUSTED_ORIGINS=https://iki.example DJANGO_READ_DOT_ENV=0 \
python manage.py check --deploy --settings=config.settings.prod
```

Expected: `System check identified no issues (0 silenced).`

- [ ] **Step 3: Prueba manual en el admin local**

Con `python manage.py runserver`, entrar a `/gestion-iki/`, crear un proyecto, guardarlo,
usar "Subir imágenes" con 2 o 3 fotos de celular, marcar una portada y cambiarla por otra.
Si no hay fotos a mano, saltear y anotarlo en el PR.

- [ ] **Step 4: Subir y abrir el PR (base: la rama del PR 2)**

```bash
git push -u origin feature/etapa-b1-admin
gh pr create --base feature/etapa-b1-proyectos-imagenes --head feature/etapa-b1-admin \
  --title "feat: admin con subida múltiple de imágenes (B1, PR 3/4)" --body-file <archivo>
```

El cuerpo debe incluir: qué cambia, el cambio de comportamiento de la portada en el PR 2,
que el admin no debe exponerse públicamente hasta la etapa B2 (2FA, axes, roles), que la base
es el PR #5 y el checklist de seguridad (subidas por el pipeline, vista protegida por
`admin_view` + permiso de cambio, CSRF, tope de 20 archivos, nombres de archivo no confiables
y escapados, sin JS de terceros). No mergear: requiere revisión de Juan Pablo.

---

## Auto-revisión contra el spec

| Requisito del spec | Dónde |
|---|---|
| `Project` con inlines de `ProjectFact` y `ProjectImage` | Task 4 |
| Vista "Subir imágenes" con input `multiple`, cada archivo por el pipeline | Task 5 |
| Orden con campo numérico editable | Tasks 2 a 4 (`list_editable`, inline) |
| Portada única | Task 1 |
| `SiteSettings` sin segundo registro ni borrado | Task 2 |
| Listados con filtros por estado, tipo y zona | Task 4 |
| Permisos del admin probados | Task 5 (anónimo y staff sin permisos) |
| `seed_projects` | PR 4 (plan aparte) |
