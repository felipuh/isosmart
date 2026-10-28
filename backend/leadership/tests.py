from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import AccessToken

from authentication.models import UserProfile
from core.models import Organization
from leadership.models import EvidenceEdge, EvidenceNode


class EvidenceEdgeTenantContainmentTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            email='evidence-edge-tests@isosmart.local',
            password='StrongPass@123',
        )
        self.tenant_a = Organization.objects.create(
            name='Evidence Tenant A',
            slug='evidence-tenant-a',
            email='evidence-tenant-a@isosmart.local',
        )
        self.tenant_b = Organization.objects.create(
            name='Evidence Tenant B',
            slug='evidence-tenant-b',
            email='evidence-tenant-b@isosmart.local',
        )
        profile = UserProfile.objects.create(
            user=self.user,
            organization=self.tenant_a,
            role='org_admin',
            is_active=True,
        )
        token = AccessToken.for_user(self.user)
        token['organization_id'] = self.tenant_a.id
        token['profile_id'] = profile.id
        token['role'] = 'org_admin'
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')

        self.node_a1 = self._node(self.tenant_a, 'A1')
        self.node_a2 = self._node(self.tenant_a, 'A2')
        self.node_b1 = self._node(self.tenant_b, 'B1')
        self.node_b2 = self._node(self.tenant_b, 'B2')

    def _node(self, organization, title):
        return EvidenceNode.objects.create(
            organization_id=organization.id,
            node_type='result',
            title=title,
        )

    def _create_edge(self, source, target):
        return self.client.post(
            '/api/leadership/evidence-edges/',
            {'source': source.id, 'target': target.id, 'edge_type': 'supports'},
            format='json',
        )

    def test_only_two_nodes_from_current_tenant_can_be_connected(self):
        allowed = self._create_edge(self.node_a1, self.node_a2)
        self.assertEqual(allowed.status_code, 201)
        edge = EvidenceEdge.objects.get(id=allowed.data['id'])
        self.assertEqual(edge.source.organization_id, self.tenant_a.id)
        self.assertEqual(edge.target.organization_id, self.tenant_a.id)

        for source, target in [
            (self.node_a1, self.node_b1),
            (self.node_b1, self.node_a1),
            (self.node_b1, self.node_b2),
        ]:
            with self.subTest(source=source.title, target=target.title):
                response = self._create_edge(source, target)
                self.assertEqual(response.status_code, 400)
                self.assertNotIn(self.tenant_b.name, str(response.data))

        self.assertEqual(EvidenceEdge.objects.count(), 1)

    def test_cross_tenant_and_missing_node_references_use_same_generic_error(self):
        cross_tenant = self._create_edge(self.node_a1, self.node_b1)
        missing = self.client.post(
            '/api/leadership/evidence-edges/',
            {'source': self.node_a1.id, 'target': 99999999, 'edge_type': 'supports'},
            format='json',
        )
        self.assertEqual(cross_tenant.status_code, 400)
        self.assertEqual(missing.status_code, 400)
        self.assertEqual(cross_tenant.data, missing.data)

    def test_foreign_edges_cannot_be_listed_retrieved_updated_or_deleted(self):
        foreign_edge = EvidenceEdge.objects.create(
            source=self.node_b1,
            target=self.node_b2,
            edge_type='supports',
            created_by=self.user,
        )
        collection_url = '/api/leadership/evidence-edges/'
        detail_url = f'{collection_url}{foreign_edge.id}/'

        listed = self.client.get(collection_url)
        self.assertEqual(listed.status_code, 200)
        self.assertNotIn(foreign_edge.id, [item['id'] for item in listed.data['results']])
        self.assertEqual(self.client.get(detail_url).status_code, 404)
        self.assertEqual(
            self.client.patch(detail_url, {'label': 'attacker'}, format='json').status_code,
            404,
        )
        self.assertEqual(self.client.delete(detail_url).status_code, 404)
        foreign_edge.refresh_from_db()
        self.assertEqual(foreign_edge.label, '')

    def test_graph_action_excludes_legacy_cross_tenant_edges(self):
        valid_edge = EvidenceEdge.objects.create(
            source=self.node_a1,
            target=self.node_a2,
            edge_type='supports',
            created_by=self.user,
        )
        legacy_cross_tenant_edge = EvidenceEdge.objects.create(
            source=self.node_a1,
            target=self.node_b1,
            edge_type='supports',
            created_by=self.user,
        )

        response = self.client.get('/api/leadership/evidence-nodes/graph/')
        self.assertEqual(response.status_code, 200)
        edge_ids = [edge['id'] for edge in response.data['edges']]
        self.assertIn(valid_edge.id, edge_ids)
        self.assertNotIn(legacy_cross_tenant_edge.id, edge_ids)
        node_a = next(node for node in response.data['nodes'] if node['id'] == self.node_a1.id)
        self.assertEqual(node_a['outgoing_edges_count'], 1)

    def test_update_cannot_repoint_current_edge_to_foreign_node(self):
        edge = EvidenceEdge.objects.create(
            source=self.node_a1,
            target=self.node_a2,
            edge_type='supports',
            created_by=self.user,
        )
        response = self.client.patch(
            f'/api/leadership/evidence-edges/{edge.id}/',
            {'target': self.node_b1.id},
            format='json',
        )
        self.assertEqual(response.status_code, 400)
        edge.refresh_from_db()
        self.assertEqual(edge.target_id, self.node_a2.id)
