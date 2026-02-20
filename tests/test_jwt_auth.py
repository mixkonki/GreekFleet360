"""
Tests for JWT Authentication Endpoints
POST /api/v1/auth/token/    — obtain access + refresh tokens
POST /api/v1/auth/refresh/  — refresh access token
POST /api/v1/auth/logout/   — blacklist refresh token

Covers:
- Token obtain: valid credentials → 200 + tokens
- Token obtain: invalid credentials → 401
- Token obtain: missing fields → 400
- Token refresh: valid refresh → 200 + new access token
- Token refresh: invalid/expired refresh → 401
- Logout: valid refresh → 200 + token blacklisted
- Logout: missing refresh field → 400
- Logout: already blacklisted token → 400
- Logout: unauthenticated → 401
- Protected endpoint: valid access token → 200
- Protected endpoint: no token → 403
- Protected endpoint: invalid token → 401
- Protected endpoint: blacklisted refresh (access still valid) → 200
"""
from django.test import TestCase
from django.contrib.auth.models import User
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

TOKEN_URL = '/api/v1/auth/token/'
REFRESH_URL = '/api/v1/auth/refresh/'
LOGOUT_URL = '/api/v1/auth/logout/'

# A protected endpoint we can use to verify access token validity
PROTECTED_URL = '/api/v1/kpis/company/summary/'


class JWTTokenObtainTest(TestCase):
    """Tests for POST /api/v1/auth/token/"""

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_superuser(
            username='jwt_test_su', email='jwt@test.com', password='securepass123'
        )

    def test_valid_credentials_return_200_with_tokens(self):
        r = self.client.post(TOKEN_URL, {
            'username': 'jwt_test_su',
            'password': 'securepass123',
        }, format='json')
        self.assertEqual(r.status_code, 200)
        data = r.json()
        self.assertIn('access', data)
        self.assertIn('refresh', data)
        self.assertIsInstance(data['access'], str)
        self.assertIsInstance(data['refresh'], str)
        self.assertGreater(len(data['access']), 20)
        self.assertGreater(len(data['refresh']), 20)

    def test_invalid_password_returns_401(self):
        r = self.client.post(TOKEN_URL, {
            'username': 'jwt_test_su',
            'password': 'wrongpassword',
        }, format='json')
        self.assertEqual(r.status_code, 401)

    def test_nonexistent_user_returns_401(self):
        r = self.client.post(TOKEN_URL, {
            'username': 'nobody',
            'password': 'whatever',
        }, format='json')
        self.assertEqual(r.status_code, 401)

    def test_missing_password_returns_400(self):
        r = self.client.post(TOKEN_URL, {
            'username': 'jwt_test_su',
        }, format='json')
        self.assertEqual(r.status_code, 400)

    def test_missing_username_returns_400(self):
        r = self.client.post(TOKEN_URL, {
            'password': 'securepass123',
        }, format='json')
        self.assertEqual(r.status_code, 400)

    def test_empty_body_returns_400(self):
        r = self.client.post(TOKEN_URL, {}, format='json')
        self.assertEqual(r.status_code, 400)


class JWTTokenRefreshTest(TestCase):
    """Tests for POST /api/v1/auth/refresh/"""

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_superuser(
            username='jwt_refresh_su', email='refresh@test.com', password='securepass123'
        )
        # Obtain a real refresh token
        r = self.client.post(TOKEN_URL, {
            'username': 'jwt_refresh_su',
            'password': 'securepass123',
        }, format='json')
        self.refresh_token = r.json()['refresh']
        self.access_token = r.json()['access']

    def test_valid_refresh_returns_200_with_new_access(self):
        r = self.client.post(REFRESH_URL, {
            'refresh': self.refresh_token,
        }, format='json')
        self.assertEqual(r.status_code, 200)
        data = r.json()
        self.assertIn('access', data)
        self.assertIsInstance(data['access'], str)
        self.assertGreater(len(data['access']), 20)

    def test_invalid_refresh_token_returns_401(self):
        r = self.client.post(REFRESH_URL, {
            'refresh': 'this.is.not.a.valid.token',
        }, format='json')
        self.assertEqual(r.status_code, 401)

    def test_missing_refresh_field_returns_400(self):
        r = self.client.post(REFRESH_URL, {}, format='json')
        self.assertEqual(r.status_code, 400)


