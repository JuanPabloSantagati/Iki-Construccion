# Etapa B1 · PR 1 — Modelos de `core`, `services` y `contact` — Plan de implementación

> **Para agentes:** SUB-SKILL REQUERIDA: usar superpowers:subagent-driven-development (recomendado)
> o superpowers:executing-plans para implementar este plan tarea por tarea. Los pasos usan
> checkboxes (`- [ ]`).

**Objetivo:** crear los modelos de `core` (`SiteSettings`, `Zone`, `TeamMember`), `services`
(`Service`, `ServiceStep`) y `contact` (`Inquiry`), con migraciones y tests.

**Arquitectura:** modelos Django planos, uno por concepto, sin lógica de negocio. Una migración
`0001_initial` por app. Sin admin (PR 3), sin imágenes (PR 2) y sin vistas (etapas C a E).

**Stack:** Django 5.2, pytest-django, ruff. Spec: `docs/superpowers/specs/2026-11-06-etapa-b1-modelos-admin-design.md`.

**Convenciones (de `CLAUDE.md`):** código y campos en inglés, `verbose_name` en español.
Commits convencionales. Cada commit termina con la línea
`Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>`.

**Desvío respecto del spec:** `TeamMember.photo` NO entra en este PR. Un `ImageField` sin el
pipeline permitiría subidas sin validar (regla 9 de `CLAUDE.md`). Se agrega en el PR 2, cuando
exista `apps/projects/images.py`.

---

## Estructura de archivos

| Archivo | Responsabilidad |
|---|---|
| `apps/core/models.py` | `SiteSettings` (singleton), `Zone`, `TeamMember` |
| `apps/services/models.py` | `Service`, `ServiceStep` |
| `apps/contact/models.py` | `Inquiry` |
| `apps/*/migrations/0001_initial.py` | generadas con `makemigrations` |
| `tests/test_models_core.py` | tests de `core` |
| `tests/test_models_services.py` | tests de `services` |
| `tests/test_models_contact.py` | tests de `contact` |

Todos los comandos se corren desde la raíz del repo, con el venv activo
(`source .venv/Scripts/activate`).

---

### Task 0: Rama de trabajo

- [ ] **Step 1: Crear la rama desde la del spec**

```bash
git switch docs/spec-etapa-b1
git switch -c feature/etapa-b1-modelos-base
```

Esta rama ya contiene el spec. El plan (este archivo) se commitea en el Step 2.

- [ ] **Step 2: Commitear el plan**

```bash
git add docs/superpowers/plans/2026-11-06-etapa-b1-pr1-modelos-base.md
git commit -m "docs: plan de implementación del PR 1 de B1" \
  -m "Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>"
```

---

### Task 1: Modelos de `core`

**Files:**
- Modify: `apps/core/models.py` (hoy vacío)
- Create: `tests/test_models_core.py`
- Create: `apps/core/migrations/0001_initial.py` (generado)

- [ ] **Step 1: Escribir los tests que fallan**

`tests/test_models_core.py`:

```python
import pytest
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction

from apps.core.models import SiteSettings, TeamMember, Zone

pytestmark = pytest.mark.django_db


def test_site_settings_es_singleton():
    SiteSettings.objects.create(email="a@iki.example")
    SiteSettings(email="b@iki.example").save()
    assert SiteSettings.objects.count() == 1
    assert SiteSettings.load().email == "b@iki.example"


def test_site_settings_load_crea_el_registro():
    assert SiteSettings.objects.count() == 0
    assert SiteSettings.load().pk == 1
    assert SiteSettings.objects.count() == 1


@pytest.mark.parametrize("value", ["abc", "123", "+5493329000000", "1" * 16])
def test_whatsapp_invalido(value):
    with pytest.raises(ValidationError):
        SiteSettings(whatsapp=value).clean_fields()


def test_whatsapp_valido_y_vacio():
    SiteSettings(whatsapp="5493329000000").clean_fields()
    SiteSettings(whatsapp="").clean_fields()


def test_zone_slug_unico():
    Zone.objects.create(name="Baradero", slug="baradero")
    with pytest.raises(IntegrityError), transaction.atomic():
        Zone.objects.create(name="Otra", slug="baradero")


def test_zone_no_publicada_por_defecto():
    zone = Zone.objects.create(name="San Pedro", slug="san-pedro")
    assert zone.is_published is False
    assert str(zone) == "San Pedro"


def test_team_member_ordenado_por_order_y_nombre():
    TeamMember.objects.create(name="Zoe", role="Arquitecta", order=1)
    TeamMember.objects.create(name="Ana", role="Arquitecta", order=1)
    TeamMember.objects.create(name="Beto", role="Maestro mayor de obras", order=0)
    assert [m.name for m in TeamMember.objects.all()] == ["Beto", "Ana", "Zoe"]
```

