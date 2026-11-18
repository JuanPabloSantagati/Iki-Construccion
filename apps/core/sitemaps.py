from django.contrib.sitemaps import Sitemap
from django.urls import reverse

from apps.projects.models import Project
from apps.services.models import Service


class StaticSitemap(Sitemap):
    priority = 0.6

    def items(self):
        return ["core:home", "core:studio", "services:list", "projects:list", "contact:form"]

    def location(self, item):
        return reverse(item)


class ProjectSitemap(Sitemap):
    priority = 0.8

    def items(self):
        return Project.objects.published()

    def lastmod(self, obj):
        return obj.updated_at


class ServiceSitemap(Sitemap):
    priority = 0.7

    def items(self):
        return Service.objects.published()


SITEMAPS = {"static": StaticSitemap, "projects": ProjectSitemap, "services": ServiceSitemap}
