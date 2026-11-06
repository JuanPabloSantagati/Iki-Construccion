"""Sanitizado de HTML cargado por usuarios (regla 6 de CLAUDE.md)."""

import nh3

ALLOWED_TAGS = {"p", "br", "strong", "em", "ul", "ol", "li", "h3", "h4", "blockquote", "a"}
ALLOWED_ATTRIBUTES = {"a": {"href", "title"}}
ALLOWED_SCHEMES = {"http", "https", "mailto"}


def clean_html(value):
    """Deja solo formato básico y enlaces http(s)/mailto; nh3 agrega rel="noopener noreferrer"."""
    return nh3.clean(
        value,
        tags=ALLOWED_TAGS,
        attributes=ALLOWED_ATTRIBUTES,
        url_schemes=ALLOWED_SCHEMES,
    )
