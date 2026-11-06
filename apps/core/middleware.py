from django.conf import settings


class PermissionsPolicyMiddleware:
    """Agrega el header Permissions-Policy (Django no lo trae de forma nativa)."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        response.headers.setdefault("Permissions-Policy", settings.PERMISSIONS_POLICY)
        return response
