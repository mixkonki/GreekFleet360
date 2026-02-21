"""
Tests for CompanyForm tax_id (ΑΦΜ) validation.

Verifies that:
- Valid 9-digit tax_id passes
- Non-digit characters fail
- Wrong length fails
- POST /settings/company/ with invalid tax_id returns form error (not saved)
"""
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from core.models import Company
from accounts.models import UserProfile
from web.forms import CompanyForm


class CompanyFormTaxIdValidationTest(TestCase):
    """Unit tests for CompanyForm.clean_tax_id()"""

    def _make_form(self, tax_id):
        return CompanyForm(data={
            'name': 'Test Company',
            'transport_type': 'FREIGHT',
            'tax_id': tax_id,
            'address': '',
            'phone': '',
            'email': '',
        })

    def test_valid_9_digit_tax_id_passes(self):
        form = self._make_form('123456789')
        self.assertTrue(form.is_valid(), form.errors)

    def test_tax_id_with_letters_fails(self):
        form = self._make_form('123ABC789')
        self.assertFalse(form.is_valid())
        self.assertIn('tax_id', form.errors)
        self.assertIn('9 ψηφία', form.errors['tax_id'][0])

    def test_tax_id_too_short_fails(self):
        form = self._make_form('12345')
        self.assertFalse(form.is_valid())
        self.assertIn('tax_id', form.errors)

    def test_tax_id_too_long_fails(self):
        form = self._make_form('1234567890')
        self.assertFalse(form.is_valid())
        self.assertIn('tax_id', form.errors)

    def test_tax_id_with_spaces_trimmed_and_valid(self):
        """Leading/trailing whitespace is stripped before validation."""
        form = self._make_form('  123456789  ')
        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(form.cleaned_data['tax_id'], '123456789')


class CompanyEditViewTaxIdValidationTest(TestCase):
    """Integration test: POST /settings/company/ with invalid tax_id."""

    def setUp(self):
        self.company = Company.objects.create(
            name='My Company',
            tax_id='111111111',
            transport_type='FREIGHT',
        )
        self.user = User.objects.create_user(
            username='settings_user',
            password='testpass123',
        )
        UserProfile.objects.create(
            user=self.user,
            company=self.company,
            role='ADMIN',
        )
        self.client = Client()
        self.client.login(username='settings_user', password='testpass123')

    def test_invalid_tax_id_does_not_save(self):
        """POST with non-digit tax_id → company not updated."""
        self.client.post(reverse('web:company_edit'), {
            'name': 'My Company',
            'transport_type': 'FREIGHT',
            'tax_id': 'INVALID!!',
            'address': '',
            'phone': '',
            'email': '',
        })
        self.company.refresh_from_db()
        self.assertEqual(self.company.tax_id, '111111111')

    def test_valid_tax_id_saves(self):
        """POST with valid 9-digit tax_id → company updated (same value)."""
        self.client.post(reverse('web:company_edit'), {
            'name': 'My Company Updated',
            'transport_type': 'FREIGHT',
            'tax_id': '111111111',  # same as existing
            'address': '',
            'phone': '',
            'email': '',
        })
        self.company.refresh_from_db()
        self.assertEqual(self.company.name, 'My Company Updated')
        self.assertEqual(self.company.tax_id, '111111111')

    def test_cannot_change_tax_id_once_set(self):
        """POST with different tax_id → company.tax_id unchanged, form error."""
        self.client.post(reverse('web:company_edit'), {
            'name': 'My Company',
            'transport_type': 'FREIGHT',
            'tax_id': '987654321',  # different from existing '111111111'
            'address': '',
            'phone': '',
            'email': '',
        })
        self.company.refresh_from_db()
        self.assertEqual(self.company.tax_id, '111111111')

    def test_resubmitting_same_tax_id_with_spaces_passes(self):
        """POST with same tax_id but with whitespace → allowed after trim."""
        self.client.post(reverse('web:company_edit'), {
            'name': 'My Company',
            'transport_type': 'FREIGHT',
            'tax_id': '  111111111  ',  # same value with spaces
            'address': '',
            'phone': '',
            'email': '',
        })
        self.company.refresh_from_db()
        self.assertEqual(self.company.tax_id, '111111111')

    def tearDown(self):
        self.client.logout()


class CompanyFormImmutabilityUnitTest(TestCase):
    """Unit tests for tax_id immutability in CompanyForm."""

    def setUp(self):
        self.company = Company.objects.create(
            name='Existing Co',
            tax_id='123456789',
            transport_type='FREIGHT',
        )

    def _make_form(self, tax_id):
        return CompanyForm(
            data={
                'name': 'Existing Co',
                'transport_type': 'FREIGHT',
                'tax_id': tax_id,
                'address': '',
                'phone': '',
                'email': '',
            },
            instance=self.company,
        )

    def test_same_tax_id_passes(self):
        form = self._make_form('123456789')
        self.assertTrue(form.is_valid(), form.errors)

    def test_same_tax_id_with_spaces_passes(self):
        form = self._make_form(' 123456789 ')
        self.assertTrue(form.is_valid(), form.errors)

    def test_different_tax_id_fails_with_immutability_message(self):
        form = self._make_form('987654321')
        self.assertFalse(form.is_valid())
        self.assertIn('tax_id', form.errors)
        self.assertIn('δεν μπορεί να αλλάξει', form.errors['tax_id'][0])
