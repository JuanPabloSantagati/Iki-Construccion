from datetime import timedelta

from django.http import Http404, HttpResponse
from django.shortcuts import redirect, render
from django.templatetags.static import static
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_GET

from apps.projects.models import Project
from apps.services.models import Service

from .models import SiteSettings, TeamMember


def home(request):
    published = Project.objects.published().for_cards()
    # Hero: el último destacado; si no hay destacados, el último publicado.
    hero = published.filter(is_featured=True).first() or published.first()
    recent = published.exclude(pk=hero.pk)[:3] if hero else []
    context = {
        "hero": hero,
        "recent": recent,
        "services": Service.objects.published(),
    }
    return render(request, "core/home.html", context)


def favicon(request):
    # Al pedirlo (no al importar urls.py): con el manifest de static, la URL lleva hash.
    return redirect(static("img/favicon.ico"), permanent=True)


def privacy(request):
    return render(request, "core/privacy.html")


def studio(request):
    context = {"team": TeamMember.objects.all()}
    return render(request, "core/studio.html", context)


@require_GET
def robots(request):
    lines = [
        "User-agent: *",
        "Allow: /",
        f"Disallow: {reverse('contact:thanks')}",
        f"Sitemap: {request.build_absolute_uri(reverse('sitemap'))}",
    ]
    # La ruta del admin no se lista acá: es secreta y robots.txt es público.
    return HttpResponse("\n".join(lines) + "\n", content_type="text/plain; charset=utf-8")


@require_GET
def security_txt(request):
    """RFC 9116. Sin email de contacto cargado en el admin no hay nada que publicar."""
    site = SiteSettings.objects.first()  # sin crear el registro en un GET
    email = site.email if site else ""
    if not email:
        raise Http404
    expires = (timezone.now() + timedelta(days=365)).strftime("%Y-%m-%dT%H:%M:%SZ")
    body = f"Contact: mailto:{email}\nExpires: {expires}\nPreferred-Languages: es, en\n"
    return HttpResponse(body, content_type="text/plain; charset=utf-8")
