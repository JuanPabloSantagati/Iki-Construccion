from django import forms
from django.contrib import admin
from django.shortcuts import redirect
from django.urls import reverse
from django.utils.html import format_html

from .images import process_image
from .models import SiteSettings, TeamMember, Zone


@admin.register(SiteSettings)
class SiteSettingsAdmin(admin.ModelAdmin):
    """Registro único: el listado lleva directo a su formulario; no se agrega ni se borra."""

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def changelist_view(self, request, extra_context=None):
        obj = SiteSettings.load()
        return redirect(reverse("admin:core_sitesettings_change", args=[obj.pk]))


@admin.register(Zone)
class ZoneAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "is_published")
    list_filter = ("is_published",)
    list_editable = ("is_published",)
    search_fields = ("name",)
    prepopulated_fields = {"slug": ("name",)}


class TeamMemberForm(forms.ModelForm):
    """La foto no se edita como ImageField: se sube por `new_photo` y pasa por el pipeline."""

    new_photo = forms.FileField(label="Foto nueva", required=False)

    class Meta:
        model = TeamMember
        fields = ("name", "role", "bio", "order")

    def clean_new_photo(self):
        upload = self.cleaned_data.get("new_photo")
        if upload:
            process_image(upload)  # lanza ValidationError si no es una imagen válida
            upload.seek(0)
        return upload


@admin.register(TeamMember)
class TeamMemberAdmin(admin.ModelAdmin):
    form = TeamMemberForm
    list_display = ("name", "role", "order")
    list_editable = ("order",)
    fields = ("name", "role", "bio", "order", "photo_preview", "new_photo")
    readonly_fields = ("photo_preview",)

    @admin.display(description="Foto actual")
    def photo_preview(self, obj):
        if obj and obj.photo:
            return format_html('<img src="{}" width="120" alt="">', obj.photo.url)
        return "—"

    def save_model(self, request, obj, form, change):
        upload = form.cleaned_data.get("new_photo")
        if upload:
            obj.set_photo(upload)
        super().save_model(request, obj, form, change)
