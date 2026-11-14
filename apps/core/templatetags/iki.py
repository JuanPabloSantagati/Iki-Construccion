import re
from urllib.parse import quote

from django import template
from django.utils.html import linebreaks
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
