# IKI | Diseño & Construcción

Sitio web del estudio IKI (Baradero, Buenos Aires) — *"La elegancia de lo esencial"*.
Portfolio de obras y renders, servicios y generación de consultas (formulario + WhatsApp).

Stack: Python 3.12 · Django 5.2 LTS · PostgreSQL (Supabase) · Supabase Storage ·
Tailwind CSS · HTMX. Convenciones y reglas del proyecto: **[CLAUDE.md](CLAUDE.md)**.
Flujo de trabajo: **[CONTRIBUTING.md](CONTRIBUTING.md)**.

> ⚠️ Este repo es **público**. Nunca commitees `.env`, credenciales, dumps de la base ni
> datos reales de clientes. Ver [SECURITY.md](SECURITY.md).

---

## Setup local

Requisitos: Python 3.12+, Git y Git Bash (en Windows). No hace falta Node.

```bash
# 1. Clonar
git clone https://github.com/JuanPabloSantagati/Iki-Construccion.git
cd Iki-Construccion

# 2. Entorno virtual y dependencias (versiones exactas, verificadas por hash)
python -m venv .venv
source .venv/Scripts/activate          # Windows (Git Bash)
# source .venv/bin/activate            # macOS / Linux
python -m pip install --require-hashes -r requirements/dev.txt

# 3. Variables de entorno
cp .env.example .env
#    Completá DATABASE_URL con la connection string del proyecto Supabase de DEV
#    (pedísela al otro socio por un canal privado, nunca por el repo ni por issues).
#    Si la dejás vacía se usa SQLite local.

# 4. Hooks de pre-commit (ruff, gitleaks, etc.)
pre-commit install

# 5. CSS (descarga el CLI de Tailwind la primera vez y verifica su checksum)
./scripts/build_css.sh               # o --watch mientras desarrollás

# 6. Base de datos y usuario admin
python manage.py migrate
python manage.py createsuperuser

# 7. Datos de prueba (disponible desde la etapa B)
# python manage.py seed_projects

# 8. Levantar
python manage.py runserver
```

- Sitio: <http://127.0.0.1:8000/>
- Admin: `http://127.0.0.1:8000/<ADMIN_URL>` (en tu `.env`; por defecto `gestion-iki/`).
  No existe en `/admin/` a propósito.

## Comandos habituales

| Tarea | Comando |
|---|---|
| Tests | `pytest` |
| Lint / formato | `ruff check . --fix && ruff format .` |
| Todos los hooks | `pre-commit run --all-files` |
| CSS en vivo | `./scripts/build_css.sh --watch` |
| Chequeo de prod | ver abajo |
| Auditar dependencias | `pip-audit --strict --disable-pip --no-deps -r requirements/base.txt -r requirements/dev.txt` |
| Agregar dependencia | editar `requirements/base.in` o `dev.in` → `python -m piptools compile --generate-hashes --allow-unsafe --strip-extras requirements/base.in -o requirements/base.txt` (ídem dev) → `python -m piptools sync requirements/dev.txt` |

Simular los settings de producción en local:

```bash
DJANGO_SETTINGS_MODULE=config.settings.prod DJANGO_READ_DOT_ENV=0 \
SECRET_KEY="$(python -c 'import secrets; print(secrets.token_urlsafe(64))')" \
ALLOWED_HOSTS=iki.example CSRF_TRUSTED_ORIGINS=https://iki.example \
ADMIN_URL=panel-local/ DATABASE_URL=postgres://iki@localhost/iki \
python manage.py check --deploy --fail-level WARNING
```

## Estructura

```
config/settings/   base · dev · test · prod (prod falla si la config es insegura)
apps/              core · projects · services · contact
templates/         base.html, partials/, páginas de error
assets/input.css   fuente de Tailwind (compila a static/css/, ignorado por git)
static/            js/htmx.min.js, fonts/, img/ (logo)
requirements/      *.in (directas) → *.txt (compiladas con hashes)
scripts/           build_css.sh
docs/              plan, Supabase, seguridad de GitHub
tests/             tests de settings, storage y seguridad
```

## Variables de entorno: públicas vs. secretas

Todas están documentadas en [`.env.example`](.env.example) con su clasificación.

| Tipo | Ejemplos | Dónde pueden estar |
|---|---|---|
| **PÚBLICA** | `ALLOWED_HOSTS`, `SUPABASE_URL`, `SUPABASE_STORAGE_BUCKET`, número de WhatsApp, site key de Turnstile (etapa E) | Repo de ejemplo, HTML, navegador |
| **PRIVADA** | `ADMIN_URL` | Solo `.env` / panel del hosting (no es credencial, pero no se publica) |
| **SECRETA** | `SECRET_KEY`, `DATABASE_URL`, `SUPABASE_S3_ACCESS_KEY_ID`, `SUPABASE_S3_SECRET_ACCESS_KEY`, SMTP y secret key de Turnstile (etapa E) | **Solo** `.env` local o variables del hosting. Nunca en templates, JS ni repo |

El navegador nunca recibe credenciales de Supabase: subidas y consultas pasan por Django.
Las imágenes públicas se leen desde la URL pública del bucket (solo lectura, sin claves).

## Configuración manual de GitHub y Supabase

Hay opciones de seguridad que no se pueden versionar y se activan a mano:

- GitHub (branch protection, Dependabot, secret scanning…): [docs/github-security.md](docs/github-security.md)
- Supabase (Data API, RLS, buckets, roles de base de datos): [docs/supabase.md](docs/supabase.md)

## Roadmap

Ver [docs/plan.md](docs/plan.md) y el checklist de etapas en [CLAUDE.md](CLAUDE.md).
