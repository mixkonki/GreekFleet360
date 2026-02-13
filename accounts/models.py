"""
Accounts Models for GreekFleet 360
User Profile linking User to Company
"""
from django.db import models
from django.contrib.auth.models import User
from core.models import Company


class UserProfile(models.Model):
    """
    User Profile - Links User to Company for Multi-Tenancy
    Separate from DriverProfile (which is for actual drivers)
    """
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='profile',
        verbose_name="Χρήστης"
    )
    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        related_name='users',
        verbose_name="Εταιρεία"
    )
    
    # Role
    ROLE_CHOICES = [
        ('ADMIN', 'Διαχειριστής'),
        ('MANAGER', 'Fleet Manager'),
        ('ACCOUNTANT', 'Λογιστής'),
        ('VIEWER', 'Θεατής'),
    ]
    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        default='VIEWER',
        verbose_name="Ρόλος"
    )
    
    # Metadata
    phone = models.CharField(max_length=20, blank=True, verbose_name="Τηλέφωνο")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Προφίλ Χρήστη"
        verbose_name_plural = "Προφίλ Χρηστών"
    
    def __str__(self):
        return f"{self.user.username} - {self.company.name}"
