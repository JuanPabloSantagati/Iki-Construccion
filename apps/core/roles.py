"""Grupos de permisos del admin. Se crean/actualizan solos después de cada migrate."""

from django.apps import apps as global_apps
from django.contrib.auth.management import create_permissions

ACTIONS = ("add", "change", "delete", "view")

# Editor: carga contenido. No ve consultas (datos personales) ni la configuración del sitio.
EDITOR_MODELS = [
    "projects.project",
    "projects.projecttype",
    "projects.projectfact",
    "projects.projectimage",
    "services.service",
    "services.servicestep",
    "core.teammember",
    "core.zone",
]

# Gestión: lo del Editor + responder consultas + datos de contacto del sitio.
MANAGEMENT_EXTRA = {
    "contact.inquiry": ("view", "change"),
    "core.sitesettings": ("view", "change"),
}

GROUPS = {
    "Editor": dict.fromkeys(EDITOR_MODELS, ACTIONS),
    "Gestión": {**dict.fromkeys(EDITOR_MODELS, ACTIONS), **MANAGEMENT_EXTRA},
}


def sync_groups(apps=global_apps, using="default"):
    Group = apps.get_model("auth", "Group")
    Permission = apps.get_model("auth", "Permission")
    # Los permisos de las apps posteriores a core todavía pueden no existir.
    for app_config in global_apps.get_app_configs():
        create_permissions(app_config, verbosity=0, using=using)
    for name, models in GROUPS.items():
        group, _ = Group.objects.using(using).get_or_create(name=name)
        perms = []
        for label, actions in models.items():
            app_label, model = label.split(".")
            codenames = [f"{action}_{model}" for action in actions]
            perms += Permission.objects.using(using).filter(
                content_type__app_label=app_label, codename__in=codenames
            )
        group.permissions.set(perms)
