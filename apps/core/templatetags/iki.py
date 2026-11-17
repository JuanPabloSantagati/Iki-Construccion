import json
import re
from urllib.parse import quote

from django import template
from django.utils.html import format_html, linebreaks
from django.utils.safestring import mark_safe

from apps.projects.sanitize import clean_html

register = template.Library()

_BLOCK_TAG = re.compile(r"<(p|ul|ol|h3|h4|blockquote)[\s>]", re.IGNORECASE)


@register.filter
def rich_text(value):
    """Texto con formato básico, re-sanitizado con nh3 al mostrarlo (regla 6).

    Se sanitiza también al guardar; repetirlo acá cubre datos que no pasaron por save().
    Si el texto no trae párrafos, los saltos de línea se convierten en <p>/<br>.
    """
    cleaned = clean_html(value or "")
    if cleaned and not _BLOCK_TAG.search(cleaned):
        # nh3 ya escapó el texto: no hay que volver a escaparlo.
        cleaned = linebreaks(cleaned, autoescape=False)
    return mark_safe(cleaned)  # noqa: S308 — salida de nh3


@register.simple_tag
def whatsapp_url(number, text=""):
    """Link a WhatsApp con mensaje prellenado. Vacío si no hay número."""
    digits = re.sub(r"\D", "", number or "")
    if not digits:
        return ""
    url = f"https://wa.me/{digits}"
    return f"{url}?text={quote(text)}" if text else url


@register.filter
def tel_href(phone):
    """`tel:` con solo dígitos y un + inicial opcional."""
    phone = (phone or "").strip()
    digits = re.sub(r"\D", "", phone)
    if not digits:
        return ""
    return f"tel:{'+' if phone.startswith('+') else ''}{digits}"


@register.simple_tag(takes_context=True)
def absolute_url(context, path):
    """URL absoluta (para canonical y Open Graph). El host ya lo validó ALLOWED_HOSTS."""
    return context["request"].build_absolute_uri(path)


@register.simple_tag(takes_context=True)
def local_business_ld(context):
    """JSON-LD de la empresa para buscadores, con los datos de contacto del sitio."""
    site = context["site"]
    data = {
        "@context": "https://schema.org",
        "@type": "HomeAndConstructionBusiness",
        "name": "IKI Diseño & Construcción",
        "url": context["request"].build_absolute_uri("/"),
        "description": "Estudio de arquitectura en Baradero: proyectos, renders, dirección de "
        "obra, planos municipales y agrimensura.",
        "address": {
            "@type": "PostalAddress",
            "addressLocality": "Baradero",
            "addressRegion": "Buenos Aires",
            "addressCountry": "AR",
        },
    }
    if site.phone:
        data["telephone"] = site.phone
    if site.email:
        data["email"] = site.email
    same_as = [url for url in (site.instagram, site.facebook) if url]
    if same_as:
        data["sameAs"] = same_as
    # json.dumps + escape de < > & (como json_script de Django): el texto del admin no puede
    # cerrar el <script>. No es mark_safe sobre HTML de usuarios, es JSON ya escapado.
    payload = json.dumps(data, ensure_ascii=False)
    payload = payload.replace("<", "\\u003c").replace(">", "\\u003e").replace("&", "\\u0026")
    return format_html('<script type="application/ld+json">{}</script>', mark_safe(payload))  # noqa: S308
