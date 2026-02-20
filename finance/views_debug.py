"""
Debug Views for Finance App
DEV-ONLY endpoints for inspecting Cost Engine results
"""
from django.http import JsonResponse, Http404
from django.conf import settings
from decimal import Decimal
from datetime import date

from core.models import Company
from core.tenant_context import tenant_context
from finance.services.cost_engine.calculator import calculate_company_costs


def _serialize_decimal(obj):
    """Convert Decimal to float for JSON serialization"""
    if isinstance(obj, Decimal):
        return float(obj)
    elif isinstance(obj, date):
        return obj.isoformat()
    elif isinstance(obj, dict):
        return {k: _serialize_decimal(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [_serialize_decimal(item) for item in obj]
    return obj


def debug_cost_engine(request):
    """
    DEV-ONLY: Inspect Cost Engine calculation results
    
    Returns JSON with meta, snapshots, breakdowns, summary
    """
    # Only available in DEBUG mode
    if not settings.DEBUG:
        raise Http404("This endpoint is only available in DEBUG mode")
    
    # Get first company
    company = Company.objects.first()
    if not company:
        return JsonResponse({
            "error": "No companies found in database"
        }, status=404)
    
    # Define period
    period_start = date(2026, 1, 1)
    period_end = date(2026, 1, 31)
    
    # Run calculation inside tenant context
    with tenant_context(company):
        result = calculate_company_costs(company, period_start, period_end)
    
    # Serialize Decimals to floats for JSON
    serialized_result = _serialize_decimal(result)
    
    return JsonResponse(serialized_result, safe=False)
