from django.contrib import admin

from .models import Inquiry


@admin.register(Inquiry)
class InquiryAdmin(admin.ModelAdmin):
    """Las consultas llegan por el formulario: acá solo se leen y se cambia el estado."""

    list_display = ("name", "email", "status", "created_at")
    list_filter = ("status",)
    search_fields = ("name", "email")
    date_hierarchy = "created_at"
    fields = (
        "status",
        "name",
        "email",
        "phone",
        "message",
        "consent",
        "consent_at",
        "created_at",
    )
    readonly_fields = (
        "name",
        "email",
        "phone",
        "message",
        "consent",
        "consent_at",
        "created_at",
    )

    def has_add_permission(self, request):
        return False
