from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from core.models import Organization, OrganizationSettings, ISOClauseConfig
from authentication.models import UserProfile, User
from planning.models import RiskOpportunity, QualityObjective, ObjectiveAction, ChangeControl
from resources.models import Resource, Infrastructure, WorkEnvironment, Competence, Training, Awareness, Communication
from operations.models import (
    OperationalControl,
    CustomerRequirement,
    DesignProject,
    ExternalProvider,
    ProductionControl,
    ProductRelease,
    Nonconformity as OperationsNonconformity,
    Disposition,
)
from performance.models import PerformanceIndicator, Measurement, DataAnalysis, InternalAudit, AuditFinding, ManagementReview
from improvement.models import Nonconformity as ImprovementNonconformity, CorrectiveAction, ContinualImprovement


class Command(BaseCommand):
    help = 'Limpia datos de prueba y deja una sola organización activa.'

    def add_arguments(self, parser):
        parser.add_argument('--organization-id', type=int, required=True, help='ID de organización a conservar')
        parser.add_argument('--dry-run', action='store_true', help='Solo muestra conteos, sin borrar')

    def _delete_by_org_id(self, model, keep_org_id, dry_run=False):
        qs = model.objects.exclude(organization_id=keep_org_id)
        count = qs.count()
        if not dry_run and count:
            qs.delete()
        return count

    @transaction.atomic
    def handle(self, *args, **options):
        keep_org_id = options['organization_id']
        dry_run = options['dry_run']

        try:
            keep_org = Organization.objects.get(id=keep_org_id)
        except Organization.DoesNotExist as exc:
            raise CommandError(f'Organización {keep_org_id} no existe') from exc

        self.stdout.write(self.style.WARNING(f"Organización a conservar: {keep_org.id} - {keep_org.name}"))

        deleted = {}

        # Modelos con organization_id (entero)
        models_with_org_id = [
            RiskOpportunity, QualityObjective, ObjectiveAction, ChangeControl,
            Resource, Infrastructure, WorkEnvironment, Competence, Training, Awareness, Communication,
            OperationalControl, CustomerRequirement, DesignProject, ExternalProvider,
            ProductionControl, ProductRelease, OperationsNonconformity,
            PerformanceIndicator, Measurement, DataAnalysis, InternalAudit, AuditFinding, ManagementReview,
            ImprovementNonconformity, CorrectiveAction, ContinualImprovement,
        ]

        for model in models_with_org_id:
            deleted[model.__name__] = self._delete_by_org_id(model, keep_org_id, dry_run=dry_run)

        # Dispositions dependen de NC operaciones
        orphan_dispositions = Disposition.objects.exclude(nonconformity__organization_id=keep_org_id)
        deleted['Disposition'] = orphan_dispositions.count()
        if not dry_run and deleted['Disposition']:
            orphan_dispositions.delete()

        # Configuración / cláusulas / perfiles
        deleted['ISOClauseConfig'] = ISOClauseConfig.objects.exclude(organization_id=keep_org_id).count()
        if not dry_run and deleted['ISOClauseConfig']:
            ISOClauseConfig.objects.exclude(organization_id=keep_org_id).delete()

        deleted['OrganizationSettings'] = OrganizationSettings.objects.exclude(organization_id=keep_org_id).count()
        if not dry_run and deleted['OrganizationSettings']:
            OrganizationSettings.objects.exclude(organization_id=keep_org_id).delete()

        deleted['UserProfile'] = UserProfile.objects.exclude(organization_id=keep_org_id).count()
        if not dry_run and deleted['UserProfile']:
            UserProfile.objects.exclude(organization_id=keep_org_id).delete()

        # Eliminar organizaciones no deseadas
        deleted['Organization'] = Organization.objects.exclude(id=keep_org_id).count()
        if not dry_run and deleted['Organization']:
            Organization.objects.exclude(id=keep_org_id).delete()

        # Eliminar usuarios huérfanos sin perfiles activos
        orphan_users = User.objects.filter(profiles__isnull=True, is_superuser=False)
        deleted['OrphanUsers'] = orphan_users.count()
        if not dry_run and deleted['OrphanUsers']:
            orphan_users.delete()

        self.stdout.write(self.style.SUCCESS('Resumen de limpieza:'))
        total = 0
        for key, value in deleted.items():
            total += value
            self.stdout.write(f' - {key}: {value}')

        if dry_run:
            self.stdout.write(self.style.WARNING(f'DRY-RUN completado. Se eliminarían {total} registros.'))
        else:
            self.stdout.write(self.style.SUCCESS(f'Limpieza completada. Registros eliminados: {total}'))
