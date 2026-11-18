from django.shortcuts import get_object_or_404, render

from apps.projects.models import Project

from .models import Service


def service_list(request):
    services = Service.objects.published().prefetch_related("steps")
    return render(request, "services/service_list.html", {"services": services})


def service_detail(request, slug):
    service = get_object_or_404(Service.objects.visible_to(request.user), slug=slug)
    context = {
        "service": service,
        "steps": service.steps.all(),
        "projects": Project.objects.published().for_cards().filter(services=service)[:6],
        "others": Service.objects.published().exclude(pk=service.pk),
    }
    return render(request, "services/service_detail.html", context)
