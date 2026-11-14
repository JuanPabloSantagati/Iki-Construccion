import re
from io import BytesIO

import pytest
from django.core.exceptions import ValidationError
from PIL import Image

from apps.core.images import MAX_UPLOAD_BYTES, process_image
from tests.factories import jpeg_bytes, png_bytes, upload

NAME = re.compile(r"^[0-9a-f]{32}_(thumb|medium|large)\.webp$")


def opened(content):
    return Image.open(BytesIO(content.read()))


def test_genera_tres_tamanos_webp_con_nombre_uuid():
    result = process_image(upload(jpeg_bytes()))
    assert set(result) == {"thumb", "medium", "large"}
    for label, content in result.items():
        assert NAME.match(content.name), content.name
        assert content.name.endswith(f"_{label}.webp")
        assert opened(content).format == "WEBP"


def test_lado_largo_por_tamano_y_proporcion():
    result = process_image(upload(jpeg_bytes(size=(3000, 2000))))
    sizes = {label: opened(c).size for label, c in result.items()}
    assert sizes == {"thumb": (640, 427), "medium": (1280, 853), "large": (2000, 1333)}


def test_no_agranda_imagenes_chicas():
    result = process_image(upload(jpeg_bytes(size=(500, 300))))
    assert all(opened(c).size == (500, 300) for c in result.values())


def test_elimina_exif_y_gps():
    source = upload(jpeg_bytes(with_gps=True))
    assert Image.open(BytesIO(source.read())).getexif().get_ifd(0x8825)  # el origen sí lo tiene
    source.seek(0)
    for content in process_image(source).values():
        image = opened(content)
        assert not image.getexif()
        assert "exif" not in image.info
        assert "icc_profile" not in image.info


def test_aplica_la_orientacion_antes_de_perder_el_exif():
    # Orientation 6 = rotar 90°: una foto de 3000x2000 debe quedar vertical.
    result = process_image(upload(jpeg_bytes(size=(3000, 2000), orientation=6)))
    width, height = opened(result["large"]).size
    assert height > width


def test_png_con_transparencia_conserva_el_alfa():
    result = process_image(upload(png_bytes(mode="RGBA"), "logo.png", "image/png"))
    assert opened(result["medium"]).mode == "RGBA"


def test_rechaza_texto_con_extension_de_imagen():
    with pytest.raises(ValidationError):
        process_image(upload(b"esto no es una imagen", "foto.jpg"))


def test_rechaza_archivo_truncado():
    data = jpeg_bytes()
    with pytest.raises(ValidationError):
        process_image(upload(data[: len(data) // 2]))


def test_rechaza_formato_no_permitido():
    buffer = BytesIO()
    Image.new("RGB", (10, 10)).save(buffer, "GIF")
    with pytest.raises(ValidationError):
        process_image(upload(buffer.getvalue(), "anim.gif", "image/gif"))


def test_rechaza_demasiados_pixeles():
    # 8000x8000 = 64 MP, bajo en bytes (PNG de 1 bit) pero sobre el tope de píxeles.
    buffer = BytesIO()
    Image.new("1", (8000, 8000)).save(buffer, "PNG")
    with pytest.raises(ValidationError):
        process_image(upload(buffer.getvalue(), "bomba.png", "image/png"))


def test_rechaza_archivo_demasiado_pesado():
    with pytest.raises(ValidationError):
        process_image(upload(b"\0" * (MAX_UPLOAD_BYTES + 1)))


def test_webp_tiene_content_type_de_imagen():
    # El bucket de Supabase solo acepta image/webp; django-storages usa mimetypes para el header.
    import mimetypes

    assert mimetypes.guess_type("foto.webp")[0] == "image/webp"
