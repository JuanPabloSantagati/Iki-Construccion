# CLAUDE.md — IKI | Diseño & Construcción

Sitio web del estudio IKI (Baradero, Buenos Aires). Lema: **"La elegancia de lo esencial"**.
Objetivos: mostrar el portfolio de obras y renders, explicar los servicios y generar consultas
(formulario + WhatsApp). Lo desarrollamos dos personas sobre el repo
`JuanPabloSantagati/Iki-Construccion`, que es **PÚBLICO**.

Este archivo es la fuente de verdad de convenciones. Si una decisión lo contradice, actualizá
este archivo en el mismo PR.

---

## Stack

| Capa | Tecnología |
|---|---|
| Backend | Python 3.12 + **Django 5.2 LTS** (versión exacta fijada en `requirements/`) |
| Base de datos | PostgreSQL en Supabase vía `DATABASE_URL` (`dj-database-url`). Dos proyectos: dev (compartido) y prod |
| Media | Supabase Storage vía `django-storages` (S3-compatible). Fallback a disco local (`MEDIA_ROOT`) si no hay credenciales |
| Frontend | Templates de Django + Tailwind CSS (compilado con el CLI standalone, sin CDN) + HTMX (archivo propio en `static/`) |
| Imágenes | Pillow: WebP optimizado, redimensionado, sin EXIF, `alt` autogenerado (proyecto + ubicación) |
| Config | `django-environ` + `.env.example` documentado |
| Calidad | `ruff` (lint + format, con reglas de seguridad `S`), `pre-commit`, `pytest-django` |
| CI | GitHub Actions con Postgres como servicio (nunca Supabase en CI) |

## Estructura

```
config/settings/{base,dev,prod,test}.py   # settings por entorno
apps/core/       # home, estudio, zonas, configuración del sitio, errores, sitemap
apps/projects/   # proyectos, imágenes, tipos, seed_projects
apps/services/   # servicios y pasos del proceso
apps/contact/    # consultas, formulario, mails, WhatsApp
templates/       # base.html, partials/, errors/, <app>/
assets/input.css  # fuente Tailwind — static/css/ compilado NO se commitea
static/js/       # htmx.min.js (versión fija), JS propio
static/img/      # logo (lo agregan los socios)
requirements/    # *.in (directas) → *.txt (compiladas con hashes)
```

## Comandos

```bash
python -m venv .venv && source .venv/Scripts/activate   # Windows Git Bash
python -m pip install --require-hashes -r requirements/dev.txt
cp .env.example .env                                     # completar valores
./scripts/build_css.sh [--watch]                         # Tailwind
python manage.py migrate && python manage.py runserver
python manage.py seed_projects                           # datos de referencia (solo DEBUG=True)
pytest                                                   # tests
ruff check . && ruff format --check .                    # lint
pre-commit run --all-files
# check --deploy con settings de prod: ver README (requiere variables de prod)
```

Agregar una dependencia: editar `requirements/*.in` → `python -m piptools compile --generate-hashes --allow-unsafe --strip-extras requirements/<x>.in -o requirements/<x>.txt` → commitear `.in` y `.txt` juntos.

Docs: `docs/plan.md` (plan), `docs/supabase.md` (DB, RLS, Storage), `docs/github-security.md` (config manual de GitHub).

## Reglas estrictas

1. **Nunca commitear** `.env`, credenciales, claves, connection strings, dumps de la DB,
   `media/`, `.venv/` ni datos reales de clientes o consultas. El repo es público y el
   historial es para siempre. Si se filtra un secreto: rotarlo primero, después limpiar.
2. Todo secreto vive en variables de entorno del servidor. Cada variable nueva se documenta
   en `.env.example` (sin valor real) indicando si es **PÚBLICA** o **SECRETA**.
