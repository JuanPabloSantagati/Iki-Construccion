from django.contrib import admin
from django.utils.html import format_html

from .models import Project, ProjectFact, ProjectImage, ProjectType


@admin.register(ProjectType)
class ProjectTypeAdmin(admin.ModelAdmin):
    list_display = ("name", "slug")
    search_fields = ("name",)
    prepopulated_fields = {"slug": ("name",)}


class ProjectFactInline(admin.TabularInline):
    model = ProjectFact
    extra = 1


class ProjectImageInline(admin.TabularInline):
    """Edita alt, orden y portada de imágenes ya subidas. Las nuevas entran por 'Subir imágenes'."""

    model = ProjectImage
    extra = 0
    fields = ("preview", "alt", "order", "is_cover")
    readonly_fields = ("preview",)

    def has_add_permission(self, request, obj=None):
        return False

    @admin.display(description="Imagen")
    def preview(self, obj):
        if obj and obj.pk:
            return format_html('<img src="{}" width="120" alt="">', obj.thumb.url)
        return "—"


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ("title", "category", "project_type", "zone", "year", "status", "is_featured")
    list_editable = ("status", "is_featured")
    list_filter = ("status", "category", "project_type", "zone", "is_featured")
    search_fields = ("title", "location")
    prepopulated_fields = {"slug": ("title",)}
    filter_horizontal = ("services",)
    inlines = [ProjectFactInline, ProjectImageInline]
    fieldsets = (
        (None, {"fields": ("title", "slug", "status", "category", "project_type", "is_featured")}),
        ("Ubicación y datos", {"fields": ("location", "zone", "area_m2", "year")}),
        ("Contenido", {"fields": ("summary", "description", "services")}),
        ("SEO", {"classes": ("collapse",), "fields": ("seo_title", "seo_description")}),
    )