- [ ] **Step 2: Verificar que falla**

Run: `pytest tests/test_models_core.py -v`
Expected: FAIL con `ImportError: cannot import name 'SiteSettings'`.

- [ ] **Step 3: Implementar los modelos**

`apps/core/models.py`:

```python
from django.core.validators import RegexValidator
from django.db import models


class SiteSettings(models.Model):
    """Datos públicos de contacto y redes. Un solo registro (pk=1)."""

    whatsapp = models.CharField(
        "WhatsApp",
        max_length=15,
        blank=True,
        validators=[
            RegexValidator(r"^\d{8,15}$", "Solo dígitos, con código de país (ej: 5493329000000).")
        ],
        help_text="Solo dígitos, con código de país. Ej: 5493329000000.",
    )
    phone = models.CharField("teléfono", max_length=30, blank=True)
    email = models.EmailField("email de contacto", blank=True)
    address = models.CharField("dirección", max_length=200, blank=True)
    instagram = models.URLField("Instagram", blank=True)
    facebook = models.URLField("Facebook", blank=True)

    class Meta:
        verbose_name = "configuración del sitio"
        verbose_name_plural = "configuración del sitio"

    def __str__(self):
        return "Configuración del sitio"

    def save(self, *args, **kwargs):
        self.pk = 1  # singleton: siempre el mismo registro
        super().save(*args, **kwargs)

    @classmethod
    def load(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj


class Zone(models.Model):
    """Zona geográfica para las landings de SEO local (etapa F)."""

    name = models.CharField("nombre", max_length=100)
    slug = models.SlugField("slug", unique=True)
    intro = models.TextField("introducción", blank=True)
    is_published = models.BooleanField("publicada", default=False)

    class Meta:
        ordering = ["name"]
        verbose_name = "zona"
        verbose_name_plural = "zonas"

    def __str__(self):
        return self.name


class TeamMember(models.Model):
    """Integrante del estudio (página Estudio). La foto se agrega en el PR 2."""

    name = models.CharField("nombre", max_length=100)
    role = models.CharField("rol", max_length=100)
    bio = models.TextField("biografía", blank=True)
    order = models.PositiveSmallIntegerField("orden", default=0)

    class Meta:
        ordering = ["order", "name"]
        verbose_name = "integrante del equipo"
        verbose_name_plural = "equipo"

    def __str__(self):
        return self.name
```

- [ ] **Step 4: Generar la migración**

Run: `python manage.py makemigrations core`
Expected: `Create model SiteSettings`, `Create model TeamMember`, `Create model Zone` en `apps/core/migrations/0001_initial.py`.

- [ ] **Step 5: Verificar que pasa**

Run: `pytest tests/test_models_core.py -v`
Expected: 10 passed.

- [ ] **Step 6: Commit**

```bash
git add apps/core tests/test_models_core.py
git commit -m "feat(core): modelos SiteSettings, Zone y TeamMember" \
  -m "Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>"
```

---

### Task 2: Modelos de `services`

**Files:**
- Modify: `apps/services/models.py` (hoy vacío)
- Create: `tests/test_models_services.py`
- Create: `apps/services/migrations/0001_initial.py` (generado)

- [ ] **Step 1: Escribir los tests que fallan**

`tests/test_models_services.py`:

```python
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
```

- [ ] **Step 2: Verificar que falla**

Run: `pytest tests/test_models_services.py -v`
Expected: FAIL con `ImportError: cannot import name 'Service'`.

- [ ] **Step 3: Implementar los modelos**

`apps/services/models.py`:

