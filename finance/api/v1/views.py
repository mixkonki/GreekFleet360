"""
Finance API v1 Views
Cost Engine Analytics API
"""
from calendar import monthrange
from datetime import date, datetime
from decimal import Decimal

from django.conf import settings
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated, IsAdminUser

from core.models import Company
from core.tenant_context import tenant_context
from finance.services.cost_engine.calculator import calculate_company_costs
from finance.services.analytics.history import get_cost_engine_history


class CostEngineRunView(APIView):
    """
    Cost Engine Analytics API
    
    GET /api/v1/cost-engine/run/?period_start=YYYY-MM-DD&period_end=YYYY-MM-DD
    
    Query Parameters:
    - period_start (required): Period start date (YYYY-MM-DD)
    - period_end (required): Period end date (YYYY-MM-DD)
    - company_id (optional): Company ID (superuser only; defaults to user's company or first company in dev)
    - only_nonzero (optional): Filter snapshots where total_cost>0 OR rate>0 (0 or 1, default 0)
    - include_breakdowns (optional): Include order breakdowns (0 or 1, default 1)
    
    Returns:
    - 200: Schema v1 JSON (meta/snapshots/breakdowns/summary)
    - 400: Invalid parameters
    - 403: Permission denied
    - 404: Company not found
    """
    
    permission_classes = [IsAuthenticated, IsAdminUser]
    
    def get(self, request):
        # Parse required parameters
        period_start_str = request.query_params.get('period_start')
        period_end_str = request.query_params.get('period_end')
        
        if not period_start_str or not period_end_str:
            return Response(
                {'error': 'period_start and period_end are required query parameters'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Parse dates
        try:
            period_start = date.fromisoformat(period_start_str)
            period_end = date.fromisoformat(period_end_str)
        except ValueError:
            return Response(
                {'error': 'Invalid date format. Use YYYY-MM-DD'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Validate date range
        if period_start > period_end:
            return Response(
                {'error': 'period_start must be before or equal to period_end'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Determine company
        company_id = request.query_params.get('company_id')
        
        if company_id:
            # Only superusers can specify company_id
            if not request.user.is_superuser:
                return Response(
                    {'error': 'Only superusers can specify company_id'},
                    status=status.HTTP_403_FORBIDDEN
                )
            
            try:
                company = Company.objects.get(id=int(company_id))
            except (Company.DoesNotExist, ValueError):
                return Response(
                    {'error': f'Company with ID {company_id} not found'},
                    status=status.HTTP_404_NOT_FOUND
                )
        else:
            # Use request user's company if available
            company = None
            
            # Try request.company (set by middleware)
            if hasattr(request, 'company') and request.company:
                company = request.company
            # Try user.company (if user profile has company relation)
            elif hasattr(request.user, 'company') and request.user.company:
                company = request.user.company
            # Fallback to first company in DEBUG mode only
            elif settings.DEBUG:
                company = Company.objects.first()
            
            if not company:
                return Response(
                    {'error': 'No company found. In DEBUG mode, ensure at least one company exists.'},
                    status=status.HTTP_404_NOT_FOUND
                )
        
        # Parse optional parameters
        only_nonzero = request.query_params.get('only_nonzero', '0') == '1'
        include_breakdowns = request.query_params.get('include_breakdowns', '1') == '1'
        
        # Run calculation inside tenant context
        with tenant_context(company):
            result = calculate_company_costs(company, period_start, period_end)
        
        # Apply filters
        if only_nonzero:
            # Filter snapshots where total_cost > 0 OR rate > 0
            filtered_snapshots = []
            for snap in result.get('snapshots', []):
                total_cost = snap.get('total_cost', 0)
                rate = snap.get('rate', 0)
                
                # Convert to Decimal for comparison
                if isinstance(total_cost, (int, float, str)):
                    total_cost = Decimal(str(total_cost))
                if isinstance(rate, (int, float, str)):
                    rate = Decimal(str(rate))
                
                if total_cost > Decimal('0') or rate > Decimal('0'):
                    filtered_snapshots.append(snap)
            
            result['snapshots'] = filtered_snapshots
        
        if not include_breakdowns:
            result['breakdowns'] = []
        
        # Serialize datetime objects
        if 'meta' in result and 'generated_at' in result['meta']:
            generated_at = result['meta']['generated_at']
            if isinstance(generated_at, datetime):
                result['meta']['generated_at'] = generated_at.isoformat()
        
        if 'meta' in result:
            if 'period_start' in result['meta'] and isinstance(result['meta']['period_start'], date):
                result['meta']['period_start'] = result['meta']['period_start'].isoformat()
            if 'period_end' in result['meta'] and isinstance(result['meta']['period_end'], date):
                result['meta']['period_end'] = result['meta']['period_end'].isoformat()
        
        return Response(result, status=status.HTTP_200_OK)


def _resolve_company(request, company_id_param):
    """
    Shared helper: resolve Company from request or company_id param.
    Returns (company, error_response) — one of them is None.
    """
    if company_id_param:
        if not request.user.is_superuser:
            return None, Response(
                {'error': 'Only superusers can specify company_id'},
                status=status.HTTP_403_FORBIDDEN,
            )
        try:
            company = Company.objects.get(id=int(company_id_param))
        except (Company.DoesNotExist, ValueError):
            return None, Response(
                {'error': f'Company with ID {company_id_param} not found'},
                status=status.HTTP_404_NOT_FOUND,
            )
        return company, None

    company = None
    if hasattr(request, 'company') and request.company:
        company = request.company
    elif hasattr(request.user, 'company') and request.user.company:
        company = request.user.company
    elif settings.DEBUG:
        company = Company.objects.first()

    if not company:
        return None, Response(
            {'error': 'No company found.'},
            status=status.HTTP_404_NOT_FOUND,
        )
    return company, None


def _previous_full_month():
    """Return (period_start, period_end) for the previous full calendar month."""
    today = date.today()
    # First day of current month
    first_of_current = today.replace(day=1)
    # Last day of previous month
    last_of_prev = first_of_current - __import__('datetime').timedelta(days=1)
    first_of_prev = last_of_prev.replace(day=1)
    return first_of_prev, last_of_prev


class CostEngineHistoryView(APIView):
    """
    Cost Engine History API — read-only, persisted data only.

    GET /api/v1/cost-engine/history/

    Query Parameters:
    - period_start (YYYY-MM-DD) optional
    - period_end   (YYYY-MM-DD) optional
    - month        (YYYY-MM)    optional shortcut — overrides period_start/end
    - include_breakdowns (0/1)  default 0
    - only_nonzero       (0/1)  default 0
    - cost_center_id     int    optional
    - basis_unit         str    optional (KM|HOUR|TRIP|REVENUE)
    - limit              int    optional (default 500, max 2000)
    - company_id         int    optional superuser-only

    Returns:
    - 200: {meta, snapshots, breakdowns, summary}
    - 400: Invalid parameters
    - 403: Permission denied
    - 404: Company not found
    """

    permission_classes = [IsAuthenticated, IsAdminUser]

    def get(self, request):
        params = request.query_params

        # --- Resolve company ---
        company, err = _resolve_company(request, params.get('company_id'))
        if err:
            return err

        # --- Resolve period ---
        month_str = params.get('month')
        period_start_str = params.get('period_start')
        period_end_str = params.get('period_end')

        if month_str:
            # month shortcut: YYYY-MM
            try:
                year, mon = int(month_str[:4]), int(month_str[5:7])
                period_start = date(year, mon, 1)
                period_end = date(year, mon, monthrange(year, mon)[1])
            except (ValueError, IndexError):
                return Response(
                    {'error': 'Invalid month format. Use YYYY-MM'},
                    status=status.HTTP_400_BAD_REQUEST,
                )
        elif period_start_str or period_end_str:
            # Both must be provided if either is given
            if not period_start_str or not period_end_str:
                return Response(
                    {'error': 'Provide both period_start and period_end, or neither (defaults to previous month)'},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            try:
                period_start = date.fromisoformat(period_start_str)
                period_end = date.fromisoformat(period_end_str)
            except ValueError:
                return Response(
                    {'error': 'Invalid date format. Use YYYY-MM-DD'},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            if period_start > period_end:
                return Response(
                    {'error': 'period_start must be before or equal to period_end'},
                    status=status.HTTP_400_BAD_REQUEST,
                )
        else:
            # Default: previous full calendar month
            period_start, period_end = _previous_full_month()

        # --- Parse optional filters ---
        include_breakdowns = params.get('include_breakdowns', '0') == '1'
        only_nonzero = params.get('only_nonzero', '0') == '1'

        cost_center_id = None
        raw_cc = params.get('cost_center_id')
        if raw_cc:
            try:
                cost_center_id = int(raw_cc)
            except ValueError:
                return Response(
                    {'error': 'cost_center_id must be an integer'},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        basis_unit = params.get('basis_unit')
        if basis_unit and basis_unit.upper() not in ('KM', 'HOUR', 'TRIP', 'REVENUE'):
            return Response(
                {'error': 'basis_unit must be one of: KM, HOUR, TRIP, REVENUE'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        limit = 500
        raw_limit = params.get('limit')
        if raw_limit:
            try:
                limit = int(raw_limit)
            except ValueError:
                return Response(
                    {'error': 'limit must be an integer'},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        # --- Fetch persisted data inside tenant context ---
        with tenant_context(company):
            payload = get_cost_engine_history(
                company,
                period_start,
                period_end,
                cost_center_id=cost_center_id,
                basis_unit=basis_unit,
                include_breakdowns=include_breakdowns,
                only_nonzero=only_nonzero,
                limit=limit,
            )

        return Response(payload, status=status.HTTP_200_OK)
