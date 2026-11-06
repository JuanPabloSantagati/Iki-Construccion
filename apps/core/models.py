from django.core.validators import RegexValidator
from django.db import models

from .images import process_image


class SiteSettings(models.Model):
    """Datos públicos de contacto y redes. Un solo registro (pk=1)."""

    whatsapp = models.CharField(
        "WhatsApp",
        max_length=15,
        blank=True,
        validators=[
            RegexValidator(r"^\d{8,15}$", "Solo dígitos, con código de país (ej: 5493329000000).")
        ],
        help_text="Solo dígitos, con código de país. Ej: 5493329000000.",
    )
    phone = models.CharField("teléfono", max_length=30, blank=True)
    email = models.EmailField("email de contacto", blank=True)
    address = models.CharField("dirección", max_length=200, blank=True)
    instagram = models.URLField("Instagram", blank=True)
    facebook = models.URLField("Facebook", blank=True)

    class Meta:
        verbose_name = "configuración del sitio"
        verbose_name_plural = "configuración del sitio"

    def __str__(self):
        return "Configuración del sitio"

    def save(self, *args, **kwargs):
        self.pk = 1  # singleton: siempre el mismo registro
        super().save(*args, **kwargs)

    @classmethod
    def load(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj


class Zone(models.Model):
    """Zona geográfica para las landings de SEO local (etapa F)."""

    name = models.CharField("nombre", max_length=100)
    slug = models.SlugField("slug", unique=True)
    intro = models.TextField("introducción", blank=True)
    is_published = models.BooleanField("publicada", default=False)

    class Meta:
        ordering = ["name"]
        verbose_name = "zona"
        verbose_name_plural = "zonas"

    def __str__(self):
        return self.name


class TeamMember(models.Model):
    """Integrante del estudio (página Estudio)."""

    name = models.CharField("nombre", max_length=100)
    role = models.CharField("rol", max_length=100)
    bio = models.TextField("biografía", blank=True)
    photo = models.ImageField("foto", upload_to="team/", blank=True)
    order = models.PositiveSmallIntegerField("orden", default=0)

    class Meta:
        ordering = ["order", "name"]
        verbose_name = "integrante del equipo"
        verbose_name_plural = "equipo"

    def __str__(self):
        return self.name

    def set_photo(self, uploaded):
        """Única vía para cargar la foto: pasa por el pipeline (lanza ValidationError)."""
        content = process_image(uploaded)["medium"]
        self.photo.save(content.name, content, save=False)
