"""PostgreSQL contract tests for the QMS Audit → Finding → NC → CAPA HTTP slice."""

from datetime import date, timedelta
from uuid import uuid4

from django.test import override_settings
from django.utils import timezone

from foundation import qms_api_views as views
from foundation import test_source_artifact_postgres_integration as base
from foundation.api_views import EvidenceCreateView
from foundation.models import (
    DomainEvent, ImmutableAuditLog, Organization, QmsCorrectiveAction,
    QmsNonconformity, TransactionalOutbox, UserProjection,
)


@override_settings(QMS_WRITE_ROLES=("quality_manager",), QMS_CAPA_CREATE_ENABLED=True)
class QmsCapaApiPostgresTests(base.SourceArtifactPostgreSQLIntegrationTests):
    def setUp(self):
        super().setUp()
        self.other_org_id = uuid4()
        Organization.objects.using("default").create(
            id=self.other_org_id, tenant_id=self.other_tenant_id, display_name="Other tenant org")
        self.other_claims = {
            "organization_id": str(self.other_external_tenant_id), "user_id": str(self.other_actor_id),
            "role": "quality_manager", "client_id": "qms-contract-test", "scope": "",
        }
        self.other_user = base.SimpleNamespace(is_authenticated=True, pk=self.other_actor_id)

    def call(self, view, method, path, data=None, *, other=False, **kwargs):
        if method == "get":
            request = self.factory.get(path, data or {})
        else:
            request = getattr(self.factory, method)(path, data, format="json")
        base.force_authenticate(
            request, user=self.other_user if other else self.user,
            token=self.other_claims if other else self.claims)
        return view.as_view()(request, **kwargs)

    def post_ok(self, view, path, data, **kwargs):
        response = self.call(view, "post", path, data, **kwargs)
        self.assertEqual(response.status_code, 201, response.data)
        return response.data

    def make_evidence(self):
        request = self.factory.post("/v1/evidence", {
            "organization_id": str(self.organization_id), "source_type": "audit_fixture",
            "content_hash": "e" * 64, "captured_at": timezone.now().isoformat()}, format="json")
        base.force_authenticate(request, user=self.user, token=self.claims)
        response = EvidenceCreateView.as_view()(request)
        self.assertEqual(response.status_code, 201)
        return response.data["evidence_id"]

    def make_chain(self):
        evidence_id = self.make_evidence()
        audit = self.post_ok(views.AuditsView, "/v1/qms/audits", {
            "organization_id": str(self.organization_id), "scope": "Production", "criteria": "Program",
            "status": "planned", "lead_auditor": "Lead", "tenant_id": str(self.other_tenant_id)})
        finding = self.post_ok(views.FindingsView, "/v1/qms/findings", {
            "audit_id": audit["id"], "requirement_id": str(self.requirement.id), "type": "nonconformity",
            "statement": "Observed gap", "evidence_id": evidence_id})
        nc = self.post_ok(views.FindingNonconformityView, "/x", {
            "description": "NC text", "severity": "major", "status": "detected"}, finding_id=finding["id"])
        capa = self.post_ok(views.NonconformityCorrectiveActionView, "/x", {
            "cause_id": str(uuid4()), "action": "Fix it", "owner_id": str(self.actor_id),
            "due_date": (date.today() + timedelta(days=30)).isoformat()}, nc_id=nc["id"])
        return evidence_id, audit, finding, nc, capa

    def test_vertical_journey_persists_readback_events_and_audit(self):
        orgs = self.call(views.QmsOrganizationsView, "get", "/v1/qms/organizations").data["results"]
        self.assertEqual([o["id"] for o in orgs], [str(self.organization_id)])
        reqs = self.call(views.QmsRequirementsView, "get", "/v1/qms/requirements").data["results"]
        self.assertIn(str(self.requirement.id), [r["id"] for r in reqs])
        evidence_id, audit, finding, nc, capa = self.make_chain()

        findings = self.call(views.FindingsView, "get", "/v1/qms/findings", {"audit_id": audit["id"]}).data["results"]
        self.assertEqual([f["id"] for f in findings], [finding["id"]])
        self.assertEqual(findings[0]["evidence_id"], evidence_id)
        ncs = self.call(views.NonconformitiesView, "get", "/v1/qms/nonconformities").data["results"]
        self.assertEqual((ncs[0]["source_type"], ncs[0]["source_id"]), ("finding", finding["id"]))
        capas = self.call(views.CorrectiveActionsView, "get", "/v1/qms/corrective-actions", {"nc_id": nc["id"]}).data["results"]
        self.assertEqual(capas[0]["id"], capa["id"])
        self.assertEqual(self.call(views.AuditsView, "get", "/v1/qms/audits").data["results"][0]["id"], audit["id"])
        self.assertEqual(self.call(views.QmsEvidenceView, "get", "/v1/qms/evidence").data["results"][0]["id"], evidence_id)

        # Server-derived tenant: the client-supplied tenant_id was ignored.
        with base.trusted_tenant_context(self.identity, actor_id=self.actor_id, trace_id=uuid4(), using="app"):
            self.assertEqual(QmsNonconformity.objects.using("app").get(pk=nc["id"]).tenant_id, self.tenant_id)
            self.assertEqual(QmsCorrectiveAction.objects.using("app").get(pk=capa["id"]).tenant_id, self.tenant_id)
            for key, event_type in (("finding", "audit.finding.created"), ("nc", "nonconformity.detected")):
                row = {"finding": finding, "nc": nc}[key]
                event = DomainEvent.objects.using("app").get(event_id=row["event_id"])
                self.assertEqual(event.event_type, event_type)
                self.assertEqual(str(event.trace_id), row["trace_id"])
                self.assertTrue(TransactionalOutbox.objects.using("app").filter(
                    domain_event_id=event.event_id, status="pending").exists())
        # No event is defined by the source for audit/CAPA creation: none is invented.
        self.assertIsNone(audit["event_id"])
        self.assertIsNone(capa["event_id"])
        for row, entity in ((audit, "audit"), (finding, "finding"), (nc, "nonconformity"), (capa, "corrective_action")):
            log = ImmutableAuditLog.objects.using("default").get(pk=row["audit_log_id"])
            self.assertEqual((log.tenant_id, log.actor_id, log.entity_type, str(log.entity_id), str(log.trace_id)),
                             (self.tenant_id, str(self.actor_id), entity, row["id"], row["trace_id"]))

    def test_cross_tenant_denied_and_same_tenant_allowed(self):
        evidence_id, audit, finding, nc, capa = self.make_chain()
        for view, path in ((views.AuditsView, "/a"), (views.FindingsView, "/f"),
                           (views.NonconformitiesView, "/n"), (views.CorrectiveActionsView, "/c"),
                           (views.QmsEvidenceView, "/e"), (views.QmsOrganizationsView, "/o")):
            data = self.call(view, "get", path, other=True).data["results"]
            self.assertEqual([r["id"] for r in data if r["id"] in (
                audit["id"], finding["id"], nc["id"], capa["id"], evidence_id, str(self.organization_id))], [])
        today = date.today().isoformat()
        denied = [
            self.call(views.AuditsView, "post", "/a", {
                "organization_id": str(self.organization_id), "scope": "s", "criteria": "c",
                "status": "planned", "lead_auditor": "l"}, other=True),
            self.call(views.FindingsView, "post", "/f", {
                "audit_id": audit["id"], "requirement_id": str(self.requirement.id), "type": "t",
                "statement": "s", "evidence_id": evidence_id}, other=True),
            self.call(views.FindingNonconformityView, "post", "/n", {
                "description": "d", "severity": "major", "status": "detected"}, other=True, finding_id=finding["id"]),
            self.call(views.NonconformityCorrectiveActionView, "post", "/c", {
                "cause_id": str(uuid4()), "action": "a", "owner_id": str(self.other_actor_id),
                "due_date": today}, other=True, nc_id=nc["id"]),
        ]
        self.assertEqual([r.status_code for r in denied], [404, 404, 404, 404])
        self.assertTrue(all(r.data["code"] == "REFERENCE_NOT_FOUND" for r in denied))

    def test_owner_must_belong_to_tenant_and_duplicate_nc_is_rejected(self):
        _, audit, finding, nc, _ = self.make_chain()
        response = self.call(views.NonconformityCorrectiveActionView, "post", "/c", {
            "cause_id": str(uuid4()), "action": "a", "owner_id": str(self.other_actor_id),
            "due_date": date.today().isoformat()}, nc_id=nc["id"])
        self.assertEqual((response.status_code, response.data["code"]), (422, "OWNER_NOT_IN_TENANT"))
        response = self.call(views.FindingNonconformityView, "post", "/n", {
            "description": "again", "severity": "major", "status": "detected"}, finding_id=finding["id"])
        self.assertEqual((response.status_code, response.data["code"]), (409, "NONCONFORMITY_ALREADY_EXISTS"))

    def test_write_authorization_is_enforced_by_backend(self):
        evidence_id, audit, finding, nc, _ = self.make_chain()
        body = {"organization_id": str(self.organization_id), "scope": "s", "criteria": "c",
                "status": "planned", "lead_auditor": "l"}
        # AUTHORIZED_ROLE_ALLOWED / SAME_TENANT_ALLOWED
        self.post_ok(views.AuditsView, "/a", body)
        before = {
            "audit": len(self.call(views.AuditsView, "get", "/a").data["results"]),
            "log": ImmutableAuditLog.objects.using("default").count(),
        }
        writes = (
            (views.AuditsView, body, {}),
            (views.FindingsView, {"audit_id": audit["id"], "requirement_id": str(self.requirement.id),
                                  "type": "t", "statement": "s", "evidence_id": evidence_id}, {}),
            (views.FindingNonconformityView, {"description": "d", "severity": "x", "status": "y"},
             {"finding_id": finding["id"]}),
            (views.NonconformityCorrectiveActionView, {
                "cause_id": str(uuid4()), "action": "a", "owner_id": str(self.actor_id),
                "due_date": date.today().isoformat()}, {"nc_id": nc["id"]}),
        )
        # UNAUTHORIZED_ROLE_DENIED: valid tenant principal, role outside the allow-list.
        self.claims["role"] = "viewer"
        for view, data, kwargs in writes:
            response = self.call(view, "post", "/x", data, **kwargs)
            self.assertEqual((response.status_code, response.data["code"]), (403, "QMS_WRITE_ROLE_REQUIRED"))
        # Reads stay available, owners (a user directory) do not.
        self.assertEqual(self.call(views.AuditsView, "get", "/a").status_code, 200)
        self.assertEqual(self.call(views.QmsOwnersView, "get", "/o").status_code, 403)
        caps = self.call(views.QmsCapabilitiesView, "get", "/c").data
        self.assertEqual((caps["can_write"], caps["capa_create_enabled"]), (False, False))
        # Fail closed when no policy is configured, even for the formerly allowed role.
        self.claims["role"] = "quality_manager"
        with override_settings(QMS_WRITE_ROLES=()):
            for view, data, kwargs in writes:
                response = self.call(view, "post", "/x", data, **kwargs)
                self.assertEqual((response.status_code, response.data["code"]),
                                 (403, "QMS_WRITE_POLICY_NOT_ESTABLISHED"))
        self.assertEqual(len(self.call(views.AuditsView, "get", "/a").data["results"]), before["audit"])
        self.assertEqual(ImmutableAuditLog.objects.using("default").count(), before["log"])

    def test_capabilities_owners_and_capa_blocker(self):
        caps = self.call(views.QmsCapabilitiesView, "get", "/c").data
        self.assertEqual((caps["can_write"], caps["capa_create_enabled"]), (True, True))
        owners = self.call(views.QmsOwnersView, "get", "/o").data["results"]
        self.assertIn(str(self.actor_id), [o["id"] for o in owners])
        self.assertNotIn(str(self.other_actor_id), [o["id"] for o in owners])
        other = self.call(views.QmsOwnersView, "get", "/o", other=True).data["results"]
        self.assertNotIn(str(self.actor_id), [o["id"] for o in other])
        _, _, _, nc, _ = self.make_chain()
        with override_settings(QMS_CAPA_CREATE_ENABLED=False):
            caps = self.call(views.QmsCapabilitiesView, "get", "/c").data
            self.assertEqual((caps["capa_create_enabled"], caps["capa_create_blocker"]),
                             (False, "CAUSE_REFERENCE_SEMANTICS_INSUFFICIENT"))
            response = self.call(views.NonconformityCorrectiveActionView, "post", "/c", {
                "cause_id": str(uuid4()), "action": "a", "owner_id": str(self.actor_id),
                "due_date": date.today().isoformat()}, nc_id=nc["id"])
            self.assertEqual((response.status_code, response.data["code"]), (409, "CAPA_CAUSE_REFERENCE_UNDEFINED"))

    def test_validation_errors(self):
        response = self.call(views.AuditsView, "post", "/a", {"organization_id": "nope", "scope": " "})
        self.assertEqual((response.status_code, response.data["code"]), (400, "REQUEST_INVALID"))
        response = self.call(views.FindingsView, "get", "/f", {"audit_id": "bad"})
        self.assertEqual(response.status_code, 400)


# Do not re-run the parent's inherited tests under this class.
for _name in dir(base.SourceArtifactPostgreSQLIntegrationTests):
    if _name.startswith("test") and _name not in QmsCapaApiPostgresTests.__dict__:
        setattr(QmsCapaApiPostgresTests, _name, None)
