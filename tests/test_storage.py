"""Media: disco local por defecto; Supabase solo con credenciales completas."""

SUPABASE_ENV = {
    "MEDIA_STORAGE": "supabase",
    "SUPABASE_URL": "https://proyecto.supabase.co",
    "SUPABASE_STORAGE_REGION": "sa-east-1",
    "SUPABASE_S3_ACCESS_KEY_ID": "id-falso",
    "SUPABASE_S3_SECRET_ACCESS_KEY": "secreto-falso",
}
PRINT_BACKEND = "from django.conf import settings; print(settings.STORAGES['default']['BACKEND'])"


def test_media_local_por_defecto(django_proc):
    result = django_proc(PRINT_BACKEND)
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == "django.core.files.storage.FileSystemStorage"


def test_media_supabase_con_credenciales(django_proc):
    code = (
        "from django.conf import settings; o = settings.STORAGES['default']['OPTIONS']; "
        "print(settings.STORAGES['default']['BACKEND']); print(o['endpoint_url']); "
        "print(o['custom_domain']); print(o['querystring_auth'])"
    )
    result = django_proc(code, **SUPABASE_ENV)
    assert result.returncode == 0, result.stderr
    assert result.stdout.split() == [
        "storages.backends.s3.S3Storage",
        "https://proyecto.supabase.co/storage/v1/s3",
        "proyecto.supabase.co/storage/v1/object/public/iki-public",
        "False",
    ]


def test_media_supabase_sin_credenciales_falla(django_proc):
    env = {**SUPABASE_ENV, "SUPABASE_S3_SECRET_ACCESS_KEY": None}
    result = django_proc(PRINT_BACKEND, **env)
    assert result.returncode != 0
    assert "SUPABASE_S3_SECRET_ACCESS_KEY" in result.stderr


def test_media_storage_invalido_falla(django_proc):
    result = django_proc(PRINT_BACKEND, MEDIA_STORAGE="ftp")
    assert result.returncode != 0
    assert "MEDIA_STORAGE" in result.stderr
