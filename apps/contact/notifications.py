import logging

from django.conf import settings
from django.core.mail import EmailMessage
from django.urls import reverse

logger = logging.getLogger(__name__)


def notify_new_inquiry(request, inquiry):
    """Avisa por mail de una consulta nueva. Si el envío falla, la consulta ya está guardada."""
    if not settings.CONTACT_NOTIFY_EMAIL:
        logger.warning("CONTACT_NOTIFY_EMAIL vacía: no se avisó la consulta %s", inquiry.pk)
        return False
    admin_url = request.build_absolute_uri(
        reverse("admin:contact_inquiry_change", args=[inquiry.pk])
    )
    lines = [
        f"Nombre: {inquiry.name}",
        f"Email: {inquiry.email}",
        f"Teléfono: {inquiry.phone}",
        f"Servicio: {inquiry.service or 'No especificado'}",
        f"Ubicación: {inquiry.location or '-'}",
        f"m² aproximados: {inquiry.approx_area or '-'}",
        "",
        inquiry.message,
        "",
        f"Ver en el admin: {admin_url}",
    ]
    message = EmailMessage(
        # El nombre ya fue validado sin saltos de línea; Django además rechaza headers con \n.
        subject=f"Nueva consulta web: {inquiry.name}",
        body="\n".join(lines),
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[settings.CONTACT_NOTIFY_EMAIL],
        reply_to=[inquiry.email],
    )
    try:
        message.send()
    except Exception:
        # Sin datos personales en el log: solo el id.
        logger.exception("No se pudo enviar el aviso de la consulta %s", inquiry.pk)
        return False
    return True
