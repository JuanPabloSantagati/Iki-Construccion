from django.urls import path

from . import views

app_name = "core"

urlpatterns = [
    path("", views.home, name="home"),
    # Algunos navegadores y lectores piden /favicon.ico aunque el HTML declare otro ícono.
    path("favicon.ico", views.favicon),
    path("estudio/", views.studio, name="studio"),
    path("robots.txt", views.robots, name="robots"),
    path(".well-known/security.txt", views.security_txt, name="security_txt"),
    path("privacidad/", views.privacy, name="privacy"),
]
