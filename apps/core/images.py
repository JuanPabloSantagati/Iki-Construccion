"""Procesado seguro de imágenes subidas (regla 9 de CLAUDE.md).

Valida por contenido real, re-codifica a WebP en varios tamaños, descarta todos los metadatos
(EXIF, GPS, perfil de color) y nombra con UUID. Ninguna imagen se guarda sin pasar por acá.
"""

import uuid
from io import BytesIO

from django.core.exceptions import ValidationError
from django.core.files.base import ContentFile
from PIL import Image, ImageOps, UnidentifiedImageError

# MPO: fotos de celular con varias capas; se decodifican como JPEG.
ALLOWED_FORMATS = {"JPEG", "MPO", "PNG", "WEBP"}
MAX_UPLOAD_BYTES = 10 * 1024 * 1024
MAX_PIXELS = 50_000_000  # protección contra decompression bombs
SIZES = {"thumb": 640, "medium": 1280, "large": 2000}  # lado largo en px
WEBP_QUALITY = 82


def _open_validated(uploaded):
    if uploaded.size > MAX_UPLOAD_BYTES:
        raise ValidationError("La imagen supera los 10 MB.")
    try:
        image = Image.open(uploaded)
        if image.format not in ALLOWED_FORMATS:
            raise ValidationError("Formato no permitido. Usá JPEG, PNG o WebP.")
        width, height = image.size
        if width * height > MAX_PIXELS:
            raise ValidationError("La imagen tiene demasiados píxeles.")
        image.load()  # decodifica todo: detecta archivos truncados o corruptos
    except (
        UnidentifiedImageError,
        OSError,
        SyntaxError,
        ValueError,
        Image.DecompressionBombError,
    ) as exc:
        raise ValidationError("El archivo no es una imagen válida.") from exc
    return image


def _strip_metadata(image):
    """Copia solo los píxeles: no hereda EXIF, GPS, ICC ni textos del original."""
    image = ImageOps.exif_transpose(image)  # aplica la rotación antes de perder el EXIF
    has_alpha = image.mode in ("RGBA", "LA", "PA") or "transparency" in image.info
    mode = "RGBA" if has_alpha else "RGB"
    image = image.convert(mode)
    return Image.frombytes(mode, image.size, image.tobytes())


def process_image(uploaded):
    """Devuelve {"thumb", "medium", "large"} -> ContentFile WebP listos para guardar.

    Lanza ValidationError si el archivo no es una imagen aceptable.
    """
    clean = _strip_metadata(_open_validated(uploaded))
    stem = uuid.uuid4().hex
    outputs = {}
    for label, long_side in SIZES.items():
        resized = clean.copy()
        resized.thumbnail((long_side, long_side), Image.Resampling.LANCZOS)  # nunca agranda
        buffer = BytesIO()
        resized.save(buffer, "WEBP", quality=WEBP_QUALITY, method=4)
        outputs[label] = ContentFile(buffer.getvalue(), name=f"{stem}_{label}.webp")
    return outputs
