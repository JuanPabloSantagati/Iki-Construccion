# Etapa B1 — Modelos, admin y pipeline de imágenes

Fecha: 2026-11-06 · Estado: diseño aprobado por Franco. Juan Pablo lo revisa junto con los PRs de B1
Contexto: `docs/plan.md`, `docs/propuesta-etapas.md`, `CLAUDE.md`.

## Objetivo

Que los socios puedan cargar y administrar el contenido del sitio (proyectos, servicios, datos
de contacto) desde el admin, con imágenes procesadas de forma segura. 2FA, django-axes, roles y
RLS quedan en la etapa B2 (obligatoria antes del primer deploy público).

## Decisiones

- **Sin fotos reales todavía.** B1 no genera imágenes de prueba. Las etapas C y D esperan las fotos.
- **`seed_projects` solo carga datos de referencia** (tipos de proyecto, servicios con pasos,
  zonas, `SiteSettings` provisorio). No inventa proyectos ni imágenes; los proyectos se cargan
  por el admin.
- **Orden con campo numérico `order`** y **subida múltiple propia** (input `multiple`), sin
  librerías ni JS de terceros. El arrastre queda para después si hace falta.
- **Categorías de proyecto** (lista fija en código): `Obra`, `Proyecto`, `Render`.

## Modelos

Código y campos en inglés; `verbose_name` en español.

**core**
- `SiteSettings` (un solo registro): WhatsApp, teléfono, mail, dirección, redes.
- `Zone`: name, slug, intro, is_published.
- `TeamMember`: name, role, bio, photo (opcional), order.

**services**
- `Service`: title, slug, summary, description, order, is_published.
- `ServiceStep`: service (FK), title, description, order.

**projects**
- `ProjectType`: name, slug.
- `Project`: title, slug, status (borrador/publicado), category, type (FK), location, zone (FK,
  opcional), area_m2, year, summary, description (sanitizada con `nh3`), services (M2M),
  is_featured, campos SEO.
- `ProjectFact`: project (FK), label, value, order.
- `ProjectImage`: project (FK), image, alt, order, is_cover. Portada única por proyecto
  (`UniqueConstraint` condicional en la DB).

**contact**
- `Inquiry`: name, email, phone, message, consent (bool) y consent_at, status, created_at.
  Sin IP ni user-agent (regla 10 de `CLAUDE.md`).

## Pipeline de imágenes

`apps/projects/images.py`, una función que recibe el archivo subido y devuelve los archivos
procesados.

1. Valida por **contenido real** con Pillow (no por extensión). Formatos: JPEG, PNG, WebP.
2. Tope de peso de subida y de píxeles totales (protección contra decompression bombs).
3. Corrige la orientación y **descarta todos los metadatos** (EXIF, GPS).
4. Genera WebP en 3 tamaños (lado largo: 640, 1280 y 2000 px, sin ampliar).
5. Nombra con UUID. Guarda con el storage por defecto (disco o Supabase según el entorno).
6. `alt` vacío → se autogenera ("Proyecto, ubicación").

## Admin

- `Project` con inlines de `ProjectFact` y `ProjectImage`.
- Vista "Subir imágenes" con input `multiple`; cada archivo pasa por el pipeline.
- `SiteSettings` sin poder crear un segundo registro ni borrarlo.
- Listados con filtros por estado, tipo y zona.

## Seed

`seed_projects` es idempotente (correrlo dos veces no duplica) y se niega a correr con
`DEBUG=False` salvo bandera explícita.

## Tests

- Modelos: slugs únicos, portada única, descripción sanitizada (sin `|safe`, regla 6).
- Pipeline: archivo corrupto, extensión falsa, GPS eliminado, imagen enorme, nombre UUID.
- Admin: subida múltiple y permisos.
- Seed: idempotencia y rechazo con `DEBUG=False`.

## Entrega

Rama base `feature/etapa-b1-*`, 4 PRs chicos revisables:
1. Modelos de `core`, `services` y `contact` + migraciones.
2. Modelos de `projects` + pipeline de imágenes.
3. Admin con subida múltiple.
4. `seed_projects`.

## Fuera de alcance

2FA, django-axes, roles y RLS (B2) · vistas públicas (C, D, E) · fotos de prueba · arrastre de
orden.
