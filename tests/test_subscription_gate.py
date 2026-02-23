"""
Tests for Subscription Gate Middleware
Ensures expired subscriptions are blocked with proper allowlist
"""
from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from django.utils import timezone
from datetime import timedelta
from accounts.models import UserProfile
from core.models import Company


class SubscriptionGateTests(TestCase):
    """Test subscription gate middleware functionality."""
    
    def setUp(self):
        """Set up test data with active and expired companies."""
        # Create active company
        self.active_company = Company.objects.create(
            name="Active Transport Co",
            tax_id="111111111",
            email="active@test.com",
            subscription_status='ACTIVE',
            subscription_expires_at=None  # No expiry
        )
        
        # Create expired company (status EXPIRED)
        self.expired_company = Company.objects.create(
            name="Expired Transport Co",
            tax_id="222222222",
            email="expired@test.com",
            subscription_status='EXPIRED',
            subscription_expires_at=timezone.now() - timedelta(days=30)
        )
        
        # Create active company user (ADMIN)
        self.active_admin = User.objects.create_user(
            username='active_admin',
            email='active_admin@test.com',
            password='TestPass123!'
        )
        UserProfile.objects.create(
            user=self.active_admin,
            company=self.active_company,
            role='ADMIN'
        )
        
        # Create expired company admin user
        self.expired_admin = User.objects.create_user(
            username='expired_admin',
            email='expired_admin@test.com',
            password='TestPass123!'
        )
        UserProfile.objects.create(
            user=self.expired_admin,
            company=self.expired_company,
            role='ADMIN'
        )
        
        # Create expired company non-admin user
        self.expired_user = User.objects.create_user(
            username='expired_user',
            email='expired_user@test.com',
            password='TestPass123!'
        )
        UserProfile.objects.create(
            user=self.expired_user,
            company=self.expired_company,
            role='VIEWER'
        )
        
        self.client = Client()
    
    def test_active_company_can_access_dashboard(self):
        """Test that active company user can access normal pages."""
        self.client.login(username='active_admin', password='TestPass123!')
        response = self.client.get(reverse('web:dashboard'))
        
        self.assertEqual(response.status_code, 200)
    
    def test_active_company_can_access_settings(self):
        """Test that active company user can access settings."""
        self.client.login(username='active_admin', password='TestPass123!')
        response = self.client.get(reverse('web:settings_hub'))
        
        self.assertEqual(response.status_code, 200)
    
    def test_expired_company_non_admin_blocked_from_dashboard(self):
        """Test that expired company non-admin user is redirected from dashboard."""
        self.client.login(username='expired_user', password='TestPass123!')
        response = self.client.get(reverse('web:dashboard'))
        
        # Should redirect to expired page
        self.assertEqual(response.status_code, 302)
        self.assertIn('/billing/expired/', response.url)
    
    def test_expired_company_non_admin_blocked_from_settings(self):
        """Test that expired company non-admin user is redirected from settings."""
        self.client.login(username='expired_user', password='TestPass123!')
        response = self.client.get(reverse('web:settings_hub'))
        
        # Should redirect to expired page
        self.assertEqual(response.status_code, 302)
        self.assertIn('/billing/expired/', response.url)
    
    def test_expired_company_admin_can_access_settings(self):
        """Test that expired company ADMIN can access settings (allowlist)."""
        self.client.login(username='expired_admin', password='TestPass123!')
        response = self.client.get(reverse('web:settings_hub'))
        
        # Admin should be able to access settings even when expired
        self.assertEqual(response.status_code, 200)
    
    def test_expired_company_can_access_expired_page(self):
        """Test that expired company users can access the expired page itself."""
        self.client.login(username='expired_user', password='TestPass123!')
        response = self.client.get(reverse('billing:expired'))
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Η Συνδρομή Έληξε')
    
    def test_expired_company_can_access_login(self):
        """Test that login page is accessible when expired (allowlist)."""
        # Don't login - test anonymous access
        response = self.client.get(reverse('accounts:login'))
        
        self.assertEqual(response.status_code, 200)
    
    def test_expired_company_can_access_password_reset(self):
        """Test that password reset routes are accessible when expired."""
        self.client.login(username='expired_user', password='TestPass123!')
        
        # Test password reset page
        response = self.client.get(reverse('accounts:password_reset'))
        self.assertEqual(response.status_code, 200)
    
    def test_expired_page_shows_company_info(self):
        """Test that expired page shows correct company information."""
        self.client.login(username='expired_user', password='TestPass123!')
        response = self.client.get(reverse('billing:expired'))
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.expired_company.name)
        self.assertContains(response, self.expired_company.tax_id)
    
    def test_expired_page_shows_admin_notice_for_admin(self):
        """Test that expired page shows admin notice for ADMIN users."""
        self.client.login(username='expired_admin', password='TestPass123!')
        response = self.client.get(reverse('billing:expired'))
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Μόνο ο διαχειριστής')
    
    def test_expired_page_no_admin_notice_for_non_admin(self):
        """Test that expired page does not show admin notice for non-admin."""
        self.client.login(username='expired_user', password='TestPass123!')
        response = self.client.get(reverse('billing:expired'))
        
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, 'Μόνο ο διαχειριστής')