```python
from django.db import models


class Service(models.Model):
    """Servicio del estudio. El texto es plano: los templates lo escapan (regla 6)."""

    title = models.CharField("título", max_length=120)
    slug = models.SlugField("slug", unique=True)
    summary = models.CharField("resumen", max_length=280, blank=True)
    description = models.TextField("descripción", blank=True)
    order = models.PositiveSmallIntegerField("orden", default=0)
    is_published = models.BooleanField("publicado", default=False)

    class Meta:
        ordering = ["order", "title"]
        verbose_name = "servicio"
        verbose_name_plural = "servicios"

    def __str__(self):
        return self.title


class ServiceStep(models.Model):
    """Paso del proceso de un servicio (se edita como inline del servicio)."""

    service = models.ForeignKey(
        Service, on_delete=models.CASCADE, related_name="steps", verbose_name="servicio"
    )
    title = models.CharField("título", max_length=120)
    description = models.TextField("descripción", blank=True)
    order = models.PositiveSmallIntegerField("orden", default=0)

    class Meta:
        ordering = ["order", "id"]
        verbose_name = "paso del proceso"
        verbose_name_plural = "pasos del proceso"

    def __str__(self):
        return self.title
```

- [ ] **Step 4: Generar la migración**

Run: `python manage.py makemigrations services`
Expected: `Create model Service`, `Create model ServiceStep`.

- [ ] **Step 5: Verificar que pasa**

Run: `pytest tests/test_models_services.py -v`
Expected: 5 passed.

- [ ] **Step 6: Commit**

```bash
git add apps/services tests/test_models_services.py
git commit -m "feat(services): modelos Service y ServiceStep" \
  -m "Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>"
```

---

### Task 3: Modelo de `contact`

**Files:**
- Modify: `apps/contact/models.py` (hoy vacío)
- Create: `tests/test_models_contact.py`
- Create: `apps/contact/migrations/0001_initial.py` (generado)

- [ ] **Step 1: Escribir los tests que fallan**

`tests/test_models_contact.py`:

```python
import pytest
from django.db import IntegrityError, transaction
from django.utils import timezone

from apps.contact.models import Inquiry

pytestmark = pytest.mark.django_db

VALID = {"name": "Ana", "email": "ana@iki.example", "message": "Hola"}


def test_consulta_valida_queda_nueva():
    inquiry = Inquiry.objects.create(**VALID, consent=True, consent_at=timezone.now())
    assert inquiry.status == Inquiry.Status.NEW
    assert inquiry.created_at is not None


def test_sin_consentimiento_no_se_guarda():
    with pytest.raises(IntegrityError), transaction.atomic():
        Inquiry.objects.create(**VALID, consent=False, consent_at=timezone.now())


def test_consentimiento_sin_fecha_no_se_guarda():
    with pytest.raises(IntegrityError), transaction.atomic():
        Inquiry.objects.create(**VALID, consent=True, consent_at=None)


def test_no_guarda_ip_ni_user_agent():
    # Regla 10 de CLAUDE.md / plan: datos mínimos, sin trazas técnicas del visitante.
    names = {f.name for f in Inquiry._meta.get_fields()}
    assert not names & {"ip", "ip_address", "user_agent"}
```

- [ ] **Step 2: Verificar que falla**

Run: `pytest tests/test_models_contact.py -v`
Expected: FAIL con `ImportError: cannot import name 'Inquiry'`.

- [ ] **Step 3: Implementar el modelo**

`apps/contact/models.py`:

```python
from django.db import models


class Inquiry(models.Model):
    """Consulta recibida por el formulario. Datos mínimos: sin IP ni user-agent."""

    class Status(models.TextChoices):
        NEW = "new", "Nueva"
        ANSWERED = "answered", "Respondida"
        ARCHIVED = "archived", "Archivada"

    name = models.CharField("nombre", max_length=120)
    email = models.EmailField("email")
    phone = models.CharField("teléfono", max_length=30, blank=True)
    message = models.TextField("mensaje")
    consent = models.BooleanField("consentimiento", default=False)
    consent_at = models.DateTimeField("fecha del consentimiento", null=True, blank=True)
    status = models.CharField("estado", max_length=10, choices=Status.choices, default=Status.NEW)
    created_at = models.DateTimeField("recibida", auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "consulta"
        verbose_name_plural = "consultas"
        constraints = [
            # Ley 25.326: no se guarda una consulta sin consentimiento explícito y fechado.
            models.CheckConstraint(
                condition=models.Q(consent=True, consent_at__isnull=False),
                name="inquiry_consent_required",
            ),
        ]

    def __str__(self):
        return f"{self.name} ({self.created_at:%d/%m/%Y})"
```