3. El navegador nunca habla con Supabase con credenciales: subidas y consultas pasan por Django.
4. Interactividad con **HTMX** (filtros del portfolio, envío de formularios). Nada de
   frameworks JS ni scripts de terceros por CDN. Sin JS ni estilos inline (por la CSP).
5. Estilos solo con **Tailwind** usando los tokens de diseño de `input.css`. Mobile-first:
   se diseña para el celular y se amplía con `md:` / `lg:`.
6. Templates: nunca `|safe` ni `mark_safe` con contenido cargado por usuarios. Si un texto
   admite formato, se sanitiza con `nh3`.
7. Solo el ORM. Si alguna vez hace falta SQL crudo, siempre parametrizado.
8. Todo formulario con `{% csrf_token %}`; HTMX envía el token CSRF en el header.
9. Las imágenes subidas se validan por contenido real (no por extensión), se re-codifican con
   Pillow, pierden los metadatos EXIF (incluido GPS) y se renombran con UUID.
10. No loguear datos personales ni secretos.
11. Código, modelos y variables en inglés; textos visibles, URLs y verbose_name en español.
12. Toda funcionalidad nueva llega con tests. CI en verde antes de mergear.

## Seguridad en producción

- `config.settings.prod` **falla al arrancar** si falta `SECRET_KEY` o si `DEBUG=True`.
- `ALLOWED_HOSTS` y `CSRF_TRUSTED_ORIGINS` explícitos por env. HTTPS forzado, HSTS,
  cookies `Secure` / `HttpOnly` / `SameSite`, `nosniff`, `X-Frame-Options: DENY`, Referrer-Policy.
- `python manage.py check --deploy` sin warnings (corre en CI).
- El admin no está en `/admin/`: su ruta sale de la variable `ADMIN_URL`.

## Flujo de Git

- `main` protegida: solo se entra por PR con revisión del otro socio y CI en verde.
- Ramas: `feature/<descripcion-corta>`, `fix/<descripcion-corta>`, `chore/...`, `docs/...`.
- Commits convencionales: `feat:`, `fix:`, `chore:`, `docs:`, `refactor:`, `test:`, `ci:`,
  `style:` (ej: `feat(projects): subida múltiple de imágenes en el admin`).
- Un PR por etapa o funcionalidad, chico y revisable. Se completa la plantilla de PR.
- Nunca `git push --force` a `main`; nunca `--no-verify` para saltear pre-commit.

## Diseño

- Referencia: ramosarquitectura.com.ar (estructura editorial). Adaptada a IKI en monocromo.
- Paleta: `ink #111111` · `graphite #2E2E2E` · `stone #5E5E5E` · `ash #6F6F6F` ·
  `line #E3E3E1` · `mist #F5F5F3` · `paper #FFFFFF`. El verde de WhatsApp solo en su botón.
- Tipografías servidas desde `static/fonts/` (sin Google Fonts): títulos en serif
  (Cormorant Garamond), texto en sans (Manrope). Pendiente de validar contra el logo.
- Contenedor máx. 1400px; navegación en mayúsculas pequeñas con tracking amplio;
  fotos grandes, mucho aire.

## Roadmap (no avanzar de etapa sin aprobación)

Orden: A → B1 → C → D → B2 → E → F (B dividida; ver `docs/propuesta-etapas.md`).

- [x] **A** — Scaffolding + settings + Supabase (DB/Storage con fallback) + Tailwind + CI + tooling
- [x] **B1** — Modelos + admin (inlines, subida múltiple) + Pillow + `seed_projects`
- [x] **C** — Portfolio con filtros HTMX + ficha de proyecto con lightbox
- [ ] **D** — Home, Estudio y Servicios (con proyectos relacionados)
- [ ] **B2** — Endurecer el admin: 2FA, django-axes, roles, RLS. **Obligatoria antes del primer deploy público**
- [ ] **E** — Contacto (HTMX, mails, WhatsApp)
- [ ] **F** — SEO (sitemap, JSON-LD, Open Graph), zonas y pulido responsive
