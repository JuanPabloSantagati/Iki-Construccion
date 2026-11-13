# Etapa B1 · PR 4 — `seed_projects` — Plan de implementación

> **Para agentes:** SUB-SKILL REQUERIDA: usar superpowers:subagent-driven-development (recomendado)
> o superpowers:executing-plans para implementar este plan tarea por tarea. Los pasos usan
> checkboxes (`- [ ]`).

**Objetivo:** un comando `python manage.py seed_projects` que deja la base de desarrollo con los
datos de referencia (tipos de proyecto, servicios con pasos, zonas y dirección del sitio), para
que los socios arranquen a cargar contenido sin tipear todo desde cero.

**Arquitectura:** un solo management command en `apps/projects/management/commands/`, con los
datos como constantes al tope del archivo. Es idempotente y **no pisa lo editado en el admin**:
usa `get_or_create` por slug, y los pasos de un servicio solo se crean cuando el servicio es
nuevo. Se niega a correr con `DEBUG=False` salvo `--force` (spec de B1). Sin dependencias nuevas.

**Stack:** Django 5.2 management commands, pytest-django, ruff. Spec:
`docs/superpowers/specs/2026-11-06-etapa-b1-modelos-admin-design.md` (sección "Seed").

**Convenciones (de `CLAUDE.md`):** código en inglés, textos visibles en español. Commits
convencionales. Cada commit termina con la línea
`Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>` (segundo `-m`).

