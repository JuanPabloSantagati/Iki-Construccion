from django.conf import settings


class PermissionsPolicyMiddleware:
    """Agrega el header Permissions-Policy (Django no lo trae de forma nativa)."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        response.headers.setdefault("Permissions-Policy", settings.PERMISSIONS_POLICY)
        return response


class ContentSecurityPolicyMiddleware:
    """CSP estricta para el sitio público: solo recursos propios, sin JS ni estilos inline.

    El admin de Django queda afuera (usa scripts y estilos inline); lo protegen 2FA y axes.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def _policy(self):
        img = "'self' data:" + (f" {settings.CSP_IMG_HOST}" if settings.CSP_IMG_HOST else "")
        return "; ".join(
            [
                "default-src 'self'",
                f"img-src {img}",
                "object-src 'none'",
                "base-uri 'self'",
                "form-action 'self'",
                "frame-ancestors 'none'",
            ]
        )

    def __call__(self, request):
        response = self.get_response(request)
        if not request.path.startswith(f"/{settings.ADMIN_URL}"):
            header = (
                "Content-Security-Policy-Report-Only"
                if settings.CSP_REPORT_ONLY
                else "Content-Security-Policy"
            )
            response.headers.setdefault(header, self._policy())
        return response
