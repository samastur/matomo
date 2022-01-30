import collections
import logging

import matomo


logger = logging.getLogger(__name__)


class Request(collections.UserDict):
    def __init__(self, request):
        data = request.META.copy()
        data["HTTPS"] = request.scheme == "https"
        data["REQUEST_URI"] = request.path
        data["PATH_INFO"] = request.path_info
        # Doesn't exist in Django and will be set to path info
        data["SCRIPT_NAME"] = ""

        self.cookie = request.COOKIES.copy()

        super().__init__(data)


class Matomo(matomo.Matomo):
    """
    Subclass of matomo.Matomo integrating support for Django

    This class will correctly read configuration values from provided Django's
    request instance including cookies.
    """

    def __init__(self, request):
        req = Request(request)
        site_id, tracking_url = self.__get_matomo_params()
        if site_id and tracking_url:
            super().__init__(req, site_id, tracking_url)
        else:
            logger.warning("MATOMO_SITE_ID or MATOMO_TRACKING_API_URL not set.")
            print("MATOMO_SITE_ID or MATOMO_TRACKING_API_URL not set.")

    def __get_matomo_params(self):
        # Somewhat indirect way of fetching params because of pdoc
        from django.conf import settings

        MATOMO_SITE_ID = getattr(settings, "MATOMO_SITE_ID", 0)
        MATOMO_TRACKING_API_URL = getattr(settings, "MATOMO_TRACKING_API_URL", "")
        return MATOMO_SITE_ID, MATOMO_TRACKING_API_URL

    def set_response(self, response):
        self.response = response
        self.set_first_party_cookies()

    def delete_cookies(self):
        """
        Deletes all first party cookies from the client
        """
        if self.response:
            cookies = ["id", "ses", "cvar", "ref"]
            for cookie in cookies:
                self.response.delete_cookie(
                    cookie,
                    path=self.configCookiePath,
                    domain=self.configCookieDomain,
                    samesite=self.configCookieSameSite,
                )
        else:
            logger.warning("No response instance set to delete cookies on.")

    def set_cookie_response(
        self,
        cookie_name,
        cookie_value,
        max_age=None,
        path="/",
        domain=None,
        secure=False,
        httponly=False,
        samesite=None,
    ):
        if self.response:
            self.response.set_cookie(
                cookie_name,
                cookie_value,
                max_age=max_age,
                path=path,
                domain=domain,
                secure=secure,
                httponly=httponly,
                samesite=samesite,
            )
        else:
            logger.warning("No response instance set to set cookies on.")


class MatomoMixin:
    """
    Matomo Django mixin

    It will build a Matomo tracker based on values read from incoming request
    and store it on self.matomo.

    WARNING: All calls to Matomo servers are synchronous and can thus noticeably
        impact the response time of views that make them.
    """

    matomo = None

    def dispatch(self, request, *args, **kwargs):
        self.matomo = Matomo(request)
        response = super().dispatch(request, *args, **kwargs)
        self.matomo.set_response(response)
        return response
