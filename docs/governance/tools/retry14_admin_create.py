"""Create the canonical Retry 14 tenant and owner through AdminApps APIs."""

import json
import os
from pathlib import Path
import secrets
import sys

ADMIN = Path(__file__).resolve().parents[4] / "adminapps/backend"
sys.path.insert(0, str(ADMIN))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

import django

django.setup()

from rest_framework.test import APIClient

from apps.integration.models import IntegrationAPIKey
from apps.organizations.models import Organization, TenantIntegrationOutbox
from apps.products.models import OrganizationProductEntitlement, ProductSystem
from apps.users.models import User, UserOrganization


actor = User.objects.create_superuser(
    email="retry14-owner@example.test",
    password=secrets.token_urlsafe(32),
)
client = APIClient()
client.force_authenticate(user=actor)
response = client.post(
    "/api/organizations/",
    {"name": "Retry 14 Native Tenant", "email": "retry14-tenant@example.test"},
)
if response.status_code != 201:
    raise RuntimeError(f"tenant create failed: {response.status_code} {response.data}")
organization = Organization.objects.get(pk=response.data["id"])
UserOrganization.objects.create(
    user=actor,
    organization=organization,
    role="superadmin",
    is_primary=True,
)
IntegrationAPIKey.objects.create(
    name="isosmart-retry14",
    key=os.environ["RETRY14_INTEGRATION_KEY"],
    is_active=True,
)
product = ProductSystem.objects.get(code="ISO_SMART")
if product.billing_enabled:
    product.billing_enabled = False
    product.save(update_fields=["billing_enabled"])
OrganizationProductEntitlement.objects.create(
    organization=organization,
    product=product,
    status="active",
    enabled=True,
    scopes=["qms"],
)
response = client.post(f"/api/organizations/{organization.id}/activate/")
if response.status_code != 200:
    raise RuntimeError(f"tenant activation failed: {response.status_code} {response.data}")
event = TenantIntegrationOutbox.objects.filter(organization=organization).order_by("-source_version").first()
if event is None:
    raise RuntimeError("tenant activation did not create a transactional outbox event")
print(json.dumps({
    "tenant_id": str(organization.id),
    "actor_id": str(actor.id),
    "event_id": str(event.id),
    "source_version": event.source_version,
}))
