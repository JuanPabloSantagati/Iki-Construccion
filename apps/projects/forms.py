from django import forms
from django.core.exceptions import ValidationError

MAX_FILES_PER_UPLOAD = 20


class MultipleFileInput(forms.ClearableFileInput):
    allow_multiple_selected = True


class MultipleFileField(forms.FileField):
    """Patrón de la documentación de Django para subir varios archivos con un solo input."""

    def __init__(self, *args, **kwargs):
        kwargs.setdefault("widget", MultipleFileInput())
        super().__init__(*args, **kwargs)

    def clean(self, data, initial=None):
        clean_one = super().clean
        if isinstance(data, list | tuple):
            return [clean_one(item, initial) for item in data]
        return [clean_one(data, initial)]


class UploadImagesForm(forms.Form):
    files = MultipleFileField(label="Imágenes")

    def clean_files(self):
        files = self.cleaned_data["files"]
        if not files:
            raise ValidationError("Elegí al menos una imagen.")
        if len(files) > MAX_FILES_PER_UPLOAD:
            raise ValidationError(f"Máximo {MAX_FILES_PER_UPLOAD} imágenes por vez.")
        return files
