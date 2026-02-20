"""
Finance API v1 URLs
"""
from django.urls import path
from .views import CostEngineRunView, CostEngineHistoryView
from .kpi_views import KPISummaryView, KPICostStructureView, KPITrendView

app_name = 'finance_api_v1'

urlpatterns = [
    # Cost Engine — runtime calculation
    path('cost-engine/run/', CostEngineRunView.as_view(), name='cost_engine_run'),
    # Cost Engine — persisted analytics
    path('cost-engine/history/', CostEngineHistoryView.as_view(), name='cost_engine_history'),
    # KPI endpoints — persisted-only, dashboard-fast
    path('kpis/company/summary/', KPISummaryView.as_view(), name='kpi_company_summary'),
    path('kpis/company/cost-structure/', KPICostStructureView.as_view(), name='kpi_cost_structure'),
    path('kpis/company/trend/', KPITrendView.as_view(), name='kpi_trend'),
]
