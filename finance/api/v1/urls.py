"""
Finance API v1 URLs
"""
from django.urls import path
from .views import CostEngineRunView, CostEngineHistoryView

app_name = 'finance_api_v1'

urlpatterns = [
    path('cost-engine/run/', CostEngineRunView.as_view(), name='cost_engine_run'),
    path('cost-engine/history/', CostEngineHistoryView.as_view(), name='cost_engine_history'),
]
