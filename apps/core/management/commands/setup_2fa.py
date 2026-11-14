import io

import qrcode
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django_otp.plugins.otp_totp.models import TOTPDevice


class Command(BaseCommand):
    help = (
        "Configura el 2FA (TOTP) de un usuario staff y muestra el QR para escanear con "
        "Google Authenticator, Microsoft Authenticator, 1Password, etc. Reemplaza el anterior."
    )

    def add_arguments(self, parser):
        parser.add_argument("username")

    def handle(self, *args, username, **options):
        User = get_user_model()
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist as exc:
            raise CommandError(f"No existe el usuario «{username}».") from exc
        if not user.is_staff:
            raise CommandError("El usuario no es staff: no puede entrar al admin.")

        # Un solo dispositivo por usuario: configurar de nuevo invalida el anterior.
        TOTPDevice.objects.filter(user=user).delete()
        device = TOTPDevice.objects.create(user=user, name="App autenticadora", confirmed=True)

        qr = qrcode.QRCode(border=1)
        qr.add_data(device.config_url)
        buffer = io.StringIO()
        qr.print_ascii(out=buffer, invert=True)

        self.stdout.write(buffer.getvalue())
        self.stdout.write(
            "Escaneá el QR con la app autenticadora. Desde ahora, para entrar al admin vas a\n"
            "necesitar el código de 6 dígitos que muestra la app.\n"
            "Este QR es secreto: no lo compartas ni le saques captura."
        )
        self.stdout.write(self.style.SUCCESS(f"2FA configurado para «{username}»."))
