from django.utils.deprecation import MiddlewareMixin
from .mixins import set_current_company

class CurrentCompanyMiddleware(MiddlewareMixin):
    def process_request(self, request):
        company = None

        if getattr(request, "user", None) and request.user.is_authenticated:
            # Canonical (preferred)
            profile = getattr(request.user, "profile", None)

            # Compat fallback (until we standardize related_name="profile")
            if profile is None:
                profile = getattr(request.user, "userprofile", None)

            if profile is not None:
                company = getattr(profile, "company", None)

        request.company = company
        set_current_company(company)

    def process_response(self, request, response):
        set_current_company(None)
        return response

    def process_exception(self, request, exception):
        set_current_company(None)
        return None