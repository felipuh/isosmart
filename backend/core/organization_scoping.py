from rest_framework.exceptions import PermissionDenied, ValidationError


class OrganizationScopedViewSetMixin:
    """Aplica filtrado estricto por organización para ViewSets."""

    organization_lookup_field = 'organization_id'
    organization_write_field = 'organization_id'
    require_organization = True

    def _parse_org_id(self, value):
        if value in (None, ''):
            return None
        try:
            return int(value)
        except (TypeError, ValueError):
            raise ValidationError({'organization_id': 'organization_id inválido'})

    def get_organization_id(self):
        query_org_id = self._parse_org_id(
            self.request.query_params.get('organization_id')
            or self.request.query_params.get('organization')
        )
        token_org_id = self._parse_org_id(getattr(self.request, 'organization_id', None))

        if query_org_id and token_org_id and query_org_id != token_org_id:
            raise PermissionDenied('organization_id no coincide con el token activo')

        organization_id = query_org_id or token_org_id
        if self.require_organization and not organization_id:
            raise ValidationError({'organization_id': 'organization_id requerido'})

        return organization_id

    def get_queryset(self):
        queryset = super().get_queryset()
        organization_id = self.get_organization_id()
        if not organization_id:
            return queryset.none()
        return queryset.filter(**{self.organization_lookup_field: organization_id})

    def perform_create(self, serializer):
        organization_id = self.get_organization_id()

        if self.organization_write_field:
            payload_org_id = self._parse_org_id(
                self.request.data.get(self.organization_write_field)
                or self.request.data.get('organization')
            )
            if payload_org_id and payload_org_id != organization_id:
                raise PermissionDenied('No puede crear registros para otra organización')
            serializer.save(**{self.organization_write_field: organization_id})
            return

        serializer.save()

    def perform_update(self, serializer):
        organization_id = self.get_organization_id()

        if self.organization_write_field:
            payload_org_id = self._parse_org_id(
                self.request.data.get(self.organization_write_field)
                or self.request.data.get('organization')
            )
            if payload_org_id and payload_org_id != organization_id:
                raise PermissionDenied('No puede mover registros entre organizaciones')

        serializer.save()
