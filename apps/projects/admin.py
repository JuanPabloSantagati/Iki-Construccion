from django.contrib import admin, messages
from django.core.exceptions import PermissionDenied, ValidationError
from django.db.models import Max
from django.http import Http404
from django.shortcuts import redirect
from django.template.response import TemplateResponse
from django.urls import path, reverse
from django.utils.html import format_html

from .forms import UploadImagesForm
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
    readonly_fields = ("upload_link",)
    fieldsets = (
        (None, {"fields": ("title", "slug", "status", "category", "project_type", "is_featured")}),
        ("Ubicación y datos", {"fields": ("location", "zone", "area_m2", "year")}),
        ("Contenido", {"fields": ("summary", "description", "services")}),
        ("Imágenes", {"fields": ("upload_link",)}),
        ("SEO", {"classes": ("collapse",), "fields": ("seo_title", "seo_description")}),
    )

    @admin.display(description="Imágenes nuevas")
    def upload_link(self, obj):
        if not obj or not obj.pk:
            return "Guardá el proyecto para poder subir imágenes."
        url = reverse("admin:projects_project_upload_images", args=[obj.pk])
        return format_html('<a class="button" href="{}">Subir imágenes</a>', url)

    def get_urls(self):
        custom = [
            path(
                "<path:object_id>/subir-imagenes/",
                self.admin_site.admin_view(self.upload_images_view),
                name="projects_project_upload_images",
            ),
        ]
        return custom + super().get_urls()

    def upload_images_view(self, request, object_id):
        project = self.get_object(request, object_id)
        if project is None:
            raise Http404
        if not self.has_change_permission(request, project):
            raise PermissionDenied
        form = UploadImagesForm(request.POST or None, request.FILES or None)
        if request.method == "POST" and form.is_valid():
            next_order = (project.images.aggregate(top=Max("order"))["top"] or 0) + 1
            saved = 0
            for uploaded in form.cleaned_data["files"]:
                try:
                    ProjectImage.from_upload(project, uploaded, order=next_order + saved)
                except ValidationError as exc:
                    self.message_user(
                        request, f"{uploaded.name}: {' '.join(exc.messages)}", messages.ERROR
                    )
                else:
                    saved += 1
            if saved:
                self.message_user(request, f"Imágenes subidas: {saved}.", messages.SUCCESS)
            return redirect(reverse("admin:projects_project_change", args=[project.pk]))
        context = {
            **self.admin_site.each_context(request),
            "opts": self.model._meta,
            "project": project,
            "form": form,
            "title": f"Subir imágenes · {project.title}",
        }
        return TemplateResponse(request, "admin/projects/project/upload_images.html", context)
