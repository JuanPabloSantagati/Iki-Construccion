# Etapa B1 · PR 2 — Modelos de `projects` y pipeline de imágenes — Plan de implementación

> **Para agentes:** SUB-SKILL REQUERIDA: usar superpowers:subagent-driven-development (recomendado)
> o superpowers:executing-plans para implementar este plan tarea por tarea. Los pasos usan
> checkboxes (`- [ ]`).

**Objetivo:** crear el pipeline seguro de imágenes, los modelos de `projects` (`ProjectType`,
`Project`, `ProjectFact`, `ProjectImage`) y la foto opcional de `TeamMember`, con tests.

**Arquitectura:** el pipeline vive en `apps/core/images.py` (lo comparten `core` y `projects`).
`process_image(uploaded)` valida por contenido, re-codifica a WebP en 3 tamaños, descarta todos
los metadatos y nombra con UUID. Los modelos nunca guardan un archivo que no haya pasado por ahí.
La descripción del proyecto se sanitiza con `nh3` al guardar.

**Stack:** Django 5.2, Pillow 13, nh3 (dependencia nueva), pytest-django, ruff.
Spec: `docs/superpowers/specs/2026-11-06-etapa-b1-modelos-admin-design.md`.

**Convenciones (de `CLAUDE.md`):** código en inglés, `verbose_name` en español. Commits
convencionales. Cada commit termina con la línea
`Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>` (segundo `-m`).

