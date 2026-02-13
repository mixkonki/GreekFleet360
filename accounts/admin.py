"""
Django Admin Configuration for Accounts App
"""
from django.contrib import admin
from .models import UserProfile


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'company', 'role', 'phone', 'created_at']
    list_filter = ['role', 'company']
    search_fields = ['user__username', 'user__email', 'phone']
    ordering = ['user__username']
    
    fieldsets = (
        ('Βασικές Πληροφορίες', {
            'fields': ('user', 'company', 'role')
        }),
        ('Επικοινωνία', {
            'fields': ('phone',)
        }),
    )
    
    readonly_fields = ['created_at', 'updated_at']
