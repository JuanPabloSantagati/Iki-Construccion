from django.contrib import admin

from .models import Service, ServiceStep


class ServiceStepInline(admin.TabularInline):
    model = ServiceStep
    extra = 1


@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ("title", "order", "is_published")
    list_editable = ("order", "is_published")
    list_filter = ("is_published",)
    search_fields = ("title",)
    prepopulated_fields = {"slug": ("title",)}
    inlines = [ServiceStepInline]