**Decisiones (a anotar en el PR):**
- **No inventa proyectos, fotos, teléfono, WhatsApp ni mail.** Solo la dirección ("Baradero,
  Buenos Aires", que ya figura en `CLAUDE.md`). Un número falso en `SiteSettings` terminaría
  como botón de WhatsApp real.
- **Todo entra sin publicar** (`is_published=False` en servicios y zonas). Los textos de los
  servicios son borradores genéricos: los socios los revisan y los publican desde el admin.
- **Zonas:** lista provisoria de localidades cercanas a Baradero; la lista real la definen los
  socios (pendiente abierto de zonas/landings).

**Dependencia de rama:** apilado sobre el PR 3 (`feature/etapa-b1-admin`, PR #6), que está sobre
el PR #5 y el PR #4. El PR se abre contra la rama del PR 3.

**Fuera de alcance:** proyectos de ejemplo, imágenes, usuarios de prueba, `SiteSettings` con
datos de contacto.

---

## Estructura de archivos

| Archivo | Responsabilidad |
|---|---|
| `apps/projects/management/__init__.py` | paquete (vacío) |
| `apps/projects/management/commands/__init__.py` | paquete (vacío) |
| `apps/projects/management/commands/seed_projects.py` | el comando y sus datos |
| `tests/test_seed_projects.py` | tests del comando |
| `CLAUDE.md` | una línea en "Comandos" |

Comandos desde la raíz del repo. En Windows, usar el Python del venv:
`.\.venv\Scripts\python.exe -m pytest ...` (PowerShell) o `source .venv/Scripts/activate` (Git Bash).

---

### Task 0: Rama de trabajo

- [ ] **Step 1: Rama apilada sobre el PR 3**

```bash
git switch feature/etapa-b1-admin
git switch -c feature/etapa-b1-seed
```

- [ ] **Step 2: Commitear el plan**

```bash
ruff format docs/superpowers/plans/2026-11-07-etapa-b1-pr4-seed.md
git add docs/superpowers/plans/2026-11-07-etapa-b1-pr4-seed.md
git commit -m "docs: plan de implementación del PR 4 de B1" \
  -m "Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>"
```

---

### Task 1: El comando `seed_projects`

**Files:**
- Create: `apps/projects/management/__init__.py` (vacío), `apps/projects/management/commands/__init__.py` (vacío), `apps/projects/management/commands/seed_projects.py`, `tests/test_seed_projects.py`

- [ ] **Step 1: Escribir los tests que fallan**

`tests/test_seed_projects.py`:

```python
from io import StringIO

import pytest
from django.core.management import call_command
from django.core.management.base import CommandError

from apps.core.models import SiteSettings, Zone
from apps.projects.models import Project, ProjectType
from apps.services.models import Service, ServiceStep

pytestmark = pytest.mark.django_db


@pytest.fixture
def debug_on(settings):
    settings.DEBUG = True


def seed(*args):
    out = StringIO()
    call_command("seed_projects", *args, stdout=out)
    return out.getvalue()


def test_carga_los_datos_de_referencia(debug_on):
    seed()
    assert ProjectType.objects.count() == 5
    assert Zone.objects.count() == 4
    assert Service.objects.count() == 5
    assert ServiceStep.objects.count() == 20
    assert SiteSettings.load().address == "Baradero, Buenos Aires"


def test_no_inventa_proyectos_ni_datos_de_contacto(debug_on):
    seed()
    assert Project.objects.count() == 0
    site = SiteSettings.load()
    assert (site.whatsapp, site.phone, site.email) == ("", "", "")


def test_nada_queda_publicado(debug_on):
    seed()
    assert not Service.objects.filter(is_published=True).exists()
    assert not Zone.objects.filter(is_published=True).exists()


def test_es_idempotente(debug_on):
    seed()
    out = seed()
    assert ProjectType.objects.count() == 5
    assert Zone.objects.count() == 4
    assert Service.objects.count() == 5
    assert ServiceStep.objects.count() == 20
    assert "Nada nuevo" in out


def test_no_pisa_lo_editado_en_el_admin(debug_on):
    seed()
    service = Service.objects.get(slug="construccion")
    service.title = "Obra llave en mano"
    service.is_published = True
    service.save()
    service.steps.all().delete()
    SiteSettings.objects.filter(pk=1).update(address="Otra calle 123")
    seed()
    service.refresh_from_db()
    assert (service.title, service.is_published) == ("Obra llave en mano", True)
    assert service.steps.count() == 0
    assert SiteSettings.load().address == "Otra calle 123"


def test_se_niega_con_debug_apagado():
    with pytest.raises(CommandError, match="DEBUG"):
        seed()
    assert ProjectType.objects.count() == 0


def test_force_permite_correr_con_debug_apagado():
    seed("--force")
    assert ProjectType.objects.count() == 5
```

- [ ] **Step 2: Verificar que falla**

Run: `pytest tests/test_seed_projects.py -v`
Expected: 7 FAIL con `CommandError: Unknown command: 'seed_projects'`.

- [ ] **Step 3: Implementar**

Crear los dos `__init__.py` vacíos y `apps/projects/management/commands/seed_projects.py`:

```python
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from apps.core.models import SiteSettings, Zone
from apps.projects.models import ProjectType
from apps.services.models import Service, ServiceStep

PROJECT_TYPES = [
    ("vivienda", "Vivienda"),
    ("local-comercial", "Local comercial"),
    ("oficina", "Oficina"),
    ("reforma", "Reforma"),
    ("ampliacion", "Ampliación"),
]

# Provisorio: la lista real de zonas la definen los socios desde el admin.
ZONES = [
    ("baradero", "Baradero"),
    ("san-pedro", "San Pedro"),
    ("zarate", "Zárate"),
    ("san-antonio-de-areco", "San Antonio de Areco"),
]

# (slug, título, resumen, pasos). Borradores genéricos: se revisan y publican desde el admin.
SERVICES = [
    (
        "diseno-arquitectonico",
        "Diseño arquitectónico",
        "Del primer boceto al proyecto ejecutivo, pensado para cómo vivís y trabajás.",
        [
            "Entrevista y relevamiento",
            "Anteproyecto",
            "Proyecto ejecutivo",
            "Documentación y trámites",
        ],
    ),
    (
        "direccion-de-obra",
        "Dirección de obra",
        "Seguimiento técnico para que la obra respete el proyecto, los plazos y el presupuesto.",
        [
            "Planificación y presupuesto",
            "Seguimiento en obra",
            "Control de calidad y plazos",
            "Entrega final",
        ],
    ),
    (
        "construccion",
        "Construcción",
        "Ejecución de la obra completa, con equipo propio y terminaciones cuidadas.",
        ["Presupuesto y contrato", "Ejecución", "Terminaciones", "Entrega"],
    ),
    (
        "reformas-y-ampliaciones",
        "Reformas y ampliaciones",
        "Renovamos y ampliamos espacios existentes con la menor interrupción posible.",
        ["Relevamiento del estado actual", "Propuesta y presupuesto", "Obra", "Entrega"],
    ),
    (
        "renders-3d",
        "Renders y visualización 3D",
        "Imágenes realistas para ver el proyecto terminado antes de construirlo.",
        [
            "Recepción de planos",
            "Modelado 3D",
            "Revisión con el cliente",
            "Entrega de imágenes finales",
        ],
    ),
]

ADDRESS = "Baradero, Buenos Aires"


class Command(BaseCommand):
    help = "Carga datos de referencia (tipos, servicios, zonas). Idempotente; solo para desarrollo."

    def add_arguments(self, parser):
        parser.add_argument(
            "--force",
            action="store_true",
            help="Permite correr con DEBUG=False.",
        )

    def handle(self, *args, **options):
        if not settings.DEBUG and not options["force"]:
            raise CommandError(
                "seed_projects se niega a correr con DEBUG=False. Usá --force si estás seguro."
            )
        with transaction.atomic():
            created = {
                "tipos de proyecto": self._seed_simple(ProjectType, PROJECT_TYPES),
                "zonas": self._seed_simple(Zone, ZONES),
                "servicios": self._seed_services(),
            }
            site = SiteSettings.load()
            if not site.address:
                site.address = ADDRESS
                site.save()
                created["dirección del sitio"] = 1
        news = [f"{n} {label}" for label, n in created.items() if n]
        self.stdout.write("Creados: " + ", ".join(news) + "." if news else "Nada nuevo para crear.")

    @staticmethod
    def _seed_simple(model, rows):
        """get_or_create por slug: lo que ya existe (y pudo editarse) no se toca."""
        return sum(
            model.objects.get_or_create(slug=slug, defaults={"name": name})[1]
            for slug, name in rows
        )

    @staticmethod
    def _seed_services():
        count = 0
        for order, (slug, title, summary, steps) in enumerate(SERVICES, start=1):
            service, is_new = Service.objects.get_or_create(
                slug=slug, defaults={"title": title, "summary": summary, "order": order}
            )
            if is_new:  # los pasos solo se crean con el servicio: borrarlos en el admin es válido
                ServiceStep.objects.bulk_create(
                    ServiceStep(service=service, title=step, order=i)
                    for i, step in enumerate(steps, start=1)
                )
                count += 1
        return count
```

- [ ] **Step 4: Verificar que pasa**

Run: `pytest tests/test_seed_projects.py -v`
Expected: 7 passed.

- [ ] **Step 5: Formato y lint**

Run: `ruff format . && ruff check .`
Expected: `All checks passed!` (ruff format puede reacomodar las listas y líneas largas; es esperado).
Run otra vez `pytest tests/test_seed_projects.py -v` → 7 passed.

- [ ] **Step 6: Commit**

```bash
git add apps/projects/management tests/test_seed_projects.py
git commit -m "feat(projects): comando seed_projects con datos de referencia" \
  -m "Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>"
```

---

### Task 2: Documentar el comando

**Files:**
- Modify: `CLAUDE.md` (sección "Comandos")

- [ ] **Step 1: Agregar la línea**

En el bloque de código de "Comandos", después de la línea
`python manage.py migrate && python manage.py runserver`, agregar:

```bash
python manage.py seed_projects                           # datos de referencia (solo DEBUG=True)
```

- [ ] **Step 2: Commit**

```bash
git add CLAUDE.md
git commit -m "docs: documentar seed_projects en CLAUDE.md" \
  -m "Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>"
```

---

### Task 3: Verificación completa y PR

- [ ] **Step 1: Suite completa y lint**

```bash
pytest -q
ruff check . && ruff format --check .
python manage.py makemigrations --check --dry-run
```

Expected: todo en verde (119 previos + 7 = 126 tests; si el conteo difiere, reportar la
diferencia exacta), `No changes detected`.

- [ ] **Step 2: Prueba real contra la base local**

```bash
python manage.py seed_projects
python manage.py seed_projects
```

Expected: la primera imprime `Creados: 5 tipos de proyecto, 4 zonas, 5 servicios, 1 dirección del sitio.`
(la dirección puede faltar si ya estaba cargada) y la segunda `Nada nuevo para crear.`
Después mirar `/gestion-iki/` y comprobar que aparecen los datos y que nada está publicado.
Si la base local ya tenía datos propios del desarrollador, avisar antes de correrlo.

- [ ] **Step 3: Subir y abrir el PR (base: la rama del PR 3)**

```bash
git push -u origin feature/etapa-b1-seed
gh pr create --base feature/etapa-b1-admin --head feature/etapa-b1-seed \
  --title "feat: seed_projects con datos de referencia (B1, PR 4/4)" --body-file <archivo>
```

El cuerpo debe incluir: qué carga, las decisiones de arriba (sin teléfono/WhatsApp inventado,
todo sin publicar, textos borradores, no pisa lo editado, `--force`), que la base es el PR #6,
el conteo de tests y que el CI no corre por el bloqueo de facturación de la cuenta de Juan
Pablo. No mergear: requiere revisión de Juan Pablo.

---

## Auto-revisión contra el spec

| Requisito del spec | Dónde |
|---|---|
| Carga tipos de proyecto, servicios con pasos, zonas y `SiteSettings` provisorio | Task 1 |
| No inventa proyectos ni imágenes | Task 1 (`test_no_inventa_proyectos_ni_datos_de_contacto`) |
| Idempotente | Task 1 (`test_es_idempotente`, `test_no_pisa_lo_editado_en_el_admin`) |
| Se niega con `DEBUG=False` salvo bandera explícita | Task 1 (`test_se_niega_con_debug_apagado`, `test_force_permite_correr_con_debug_apagado`) |
