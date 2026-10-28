"""Create a Retry 10 tenant through the native AdminApps API."""

import json
import os
import secrets
import sys
from pathlib import Path

ADMIN = Path(__file__).resolve().parents[4] / "adminapps/backend"
sys.path.insert(0, str(ADMIN))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
import django
django.setup()

from rest_framework.test import APIClient
from apps.users.models import User, UserOrganization
from apps.organizations.models import Organization, TenantIntegrationOutbox
from apps.products.models import OrganizationProductEntitlement, ProductSystem
from apps.integration.models import IntegrationAPIKey
from django.utils import timezone

actor = User.objects.filter(email="retry10-owner@example.test").first()
if actor is None:
    actor = User.objects.create_superuser(email="retry10-owner@example.test", password=secrets.token_urlsafe(32))
client = APIClient()
client.force_authenticate(user=actor)
organization = Organization.objects.filter(email="retry10-tenant@example.test").first()
created_now = organization is None
if created_now:
    response = client.post("/api/organizations/", {"name": "Retry 10 Native Tenant", "email": "retry10-tenant@example.test"})
    if response.status_code != 201:
        raise RuntimeError(f"native AdminApps tenant API returned {response.status_code}: {response.data}")
    organization = Organization.objects.get(pk=response.data["id"])
UserOrganization.objects.get_or_create(user=actor, organization=organization, defaults={"role": "superadmin", "is_primary": True})
product = ProductSystem.objects.get(code="ISO_SMART")
if product.billing_enabled:
    # The isolated Stage EXT product has no billing subscription; configure
    # the product's supported non-billing mode before checking entitlement.
    product.billing_enabled = False
    product.save(update_fields=["billing_enabled"])
entitlement, _ = OrganizationProductEntitlement.objects.get_or_create(
    organization=organization, product=product,
    defaults={"status": "active", "enabled": True, "scopes": ["qms"]})
IntegrationAPIKey.objects.update_or_create(name="isosmart", defaults={"key": os.environ["RETRY10_INTEGRATION_KEY"], "is_active": True})
if organization.status != "active":
    activated = client.post(f"/api/organizations/{organization.id}/activate/")
    if activated.status_code != 200:
        raise RuntimeError(f"native AdminApps activation API returned {activated.status_code}: {activated.data}")
event = TenantIntegrationOutbox.objects.filter(organization=organization).order_by("-source_version").first()
if event.status == "failed":
    # Advance only this disposable event's retry clock after correcting ingress configuration.
    event.available_at = timezone.now()
    event.save(update_fields=["available_at"])
print(json.dumps({"tenant_id": str(organization.id), "actor_id": str(actor.id), "event_id": str(event.id), "created_now": created_now,
                  "product_billing_enabled": product.billing_enabled,
                  "source_version": event.source_version, "schema_version": event.envelope["schema_version"],
                  "aggregate_id": event.envelope["aggregate_id"], "entitlement_id": str(entitlement.id)}))
