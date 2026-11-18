from django.shortcuts import redirect, render
from django.templatetags.static import static

from apps.projects.models import Project
from apps.services.models import Service

from .models import TeamMember


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
