from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from .sanitize import clean_html


class ProjectType(models.Model):
    """Tipo de proyecto (vivienda, local comercial, reforma...), para filtrar el portfolio."""

    name = models.CharField("nombre", max_length=100)
    slug = models.SlugField("slug", unique=True)

    class Meta:
        ordering = ["name"]
        verbose_name = "tipo de proyecto"
        verbose_name_plural = "tipos de proyecto"

    def __str__(self):
        return self.name


class Project(models.Model):
    class Status(models.TextChoices):
        DRAFT = "draft", "Borrador"
        PUBLISHED = "published", "Publicado"

    class Category(models.TextChoices):
        OBRA = "obra", "Obra"
        PROYECTO = "proyecto", "Proyecto"
        RENDER = "render", "Render"

    title = models.CharField("título", max_length=150)
    slug = models.SlugField("slug", unique=True)
    status = models.CharField("estado", max_length=10, choices=Status, default=Status.DRAFT)
    category = models.CharField("categoría", max_length=10, choices=Category)
    project_type = models.ForeignKey(
        ProjectType,
        on_delete=models.PROTECT,
        related_name="projects",
        verbose_name="tipo",
    )
    location = models.CharField("ubicación", max_length=150)
    zone = models.ForeignKey(
        "core.Zone",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="projects",
        verbose_name="zona",
    )
    area_m2 = models.PositiveIntegerField("superficie (m²)", null=True, blank=True)
    year = models.PositiveSmallIntegerField(
        "año",
        null=True,
        blank=True,
        validators=[MinValueValidator(1900), MaxValueValidator(2100)],
    )
    summary = models.CharField("resumen", max_length=280, blank=True)
    description = models.TextField(
        "descripción", blank=True, help_text="Admite formato básico; se sanitiza al guardar."
    )
    services = models.ManyToManyField(
        "services.Service", blank=True, related_name="projects", verbose_name="servicios"
    )
    is_featured = models.BooleanField("destacado", default=False)
    seo_title = models.CharField("título SEO", max_length=70, blank=True)
    seo_description = models.CharField("descripción SEO", max_length=160, blank=True)
    created_at = models.DateTimeField("creado", auto_now_add=True)
    updated_at = models.DateTimeField("actualizado", auto_now=True)

    class Meta:
        ordering = ["-year", "-created_at"]
        verbose_name = "proyecto"
        verbose_name_plural = "proyectos"

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        self.description = clean_html(self.description)
        super().save(*args, **kwargs)


class ProjectFact(models.Model):
    """Dato extra de la ficha (ej: "Superficie" / "180 m²")."""

    project = models.ForeignKey(
        Project, on_delete=models.CASCADE, related_name="facts", verbose_name="proyecto"
    )
    label = models.CharField("dato", max_length=80)
    value = models.CharField("valor", max_length=150)
    order = models.PositiveSmallIntegerField("orden", default=0)

    class Meta:
        ordering = ["order", "id"]
        verbose_name = "dato del proyecto"
        verbose_name_plural = "datos del proyecto"

    def __str__(self):
        return f"{self.label}: {self.value}"
