from django.urls import path
from finance.views_debug import debug_cost_engine

urlpatterns = [
    path("debug/cost-engine/", debug_cost_engine, name="debug_cost_engine"),
]
