import pytest
from django.core.exceptions import ValidationError

from apps.core.models import TeamMember
from tests.factories import jpeg_bytes, upload

pytestmark = pytest.mark.django_db


def test_sin_foto_por_defecto():
    member = TeamMember.objects.create(name="Ana", role="Arquitecta")
    assert not member.photo


def test_set_photo_guarda_una_version_webp_con_nombre_uuid():
    member = TeamMember.objects.create(name="Ana", role="Arquitecta")
    member.set_photo(upload(jpeg_bytes(size=(1600, 1200))))
    member.save()
    member.refresh_from_db()
    assert member.photo.name.startswith("team/")
    assert member.photo.name.endswith("_medium.webp")
    assert member.photo.storage.exists(member.photo.name)


def test_set_photo_rechaza_archivos_que_no_son_imagen():
    member = TeamMember.objects.create(name="Ana", role="Arquitecta")
    with pytest.raises(ValidationError):
        member.set_photo(upload(b"no soy una imagen"))
    assert not member.photo
