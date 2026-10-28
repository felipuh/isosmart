import json
import os
import secrets
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4] / "adminapps/backend"))
import django
from rest_framework.test import APIClient

django.setup()

from apps.integration.models import IntegrationAPIKey
from apps.organizations.models import Organization
from apps.products.models import OrganizationProductEntitlement, ProductSystem
from apps.users.models import User, UserOrganization

actor, created = User.objects.get_or_create(email="retry16-owner@example.test", defaults={"is_staff": True, "is_superuser": True, "is_active": True})
if created:
    actor.set_password(secrets.token_urlsafe(32))
    actor.save(update_fields=["password"])
client = APIClient()
client.force_authenticate(user=actor)
organization = Organization.objects.filter(email="retry16-tenant@example.test").first()
if organization is None:
    response = client.post("/api/organizations/", {"name": "Retry 16 Native Tenant", "email": "retry16-tenant@example.test"})
    if response.status_code != 201:
        raise RuntimeError(f"tenant create failed: {response.status_code} {response.data}")
    organization = Organization.objects.get(pk=response.data["id"])
UserOrganization.objects.get_or_create(user=actor, organization=organization, defaults={"role": "superadmin", "is_primary": True})
key, _ = IntegrationAPIKey.objects.get_or_create(name="isosmart-retry16", defaults={"key": os.environ["RETRY16_INTEGRATION_KEY"], "is_active": True})
key.key = os.environ["RETRY16_INTEGRATION_KEY"]
key.is_active = True
key.save(update_fields=["key", "is_active"])
product = ProductSystem.objects.get(code="ISO_SMART")
if product.billing_enabled:
    product.billing_enabled = False
    product.save(update_fields=["billing_enabled"])
OrganizationProductEntitlement.objects.get_or_create(organization=organization, product=product, defaults={"status": "active", "enabled": True, "scopes": ["qms"]})
if organization.status != "active":
    response = client.post(f"/api/organizations/{organization.id}/activate/")
    if response.status_code != 200:
        raise RuntimeError(f"tenant activation failed: {response.status_code} {response.data}")
print(json.dumps({"tenant_id": str(organization.id), "actor_id": str(actor.id)}))
