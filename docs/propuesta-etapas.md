# Propuesta: ajustar el plan de etapas

> **Estado:** propuesta para discutir. **No cambia** `CLAUDE.md` ni `docs/plan.md`: si se acepta,
> se aplica en un PR aparte (ver "Cambios concretos si se acepta").
> Origen: revisión del PR #1 (etapa A) y del plan completo, hecha por Franco con Claude Code.

## Opinión general

El plan está bien encaminado en lo técnico. Lo que sugerimos es **ajustar la proporción entre
seguridad y producto**: hoy la seguridad llega muy temprano y lo visible, tarde.

### Lo que está bien
- Base sólida: Django, Postgres, Tailwind y HTMX, sin frameworks JS. Fácil de mantener entre dos.
- Seguridad seria desde el día uno: prod falla al arrancar con config insegura, CI estricto,
  reglas claras para un repo público.
- El orden del contenido es correcto: portfolio, servicios y contacto es lo que da valor a un
  estudio de arquitectura.
- Mobile-first, imágenes WebP sin EXIF y SEO local por zonas son las prioridades justas.

### Lo que cambiaríamos
1. **La etapa B es pesada para lo que es el sitio** (ver propuesta B1/B2 abajo).
2. **Falta decidir el hosting.** Condiciona `TRUST_PROXY_SSL_HEADER`, el build y las
   migraciones. Conviene resolverlo antes de la etapa B, no después.
3. **El contenido real es la verdadera dependencia.** Fotos, renders, logo, textos del estudio y
   datos de contacto. Sin eso, las etapas C a F quedan con datos de prueba. Hay que pedirlo ya.
4. **Turnstile (etapa E) choca con una regla propia.** Su script es de terceros, y `CLAUDE.md`
   prohíbe scripts externos y exige CSP estricta. Decidir: excepción documentada (con
   `script-src`/`frame-src` solo para Cloudflare) o alcanzan honeypot + rate limit.
5. **Las landings de zona (etapa F) pueden quedar como contenido repetido.** Funcionan para SEO
   local solo si cada una tiene texto y obras propias de esa zona. Si no, dejarlas para el
   final y solo con contenido real.

### Lo que falta pensar
- **Qué mide el éxito:** consultas por WhatsApp y por formulario. Hace falta una forma simple y
  privada de contarlas (sin cookies de terceros).
- **Quién carga el contenido después** y si el admin le resulta cómodo a esa persona.

El lema es "La elegancia de lo esencial"; la etapa B, tal como está, se parece más a un sistema
empresarial que a lo esencial.

## Propuesta: dividir la etapa B

| Etapa | Contenido | Por qué |
|---|---|---|
| **B1** | Modelos (`SiteSettings`, `Zone`, `TeamMember`, `Service`, `ServiceStep`, `ProjectType`, `Project`, `ProjectFact`, `ProjectImage`, `Inquiry`), admin con inlines y **subida múltiple**, orden por arrastre y portada, Pillow (validación por contenido, WebP, sin EXIF, UUID, alt autogenerado), `seed_projects` | Es lo mínimo para cargar y mostrar obras. Desbloquea C y D |
| **B2** | 2FA, django-axes, roles Editor/Gestión, RLS automatizado | Endurecimiento del admin. Importa **antes de publicar**, no antes de ver el sitio funcionando |

Orden propuesto: `A → B1 → C → D → B2 → E → F`.

- B2 queda **obligatoria antes del primer deploy público**: no se baja la exigencia, se mueve
  en el tiempo.
- Mientras tanto el admin vive en `ADMIN_URL` (no `/admin/`), con contraseñas de 12+
  caracteres, y solo corre en local/dev: no hay exposición.
- Si B2 se siente demasiado, se puede recortar a "2FA + axes" y dejar roles para cuando haya
  más de dos usuarios en el admin.

## Cambios concretos si se acepta

1. `CLAUDE.md` → Roadmap: reemplazar la línea **B** por **B1** y **B2** y reordenar según arriba.
2. `docs/plan.md` → sección "Etapas": mismo cambio, con el detalle de cada una.
3. `docs/plan.md` → "Pendientes de definir": agregar la decisión sobre Turnstile, el medio de
   medición de consultas y la fecha límite de entrega de contenido real.

## Decisiones que necesitamos de ustedes

- [ ] ¿Dividimos B en B1/B2 y usamos el orden `A → B1 → C → D → B2 → E → F`?
- [ ] ¿Hosting? (bloquea el deploy y algunas variables de prod)
- [ ] ¿Quién junta fotos, renders, logo y textos, y para cuándo?
- [ ] ¿Turnstile con excepción de CSP, o honeypot + rate limit?
- [ ] ¿Cómo medimos las consultas (WhatsApp / formulario)?
- [ ] ¿Las landings de zona entran o se postergan hasta tener contenido propio por zona?
