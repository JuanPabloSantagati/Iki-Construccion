# Archivos de terceros servidos desde nuestros static

Nada se carga por CDN. Para actualizar: bajar el tarball del registry de npm,
verificar el `integrity` (sha512) contra `https://registry.npmjs.org/<paquete>/<versión>`,
copiar el archivo y actualizar esta tabla y el atributo `integrity` en `templates/base.html`.

| Archivo | Paquete | Versión | Licencia |
|---|---|---|---|
| `js/htmx.min.js` | `htmx.org` | 2.0.11 | 0BSD |
| `fonts/manrope-latin-wght-normal.woff2` | `@fontsource-variable/manrope` | 5.3.0 | OFL 1.1 |
| `fonts/cormorant-garamond-latin-*.woff2` | `@fontsource/cormorant-garamond` | 5.3.0 | OFL 1.1 |

Tailwind CSS no se vendorea: `scripts/build_css.sh` descarga el CLI standalone
(versión fija, SHA256 verificado contra `scripts/tailwindcss.sha256`).
