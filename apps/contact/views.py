import logging

from django.shortcuts import redirect, render
from django.utils.cache import patch_vary_headers
from django.views.decorators.http import require_http_methods

from apps.projects.models import Project
from apps.services.models import Service

from . import ratelimit
from .forms import InquiryForm
from .notifications import notify_new_inquiry

security_logger = logging.getLogger("security")


def _initial_from_query(request):
    """Precarga desde los CTA: ?servicio=<slug> y ?proyecto=<slug> (solo publicados)."""
    initial = {}
    service = Service.objects.published().filter(slug=request.GET.get("servicio", "")).first()
    if service:
        initial["service"] = service
    project = Project.objects.published().filter(slug=request.GET.get("proyecto", "")).first()
    if project:
        initial["message"] = f"Me interesa un proyecto como «{project.title}». "
    return initial


@require_http_methods(["GET", "POST"])
def contact(request):
    is_htmx = "HX-Request" in request.headers
    status = 200
    if request.method == "POST":
        form = InquiryForm(request.POST)
        if ratelimit.is_limited(request):
            security_logger.warning("Formulario de contacto: límite de envíos alcanzado")
            form.add_error(None, "Recibimos varias consultas seguidas. Probá de nuevo más tarde.")
            status = 429
        elif form.is_valid():
            ratelimit.register_hit(request)
            if form.is_spam:
                # Al bot le respondemos igual que a una persona: no le damos pistas.
                security_logger.info("Formulario de contacto: envío descartado como spam")
            else:
                notify_new_inquiry(request, form.save())
            if is_htmx:
                return render(request, "contact/_success.html")
            return redirect("contact:thanks")
    else:
        form = InquiryForm(initial=_initial_from_query(request))

    template = "contact/_form.html" if is_htmx else "contact/contact.html"
    # HTMX no reemplaza el contenido en respuestas 4xx: el error se muestra con un 200.
    response = render(request, template, {"form": form}, status=200 if is_htmx else status)
    patch_vary_headers(response, ["HX-Request"])
    return response


def thanks(request):
    return render(request, "contact/thanks.html")
