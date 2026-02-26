"""
Fuel Entry API Views
Tenant-scoped fuel entry management
"""
from rest_framework import serializers
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import PermissionDenied

from operations.models import FuelEntry, Vehicle
from core.tenant_context import tenant_context
from core.api.tenancy import TenantScopedModelViewSet, ORPHAN_COMPANY_MESSAGE


class FuelEntrySerializer(serializers.ModelSerializer):
    """
    Serializer for FuelEntry
    - Company is set server-side, not accepted from payload
    - Vehicle queryset is scoped to current tenant
    - Hard validation ensures vehicle belongs to request.company
    """

    class Meta:
        model = FuelEntry
        fields = [
            'id', 'vehicle', 'driver', 'date', 'fuel_station_name',
            'liters', 'cost_per_liter', 'total_cost',
            'is_full_tank', 'odometer_reading',
            'adblue_liters', 'adblue_cost', 'notes',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        request = self.context.get('request')
        company = getattr(request, 'company', None) if request else None

        if company:
            with tenant_context(company):
                self.fields['vehicle'].queryset = Vehicle.objects.filter(company=company)

    def validate_vehicle(self, vehicle):
        request = self.context.get('request')
        company = getattr(request, 'company', None) if request else None

        if not company:
            # Keep behavior consistent with viewset: orphan -> 403
            raise PermissionDenied(ORPHAN_COMPANY_MESSAGE)

        if vehicle.company_id != company.id:
            raise serializers.ValidationError('Μη έγκυρο όχημα για την εταιρεία σας.')

        return vehicle


class FuelEntryViewSet(TenantScopedModelViewSet):
    """
    ViewSet for FuelEntry (list + create only)

    Tenant Isolation:
    - request.company enforced by base class
    - queryset filtered by company in base class
    - company injected server-side in base class perform_create
    """

    serializer_class = FuelEntrySerializer
    permission_classes = [IsAuthenticated]
    http_method_names = ['get', 'post', 'head', 'options']  # list, create only

    # Important: base class needs a queryset to start from
    queryset = FuelEntry.objects.all()

    def get_queryset_base(self):
        """
        Build base queryset (ordering, joins) WITHOUT tenant filter.
        TenantScopedModelViewSet will apply .filter(company=company) in tenant_context.
        """
        return (
            FuelEntry.objects
            .select_related('vehicle', 'driver', 'company')
            .order_by('-date', '-created_at')
        )