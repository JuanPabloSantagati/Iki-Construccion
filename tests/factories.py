from io import BytesIO

from django.core.files.uploadedfile import SimpleUploadedFile
from PIL import Image


def jpeg_bytes(size=(3000, 2000), orientation=None, with_gps=True):
    """JPEG con EXIF de cámara y (opcionalmente) coordenadas GPS."""
    image = Image.new("RGB", size, (200, 120, 40))
    exif = Image.Exif()
    exif[0x010F] = "CamMaker"
    if orientation:
        exif[0x0112] = orientation
    if with_gps:
        gps = exif.get_ifd(0x8825)
        gps[1] = "S"
        gps[2] = (33.0, 24.0, 0.0)
    buffer = BytesIO()
    image.save(buffer, "JPEG", exif=exif)
    return buffer.getvalue()


def png_bytes(size=(400, 300), mode="RGBA"):
    buffer = BytesIO()
    Image.new(mode, size, (10, 20, 30, 128) if mode == "RGBA" else (10, 20, 30)).save(buffer, "PNG")
    return buffer.getvalue()


def upload(data, name="foto.jpg", content_type="image/jpeg"):
    return SimpleUploadedFile(name, data, content_type=content_type)
