import json
from urllib.parse import urlencode, parse_qs
import requests

from .tracker import MatomoTracker, urlencode_plus


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

    HTTP_SEC_CH_UA_MODEL
    HTTP_SEC_CH_UA_PLATFORM
    HTTP_SEC_CH_UA_PLATFORM_VERSION
    HTTP_SEC_CH_UA_FULL_VERSION_LIST
    HTTP_SEC_CH_UA_FULL_VERSION

    PATH_INFO
    REQUEST_URI
    SCRIPT_NAME

    Last 3 are used to determine the request's path in order of precedence
    (SCRIPT_NAME is used only if both PATH_INFO and REQUEST_URI are missing/empty)

"""


class Matomo(MatomoTracker):
    PATH_TO_CERTIFICATES_FILE = None  # Same purpose and limitations as CURLOPT_CAINFO

    def send_request(self, url, method="GET", data=None, force=False):
        # parameter data, when present, is a JSON string
        if self.doBulkRequests and not force:
            # Store request and send it with other's with do_bulk_track
            self.storedTrackingActions.append(
                "{}{}{}".format(
                    url,
                    ("&ua=" + urlencode(self.user_agent) if self.user_agent else ""),
                    (
                        "&lang=" + urlencode(self.accept_language)
                        if self.accept_language
                        else ""
                    ),
                )
            )
            self.clear_custom_variables()
            self.clear_custom_dimensions()
            self.clear_custom_tracking_parameters()
            self.user_agent = ""
            self.clientHints = {}
            self.accept_language = ""

            return True

        force_post_url_encoded = False
        if not self.doBulkRequests:
            if self.request_method and self.request_method.upper() == "POST":
                url, data = url.split("?")
                force_post_url_encoded = True
                method = "POST"

            if self.token_auth:
                append_token_str = f"&token_auth={urlencode_plus(self.token_auth)}"
                if not self.request_method or method == "POST":
                    # Only post token_auth but use GET URL parameters for everything else
                    force_post_url_encoded = True
                    if not data:
                        data = ""
                    data += append_token_str
                    data = data.lstrip(
                        "&"
                    )  # when no request method set we don't want it to start with '&'
                # In original 'elseif (!empty($this->token_auth))' which has to be true
                else:
                    # Use GET for all URL parameters
                    url += append_token_str

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

        if method == "POST" or data or force_post_url_encoded:
            # Send tokenAuth only over POST
            if self.token_auth:
                data["token_auth"] = self.token_auth

            response = requests.post(
                url,
                data=data,
                headers=headers,
                proxies=proxies,
                timeout=self.requestTimeout,
                cookies=cookies,
                cert=self.PATH_TO_CERTIFICATES_FILE,
            )
        elif method == "GET":
            response = requests.get(
                url,
                headers=headers,
                proxies=proxies,
                timeout=self.requestTimeout,
                cookies=cookies,
                cert=self.PATH_TO_CERTIFICATES_FILE,
            )
        else:
            raise Exception(f"Unsupported HTTP method: {method}")
        return response


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
