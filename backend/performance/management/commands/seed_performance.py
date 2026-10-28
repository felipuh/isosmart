from datetime import date, timedelta
from decimal import Decimal

from django.core.management.base import BaseCommand
from django.db import transaction

from performance.models import (
    PerformanceIndicator,
    Measurement,
    DataAnalysis,
    InternalAudit,
    AuditFinding,
    ManagementReview,
)


class Command(BaseCommand):
    help = "Seed performance module with sample data."

    def add_arguments(self, parser):
        parser.add_argument("--organization-id", type=int, default=1)
        parser.add_argument("--organization-name", type=str, default="Organizacion Principal")

    @transaction.atomic
    def handle(self, *args, **options):
        organization_id = options["organization_id"]
        organization_name = options["organization_name"]

        indicators = [
            {
                "code": "KPI-Q01",
                "name": "Defect Rate",
                "description": "Percentage of defects per batch.",
                "indicator_type": "quality",
                "measurement_method": "Defects / Total units * 100",
                "formula": "(defects / units) * 100",
                "target_value": Decimal("2.50"),
                "unit_of_measure": "%",
                "frequency": "monthly",
                "status": "active",
            },
            {
                "code": "KPI-E02",
                "name": "On-time Delivery",
                "description": "Orders delivered on or before promised date.",
                "indicator_type": "efficiency",
                "measurement_method": "On-time orders / total orders * 100",
                "formula": "(on_time / total) * 100",
                "target_value": Decimal("95.00"),
                "unit_of_measure": "%",
                "frequency": "monthly",
                "status": "active",
            },
            {
                "code": "KPI-C03",
                "name": "Customer Satisfaction",
                "description": "Average customer satisfaction score.",
                "indicator_type": "customer_satisfaction",
                "measurement_method": "Average survey score",
                "formula": "sum(scores) / count(scores)",
                "target_value": Decimal("4.50"),
                "unit_of_measure": "score",
                "frequency": "quarterly",
                "status": "active",
            },
        ]

        indicator_objects = []
        for data in indicators:
            indicator, _ = PerformanceIndicator.objects.update_or_create(
                organization_id=organization_id,
                code=data["code"],
                defaults={
                    **data,
                    "organization_name": organization_name,
                },
            )
            indicator_objects.append(indicator)

        today = date.today()
        measurements = [
            {
                "indicator": indicator_objects[0],
                "measurement_date": today - timedelta(days=30),
                "actual_value": Decimal("2.10"),
                "target_value": Decimal("2.50"),
                "status": "on_target",
                "comments": "Stable quality levels.",
            },
            {
                "indicator": indicator_objects[0],
                "measurement_date": today,
                "actual_value": Decimal("2.90"),
                "target_value": Decimal("2.50"),
                "status": "needs_attention",
                "comments": "Spike in defects after vendor change.",
            },
            {
                "indicator": indicator_objects[1],
                "measurement_date": today - timedelta(days=30),
                "actual_value": Decimal("96.50"),
                "target_value": Decimal("95.00"),
                "status": "on_target",
                "comments": "Delivery performance above target.",
            },
            {
                "indicator": indicator_objects[1],
                "measurement_date": today,
                "actual_value": Decimal("92.00"),
                "target_value": Decimal("95.00"),
                "status": "below_target",
                "comments": "Delays due to transport issues.",
            },
            {
                "indicator": indicator_objects[2],
                "measurement_date": today - timedelta(days=90),
                "actual_value": Decimal("4.60"),
                "target_value": Decimal("4.50"),
                "status": "on_target",
                "comments": "Positive survey feedback.",
            },
        ]

        for data in measurements:
            Measurement.objects.update_or_create(
                organization_id=organization_id,
                indicator=data["indicator"],
                measurement_date=data["measurement_date"],
                defaults={
                    **data,
                },
            )

        analyses = [
            {
                "title": "Q1 Performance Trend",
                "analysis_type": "trend",
                "period_start": today - timedelta(days=90),
                "period_end": today,
                "objectives": "Identify performance trends across indicators.",
                "methodology": "Compare monthly results and highlight variance.",
                "findings": "Delivery dropped in the last month.",
                "conclusions": "Logistics disruptions impacted on-time delivery.",
                "recommendations": "Review logistics partner SLA and capacity.",
                "status": "completed",
            },
            {
                "title": "Customer Satisfaction Review",
                "analysis_type": "comparative",
                "period_start": today - timedelta(days=180),
                "period_end": today - timedelta(days=90),
                "objectives": "Compare satisfaction score across regions.",
                "methodology": "Analyze survey responses by region.",
                "findings": "Region B scores 0.4 points lower.",
                "conclusions": "Support response times are inconsistent.",
                "recommendations": "Implement service response SLAs.",
                "status": "in_review",
            },
        ]

        for data in analyses:
            DataAnalysis.objects.update_or_create(
                organization_id=organization_id,
                title=data["title"],
                period_start=data["period_start"],
                defaults={
                    **data,
                },
            )

        audits = [
            {
                "audit_code": "AUD-2026-001",
                "audit_type": "system",
                "title": "QMS System Audit",
                "objectives": "Verify compliance with ISO 9001.",
                "scope": "Entire QMS.",
                "criteria": "ISO 9001:2015 clauses.",
                "planned_date": today + timedelta(days=7),
                "status": "planned",
            },
            {
                "audit_code": "AUD-2026-002",
                "audit_type": "process",
                "title": "Production Process Audit",
                "objectives": "Check production controls.",
                "scope": "Production line A.",
                "criteria": "Internal procedures PR-01.",
                "planned_date": today - timedelta(days=14),
                "status": "completed",
            },
        ]

        audit_objects = []
        for data in audits:
            audit, _ = InternalAudit.objects.update_or_create(
                organization_id=organization_id,
                audit_code=data["audit_code"],
                defaults={
                    **data,
                    "organization_name": organization_name,
                },
            )
            audit_objects.append(audit)

        findings = [
            {
                "audit": audit_objects[0],
                "finding_number": "FND-001",
                "finding_type": "observation",
                "clause_reference": "9.1",
                "description": "Trend analysis documentation could be improved.",
                "evidence": "Missing variance notes in Q1 report.",
                "status": "open",
            },
            {
                "audit": audit_objects[1],
                "finding_number": "FND-002",
                "finding_type": "nc_minor",
                "clause_reference": "8.5",
                "description": "Calibration records incomplete.",
                "evidence": "Calibration log missing signatures.",
                "status": "in_progress",
            },
            {
                "audit": audit_objects[1],
                "finding_number": "FND-003",
                "finding_type": "opportunity",
                "clause_reference": "10.2",
                "description": "Automate corrective action tracking.",
                "evidence": "Manual tracking in spreadsheets.",
                "status": "open",
            },
        ]

        for data in findings:
            AuditFinding.objects.update_or_create(
                organization_id=organization_id,
                audit=data["audit"],
                finding_number=data["finding_number"],
                defaults={
                    **data,
                },
            )

        review, _ = ManagementReview.objects.update_or_create(
            organization_id=organization_id,
            review_code="MR-2026-001",
            defaults={
                "organization_name": organization_name,
                "title": "Management Review Q1",
                "scheduled_date": today + timedelta(days=21),
                "performance_results": "KPI review and improvement actions.",
                "customer_feedback": "Overall positive sentiment.",
                "status": "scheduled",
            },
        )

        self.stdout.write(self.style.SUCCESS("Performance seed data created."))
