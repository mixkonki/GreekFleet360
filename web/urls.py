"""
URL Configuration for Web App
"""
from django.urls import path
from . import views

app_name = 'web'

urlpatterns = [
    path('', views.dashboard_home, name='dashboard'),
    path('vehicles/', views.vehicle_list, name='vehicle_list'),
    path('orders/', views.order_list, name='order_list'),
    path('orders/<int:order_id>/', views.order_detail, name='order_detail'),
    path('orders/create/', views.order_create, name='order_create'),
    path('fuel/create/', views.fuel_create, name='fuel_create'),
    path('finance/settings/', views.finance_settings, name='finance_settings'),
    path('finance/expense/form/', views.expense_form, name='expense_form'),
    path('finance/expense/create/', views.expense_create, name='expense_create'),
    path('finance/expense/<int:expense_id>/delete/', views.expense_delete, name='expense_delete'),
    path('finance/cost-center/form/', views.cost_center_form, name='cost_center_form'),
    path('finance/cost-center/create/', views.cost_center_create, name='cost_center_create'),
    path('finance/cost-center/<int:cost_center_id>/edit/', views.cost_center_edit, name='cost_center_edit'),
    path('finance/cost-center/<int:cost_center_id>/update/', views.cost_center_update, name='cost_center_update'),
    path('finance/cost-center/<int:cost_center_id>/delete/', views.cost_center_delete, name='cost_center_delete'),
    path('finance/employee/create/', views.employee_create, name='employee_create'),
    path('finance/employee/<int:employee_id>/edit/', views.employee_edit, name='employee_edit'),
    path('finance/employee/<int:employee_id>/delete/', views.employee_delete, name='employee_delete'),
    
    # Fleet Management (New Vehicle Model)
    path('fleet/', views.fleet_list, name='fleet_list'),
    path('fleet/create/', views.fleet_create, name='fleet_create'),
    path('fleet/<int:vehicle_id>/edit/', views.fleet_update, name='fleet_update'),
    path('fleet/<int:vehicle_id>/delete/', views.fleet_delete, name='fleet_delete'),
    
    # Settings Hub
    path('settings/', views.settings_hub, name='settings_hub'),
    path('settings/company/', views.company_edit, name='company_edit'),
    path('settings/users/create/', views.user_create, name='user_create'),
    path('settings/users/<int:user_id>/delete/', views.user_delete, name='user_delete'),
    path('settings/categories/create/', views.category_create, name='category_create'),
    path('settings/categories/<int:category_id>/delete/', views.category_delete, name='category_delete'),
]
