"""Etapa B2: 2FA obligatorio, bloqueo por intentos fallidos, roles y RLS."""

import pytest
from django.contrib.auth.models import Group, User
from django.core.management import CommandError, call_command
from django.db import connection
from django.test import override_settings
from django_otp.oath import TOTP
from django_otp.plugins.otp_totp.models import TOTPDevice

from apps.core.security import tables_without_rls

pytestmark = pytest.mark.django_db

PASSWORD = "una-clave-larga-de-prueba"  # noqa: S105


@pytest.fixture
def staff():
    return User.objects.create_user("socio", password=PASSWORD, is_staff=True, is_superuser=True)


@pytest.fixture
def admin_url(settings):
    return f"/{settings.ADMIN_URL}"


def current_token(device):
    return TOTP(device.bin_key, device.step, device.t0, device.digits, device.drift).token()


def login(client, admin_url, **extra):
    data = {"username": "socio", "password": PASSWORD, "next": admin_url, **extra}
    return client.post(f"{admin_url}login/", data)


# --- 2FA ----------------------------------------------------------------------


@override_settings(ADMIN_REQUIRE_2FA=True)
def test_sesion_sin_2fa_no_entra_al_admin(client, staff, admin_url):
    client.force_login(staff)
    response = client.get(admin_url)
    assert response.status_code == 302
    assert "/login/" in response.headers["Location"]


@override_settings(ADMIN_REQUIRE_2FA=True)
def test_login_pide_codigo(client, admin_url):
    body = client.get(f"{admin_url}login/").content.decode()
    assert 'name="otp_token"' in body


@override_settings(ADMIN_REQUIRE_2FA=True)
def test_contraseña_correcta_sin_codigo_no_alcanza(client, staff, admin_url):
    TOTPDevice.objects.create(user=staff, name="app", confirmed=True)
    response = login(client, admin_url)
    assert response.status_code == 200  # vuelve al formulario con error
    assert client.get(admin_url).status_code == 302


@override_settings(ADMIN_REQUIRE_2FA=True)
def test_codigo_incorrecto_no_entra(client, staff, admin_url):
    device = TOTPDevice.objects.create(user=staff, name="app", confirmed=True)
    login(client, admin_url, otp_device=device.persistent_id, otp_token="000000")  # noqa: S106
    assert client.get(admin_url).status_code == 302


@override_settings(ADMIN_REQUIRE_2FA=True)
def test_contraseña_y_codigo_correctos_entran(client, staff, admin_url):
    device = TOTPDevice.objects.create(user=staff, name="app", confirmed=True)
    response = login(
        client, admin_url, otp_device=device.persistent_id, otp_token=current_token(device)
    )
    assert response.status_code == 302
    assert client.get(admin_url).status_code == 200


def test_prod_no_arranca_sin_2fa(django_proc):
    result = django_proc("", ADMIN_REQUIRE_2FA="False")
    assert result.returncode != 0
    assert "ADMIN_REQUIRE_2FA" in result.stderr


def test_2fa_activo_por_defecto(django_proc):
    result = django_proc("from django.conf import settings; print(settings.ADMIN_REQUIRE_2FA)")
    assert result.stdout.strip() == "True"


# --- Bloqueo por intentos fallidos (django-axes) --------------------------------


def test_bloqueo_tras_5_intentos_fallidos(client, staff, admin_url):
    for _ in range(5):
        client.post(f"{admin_url}login/", {"username": "socio", "password": "mal"})
    # Aun con la contraseña correcta, queda bloqueado.
    response = client.post(f"{admin_url}login/", {"username": "socio", "password": PASSWORD})
    assert response.status_code == 429
    assert "Demasiados intentos" in response.content.decode()


def test_menos_de_5_intentos_no_bloquea(client, staff, admin_url):
    for _ in range(4):
        client.post(f"{admin_url}login/", {"username": "socio", "password": "mal"})
    response = login(client, admin_url)
    assert response.status_code == 302


# --- Roles --------------------------------------------------------------------


def test_grupos_creados_despues_de_migrate():
    editor = set(Group.objects.get(name="Editor").permissions.values_list("codename", flat=True))
    gestion = set(Group.objects.get(name="Gestión").permissions.values_list("codename", flat=True))
    assert {"add_project", "change_projectimage", "change_service", "view_teammember"} <= editor
    assert "view_inquiry" not in editor
    assert "change_sitesettings" not in editor
    assert not any(code.endswith(("_user", "_group")) for code in editor | gestion)
    assert {"view_inquiry", "change_inquiry", "change_sitesettings"} <= gestion
    assert "delete_inquiry" not in gestion


def make_member(group_name):
    user = User.objects.create_user("persona", password=PASSWORD, is_staff=True)
    user.groups.add(Group.objects.get(name=group_name))
    return user


def test_editor_carga_proyectos_pero_no_ve_consultas(client, admin_url):
    client.force_login(make_member("Editor"))
    assert client.get(f"{admin_url}projects/project/").status_code == 200
    assert client.get(f"{admin_url}contact/inquiry/").status_code == 403
    assert client.get(f"{admin_url}auth/user/").status_code == 403


def test_gestion_ve_consultas(client, admin_url):
    client.force_login(make_member("Gestión"))
    assert client.get(f"{admin_url}contact/inquiry/").status_code == 200
    assert client.get(f"{admin_url}auth/user/").status_code == 403


# --- Comando setup_2fa ----------------------------------------------------------


def test_setup_2fa_crea_un_unico_dispositivo(staff, capsys):
    TOTPDevice.objects.create(user=staff, name="viejo", confirmed=True)
    call_command("setup_2fa", "socio")
    devices = TOTPDevice.objects.filter(user=staff)
    assert devices.count() == 1
    assert devices.get().confirmed
    assert "2FA configurado" in capsys.readouterr().out


def test_setup_2fa_rechaza_usuarios_no_staff():
    User.objects.create_user("cliente", password=PASSWORD)
    with pytest.raises(CommandError):
        call_command("setup_2fa", "cliente")


# --- RLS (solo en PostgreSQL: corre en el CI) -----------------------------------


@pytest.mark.skipif(connection.vendor != "postgresql", reason="RLS solo existe en PostgreSQL")
def test_todas_las_tablas_tienen_rls_despues_de_migrate():
    with connection.cursor() as cursor:
        assert tables_without_rls(cursor) == []


@pytest.mark.skipif(connection.vendor == "postgresql", reason="en PostgreSQL el comando aplica")
def test_check_supabase_security_solo_en_postgres():
    with pytest.raises(CommandError):
        call_command("check_supabase_security")
