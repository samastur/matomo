.. _usage:

Usage
=====

First, make sure that Matomo is :ref:`installed <install>`.


Basic usage
-----------

Probably best is to start with an example::

    import matomo
    import matomo.request as request

    from config import (
        MATOMO_SITE_ID, MATOMO_TRACKING_API_URL, HOST, REMOTE_ADDR
    )


    request_data = {
        "HTTP_REFERER": "http://localhost:7000/matomo_test",
        "REMOTE_ADDR": REMOTE_ADDR,
        "HTTP_HOST": HOST,
        "REQUEST_URI": "/matomo_test_fake",
        "QUERY_STRING": "test=1",
    }


    request = request.Request(request_data)
    tracker = matomo.Matomo(request, MATOMO_SITE_ID, MATOMO_TRACKING_API_URL)
    tracker.do_track_page_view("Fake Matomo Test Url")

In the above example request's data is wrapped into a new request object matching
Matomo's request format. Then a new Matomo tracker is initialized with the
request with 3 parameters: a request object containing information about the
request we want to track and Matomo's site ID and tracking API address you got
from Matomo.

Request can be any dict-like object containing information about request with
a cookie parameter containing cookie data (which is another dict-like object).

Request data can be one of the following HTTP information:

- HTTPS
- HTTP_ACCEPT_LANGUAGE
- HTTP_HOST
- HTTP_REFERER
- HTTP_USER_AGENT
- QUERY_STRING
- REMOTE_ADDR

- PATH_INFO
- REQUEST_URI
- SCRIPT_NAME

- HTTP_SEC_CH_UA_MODEL
- HTTP_SEC_CH_UA_PLATFORM
- HTTP_SEC_CH_UA_PLATFORM_VERSION
- HTTP_SEC_CH_UA_FULL_VERSION_LIST
- HTTP_SEC_CH_UA_FULL_VERSION

PATH_INFO, REQUEST_URI and SCRIPT_NAME are used to determine the request's
path in order of precedence (SCRIPT_NAME is used only if both PATH_INFO
and REQUEST_URI are missing/empty).

You can check :ref:`api` for more information about Matomo API or
`original PHP documentation <https://developer.matomo.org/api-reference/PHP-Matomo-Tracker>`_.


Django
------

If you are using Django, then you can use the Django helper classes
from :ref:`the Django module <api>`:

- ``Matomo`` -- a class which will correctly read configuration values from provided Django’s request instance including cookies.
- ``MatomoMixin`` -- a Django view mixin that will build a Matomo tracker based on values read from incoming request and store it on self.matomo.

Both Matomo and MatomoMixin read Matomo's site ID and API url from Django's
settings (``MATOMO_SITE_ID`` and ``MATOMO_TRACKING_API_URL`` respectively).

**WARNING: All calls to Matomo servers are currently synchronous and can thus
noticeably impact the response time of views that make them.**

Example Django view::

    import json
    import random
    from django.views.generic.base import TemplateView
    from matomo.django import MatomoMixin


    class HomePageView(MatomoMixin, TemplateView):

        template_name = "home.html"

        def get_context_data(self, **kwargs):
            context = super().get_context_data(**kwargs)

            current_value = self.matomo.get_attribution_info()
            context["current"] = current_value

            rand_int = random.randint(10000, 99999)
            future_value = ["", "", rand_int, ""]

            json_info = json.dumps(future_value)
            self.matomo.set_attribution_info(json_info)

            context["future"] = future_value

            self.matomo.do_track_page_view("Matomo Cookie Test Page")

