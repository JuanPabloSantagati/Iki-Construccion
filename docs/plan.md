# Plan del proyecto

Resumen del plan aprobado. Las convenciones vigentes están en `CLAUDE.md`.

## Referencia y diseño

Referencia: ramosarquitectura.com.ar (`/obras/casa-ll`, home, servicios). De ahí tomamos la
estructura editorial: contenedor de 1400px, navegación en mayúsculas chicas con tracking
amplio, hero de foto a todo el ancho, ficha de proyecto con metadatos en una línea y grilla
de datos, CTAs de consulta/WhatsApp/llamada, galería grande.

Adaptación a IKI: monocromo (como el logo) en vez de los neutros cálidos de la referencia;
Cormorant Garamond (títulos) + Manrope (texto), servidas por nosotros. Tokens en
`assets/input.css`.

## Páginas y URLs

| URL | Página |
|---|---|
| `/` | Inicio: hero, servicios resumidos, últimos 3 proyectos, CTA |
| `/estudio/` | Quiénes son, enfoque, equipo |
| `/servicios/` · `/servicios/<slug>/` | Índice + detalle (proceso, proyectos relacionados, CTA) |
| `/proyectos/?categoria=&tipo=` | Grilla filtrable con HTMX (URL compartible) |
| `/proyectos/<slug>/` | Ficha: hero → metadatos → sobre el proyecto → datos → servicios → CTA → galería con lightbox → CTA final |
| `/contacto/` | Formulario HTMX (guarda en DB + mail) + WhatsApp prellenado |
| `/zonas/<slug>/` | Landings de SEO local administrables |
| `/privacidad/` | Política de privacidad (Ley 25.326) |
| `/sitemap.xml` · `/robots.txt` · `/.well-known/security.txt` | SEO y seguridad |
| `/<ADMIN_URL>` | Admin (nunca `/admin/`) |

## Modelos (etapa B)

- **core**: `SiteSettings` (datos públicos de contacto y redes, un solo registro), `Zone`, `TeamMember`.
- **services**: `Service`, `ServiceStep` (proceso paso a paso, inline).
- **projects**: `ProjectType`; `Project` (borrador/publicado, categoría, tipo, ubicación,
  zona, m², año, resumen, descripción sanitizada, servicios M2M, destacado, SEO);
  `ProjectFact` (datos extra de la grilla); `ProjectImage` (WebP en 3 tamaños, alt
  autogenerado, orden por arrastre, portada única).
- **contact**: `Inquiry` (datos mínimos + consentimiento; sin IP ni user-agent).

## Etapas

Orden: A → B1 → C → D → B2 → E → F. La etapa B se dividió en B1 y B2 (aprobado por ambos
socios; fundamento en `docs/propuesta-etapas.md`).

- **A** — Scaffolding, settings seguros, Supabase (DB + Storage con fallback), Tailwind, CI, tooling.
- **B1** — Modelos, admin (subida múltiple, orden por arrastre, portada), Pillow, `seed_projects`.
- **C** — Portfolio con filtros HTMX y ficha de proyecto con lightbox.
- **D** — Home, Estudio, Servicios.
- **B2** — Endurecer el admin: 2FA, django-axes, roles Editor/Gestión, RLS automatizado.
  **Obligatoria antes del primer deploy público.**
- **E** — Contacto: HTMX, mails, WhatsApp, Turnstile, honeypot, rate limit, privacidad,
  `purge_inquiries`.
- **F** — Zonas, SEO (sitemap, JSON-LD LocalBusiness, Open Graph), CSP estricta, security.txt,
  pulido mobile-first.

## Pendientes de definir

- Hosting (define `TRUST_PROXY_SSL_HEADER`, build y comando de migraciones).
- Proveedor de mail y casilla de avisos (etapa E).
- Tipografía final según el logo.
- Plazo de retención de consultas (propuesta: 24 meses y luego anonimizar).
- Turnstile (etapa E): excepción documentada de CSP, o solo honeypot + rate limit.
- Cómo medir las consultas (WhatsApp / formulario) sin cookies de terceros.
- Quién junta fotos, renders, logo y textos reales, y para cuándo.
- Landings de zona (etapa F): entran solo si hay contenido propio por zona.
