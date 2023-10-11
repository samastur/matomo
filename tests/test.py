import http.cookiejar
import pathlib
import time

import requests

import matomo
import matomo.request as request

from config import (
    MATOMO_SITE_ID, MATOMO_TRACKING_API_URL, HOST, REMOTE_ADDR
)


class TestCookieJar(http.cookiejar.MozillaCookieJar, requests.cookies.RequestsCookieJar):
    pass


class TestRequest(request.Request):
    cookie = TestCookieJar()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        cookie_file = kwargs.get("cookie_file", "cookies.txt")
        self.cookie = TestCookieJar(cookie_file)

        p = pathlib.Path(cookie_file)
        if p.exists() and p.is_file():
            self.cookie.load(cookie_file)


request_data = {
    "HTTP_REFERER": "http://localhost:7000/matomo_test",
    "REMOTE_ADDR": REMOTE_ADDR,
    "HTTP_HOST": HOST,
    "REQUEST_URI": "/matomo_test_fake",
    "QUERY_STRING": "test=1",
}
request_data2 = {
    "HTTP_REFERER": "http://localhost:7000/matomo_test2",
    "REMOTE_ADDR": REMOTE_ADDR,
    "HTTP_HOST": HOST,
    "REQUEST_URI": "/matomo_test_fake2",
    "QUERY_STRING": "test=1",
}

for i, data in enumerate([request_data, request_data2]):
    request = TestRequest(data)
    tracker = matomo.Matomo(request, MATOMO_SITE_ID, MATOMO_TRACKING_API_URL)
    tracker.do_track_page_view("Fake Matomo Test Url {}".format(i+1))
    tracker.request.cookie.save(ignore_discard=True)
    time.sleep(1)

