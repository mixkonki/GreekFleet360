"""
Tests for Settings Hub 403 enforcement.

Verifies that users without a company association receive HTTP 403
on settings endpoints, with no silent fallback to Company.objects.first().
"""
from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse


class SettingsHubNoCompanyTest(TestCase):
    """
    A user with NO UserProfile (i.e., no company association) must receive
    HTTP 403 on both GET /settings/ and POST /settings/company/.
    """

    def setUp(self):
        # User with no UserProfile at all — simulates missing company association
        self.user_no_profile = User.objects.create_user(
            username='orphan_user',
            password='testpass123',
        )
        self.client = Client()

    def test_settings_hub_returns_403_for_user_without_profile(self):
        """
        GET /settings/ → 403 when user has no UserProfile.
        """
        self.client.login(username='orphan_user', password='testpass123')
        response = self.client.get(reverse('web:settings_hub'))
        self.assertEqual(response.status_code, 403)

    def test_company_edit_returns_403_for_user_without_profile(self):
        """
        POST /settings/company/ → 403 when user has no UserProfile.
        """
        self.client.login(username='orphan_user', password='testpass123')
        response = self.client.post(reverse('web:company_edit'), {
            'name': 'Hacked Company',
            'tax_id': '999999999',
        })
        self.assertEqual(response.status_code, 403)

    def test_403_response_contains_greek_error_message(self):
        """
        The 403 response body must contain the Greek error message.
        """
        self.client.login(username='orphan_user', password='testpass123')
        response = self.client.get(reverse('web:settings_hub'))
        self.assertEqual(response.status_code, 403)
        self.assertIn(
            'Ο λογαριασμός σας δεν έχει συσχετισμένη εταιρεία',
            response.content.decode('utf-8')
        )

    def tearDown(self):
        self.client.logout()