**Dependencia de rama:** este PR se apila sobre el PR 1 (`feature/etapa-b1-modelos-base`,
PR #4) porque `Project` referencia `core.Zone` y `services.Service`. El PR se abre contra esa
rama; cuando se mergee el PR 1, GitHub cambia la base a `main`.

**Desvíos respecto del spec (a anotar en el PR):**
1. El pipeline queda en `apps/core/images.py` y no en `apps/projects/images.py`, porque también
   lo usa `TeamMember` (evita que `core` dependa de `projects`).
2. Se acepta también el formato `MPO` (fotos de celular con varias capas), además de JPEG, PNG y WebP.
3. `TeamMember.photo` entra acá, con un método `set_photo` que obliga a pasar por el pipeline.
4. Al borrar una imagen se borran sus archivos del storage (si no, las fotos "borradas" seguirían
   públicas en el bucket).

---

## Estructura de archivos

| Archivo | Responsabilidad |
|---|---|
| `requirements/base.in`, `base.txt`, `dev.txt` | agregar `nh3` (con hashes) |
| `apps/core/images.py` | `process_image`: validar, limpiar metadatos, redimensionar, WebP, UUID |
| `apps/projects/sanitize.py` | `clean_html`: sanitiza el HTML de las descripciones |
| `apps/projects/models.py` | `ProjectType`, `Project`, `ProjectFact`, `ProjectImage` + borrado de archivos |
| `apps/core/models.py` | `TeamMember.photo` y `set_photo` |
| `apps/projects/migrations/0001_initial.py`, `apps/core/migrations/0002_*.py` | generadas |
| `tests/factories.py` | helpers para fabricar imágenes de prueba |
| `tests/test_images.py`, `tests/test_sanitize.py`, `tests/test_models_projects.py`, `tests/test_team_photo.py` | tests |

Comandos desde la raíz del repo, con el venv activo (`source .venv/Scripts/activate`).

---

### Task 0: Rama de trabajo

- [ ] **Step 1: Rama apilada sobre el PR 1**

```bash
git switch feature/etapa-b1-modelos-base
git switch -c feature/etapa-b1-proyectos-imagenes
```

- [ ] **Step 2: Commitear el plan**

```bash
ruff format docs/superpowers/plans/2026-11-06-etapa-b1-pr2-proyectos-imagenes.md
git add docs/superpowers/plans/2026-11-06-etapa-b1-pr2-proyectos-imagenes.md
git commit -m "docs: plan de implementación del PR 2 de B1" \
  -m "Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>"
```

---

### Task 1: Dependencia `nh3`

**Files:**
- Modify: `requirements/base.in`, `requirements/base.txt`, `requirements/dev.txt`

- [ ] **Step 1: Agregar la dependencia directa**

Agregar la línea `nh3` al final de `requirements/base.in`.

- [ ] **Step 2: Compilar con hashes**

```bash
python -m piptools compile --generate-hashes --allow-unsafe --strip-extras requirements/base.in -o requirements/base.txt
python -m piptools compile --generate-hashes --allow-unsafe --strip-extras requirements/dev.in -o requirements/dev.txt
```

- [ ] **Step 3: Verificar que el diff solo agrega `nh3`**

Run: `git diff --stat requirements/ && git diff requirements/ | grep '^[-+]' | grep -v '^+++\|^---' | grep -v hash`
Expected: solo aparecen líneas `+nh3==...` (y `# via` correspondientes). Si el encabezado
`# by pip-compile with Python 3.12` cambió a 3.13 o se movieron/actualizaron otros paquetes,
**revertir** (`git checkout requirements/*.txt`) y recompilar con Python 3.12
(`py -3.12 -m piptools ...`, como el CI); si no hay 3.12 instalado, reportar BLOCKED.

- [ ] **Step 4: Instalar con hashes y auditar**

```bash
python -m pip install --require-hashes -r requirements/dev.txt
python -c "import nh3; print(nh3.__name__)"
pip-audit --strict --disable-pip --no-deps -r requirements/base.txt -r requirements/dev.txt
```

Expected: imprime `nh3`; pip-audit sin vulnerabilidades.

- [ ] **Step 5: Commit**

```bash
git add requirements/
git commit -m "chore(deps): agregar nh3 para sanitizar HTML" \
  -m "Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>"
```

---

### Task 2: Pipeline de imágenes

**Files:**
- Create: `tests/factories.py`, `tests/test_images.py`, `apps/core/images.py`
- Modify: `docs/superpowers/specs/2026-11-06-etapa-b1-modelos-admin-design.md` (ruta del módulo)

- [ ] **Step 1: Helpers de prueba**

`tests/factories.py`:

```python
from io import BytesIO

from django.core.files.uploadedfile import SimpleUploadedFile
from PIL import Image


def jpeg_bytes(size=(3000, 2000), orientation=None, with_gps=True):
    """JPEG con EXIF de cámara y (opcionalmente) coordenadas GPS."""
    image = Image.new("RGB", size, (200, 120, 40))
    exif = Image.Exif()
    exif[0x010F] = "CamMaker"
    if orientation:
        exif[0x0112] = orientation
    if with_gps:
        gps = exif.get_ifd(0x8825)
        gps[1] = "S"
        gps[2] = (33.0, 24.0, 0.0)
    buffer = BytesIO()
    image.save(buffer, "JPEG", exif=exif)
    return buffer.getvalue()


def png_bytes(size=(400, 300), mode="RGBA"):
    buffer = BytesIO()
    Image.new(mode, size, (10, 20, 30, 128) if mode == "RGBA" else (10, 20, 30)).save(buffer, "PNG")
    return buffer.getvalue()


def upload(data, name="foto.jpg", content_type="image/jpeg"):
    return SimpleUploadedFile(name, data, content_type=content_type)
```

- [ ] **Step 2: Escribir los tests que fallan**

`tests/test_images.py`:

```python
import re
from io import BytesIO

import pytest
from django.core.exceptions import ValidationError
from PIL import Image

from apps.core.images import MAX_UPLOAD_BYTES, process_image
from tests.factories import jpeg_bytes, png_bytes, upload

NAME = re.compile(r"^[0-9a-f]{32}_(thumb|medium|large)\.webp$")


def opened(content):
    return Image.open(BytesIO(content.read()))


def test_genera_tres_tamanos_webp_con_nombre_uuid():
    result = process_image(upload(jpeg_bytes()))
    assert set(result) == {"thumb", "medium", "large"}
    for label, content in result.items():
        assert NAME.match(content.name), content.name
        assert content.name.endswith(f"_{label}.webp")
        assert opened(content).format == "WEBP"


def test_lado_largo_por_tamano_y_proporcion():
    result = process_image(upload(jpeg_bytes(size=(3000, 2000))))
    sizes = {label: opened(c).size for label, c in result.items()}
    assert sizes == {"thumb": (640, 427), "medium": (1280, 853), "large": (2000, 1333)}


def test_no_agranda_imagenes_chicas():
    result = process_image(upload(jpeg_bytes(size=(500, 300))))
    assert all(opened(c).size == (500, 300) for c in result.values())


def test_elimina_exif_y_gps():
    source = upload(jpeg_bytes(with_gps=True))
    assert Image.open(BytesIO(source.read())).getexif().get_ifd(0x8825)  # el origen sí lo tiene
    source.seek(0)
    for content in process_image(source).values():
        image = opened(content)
        assert not image.getexif()
        assert "exif" not in image.info
        assert "icc_profile" not in image.info


def test_aplica_la_orientacion_antes_de_perder_el_exif():
    # Orientation 6 = rotar 90°: una foto de 3000x2000 debe quedar vertical.
    result = process_image(upload(jpeg_bytes(size=(3000, 2000), orientation=6)))
    width, height = opened(result["large"]).size
    assert height > width


def test_png_con_transparencia_conserva_el_alfa():
    result = process_image(upload(png_bytes(mode="RGBA"), "logo.png", "image/png"))
    assert opened(result["medium"]).mode == "RGBA"


def test_rechaza_texto_con_extension_de_imagen():
    with pytest.raises(ValidationError):
        process_image(upload(b"esto no es una imagen", "foto.jpg"))


def test_rechaza_archivo_truncado():
    data = jpeg_bytes()
    with pytest.raises(ValidationError):
        process_image(upload(data[: len(data) // 2]))


def test_rechaza_formato_no_permitido():
    buffer = BytesIO()
    Image.new("RGB", (10, 10)).save(buffer, "GIF")
    with pytest.raises(ValidationError):
        process_image(upload(buffer.getvalue(), "anim.gif", "image/gif"))


def test_rechaza_demasiados_pixeles():
    # 8000x8000 = 64 MP, bajo en bytes (PNG de 1 bit) pero sobre el tope de píxeles.
    buffer = BytesIO()
    Image.new("1", (8000, 8000)).save(buffer, "PNG")
    with pytest.raises(ValidationError):
        process_image(upload(buffer.getvalue(), "bomba.png", "image/png"))


def test_rechaza_archivo_demasiado_pesado():
    with pytest.raises(ValidationError):
        process_image(upload(b"\0" * (MAX_UPLOAD_BYTES + 1)))
```

- [ ] **Step 3: Verificar que falla**

Run: `pytest tests/test_images.py -v`
Expected: FAIL con `ModuleNotFoundError: No module named 'apps.core.images'`.

- [ ] **Step 4: Implementar el pipeline**

`apps/core/images.py`:

```python
"""Procesado seguro de imágenes subidas (regla 9 de CLAUDE.md).

Valida por contenido real, re-codifica a WebP en varios tamaños, descarta todos los metadatos
(EXIF, GPS, perfil de color) y nombra con UUID. Ninguna imagen se guarda sin pasar por acá.
"""

import uuid
from io import BytesIO

from django.core.exceptions import ValidationError
from django.core.files.base import ContentFile
from PIL import Image, ImageOps, UnidentifiedImageError

# MPO: fotos de celular con varias capas; se decodifican como JPEG.
ALLOWED_FORMATS = {"JPEG", "MPO", "PNG", "WEBP"}
MAX_UPLOAD_BYTES = 10 * 1024 * 1024
MAX_PIXELS = 50_000_000  # protección contra decompression bombs
SIZES = {"thumb": 640, "medium": 1280, "large": 2000}  # lado largo en px
WEBP_QUALITY = 82


def _open_validated(uploaded):
    if uploaded.size > MAX_UPLOAD_BYTES:
        raise ValidationError("La imagen supera los 10 MB.")
    try:
        image = Image.open(uploaded)
        if image.format not in ALLOWED_FORMATS:
            raise ValidationError("Formato no permitido. Usá JPEG, PNG o WebP.")
        width, height = image.size
        if width * height > MAX_PIXELS:
            raise ValidationError("La imagen tiene demasiados píxeles.")
        image.load()  # decodifica todo: detecta archivos truncados o corruptos
    except (
        UnidentifiedImageError,
        OSError,
        SyntaxError,
        ValueError,
        Image.DecompressionBombError,
    ) as exc:
        raise ValidationError("El archivo no es una imagen válida.") from exc
    return image


def _strip_metadata(image):
    """Copia solo los píxeles: no hereda EXIF, GPS, ICC ni textos del original."""
    image = ImageOps.exif_transpose(image)  # aplica la rotación antes de perder el EXIF
    has_alpha = image.mode in ("RGBA", "LA", "PA") or "transparency" in image.info
    mode = "RGBA" if has_alpha else "RGB"
    image = image.convert(mode)
    return Image.frombytes(mode, image.size, image.tobytes())


def process_image(uploaded):
    """Devuelve {"thumb", "medium", "large"} -> ContentFile WebP listos para guardar.

    Lanza ValidationError si el archivo no es una imagen aceptable.
    """
    clean = _strip_metadata(_open_validated(uploaded))
    stem = uuid.uuid4().hex
    outputs = {}
    for label, long_side in SIZES.items():
        resized = clean.copy()
        resized.thumbnail((long_side, long_side), Image.Resampling.LANCZOS)  # nunca agranda
        buffer = BytesIO()
        resized.save(buffer, "WEBP", quality=WEBP_QUALITY, method=4)
        outputs[label] = ContentFile(buffer.getvalue(), name=f"{stem}_{label}.webp")
    return outputs
```

- [ ] **Step 5: Verificar que pasa**

Run: `pytest tests/test_images.py -v`
Expected: 11 passed.

- [ ] **Step 6: Corregir la ruta del módulo en el spec**

```bash
sed -i 's#`apps/projects/images.py`, una función#`apps/core/images.py` (compartido por `core` y `projects`), una función#' \
  docs/superpowers/specs/2026-11-06-etapa-b1-modelos-admin-design.md
grep -n "apps/core/images.py" docs/superpowers/specs/2026-11-06-etapa-b1-modelos-admin-design.md
```

Expected: una línea con la ruta nueva.

- [ ] **Step 7: Lint y commit**

```bash
ruff check . && ruff format --check .
git add apps/core/images.py tests/factories.py tests/test_images.py docs/superpowers/specs
git commit -m "feat(core): pipeline seguro de imágenes (WebP, sin EXIF, UUID)" \
  -m "Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>"
```

---

### Task 3: Sanitizador de HTML

**Files:**
- Create: `apps/projects/sanitize.py`, `tests/test_sanitize.py`

- [ ] **Step 1: Escribir los tests que fallan**

`tests/test_sanitize.py`:

```python
from apps.projects.sanitize import clean_html


def test_quita_scripts_y_manejadores_de_eventos():
    html = '<p onclick="x()">Hola<script>alert(1)</script></p>'
    result = clean_html(html)
    assert "<script" not in result
    assert "alert" not in result
    assert "onclick" not in result
    assert "Hola" in result


def test_quita_enlaces_javascript():
    assert "javascript" not in clean_html('<a href="javascript:alert(1)">x</a>')


def test_conserva_formato_permitido_y_enlaces_seguros():
    result = clean_html('<p><strong>Casa</strong> <a href="https://iki.example">sitio</a></p>')
    assert "<strong>Casa</strong>" in result
    assert 'href="https://iki.example"' in result
    assert 'rel="noopener noreferrer"' in result


def test_quita_etiquetas_no_permitidas():
    result = clean_html('<iframe src="https://x.example"></iframe><img src="a.png"><p>ok</p>')
    assert "<iframe" not in result
    assert "<img" not in result
    assert "<p>ok</p>" in result
```

- [ ] **Step 2: Verificar que falla**

Run: `pytest tests/test_sanitize.py -v`
Expected: FAIL con `ModuleNotFoundError: No module named 'apps.projects.sanitize'`.

- [ ] **Step 3: Implementar**

`apps/projects/sanitize.py`:

```python
"""Sanitizado de HTML cargado por usuarios (regla 6 de CLAUDE.md)."""

import nh3

ALLOWED_TAGS = {"p", "br", "strong", "em", "ul", "ol", "li", "h3", "h4", "blockquote", "a"}
ALLOWED_ATTRIBUTES = {"a": {"href", "title"}}
ALLOWED_SCHEMES = {"http", "https", "mailto"}


def clean_html(value):
    """Deja solo formato básico y enlaces http(s)/mailto; nh3 agrega rel="noopener noreferrer"."""
    return nh3.clean(
        value,
        tags=ALLOWED_TAGS,
        attributes=ALLOWED_ATTRIBUTES,
        url_schemes=ALLOWED_SCHEMES,
    )
```

- [ ] **Step 4: Verificar que pasa**

Run: `pytest tests/test_sanitize.py -v`
Expected: 4 passed.

- [ ] **Step 5: Commit**

```bash
ruff check . && ruff format --check .
git add apps/projects/sanitize.py tests/test_sanitize.py
git commit -m "feat(projects): sanitizador de HTML con nh3" \
  -m "Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>"
```

---

### Task 4: `ProjectType`, `Project` y `ProjectFact`

**Files:**
- Modify: `apps/projects/models.py` (hoy vacío)
- Create: `tests/test_models_projects.py`, `apps/projects/migrations/0001_initial.py` (generado)

- [ ] **Step 1: Escribir los tests que fallan**

`tests/test_models_projects.py`:

```python
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
```

- [ ] **Step 2: Verificar que falla**

Run: `pytest tests/test_models_projects.py -v`
Expected: FAIL con `ImportError: cannot import name 'Project'`.

- [ ] **Step 3: Implementar los modelos**

`apps/projects/models.py`:

```python
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from .sanitize import clean_html


class ProjectType(models.Model):
    """Tipo de proyecto (vivienda, local comercial, reforma...), para filtrar el portfolio."""

    name = models.CharField("nombre", max_length=100)
    slug = models.SlugField("slug", unique=True)

    class Meta:
        ordering = ["name"]
        verbose_name = "tipo de proyecto"
        verbose_name_plural = "tipos de proyecto"

    def __str__(self):
        return self.name


class Project(models.Model):
    class Status(models.TextChoices):
        DRAFT = "draft", "Borrador"
        PUBLISHED = "published", "Publicado"

    class Category(models.TextChoices):
        OBRA = "obra", "Obra"
        PROYECTO = "proyecto", "Proyecto"
        RENDER = "render", "Render"

    title = models.CharField("título", max_length=150)
    slug = models.SlugField("slug", unique=True)
    status = models.CharField("estado", max_length=10, choices=Status, default=Status.DRAFT)
    category = models.CharField("categoría", max_length=10, choices=Category)
    project_type = models.ForeignKey(
        ProjectType,
        on_delete=models.PROTECT,
        related_name="projects",
        verbose_name="tipo",
    )
    location = models.CharField("ubicación", max_length=150)
    zone = models.ForeignKey(
        "core.Zone",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="projects",
        verbose_name="zona",
    )
    area_m2 = models.PositiveIntegerField("superficie (m²)", null=True, blank=True)
    year = models.PositiveSmallIntegerField(
        "año",
        null=True,
        blank=True,
        validators=[MinValueValidator(1900), MaxValueValidator(2100)],
    )
    summary = models.CharField("resumen", max_length=280, blank=True)
    description = models.TextField(
        "descripción", blank=True, help_text="Admite formato básico; se sanitiza al guardar."
    )
    services = models.ManyToManyField(
        "services.Service", blank=True, related_name="projects", verbose_name="servicios"
    )
    is_featured = models.BooleanField("destacado", default=False)
    seo_title = models.CharField("título SEO", max_length=70, blank=True)
    seo_description = models.CharField("descripción SEO", max_length=160, blank=True)
    created_at = models.DateTimeField("creado", auto_now_add=True)
    updated_at = models.DateTimeField("actualizado", auto_now=True)

    class Meta:
        ordering = ["-year", "-created_at"]
        verbose_name = "proyecto"
        verbose_name_plural = "proyectos"

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        self.description = clean_html(self.description)
        super().save(*args, **kwargs)


class ProjectFact(models.Model):
    """Dato extra de la ficha (ej: "Superficie" / "180 m²")."""

    project = models.ForeignKey(
        Project, on_delete=models.CASCADE, related_name="facts", verbose_name="proyecto"
    )
    label = models.CharField("dato", max_length=80)
    value = models.CharField("valor", max_length=150)
    order = models.PositiveSmallIntegerField("orden", default=0)

    class Meta:
        ordering = ["order", "id"]
        verbose_name = "dato del proyecto"
        verbose_name_plural = "datos del proyecto"

    def __str__(self):
        return f"{self.label}: {self.value}"
```

- [ ] **Step 4: Generar la migración**

Run: `python manage.py makemigrations projects`
Expected: `Create model ProjectType`, `Create model Project`, `Create model ProjectFact`.

- [ ] **Step 5: Verificar que pasa**

Run: `pytest tests/test_models_projects.py -v`
Expected: 9 passed.

- [ ] **Step 6: Commit**

```bash
ruff check . && ruff format --check .
git add apps/projects tests/test_models_projects.py
git commit -m "feat(projects): modelos ProjectType, Project y ProjectFact" \
  -m "Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>"
```

---

### Task 5: `ProjectImage`

**Files:**
- Modify: `apps/projects/models.py` (agregar al final), `tests/test_models_projects.py` (agregar al final)
- Create: `apps/projects/migrations/0002_projectimage.py` (generado)

- [ ] **Step 1: Agregar los tests que fallan**

Agregar al final de `tests/test_models_projects.py` (y estas líneas a los imports del archivo:
`from django.core.exceptions import ValidationError`, `from apps.projects.models import ProjectImage`,
`from tests.factories import jpeg_bytes, upload`):

```python
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
```

- [ ] **Step 2: Verificar que falla**

Run: `pytest tests/test_models_projects.py -v`
Expected: FAIL con `ImportError: cannot import name 'ProjectImage'`.

- [ ] **Step 3: Implementar el modelo**

En `apps/projects/models.py`, reemplazar los imports del tope por:

```python
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models, transaction
from django.db.models.signals import post_delete
from django.dispatch import receiver

from apps.core.images import SIZES, process_image

from .sanitize import clean_html
```

y agregar al final del archivo:

```python
class ProjectImage(models.Model):
    """Imagen de un proyecto en 3 tamaños WebP. Se crea SIEMPRE con `from_upload`."""

    project = models.ForeignKey(
        Project, on_delete=models.CASCADE, related_name="images", verbose_name="proyecto"
    )
    thumb = models.ImageField("miniatura", upload_to="projects/")
    medium = models.ImageField("mediana", upload_to="projects/")
    large = models.ImageField("grande", upload_to="projects/")
    alt = models.CharField("texto alternativo", max_length=200, blank=True)
    order = models.PositiveSmallIntegerField("orden", default=0)
    is_cover = models.BooleanField("portada", default=False)
    created_at = models.DateTimeField("subida", auto_now_add=True)

    class Meta:
        ordering = ["order", "id"]
        verbose_name = "imagen"
        verbose_name_plural = "imágenes"
        constraints = [
            models.UniqueConstraint(
                fields=["project"],
                condition=models.Q(is_cover=True),
                name="unique_cover_per_project",
            ),
        ]

    def __str__(self):
        return self.alt or f"Imagen de {self.project}"

    def save(self, *args, **kwargs):
        if not self.alt:
            parts = [self.project.title, self.project.location]
            self.alt = ", ".join(part for part in parts if part)[:200]
        super().save(*args, **kwargs)

    @classmethod
    def from_upload(cls, project, uploaded, *, order=0, alt="", is_cover=False):
        """Procesa el archivo (lanza ValidationError si no es una imagen válida) y lo guarda."""
        files = process_image(uploaded)
        image = cls(project=project, order=order, alt=alt, is_cover=is_cover)
        for label, content in files.items():
            getattr(image, label).save(content.name, content, save=False)
        image.save()
        return image


@receiver(post_delete, sender=ProjectImage)
def delete_image_files(sender, instance, **kwargs):
    """Borra los archivos del storage al borrar la imagen (si no, seguirían públicos)."""
    names = [getattr(instance, label).name for label in SIZES]
    storage = instance.thumb.storage
    transaction.on_commit(lambda: [storage.delete(name) for name in names if name])
```

- [ ] **Step 4: Generar la migración**

Run: `python manage.py makemigrations projects`
Expected: `Create model ProjectImage` y `Create constraint unique_cover_per_project`.

- [ ] **Step 5: Verificar que pasa**

Run: `pytest tests/test_models_projects.py -v`
Expected: 18 passed.

- [ ] **Step 6: Commit**

```bash
ruff check . && ruff format --check .
git add apps/projects tests/test_models_projects.py
git commit -m "feat(projects): ProjectImage con portada única y borrado de archivos" \
  -m "Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>"
```

---

### Task 6: Foto opcional de `TeamMember`

**Files:**
- Modify: `apps/core/models.py`
- Create: `tests/test_team_photo.py`, `apps/core/migrations/0002_teammember_photo.py` (generado)

- [ ] **Step 1: Escribir los tests que fallan**

`tests/test_team_photo.py`:

```python
import pytest
from django.core.exceptions import ValidationError

from apps.core.models import TeamMember
from tests.factories import jpeg_bytes, upload

pytestmark = pytest.mark.django_db


def test_sin_foto_por_defecto():
    member = TeamMember.objects.create(name="Ana", role="Arquitecta")
    assert not member.photo


def test_set_photo_guarda_una_version_webp_con_nombre_uuid():
    member = TeamMember.objects.create(name="Ana", role="Arquitecta")
    member.set_photo(upload(jpeg_bytes(size=(1600, 1200))))
    member.save()
    member.refresh_from_db()
    assert member.photo.name.startswith("team/")
    assert member.photo.name.endswith("_medium.webp")
    assert member.photo.storage.exists(member.photo.name)


def test_set_photo_rechaza_archivos_que_no_son_imagen():
    member = TeamMember.objects.create(name="Ana", role="Arquitecta")
    with pytest.raises(ValidationError):
        member.set_photo(upload(b"no soy una imagen"))
    assert not member.photo
```

- [ ] **Step 2: Verificar que falla**

Run: `pytest tests/test_team_photo.py -v`
Expected: FAIL con `AttributeError: ... 'set_photo'` (o campo `photo` inexistente).

- [ ] **Step 3: Implementar**

En `apps/core/models.py`, agregar `from .images import process_image` a los imports y, en
`TeamMember`, el campo (después de `bio`) y el método (después de `__str__`):

```python
    photo = models.ImageField("foto", upload_to="team/", blank=True)
```

```python
    def set_photo(self, uploaded):
        """Única vía para cargar la foto: pasa por el pipeline (lanza ValidationError)."""
        content = process_image(uploaded)["medium"]
        self.photo.save(content.name, content, save=False)
```

También cambiar el docstring de la clase a `"""Integrante del estudio (página Estudio)."""`.

- [ ] **Step 4: Generar la migración**

Run: `python manage.py makemigrations core`
Expected: `Add field photo to teammember` en `apps/core/migrations/0002_teammember_photo.py`.

- [ ] **Step 5: Verificar que pasa**

Run: `pytest tests/test_team_photo.py tests/test_models_core.py -v`
Expected: 13 passed.

- [ ] **Step 6: Commit**

```bash
ruff check . && ruff format --check .
git add apps/core tests/test_team_photo.py
git commit -m "feat(core): foto opcional de TeamMember vía pipeline" \
  -m "Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>"
```

---

### Task 7: Verificación completa y PR

- [ ] **Step 1: Suite completa y lint**

```bash
pytest -q
ruff check . && ruff format --check .
python manage.py makemigrations --check --dry-run
```

Expected: todo en verde (49 previos + 11 + 4 + 18 + 3 = 85 tests), `No changes detected`.

- [ ] **Step 2: Chequeo de prod y auditoría**

```bash
SECRET_KEY=$(python -c "import secrets;print(secrets.token_urlsafe(60))") \
ADMIN_URL=panel-xyz/ DATABASE_URL=postgres://u:p@localhost/db \
ALLOWED_HOSTS=iki.example CSRF_TRUSTED_ORIGINS=https://iki.example DJANGO_READ_DOT_ENV=0 \
python manage.py check --deploy --settings=config.settings.prod
pip-audit --strict --disable-pip --no-deps -r requirements/base.txt -r requirements/dev.txt
```

Expected: `System check identified no issues` y pip-audit sin vulnerabilidades.

- [ ] **Step 3: Subir y abrir el PR (base: la rama del PR 1)**

```bash
git push -u origin feature/etapa-b1-proyectos-imagenes
gh pr create --base feature/etapa-b1-modelos-base --head feature/etapa-b1-proyectos-imagenes \
  --title "feat: modelos de projects y pipeline de imágenes (B1, PR 2/4)" --body-file <archivo>
```

El cuerpo debe incluir: qué cambia, los 4 desvíos del spec (arriba), la dependencia nueva
`nh3`, y el checklist de seguridad (subidas validadas por contenido, EXIF/GPS eliminado,
nombres UUID, sin `|safe`, sin SQL crudo). Aclarar que la base es el PR #4 y que cambia a
`main` cuando ese se mergee. No mergear: requiere revisión de Juan Pablo.

---

## Auto-revisión contra el spec

| Requisito del spec | Dónde |
|---|---|
| `ProjectType`, `Project`, `ProjectFact`, `ProjectImage` | Tasks 4 y 5 |
| Categorías `Obra`, `Proyecto`, `Render` | Task 4 |
| Descripción sanitizada con `nh3` | Tasks 1, 3 y 4 |
| Portada única por proyecto (restricción en DB) | Task 5 |
| Validación por contenido, tope de peso y de píxeles | Task 2 |
| Orientación aplicada y EXIF/GPS eliminados | Task 2 |
| WebP en 3 tamaños, sin agrandar, nombre UUID | Task 2 |
| `alt` autogenerado ("Proyecto, ubicación") | Task 5 |
| `TeamMember.photo` (diferido del PR 1) | Task 6 |
| Admin con subida múltiple | PR 3 (plan aparte) |
| `seed_projects` | PR 4 (plan aparte) |
