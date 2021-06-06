import json
from urllib.parse import urlencode, parse_qs
import requests

from .tracker import MatomoTracker


"""
Request structure:
    request.server -- data about server
    request.cookie -- cookie data

request server data:
    HTTPS
    HTTP_ACCEPT_LANGUAGE
    HTTP_HOST
    HTTP_REFERER
    HTTP_USER_AGENT
    PATH_INFO
    QUERY_STRING
    REMOTE_ADDR
    REQUEST_URI
    SCRIPT_NAME

"""


class Matomo(MatomoTracker):
    def send_request(self, url, method="GET", data=None, force=False):
        # parameter data, when present, is a JSON string
        if self.doBulkRequests and not force:
            self.storedTrackingActions = "{}{}{}".format(
                url,
                ("&ua=" + urlencode(self.user_agent) if self.user_agent else ""),
                (
                    "&lang=" + urlencode(self.accept_language)
                    if self.accept_language
                    else ""
                ),
            )
            self.clear_custom_variables()
            self.clear_custom_dimensions()
            self.clear_custom_tracking_parameters()
            self.user_agent = ""
            self.accept_language = ""

            return True

        proxies = None
        if self.get_proxy():
            proxy = self.get_proxy()
            scheme = "https" if proxy.lower().startswith("https") else "http"
            proxies = {scheme: proxy}

        post_data = None
        if (
            self.request_method
            and self.request_method == "POST"
            and not self.doBulkRequests
        ):
            url, post_data = url.split("?")
            post_data = parse_qs(post_data) if post_data else {}
            method = "POST"

        data = json.loads(data) if data else post_data

        headers = {
            "user-agent": self.user_agent,
            "accept-language": self.accept_language,
        }

        cookies = self.get_cookies()

        # TODO Missing certificate section

        if method == "GET":
            response = requests.get(
                url,
                headers=headers,
                proxies=proxies,
                timeout=self.requestTimeout,
                cookies=cookies,
            )
        elif method == "POST":
            response = requests.post(
                url,
                data=data,
                headers=headers,
                proxies=proxies,
                timeout=self.requestTimeout,
                cookies=cookies
            )
        else:
            raise Exception(f"Unsupported HTTP method: {method}")
        return response.content
