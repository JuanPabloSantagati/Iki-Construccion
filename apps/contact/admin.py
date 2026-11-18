from django.contrib import admin

from .models import Inquiry


@admin.register(Inquiry)
class InquiryAdmin(admin.ModelAdmin):
    """Las consultas llegan por el formulario: acá solo se leen y se cambia el estado."""

    list_display = ("name", "phone", "service", "location", "status", "created_at")
    list_filter = ("status", "service")
    search_fields = ("name", "email")
    date_hierarchy = "created_at"
    fields = (
        "status",
        "name",
        "email",
        "phone",
        "service",
        "location",
        "approx_area",
        "message",
        "consent",
        "consent_at",
        "created_at",
        "anonymized_at",
    )
    readonly_fields = (
        "name",
        "email",
        "phone",
        "service",
        "location",
        "approx_area",
        "message",
        "consent",
        "consent_at",
        "created_at",
        "anonymized_at",
    )

    def has_add_permission(self, request):
        return False
