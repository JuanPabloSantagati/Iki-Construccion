from django.conf import settings
from django.contrib.admin.forms import AdminAuthenticationForm
from django_otp.admin import OTPAdminAuthenticationForm, OTPAdminSite


class IkiAdminSite(OTPAdminSite):
    """Admin de IKI: además de usuario y contraseña, exige un código TOTP (2FA).

    Solo entra el staff con un dispositivo TOTP confirmado (`manage.py setup_2fa`).
    ADMIN_REQUIRE_2FA=False lo desactiva en desarrollo y tests; prod no arranca así.
    """

    site_header = "IKI — Administración"
    site_title = "IKI"
    index_title = "Gestión del sitio"

    def __init__(self, name="admin"):
        super().__init__(name)

    @property
    def login_form(self):
        return OTPAdminAuthenticationForm if settings.ADMIN_REQUIRE_2FA else AdminAuthenticationForm

    @property
    def login_template(self):
        return super().login_template if settings.ADMIN_REQUIRE_2FA else None

    def has_permission(self, request):
        if settings.ADMIN_REQUIRE_2FA:
            return super().has_permission(request)  # incluye request.user.is_verified()
        return super(OTPAdminSite, self).has_permission(request)
