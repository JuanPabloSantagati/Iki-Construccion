import pytest
from django.db import IntegrityError, transaction
from django.utils import timezone

from apps.contact.models import Inquiry

pytestmark = pytest.mark.django_db

VALID = {"name": "Ana", "email": "ana@iki.example", "message": "Hola"}


def test_consulta_valida_queda_nueva():
    inquiry = Inquiry.objects.create(**VALID, consent=True, consent_at=timezone.now())
    assert inquiry.status == Inquiry.Status.NEW
    assert inquiry.created_at is not None


def test_sin_consentimiento_no_se_guarda():
    with pytest.raises(IntegrityError), transaction.atomic():
        Inquiry.objects.create(**VALID, consent=False, consent_at=timezone.now())


def test_consentimiento_sin_fecha_no_se_guarda():
    with pytest.raises(IntegrityError), transaction.atomic():
        Inquiry.objects.create(**VALID, consent=True, consent_at=None)


def test_no_guarda_ip_ni_user_agent():
    # Regla 10 de CLAUDE.md / plan: datos mínimos, sin trazas técnicas del visitante.
    names = {f.name for f in Inquiry._meta.get_fields()}
    assert not names & {"ip", "ip_address", "user_agent"}
