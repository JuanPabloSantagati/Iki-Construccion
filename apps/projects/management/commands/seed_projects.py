from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from apps.core.models import SiteSettings, Zone
from apps.projects.models import ProjectType
from apps.services.models import Service, ServiceStep

PROJECT_TYPES = [
    ("vivienda", "Vivienda"),
    ("local-comercial", "Local comercial"),
    ("oficina", "Oficina"),
    ("reforma", "Reforma"),
    ("ampliacion", "Ampliación"),
]

# Provisorio: la lista real de zonas la definen los socios desde el admin.
ZONES = [
    ("baradero", "Baradero"),
    ("san-pedro", "San Pedro"),
    ("zarate", "Zárate"),
    ("san-antonio-de-areco", "San Antonio de Areco"),
]

# Los 5 servicios de IKI: (slug, título, resumen, pasos).
# Borradores: los socios revisan textos y pasos y los publican desde el admin.
SERVICES = [
    (
        "proyecto-y-anteproyecto",
        "Proyecto y anteproyecto",
        "Del primer boceto al proyecto completo, pensado para cómo vivís y trabajás.",
        [
            "Entrevista y relevamiento",
            "Anteproyecto",
            "Ajustes con el cliente",
            "Proyecto final y documentación",
        ],
    ),
    (
        "renders",
        "Renders",
        "Imágenes realistas para ver el proyecto terminado antes de construirlo.",
        [
            "Recepción de planos o ideas",
            "Modelado 3D",
            "Revisión con el cliente",
            "Entrega de imágenes finales",
        ],
    ),
    (
        "direccion-de-obra",
        "Dirección de obra",
        "Seguimiento técnico para que la obra respete el proyecto, los plazos y el presupuesto.",
        [
            "Planificación",
            "Seguimiento en obra",
            "Control de calidad y plazos",
            "Entrega",
        ],
    ),
    (
        "planos-municipales",
        "Planos municipales",
        "Planos y gestiones para registrar o aprobar tu obra ante el municipio.",
        [
            "Relevamiento",
            "Planos según el código de edificación local",
            "Presentación en la municipalidad",
            "Seguimiento hasta la aprobación",
        ],
    ),
    (
        "agrimensura-y-legajos",
        "Agrimensura y legajos",
        "Mensuras, estudio de antecedentes y legajos para que tu terreno esté en regla.",
        [
            "Relevamiento y mensura del terreno",
            "Estudio de títulos y antecedentes",
            "Planos y legajo",
            "Presentación y registro",
        ],
    ),
]

ADDRESS = "Baradero, Buenos Aires"


class Command(BaseCommand):
    help = "Carga datos de referencia (tipos, servicios, zonas). Idempotente; solo para desarrollo."

    def add_arguments(self, parser):
        parser.add_argument(
            "--force",
            action="store_true",
            help="Permite correr con DEBUG=False.",
        )

    def handle(self, *args, **options):
        if not settings.DEBUG and not options["force"]:
            raise CommandError(
                "seed_projects se niega a correr con DEBUG=False. Usá --force si estás seguro."
            )
        with transaction.atomic():
            created = {
                "tipos de proyecto": self._seed_simple(ProjectType, PROJECT_TYPES),
                "zonas": self._seed_simple(Zone, ZONES),
                "servicios": self._seed_services(),
            }
            site = SiteSettings.load()
            if not site.address:
                site.address = ADDRESS
                site.save()
                created["dirección del sitio"] = 1
        news = [f"{n} {label}" for label, n in created.items() if n]
        self.stdout.write("Creados: " + ", ".join(news) + "." if news else "Nada nuevo para crear.")

    @staticmethod
    def _seed_simple(model, rows):
        """get_or_create por slug: lo que ya existe (y pudo editarse) no se toca."""
        return sum(
            model.objects.get_or_create(slug=slug, defaults={"name": name})[1]
            for slug, name in rows
        )

    @staticmethod
    def _seed_services():
        count = 0
        for order, (slug, title, summary, steps) in enumerate(SERVICES, start=1):
            service, is_new = Service.objects.get_or_create(
                slug=slug, defaults={"title": title, "summary": summary, "order": order}
            )
            if is_new:  # los pasos solo se crean con el servicio: borrarlos en el admin es válido
                ServiceStep.objects.bulk_create(
                    ServiceStep(service=service, title=step, order=i)
                    for i, step in enumerate(steps, start=1)
                )
                count += 1
        return count
