from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import get_object_or_404, render
from django.utils.cache import patch_vary_headers

from .models import Project, ProjectType

PAGE_SIZE = 12


def _is_htmx(request):
    # En un "volver atrás" sin caché, HTMX pide la página completa: no devolver un fragmento.
    return "HX-Request" in request.headers and "HX-History-Restore-Request" not in request.headers


def project_list(request):
    projects = Project.objects.published().for_cards()

    # Filtros: valores desconocidos se ignoran (equivale a "Todos").
    category = request.GET.get("categoria", "")
    if category not in Project.Category.values:
        category = ""
    types = ProjectType.objects.filter(projects__status=Project.Status.PUBLISHED).distinct()
    type_slug = request.GET.get("tipo", "")
    if not types.filter(slug=type_slug).exists():
        type_slug = ""

    if category:
        projects = projects.filter(category=category)
    if type_slug:
        projects = projects.filter(project_type__slug=type_slug)

    page = Paginator(projects, PAGE_SIZE).get_page(request.GET.get("pagina"))
    context = {
        "page": page,
        "categories": Project.Category.choices,
        "types": types,
        "category": category,
        "type_slug": type_slug,
    }

    template = "projects/project_list.html"
    if _is_htmx(request):
        # "Ver más" agrega tarjetas; un filtro reemplaza filtros + grilla.
        if request.headers.get("HX-Target") == "load-more":
            template = "projects/_page.html"
        else:
            template = "projects/_results.html"
    response = render(request, template, context)
    patch_vary_headers(response, ["HX-Request", "HX-Target"])
    return response


def project_detail(request, slug):
    project = get_object_or_404(
        Project.objects.visible_to(request.user).select_related("project_type"), slug=slug
    )
    related = (
        Project.objects.published()
        .for_cards()
        .filter(Q(project_type=project.project_type) | Q(category=project.category))
        .exclude(pk=project.pk)[:3]
    )
    context = {
        "project": project,
        "images": project.images.all(),  # orden del admin (Meta.ordering)
        "facts": project.facts.all(),
        "services": project.services.filter(is_published=True),
        "related": related,
        "whatsapp_text": f"Hola IKI, vi el proyecto «{project.title}» en la web y quiero hacer "
        "una consulta.",
    }
    return render(request, "projects/project_detail.html", context)
