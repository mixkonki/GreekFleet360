"""
Tests for ADMIN-only user management enforcement
"""
from django.test import TestCase, Client
from django.contrib.auth.models import User
from accounts.models import UserProfile
from core.models import Company


class UserManagementAdminOnlyTestCase(TestCase):
    """Test ADMIN-only enforcement for user_create and user_delete"""
    
    def setUp(self):
        """Create test companies and users"""
        # Company A
        self.company_a = Company.objects.create(
            name="Company A",
            tax_id="111111111",
            business_type="MIXED",
            is_active=True
        )
        
        # Company B (for cross-tenant tests)
        self.company_b = Company.objects.create(
            name="Company B",
            tax_id="222222222",
            business_type="MIXED",
            is_active=True
        )
        
        # Admin user (Company A)
        self.admin_user = User.objects.create_user(
            username='admin_a',
            password='testpass123',
            email='admin@companya.gr'
        )
        UserProfile.objects.create(
            user=self.admin_user,
            company=self.company_a,
            role='ADMIN'
        )
        
        # Manager user (Company A) - non-admin
        self.manager_user = User.objects.create_user(
            username='manager_a',
            password='testpass123',
            email='manager@companya.gr'
        )
        UserProfile.objects.create(
            user=self.manager_user,
            company=self.company_a,
            role='MANAGER'
        )
        
        # Target user to delete (Company A)
        self.target_user = User.objects.create_user(
            username='target_a',
            password='testpass123',
            email='target@companya.gr'
        )
        UserProfile.objects.create(
            user=self.target_user,
            company=self.company_a,
            role='VIEWER'
        )
        
        # User from Company B (for cross-tenant test)
        self.user_b = User.objects.create_user(
            username='user_b',
            password='testpass123',
            email='user@companyb.gr'
        )
        UserProfile.objects.create(
            user=self.user_b,
            company=self.company_b,
            role='VIEWER'
        )
        
        self.client = Client()
    
    def test_admin_can_get_create_page(self):
        """Admin user should be able to access create user page"""
        self.client.login(username='admin_a', password='testpass123')
        
        response = self.client.get('/settings/users/create/')
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Προσθήκη Χρήστη')
        self.assertContains(response, 'Company A')
    
    def test_non_admin_cannot_get_create_page(self):
        """Non-admin user should get 403 when trying to access create user page"""
        self.client.login(username='manager_a', password='testpass123')
        
        response = self.client.get('/settings/users/create/')
        
        self.assertEqual(response.status_code, 403)
    
    def test_orphan_user_cannot_get_create_page(self):
        """User without profile/company should get 403 when trying to access create user page"""
        # Create orphan user (no UserProfile)
        orphan_user = User.objects.create_user(
            username='orphan',
            password='testpass123',
            email='orphan@example.com'
        )
        self.client.login(username='orphan', password='testpass123')
        
        response = self.client.get('/settings/users/create/')
        
        self.assertEqual(response.status_code, 403)
    
    def test_orphan_user_cannot_create_user(self):
        """User without profile/company should get 403 when trying to create user"""
        # Create orphan user (no UserProfile)
        orphan_user = User.objects.create_user(
            username='orphan',
            password='testpass123',
            email='orphan@example.com'
        )
        self.client.login(username='orphan', password='testpass123')
        
        response = self.client.post('/settings/users/create/', {
            'username': 'newuser',
            'email': 'new@companya.gr',
            'first_name': 'New',
            'last_name': 'User',
            'password': 'newpass123',
            'role': 'VIEWER'
        })
        
        self.assertEqual(response.status_code, 403)
        # Verify user was NOT created
        self.assertFalse(User.objects.filter(username='newuser').exists())
    
    def test_orphan_user_cannot_delete_user(self):
        """User without profile/company should get 403 when trying to delete user"""
        # Create orphan user (no UserProfile)
        orphan_user = User.objects.create_user(
            username='orphan',
            password='testpass123',
            email='orphan@example.com'
        )
        self.client.login(username='orphan', password='testpass123')
        
        response = self.client.delete(f'/settings/users/{self.target_user.id}/delete/')
        
        self.assertEqual(response.status_code, 403)
        # Verify user was NOT deleted
        self.assertTrue(User.objects.filter(id=self.target_user.id).exists())
    
    def test_non_admin_cannot_create_user(self):
        """Non-admin user should get 403 when trying to create user"""
        self.client.login(username='manager_a', password='testpass123')
        
        response = self.client.post('/settings/users/create/', {
            'username': 'newuser',
            'email': 'new@companya.gr',
            'first_name': 'New',
            'last_name': 'User',
            'password': 'newpass123',
            'role': 'VIEWER'
        })
        
        self.assertEqual(response.status_code, 403)
        # Verify user was NOT created
        self.assertFalse(User.objects.filter(username='newuser').exists())
    
    def test_admin_can_create_user(self):
        """Admin user should be able to create user"""
        self.client.login(username='admin_a', password='testpass123')
        
        response = self.client.post('/settings/users/create/', {
            'username': 'newuser',
            'email': 'new@companya.gr',
            'first_name': 'New',
            'last_name': 'User',
            'password': 'newpass123',
            'role': 'VIEWER'
        })
        
        # Should redirect on success
        self.assertEqual(response.status_code, 302)
        # Verify user was created
        self.assertTrue(User.objects.filter(username='newuser').exists())
        new_user = User.objects.get(username='newuser')
        self.assertEqual(new_user.profile.company, self.company_a)
        self.assertEqual(new_user.profile.role, 'VIEWER')
    
    def test_non_admin_cannot_delete_user(self):
        """Non-admin user should get 403 when trying to delete user"""
        self.client.login(username='manager_a', password='testpass123')
        
        response = self.client.delete(f'/settings/users/{self.target_user.id}/delete/')
        
        self.assertEqual(response.status_code, 403)
        # Verify user was NOT deleted
        self.assertTrue(User.objects.filter(id=self.target_user.id).exists())
    
    def test_admin_can_delete_user(self):
        """Admin user should be able to delete user"""
        self.client.login(username='admin_a', password='testpass123')
        
        response = self.client.delete(f'/settings/users/{self.target_user.id}/delete/')
        
        self.assertEqual(response.status_code, 200)
        # Verify user was deleted
        self.assertFalse(User.objects.filter(id=self.target_user.id).exists())
    
    def test_admin_cannot_delete_cross_tenant_user(self):
        """Admin should get 403 when trying to delete user from another company"""
        self.client.login(username='admin_a', password='testpass123')
        
        response = self.client.delete(f'/settings/users/{self.user_b.id}/delete/')
        
        self.assertEqual(response.status_code, 403)
        # Verify user was NOT deleted
        self.assertTrue(User.objects.filter(id=self.user_b.id).exists())
    
    def test_admin_cannot_delete_self(self):
        """Admin should get 400 when trying to delete themselves"""
        self.client.login(username='admin_a', password='testpass123')
        
        response = self.client.delete(f'/settings/users/{self.admin_user.id}/delete/')
        
        self.assertEqual(response.status_code, 400)
        # Verify user was NOT deleted
        self.assertTrue(User.objects.filter(id=self.admin_user.id).exists())
    
    def test_admin_can_deactivate_user(self):
        """Admin should be able to deactivate another user"""
        self.client.login(username='admin_a', password='testpass123')
        
        # Verify user is initially active
        self.assertTrue(self.target_user.is_active)
        
        response = self.client.post(f'/settings/users/{self.target_user.id}/toggle-active/')
        
        self.assertEqual(response.status_code, 302)
        # Verify user was deactivated
        self.target_user.refresh_from_db()
        self.assertFalse(self.target_user.is_active)
    
    def test_admin_can_reactivate_user(self):
        """Admin should be able to reactivate a deactivated user"""
        self.client.login(username='admin_a', password='testpass123')
        
        # Deactivate user first
        self.target_user.is_active = False
        self.target_user.save()
        
        response = self.client.post(f'/settings/users/{self.target_user.id}/toggle-active/')
        
        self.assertEqual(response.status_code, 302)
        # Verify user was reactivated
        self.target_user.refresh_from_db()
        self.assertTrue(self.target_user.is_active)
    
    def test_non_admin_cannot_toggle_active(self):
        """Non-admin user should get 403 when trying to toggle user active status"""
        self.client.login(username='manager_a', password='testpass123')
        
        response = self.client.post(f'/settings/users/{self.target_user.id}/toggle-active/')
        
        self.assertEqual(response.status_code, 403)
        # Verify user status unchanged
        self.target_user.refresh_from_db()
        self.assertTrue(self.target_user.is_active)
    
    def test_orphan_cannot_toggle_active(self):
        """User without profile/company should get 403 when trying to toggle user"""
        orphan_user = User.objects.create_user(
            username='orphan',
            password='testpass123',
            email='orphan@example.com'
        )
        self.client.login(username='orphan', password='testpass123')
        
        response = self.client.post(f'/settings/users/{self.target_user.id}/toggle-active/')
        
        self.assertEqual(response.status_code, 403)
    
    def test_admin_cannot_toggle_cross_tenant_user(self):
        """Admin should get 403 when trying to toggle user from another company"""
        self.client.login(username='admin_a', password='testpass123')
        
        response = self.client.post(f'/settings/users/{self.user_b.id}/toggle-active/')
        
        self.assertEqual(response.status_code, 403)
        # Verify user status unchanged
        self.user_b.refresh_from_db()
        self.assertTrue(self.user_b.is_active)
    
    def test_admin_cannot_toggle_self(self):
        """Admin should get 400 when trying to toggle themselves"""
        self.client.login(username='admin_a', password='testpass123')
        
        response = self.client.post(f'/settings/users/{self.admin_user.id}/toggle-active/')
        
        self.assertEqual(response.status_code, 400)
        # Verify user status unchanged
        self.admin_user.refresh_from_db()
        self.assertTrue(self.admin_user.is_active)
