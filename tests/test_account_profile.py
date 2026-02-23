"""
Tests for Account Profile Management
Self-service profile editing and password change
"""
from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from accounts.models import UserProfile
from core.models import Company


class AccountProfileTests(TestCase):
    """Test account profile management functionality."""
    
    def setUp(self):
        """Set up test data."""
        # Create company
        self.company = Company.objects.create(
            name="Test Transport Co",
            tax_id="123456789",
            email="company@test.com"
        )
        
        # Create user
        self.user = User.objects.create_user(
            username='testuser',
            email='testuser@example.com',
            password='OldPassword123!',
            first_name='John',
            last_name='Doe'
        )
        
        # Create user profile
        UserProfile.objects.create(
            user=self.user,
            company=self.company,
            role='ADMIN'
        )
        
        self.client = Client()
    
    def test_profile_page_requires_login(self):
        """Test that anonymous users are redirected to login."""
        url = reverse('accounts:me')
        response = self.client.get(url)
        
        # Should redirect to login
        self.assertEqual(response.status_code, 302)
        self.assertIn('/accounts/login/', response.url)
    
    def test_logged_in_user_can_access_profile_page(self):
        """Test that logged-in user can GET /accounts/me/ (200)."""
        self.client.login(username='testuser', password='OldPassword123!')
        url = reverse('accounts:me')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Ο Λογαριασμός μου')
        self.assertContains(response, 'testuser')
        self.assertContains(response, 'testuser@example.com')
    
    def test_user_can_update_first_and_last_name(self):
        """Test that logged-in user can POST update first/last name and it persists."""
        self.client.login(username='testuser', password='OldPassword123!')
        url = reverse('accounts:me')
        
        response = self.client.post(url, {
            'first_name': 'Jane',
            'last_name': 'Smith'
        })
        
        # Should redirect back to profile page
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('accounts:me'))
        
        # Verify changes persisted
        self.user.refresh_from_db()
        self.assertEqual(self.user.first_name, 'Jane')
        self.assertEqual(self.user.last_name, 'Smith')
    
    def test_profile_update_shows_success_message(self):
        """Test that profile update shows success message."""
        self.client.login(username='testuser', password='OldPassword123!')
        url = reverse('accounts:me')
        
        response = self.client.post(url, {
            'first_name': 'Updated',
            'last_name': 'Name'
        }, follow=True)
        
        # Check for success message
        messages = list(response.context['messages'])
        self.assertEqual(len(messages), 1)
        self.assertIn('επιτυχώς', str(messages[0]))
    
    def test_password_change_page_requires_login(self):
        """Test that password change page requires login."""
        url = reverse('accounts:password_change')
        response = self.client.get(url)
        
        # Should redirect to login
        self.assertEqual(response.status_code, 302)
        self.assertIn('/accounts/login/', response.url)
    
    def test_password_change_page_loads_for_logged_in_user(self):
        """Test that GET password change page works."""
        self.client.login(username='testuser', password='OldPassword123!')
        url = reverse('accounts:password_change')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Αλλαγή Κωδικού')
    
    def test_password_change_with_valid_passwords(self):
        """Test that POST with valid old/new password changes password."""
        self.client.login(username='testuser', password='OldPassword123!')
        url = reverse('accounts:password_change')
        
        response = self.client.post(url, {
            'old_password': 'OldPassword123!',
            'new_password1': 'NewSecurePassword456!',
            'new_password2': 'NewSecurePassword456!'
        })
        
        # Should redirect to done page
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('accounts:password_change_done'))
        
        # Verify password was changed
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password('NewSecurePassword456!'))
        self.assertFalse(self.user.check_password('OldPassword123!'))
    
    def test_password_change_with_wrong_old_password(self):
        """Test that password change fails with wrong old password."""
        self.client.login(username='testuser', password='OldPassword123!')
        url = reverse('accounts:password_change')
        
        response = self.client.post(url, {
            'old_password': 'WrongPassword',
            'new_password1': 'NewSecurePassword456!',
            'new_password2': 'NewSecurePassword456!'
        })
        
        # Should stay on same page with error
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Αλλαγή Κωδικού')
        
        # Password should not have changed
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password('OldPassword123!'))
    
    def test_password_change_done_page(self):
        """Test password change done page."""
        self.client.login(username='testuser', password='OldPassword123!')
        url = reverse('accounts:password_change_done')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Επιτυχής Αλλαγή')
