from django.db import models
from django.urls import reverse


class ServiceQuerySet(models.QuerySet):
    def published(self):
        return self.filter(is_published=True)

    def visible_to(self, user):
        """Publicados para todos; el staff además puede previsualizar borradores."""
        return self if user.is_staff else self.published()


class Service(models.Model):
    """Servicio del estudio. El texto es plano: los templates lo escapan (regla 6)."""

    title = models.CharField("título", max_length=120)
    slug = models.SlugField("slug", unique=True)
    summary = models.CharField("resumen", max_length=280, blank=True)
    description = models.TextField("descripción", blank=True)
    order = models.PositiveSmallIntegerField("orden", default=0)
    is_published = models.BooleanField("publicado", default=False)

    objects = ServiceQuerySet.as_manager()

    class Meta:
        ordering = ["order", "title"]
        verbose_name = "servicio"
        verbose_name_plural = "servicios"

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse("services:detail", args=[self.slug])


class ServiceStep(models.Model):
    """Paso del proceso de un servicio (se edita como inline del servicio)."""

    service = models.ForeignKey(
        Service, on_delete=models.CASCADE, related_name="steps", verbose_name="servicio"
    )
    title = models.CharField("título", max_length=120)
    description = models.TextField("descripción", blank=True)
    order = models.PositiveSmallIntegerField("orden", default=0)

    class Meta:
        ordering = ["order", "id"]
        verbose_name = "paso del proceso"
        verbose_name_plural = "pasos del proceso"

    def __str__(self):
        return self.title
