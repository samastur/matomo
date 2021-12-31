import json
from urllib.parse import urlencode, parse_qs
import requests

from .tracker import MatomoTracker


"""
Request structure:
    request        -- meta data about request accessible as a dict
    request.cookie -- cookie data

request data:
    HTTPS
    HTTP_ACCEPT_LANGUAGE
    HTTP_HOST
    HTTP_REFERER
    HTTP_USER_AGENT
    QUERY_STRING
    REMOTE_ADDR

    PATH_INFO
    REQUEST_URI
    SCRIPT_NAME

    Last 3 are used to determine the request's path if order of precedence
    (SCRIPT_NAME is used only if both PATH_INFO and REQUEST_URI are missing/empty)

"""


class Matomo(MatomoTracker):
    def send_request(self, url, method="GET", data=None, force=False):
        # parameter data, when present, is a JSON string
        if self.doBulkRequests and not force:
            self.storedTrackingActions.append("{}{}{}".format(
                url,
                ("&ua=" + urlencode(self.user_agent) if self.user_agent else ""),
                (
                    "&lang=" + urlencode(self.accept_language)
                    if self.accept_language
                    else ""
                ),
            ))
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
            # Send tokenAuth only over POST
            if self.token_auth:
                data["token_auth"] = self.token_auth
                
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


def matomo_get_url_track_page_view(request, id_site, document_title=""):
    """
    Helper function to quickly generate the URL to track a page view.

    * @param id_site
    * @param str document_title
    * @return str
    """
    tracker = Matomo(request, id_site)
    return tracker.get_url_track_page_view(document_title)


def matomo_get_url_track_goal(request, id_site, id_goal, revenue=0.0):
    """
    Helper function to quickly generate the URL to track a goal.

    * @param id_site
    * @param id_goal
    * @param float revenue
    * @return str
    """
    tracker = Matomo(request, id_site)
    return tracker.get_url_track_goal(id_goal, revenue)
