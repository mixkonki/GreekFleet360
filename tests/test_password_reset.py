"""
Tests for Password Reset Flow
Ensures production-ready password reset with security best practices.
"""
from django.test import TestCase, override_settings
from django.contrib.auth.models import User
from django.core import mail
from django.urls import reverse
from accounts.models import UserProfile
from core.models import Company


@override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
class PasswordResetFlowTests(TestCase):
    """Test password reset functionality with security requirements."""
    
    def setUp(self):
        """Set up test data."""
        # Create company
        self.company = Company.objects.create(
            name="Test Transport Co",
            tax_id="123456789",
            email="company@test.com"
        )
        
        # Create user with email
        self.user = User.objects.create_user(
            username='testuser',
            email='testuser@example.com',
            password='OldPassword123!'
        )
        
        # Create user profile
        UserProfile.objects.create(
            user=self.user,
            company=self.company,
            role='ADMIN'
        )
        
        # Clear mail outbox
        mail.outbox = []
    
    def test_password_reset_page_loads(self):
        """Test that password reset page returns 200."""
        url = reverse('accounts:password_reset')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Επαναφορά Κωδικού')
        self.assertContains(response, 'Email')
    
    def test_password_reset_with_nonexistent_email_no_enumeration(self):
        """Test that non-existing email still shows success (no enumeration)."""
        url = reverse('accounts:password_reset')
        response = self.client.post(url, {
            'email': 'nonexistent@example.com'
        })
        
        # Should redirect to done page regardless
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('accounts:password_reset_done'))
        
        # No email should be sent
        self.assertEqual(len(mail.outbox), 0)
    
    def test_password_reset_with_existing_email_sends_email(self):
        """Test that existing email sends reset email with correct subject."""
        url = reverse('accounts:password_reset')
        response = self.client.post(url, {
            'email': 'testuser@example.com'
        })
        
        # Should redirect to done page
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('accounts:password_reset_done'))
        
        # Exactly 1 email should be sent
        self.assertEqual(len(mail.outbox), 1)
        
        # Check email subject matches requirement
        email = mail.outbox[0]
        self.assertIn('Επαναφορά κωδικού', email.subject)
        self.assertIn('GreekFleet 360', email.subject)
        
        # Check email recipient
        self.assertEqual(email.to, ['testuser@example.com'])
        
        # Check email body contains reset link
        self.assertIn('password-reset-confirm', email.body)
    
    def test_password_reset_done_page_shows_generic_message(self):
        """Test that done page shows generic message (security)."""
        url = reverse('accounts:password_reset_done')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Email Εστάλη')
        self.assertContains(response, 'Εάν υπάρχει λογαριασμός')
    
    def test_password_reset_confirm_with_valid_token(self):
        """Test password reset confirm page with valid token."""
        # First, request password reset
        self.client.post(reverse('accounts:password_reset'), {
            'email': 'testuser@example.com'
        })
        
        # Extract token and uid from email
        email_body = mail.outbox[0].body
        # Extract URL from email (simplified - in real scenario parse properly)
        import re
        match = re.search(r'/accounts/password-reset-confirm/([^/]+)/([^/]+)/', email_body)
        self.assertIsNotNone(match, "Reset link not found in email")
        
        uidb64 = match.group(1)
        token = match.group(2)
        
        # Visit confirm page (Django redirects to set-password on first visit)
        url = reverse('accounts:password_reset_confirm', kwargs={
            'uidb64': uidb64,
            'token': token
        })
        response = self.client.get(url, follow=True)
        
        # Should show password reset form after redirect
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Νέος Κωδικός')
    
    def test_password_reset_confirm_with_invalid_token(self):
        """Test password reset confirm page with invalid token."""
        url = reverse('accounts:password_reset_confirm', kwargs={
            'uidb64': 'invalid',
            'token': 'invalid-token'
        })
        response = self.client.get(url)
        
        # Should show invalid link message
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Μη Έγκυρος Σύνδεσμος')
    
    def test_password_reset_complete_flow(self):
        """Test complete password reset flow end-to-end."""
        # Step 1: Request password reset
        self.client.post(reverse('accounts:password_reset'), {
            'email': 'testuser@example.com'
        })
        
        # Step 2: Extract token from email
        email_body = mail.outbox[0].body
        import re
        match = re.search(r'/accounts/password-reset-confirm/([^/]+)/([^/]+)/', email_body)
        uidb64 = match.group(1)
        token = match.group(2)
        
        # Step 3: Visit confirm page (this sets session)
        confirm_url = reverse('accounts:password_reset_confirm', kwargs={
            'uidb64': uidb64,
            'token': token
        })
        self.client.get(confirm_url)
        
        # Step 4: Submit new password (use set-password URL)
        set_password_url = reverse('accounts:password_reset_confirm', kwargs={
            'uidb64': uidb64,
            'token': 'set-password'
        })
        response = self.client.post(set_password_url, {
            'new_password1': 'NewSecurePassword123!',
            'new_password2': 'NewSecurePassword123!'
        })
        
        # Should redirect to complete page
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('accounts:password_reset_complete'))
        
        # Step 5: Verify password was changed
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password('NewSecurePassword123!'))
        self.assertFalse(self.user.check_password('OldPassword123!'))
    
    def test_login_page_shows_password_reset_link(self):
        """Test that login page contains password reset link."""
        url = reverse('accounts:login')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Ξεχάσατε τον κωδικό;')
        self.assertContains(response, reverse('accounts:password_reset'))
    
    def test_password_reset_email_contains_required_elements(self):
        """Test that reset email contains all required elements."""
        self.client.post(reverse('accounts:password_reset'), {
            'email': 'testuser@example.com'
        })
        
        email = mail.outbox[0]
        
        # Check subject
        self.assertIn('Επαναφορά κωδικού', email.subject)
        self.assertIn('GreekFleet 360', email.subject)
        
        # Check body contains required elements
        self.assertIn('GreekFleet 360', email.body)
        self.assertIn('password-reset-confirm', email.body)
        self.assertIn('24 ώρες', email.body)  # Expiry notice
    
    def test_password_reset_complete_page(self):
        """Test password reset complete page."""
        url = reverse('accounts:password_reset_complete')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Επιτυχής Επαναφορά')
        self.assertContains(response, 'Σύνδεση')