- [ ] **Step 4: Generar la migración**

Run: `python manage.py makemigrations contact`
Expected: `Create model Inquiry` y `Create constraint inquiry_consent_required`.

- [ ] **Step 5: Verificar que pasa**

Run: `pytest tests/test_models_contact.py -v`
Expected: 4 passed.

- [ ] **Step 6: Commit**

```bash
git add apps/contact tests/test_models_contact.py
git commit -m "feat(contact): modelo Inquiry con consentimiento obligatorio" \
  -m "Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>"
```

---

### Task 4: Verificación completa y PR

- [ ] **Step 1: Suite completa y lint**

```bash
pytest -q
ruff check . && ruff format --check .
python manage.py makemigrations --check --dry-run
```

Expected: todos los tests pasan (30 previos + 19 nuevos = 49), ruff sin errores,
`No changes detected`. Si `ruff format --check` falla, correr `ruff format .` y commitear
como `style:`.

- [ ] **Step 2: Chequeo de prod**

```bash
SECRET_KEY=$(python -c "import secrets;print(secrets.token_urlsafe(60))") \
ADMIN_URL=panel-xyz/ DATABASE_URL=postgres://u:p@localhost/db \
ALLOWED_HOSTS=iki.example CSRF_TRUSTED_ORIGINS=https://iki.example DJANGO_READ_DOT_ENV=0 \
python manage.py check --deploy --settings=config.settings.prod
```

Expected: `System check identified no issues (0 silenced).`

- [ ] **Step 3: Subir y abrir el PR**

```bash
git push -u origin feature/etapa-b1-modelos-base
gh pr create --base main --title "feat: modelos de core, services y contact (B1, PR 1/4)" --body-file <(cat <<'EOF'
## Qué cambia

Primer PR de la etapa B1 (spec: `docs/superpowers/specs/2026-11-06-etapa-b1-modelos-admin-design.md`).

- `core`: `SiteSettings` (singleton), `Zone`, `TeamMember`.
- `services`: `Service`, `ServiceStep`.
- `contact`: `Inquiry`, con `CheckConstraint` que exige consentimiento fechado.
- Migraciones `0001_initial` por app y 19 tests nuevos.
- Incluye el spec y el plan de implementación de B1 (para revisión de Juan Pablo).

## Para revisar

- **Desvío del spec:** `TeamMember.photo` queda para el PR 2, porque un `ImageField` sin el pipeline permitiría subidas sin validar (regla 9).
- Sin admin (PR 3), sin imágenes (PR 2) ni vistas.

## Checklist de seguridad

- [x] Sin secretos ni datos reales
- [x] Sin `|safe`, sin SQL crudo
- [x] `Inquiry` sin IP ni user-agent; consentimiento obligatorio en la DB
- [x] Variables nuevas: ninguna

🤖 Generated with [Claude Code](https://claude.com/claude-code)
EOF
)
```

Expected: URL del PR. No mergear: requiere la revisión de Juan Pablo.

---

## Auto-revisión contra el spec

| Requisito del spec | Dónde |
|---|---|
| `SiteSettings` singleton | Task 1 |
| `Zone`, `TeamMember` | Task 1 (sin `photo`: desvío anotado arriba) |
| `Service`, `ServiceStep` con orden | Task 2 |
| `Inquiry` sin IP/UA, con consentimiento y fecha | Task 3 |
| `verbose_name` en español, código en inglés | Tasks 1 a 3 |
| Migraciones y tests | Tasks 1 a 4 |
| `ProjectType`, `Project`, `ProjectFact`, `ProjectImage`, pipeline | PR 2 (plan aparte) |
| Admin, subida múltiple, seed | PR 3 y PR 4 (planes aparte) |
