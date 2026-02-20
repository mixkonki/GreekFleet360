"""
JWT Auth Views
POST /api/v1/auth/logout/ — blacklist refresh token
"""
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError


class LogoutView(APIView):
    """
    POST /api/v1/auth/logout/

    Blacklists the provided refresh token, preventing further use.
    The access token remains valid until it expires (15 min by default).

    Body: { "refresh": "<refresh_token>" }

    Returns:
    - 200: Token blacklisted successfully
    - 400: Invalid or already blacklisted token
    - 401: Not authenticated
    """

    permission_classes = [IsAuthenticated]

    def post(self, request):
        refresh_token = request.data.get("refresh")
        if not refresh_token:
            return Response(
                {"error": "refresh token is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            token = RefreshToken(refresh_token)
            token.blacklist()
        except TokenError as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(
            {"detail": "Successfully logged out. Refresh token has been blacklisted."},
            status=status.HTTP_200_OK,
        )
