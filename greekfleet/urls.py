from django.contrib import admin
from django.urls import path, include
from finance.views_debug import debug_cost_engine

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('accounts.urls')),
    path('api/v1/auth/', include('finance.api.v1.auth_urls')),
    path('billing/', include('billing.urls')),
    path('api/v1/', include('finance.api.v1.urls')),
    path('finance/debug/cost-engine/', debug_cost_engine, name='debug_cost_engine'),
    path('', include('web.urls')),
]