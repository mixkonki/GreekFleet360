"""
Finance API v1 URLs
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import CostEngineRunView, CostEngineHistoryView
from .kpi_views import KPISummaryView, KPICostStructureView, KPITrendView
from .fuel_views import FuelEntryViewSet

app_name = 'finance_api_v1'

# DRF Router for ViewSets
router = DefaultRouter()
router.register(r'fuel-entries', FuelEntryViewSet, basename='fuel-entry')

urlpatterns = [
    # Cost Engine — runtime calculation
    path('cost-engine/run/', CostEngineRunView.as_view(), name='cost_engine_run'),
    # Cost Engine — persisted analytics
    path('cost-engine/history/', CostEngineHistoryView.as_view(), name='cost_engine_history'),
    # KPI endpoints — persisted-only, dashboard-fast
    path('kpis/company/summary/', KPISummaryView.as_view(), name='kpi_company_summary'),
    path('kpis/company/cost-structure/', KPICostStructureView.as_view(), name='kpi_cost_structure'),
    path('kpis/company/trend/', KPITrendView.as_view(), name='kpi_trend'),
    # Fuel Entries ViewSet
    path('', include(router.urls)),
]
