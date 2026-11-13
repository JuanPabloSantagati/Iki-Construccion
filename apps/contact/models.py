from django.db import models


class Inquiry(models.Model):
    """Consulta recibida por el formulario. Datos mínimos: sin IP ni user-agent."""

    class Status(models.TextChoices):
        NEW = "new", "Nueva"
        ANSWERED = "answered", "Respondida"
        ARCHIVED = "archived", "Archivada"

    name = models.CharField("nombre", max_length=120)
    email = models.EmailField("email")
    phone = models.CharField("teléfono", max_length=30, blank=True)
    message = models.TextField("mensaje")
    consent = models.BooleanField("consentimiento", default=False)
    consent_at = models.DateTimeField("fecha del consentimiento", null=True, blank=True)
    status = models.CharField("estado", max_length=10, choices=Status.choices, default=Status.NEW)
    created_at = models.DateTimeField("recibida", auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "consulta"
        verbose_name_plural = "consultas"
        constraints = [
            # Ley 25.326: no se guarda una consulta sin consentimiento explícito y fechado.
            models.CheckConstraint(
                condition=models.Q(consent=True, consent_at__isnull=False),
                name="inquiry_consent_required",
            ),
        ]

    def __str__(self):
        return f"{self.name} ({self.created_at:%d/%m/%Y})"
