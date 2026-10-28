import json, os, secrets
from pathlib import Path
import sys
ADMIN = Path(__file__).resolve().parents[4] / "adminapps/backend"
sys.path.insert(0, str(ADMIN)); os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
import django; django.setup()
from rest_framework.test import APIClient
from apps.users.models import User, UserOrganization
from apps.organizations.models import Organization, TenantIntegrationOutbox
from apps.integration.models import IntegrationAPIKey
from apps.products.models import OrganizationProductEntitlement, ProductSystem
actor = User.objects.filter(email="retry12-owner@example.test").first()
if actor is None:
	actor = User.objects.create_superuser(email="retry12-owner@example.test", password=secrets.token_urlsafe(32))
client = APIClient(); client.force_authenticate(user=actor)
organization = Organization.objects.filter(email="retry12-tenant@example.test").first()
if organization is None:
	r = client.post("/api/organizations/", {"name": "Retry 12 Native Tenant", "email": "retry12-tenant@example.test"})
	if r.status_code != 201: raise RuntimeError(f"tenant create failed: {r.status_code} {r.data}")
	organization = Organization.objects.get(pk=r.data["id"])
UserOrganization.objects.get_or_create(user=actor, organization=organization, defaults={"role": "superadmin", "is_primary": True})
IntegrationAPIKey.objects.update_or_create(name="isosmart", defaults={"key": os.environ["RETRY11_INTEGRATION_KEY"], "is_active": True})
product = ProductSystem.objects.get(code="ISO_SMART")
if product.billing_enabled:
	product.billing_enabled = False
	product.save(update_fields=["billing_enabled"])
OrganizationProductEntitlement.objects.get_or_create(organization=organization, product=product, defaults={"status": "active", "enabled": True, "scopes": ["qms"]})
if organization.status != "active":
	r = client.post(f"/api/organizations/{organization.id}/activate/")
	if r.status_code != 200: raise RuntimeError(f"tenant activation failed: {r.status_code} {r.data}")
event = TenantIntegrationOutbox.objects.filter(organization=organization).order_by("-source_version").first()
print(json.dumps({"tenant_id": str(organization.id), "actor_id": str(actor.id), "event_id": str(event.id), "source_version": event.source_version}))
