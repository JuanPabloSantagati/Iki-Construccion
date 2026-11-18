import re
import time

from django import forms
from django.conf import settings
from django.core import signing
from django.core.exceptions import ValidationError
from django.utils import timezone

from apps.services.models import Service

from .models import Inquiry

_SIGNER = signing.TimestampSigner(salt="contact.form-started")
FORM_MAX_AGE = 24 * 60 * 60  # un formulario abierto más de un día se vuelve a cargar
_PHONE = re.compile(r"^[0-9+()\-\s]{6,30}$")


def started_token():
    """Marca de tiempo firmada: el servidor sabe cuándo se mostró el formulario."""
    return _SIGNER.sign(str(int(time.time())))


def _single_line(value):
    # Sin saltos de línea: estos campos van al asunto del mail (header injection).
    if "\r" in value or "\n" in value:
        raise ValidationError("No puede tener saltos de línea.")
    return value.strip()


class InquiryForm(forms.ModelForm):
    # Honeypot: invisible para las personas; los bots suelen completarlo.
    website = forms.CharField(required=False, label="Sitio web")
    started = forms.CharField(widget=forms.HiddenInput)
    consent = forms.BooleanField(required=True)

    class Meta:
        model = Inquiry
        fields = ["name", "email", "phone", "service", "location", "approx_area", "message"]
        labels = {
            "name": "Nombre y apellido",
            "phone": "Teléfono",
            "service": "¿Qué necesitás?",
            "location": "Ubicación del terreno u obra",
            "approx_area": "m² aproximados",
            "message": "Contanos tu proyecto",
        }
        widgets = {
            "message": forms.Textarea(attrs={"rows": 5}),
            "approx_area": forms.NumberInput(attrs={"min": 1, "max": 100000}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["phone"].required = True
        self.fields["service"].queryset = Service.objects.published()
        self.fields["service"].empty_label = "No estoy seguro / varios"
        self.fields["message"].max_length = 3000
        self.fields["approx_area"].validators.append(_max_area)
        if not self.is_bound:
            self.initial["started"] = started_token()
        autocomplete = {"name": "name", "email": "email", "phone": "tel"}
        for name, field in self.fields.items():
            if name in autocomplete:
                field.widget.attrs["autocomplete"] = autocomplete[name]
        self.fields["website"].widget.attrs.update({"tabindex": "-1", "autocomplete": "off"})
        self.is_spam = False

    def clean_name(self):
        return _single_line(self.cleaned_data["name"])

    def clean_location(self):
        return _single_line(self.cleaned_data["location"])

    def clean_phone(self):
        phone = _single_line(self.cleaned_data["phone"])
        if not _PHONE.match(phone):
            raise ValidationError("Ingresá un teléfono válido (solo números, espacios, + o -).")
        return phone

    def clean_message(self):
        message = self.cleaned_data["message"].strip()
        if len(message) > 3000:
            raise ValidationError("El mensaje puede tener hasta 3000 caracteres.")
        return message

    def clean_started(self):
        try:
            started = int(_SIGNER.unsign(self.cleaned_data["started"], max_age=FORM_MAX_AGE))
        except (signing.BadSignature, ValueError) as exc:
            raise ValidationError(
                "El formulario venció. Recargá la página y volvé a enviarlo."
            ) from exc
        if time.time() - started < settings.CONTACT_MIN_SECONDS:
            self.is_spam = True  # demasiado rápido para una persona
        return started

    def clean_website(self):
        if self.cleaned_data["website"]:
            self.is_spam = True
        return ""

    def save(self, commit=True):
        inquiry = super().save(commit=False)
        inquiry.consent = True
        inquiry.consent_at = timezone.now()
        if commit:
            inquiry.save()
        return inquiry


def _max_area(value):
    if value is not None and value > 100000:
        raise ValidationError("Revisá los m²: el máximo es 100.000.")
