from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.sitemaps.views import sitemap
from django.urls import include, path

from apps.core.sitemaps import SITEMAPS

urlpatterns = [
    path(settings.ADMIN_URL, admin.site.urls),
    path("proyectos/", include("apps.projects.urls")),
    path("servicios/", include("apps.services.urls")),
    path("contacto/", include("apps.contact.urls")),
    path("sitemap.xml", sitemap, {"sitemaps": SITEMAPS}, name="sitemap"),
    path("", include("apps.core.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
