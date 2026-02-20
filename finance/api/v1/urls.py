"""
Finance API v1 URLs
"""
from django.urls import path
from .views import CostEngineRunView

app_name = 'finance_api_v1'

urlpatterns = [
    path('cost-engine/run/', CostEngineRunView.as_view(), name='cost_engine_run'),
]
