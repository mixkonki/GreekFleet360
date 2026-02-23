"""
Fuel Entry API Views
Tenant-scoped fuel entry management
"""
from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import PermissionDenied

from operations.models import FuelEntry, Vehicle
from core.models import Company
from core.tenant_context import tenant_context
from rest_framework import serializers


class FuelEntrySerializer(serializers.ModelSerializer):
    """
    Serializer for FuelEntry
    Company is set server-side, not accepted from payload
    Vehicle queryset is scoped to current tenant
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
        # Override vehicle field queryset to be tenant-scoped
        request = self.context.get('request')
        if request and hasattr(request, 'user') and request.user.is_authenticated:
            company = self._get_company_from_request(request)
            if company:
                # Scope vehicle queryset to current company
                with tenant_context(company):
                    self.fields['vehicle'].queryset = Vehicle.objects.filter(company=company)
    
    def _get_company_from_request(self, request):
        """
        Get company from request (middleware or user profile)
        Raises PermissionDenied if no company found (orphan user)
        """
        if hasattr(request, 'company') and request.company:
            return request.company
        elif hasattr(request.user, 'profile') and hasattr(request.user.profile, 'company'):
            return request.user.profile.company
        
        # No fallbacks - orphan users get 403
        raise PermissionDenied(
            'Ο λογαριασμός σας δεν έχει συσχετισμένη εταιρεία. Επικοινωνήστε με τον διαχειριστή.'
        )


class FuelEntryViewSet(viewsets.ModelViewSet):
    """
    ViewSet for FuelEntry
    
    Endpoints:
    - GET /api/v1/fuel-entries/ - List fuel entries (tenant-scoped)
    - POST /api/v1/fuel-entries/ - Create fuel entry (company set server-side)
    - GET /api/v1/fuel-entries/{id}/ - Retrieve fuel entry
    - PUT/PATCH /api/v1/fuel-entries/{id}/ - Update fuel entry
    - DELETE /api/v1/fuel-entries/{id}/ - Delete fuel entry
    
    Tenant Isolation:
    - Queryset strictly scoped to current tenant
    - Company set server-side on create
    - Vehicle validation ensures same-company only
    """
    
    serializer_class = FuelEntrySerializer
    permission_classes = [IsAuthenticated]
    http_method_names = ['get', 'post', 'head', 'options']  # list, create only
    
    def get_serializer_context(self):
        """
        Add request to serializer context
        """
        context = super().get_serializer_context()
        context['request'] = self.request
        return context
    
    def get_queryset(self):
        """
        Return queryset strictly scoped to current tenant
        NEVER use .all() or .all_objects
        Raises PermissionDenied if no company (orphan user)
        """
        company = self._get_company()
        
        # Use tenant context for strict isolation
        with tenant_context(company):
            return FuelEntry.objects.filter(company=company).select_related(
                'vehicle', 'driver', 'company'
            ).order_by('-date', '-created_at')
    
    def perform_create(self, serializer):
        """
        Set company server-side on create
        Do NOT accept company from payload
        Raises PermissionDenied if no company (orphan user)
        """
        company = self._get_company()
        
        # Save with company set server-side
        with tenant_context(company):
            serializer.save(company=company)
    
    def _get_company(self):
        """
        Get company from request (middleware or user profile)
        Raises PermissionDenied if no company found (orphan user)
        """
        if hasattr(self.request, 'company') and self.request.company:
            return self.request.company
        elif hasattr(self.request.user, 'profile') and hasattr(self.request.user.profile, 'company'):
            return self.request.user.profile.company
        
        # No fallbacks - orphan users get 403
        raise PermissionDenied(
            'Ο λογαριασμός σας δεν έχει συσχετισμένη εταιρεία. Επικοινωνήστε με τον διαχειριστή.'
        )
