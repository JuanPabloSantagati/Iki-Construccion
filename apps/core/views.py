from django.shortcuts import render


def home(request):
    # Provisoria: la home real llega en la etapa D.
    return render(request, "core/home.html")
