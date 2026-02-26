from django.test import TestCase, RequestFactory
from django.contrib.auth.models import User

from core.middleware import CurrentCompanyMiddleware
from core.models import Company
from accounts.models import UserProfile


class CurrentCompanyMiddlewareTests(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.middleware = CurrentCompanyMiddleware(get_response=lambda r: None)

        self.company = Company.objects.create(
            name="Company X",
            tax_id="999999999",
            business_type="TRANSPORT",
            is_active=True
        )

        self.user = User.objects.create_user(username="u", password="pass")
        UserProfile.objects.create(user=self.user, company=self.company, role="MANAGER")

        self.orphan = User.objects.create_user(username="orphan2", password="pass")

    def test_sets_request_company_for_authenticated_user(self):
        request = self.factory.get("/api/v1/fuel-entries/")
        request.user = self.user

        self.middleware.process_request(request)
        self.assertEqual(request.company, self.company)

    def test_sets_request_company_none_for_orphan(self):
        request = self.factory.get("/api/v1/fuel-entries/")
        request.user = self.orphan

        self.middleware.process_request(request)
        self.assertIsNone(request.company)

    def test_sets_request_company_none_for_anonymous(self):
        request = self.factory.get("/api/v1/fuel-entries/")

        # Simulate anonymous (Django sets AnonymousUser typically, but None is enough for this check)
        request.user = type("Anon", (), {"is_authenticated": False})()

        self.middleware.process_request(request)
        self.assertIsNone(request.company)