class JWTLogoutTest(TestCase):
    """Tests for POST /api/v1/auth/logout/"""

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_superuser(
            username='jwt_logout_su', email='logout@test.com', password='securepass123'
        )
        # Obtain tokens
        r = self.client.post(TOKEN_URL, {
            'username': 'jwt_logout_su',
            'password': 'securepass123',
        }, format='json')
        self.refresh_token = r.json()['refresh']
        self.access_token = r.json()['access']

    def _auth_header(self):
        return {'HTTP_AUTHORIZATION': f'Bearer {self.access_token}'}

    def test_logout_with_valid_refresh_returns_200(self):
        r = self.client.post(
            LOGOUT_URL,
            {'refresh': self.refresh_token},
            format='json',
            **self._auth_header(),
        )
        self.assertEqual(r.status_code, 200)
        data = r.json()
        self.assertIn('detail', data)

    def test_logout_blacklists_refresh_token(self):
        """After logout, using the same refresh token should return 401."""
        # Logout
        self.client.post(
            LOGOUT_URL,
            {'refresh': self.refresh_token},
            format='json',
            **self._auth_header(),
        )
        # Try to refresh with the now-blacklisted token
        r = self.client.post(REFRESH_URL, {'refresh': self.refresh_token}, format='json')
        self.assertEqual(r.status_code, 401)

    def test_logout_already_blacklisted_returns_400(self):
        """Blacklisting the same token twice should return 400."""
        auth = self._auth_header()
        # First logout
        self.client.post(LOGOUT_URL, {'refresh': self.refresh_token}, format='json', **auth)
        # Second logout with same token
        r = self.client.post(LOGOUT_URL, {'refresh': self.refresh_token}, format='json', **auth)
        self.assertEqual(r.status_code, 400)

    def test_logout_missing_refresh_returns_400(self):
        r = self.client.post(
            LOGOUT_URL,
            {},
            format='json',
            **self._auth_header(),
        )
        self.assertEqual(r.status_code, 400)
        self.assertIn('error', r.json())

    def test_logout_unauthenticated_returns_401(self):
        """No Authorization header → 401 (IsAuthenticated)."""
        r = self.client.post(LOGOUT_URL, {'refresh': self.refresh_token}, format='json')
        self.assertEqual(r.status_code, 401)

    def test_logout_invalid_refresh_token_returns_400(self):
        r = self.client.post(
            LOGOUT_URL,
            {'refresh': 'not.a.real.token'},
            format='json',
            **self._auth_header(),
        )
        self.assertEqual(r.status_code, 400)


class JWTProtectedEndpointTest(TestCase):
    """
    Tests that protected API endpoints correctly enforce JWT authentication.
    Uses the KPI summary endpoint as the test target.
    """

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_superuser(
            username='jwt_protected_su', email='protected@test.com', password='securepass123'
        )
        # Obtain tokens
        r = self.client.post(TOKEN_URL, {
            'username': 'jwt_protected_su',
            'password': 'securepass123',
        }, format='json')
        self.refresh_token = r.json()['refresh']
        self.access_token = r.json()['access']

    def test_valid_access_token_allows_access(self):
        """Bearer token → 200 (or 400 for missing params, not 401/403)."""
        r = self.client.get(
            PROTECTED_URL,
            HTTP_AUTHORIZATION=f'Bearer {self.access_token}',
        )
        # 200 or 400 (missing company_id) — both mean auth passed
        self.assertIn(r.status_code, [200, 400, 404])
        self.assertNotIn(r.status_code, [401, 403])

    def test_no_token_returns_401_or_403(self):
        """
        No auth header → 401 (JWT auth) or 403 (session auth).
        DRF returns 401 when JWTAuthentication is the first authenticator
        and no credentials are provided at all.
        """
        r = self.client.get(PROTECTED_URL)
        self.assertIn(r.status_code, [401, 403])

    def test_invalid_token_returns_401(self):
        """Malformed/invalid Bearer token → 401."""
        r = self.client.get(
            PROTECTED_URL,
            HTTP_AUTHORIZATION='Bearer this.is.not.valid',
        )
        self.assertEqual(r.status_code, 401)

    def test_access_token_still_valid_after_refresh_token_blacklisted(self):
        """
        Blacklisting the refresh token does NOT invalidate the access token.
        Access tokens are stateless — they remain valid until expiry.
        """
        # Logout (blacklist refresh)
        self.client.post(
            LOGOUT_URL,
            {'refresh': self.refresh_token},
            format='json',
            HTTP_AUTHORIZATION=f'Bearer {self.access_token}',
        )
        # Access token should still work
        r = self.client.get(
            PROTECTED_URL,
            HTTP_AUTHORIZATION=f'Bearer {self.access_token}',
        )
        self.assertNotIn(r.status_code, [401, 403])

    def test_programmatic_token_generation_works(self):
        """
        Verify that programmatically generated tokens (for tests) work correctly.
        This is the pattern used in test_kpi_endpoints.py via force_authenticate.
        """
        refresh = RefreshToken.for_user(self.user)
        access = str(refresh.access_token)
        r = self.client.get(
            PROTECTED_URL,
            HTTP_AUTHORIZATION=f'Bearer {access}',
        )
        self.assertNotIn(r.status_code, [401, 403])
