from datetime import datetime
import hashlib
import json
import random
import re
import time
from urllib.parse import urlencode, quote, parse_qs
import uuid

#
# This module is a mostly automated translation of PHP MatomoTracker
#

is_int = lambda x: isinstance(x, int)
is_list = lambda x: isinstance(x, list)
is_numeric = lambda x: isinstance(x, float)  # Used only once with float parameter
strpos = lambda s, sub: s.find(sub) if s.find(sub) != -1 else False


def strspn(str1, str2, start=0, length=None):
    if not length:
        length = len(str1)
    return len(re.search("^[" + str2 + "]*", str1[start: start + length]).group(0))


"""
 * Matomo - free/libre analytics platform
 *
 * For more information, see README.md
 *
 * @license released under BSD License http://www.opensource.org/licenses/bsd-license.php
 * @link https://matomo.org/docs/tracking-api/
 *
 * @category Matomo
 * @package MatomoTracker
"""

"""
 * MatomoTracker implements the Matomo Tracking Web API.
 *
 * For more information, see: https://github.com/matomo-org/matomo-php-tracker/
 *
 * @package MatomoTracker
 * @api
"""


class MatomoTracker:
    """
     * Matomo base URL, for example http://example.org/matomo/
     * Must be set before using the class by calling
     * MatomoTracker.URL = 'http://yourwebsite.org/matomo/'
     *
     * @var string
    """

    URL = ""

    """
     * API Version
     *
     * @ignore
     * @var int
    """
    VERSION = 1

    """
     * @ignore
    """
    DEBUG_APPEND_URL = ""

    """
     * Visitor ID length
     *
     * @ignore
    """
    LENGTH_VISITOR_ID = 16

    """
     * Charset
     * @see set_page_charset
     * @ignore
    """
    DEFAULT_CHARSET_PARAMETER_VALUES = "utf-8"

    """
     * See matomo.js
    """
    FIRST_PARTY_COOKIES_PREFIX = "_pk_"

    """
     * Ecommerce item page view tracking stores item's metadata in these Custom Variables slots.
    """
    CVAR_INDEX_ECOMMERCE_ITEM_PRICE = 2
    CVAR_INDEX_ECOMMERCE_ITEM_SKU = 3
    CVAR_INDEX_ECOMMERCE_ITEM_NAME = 4
    CVAR_INDEX_ECOMMERCE_ITEM_CATEGORY = 5

    """
     * Defines how many categories can be used max when calling add_ecommerce_item().
     * @var int
    """
    MAX_NUM_ECOMMERCE_ITEM_CATEGORIES = 5

    DEFAULT_COOKIE_PATH = "/"

    """
     * Builds a MatomoTracker object, used to track visits, pages and Goal conversions
     * for a specific website, by using the Matomo Tracking API.
     *
     * @param int id_site Id site to be tracked
     * @param string api_url "http://example.org/matomo/" or "http://matomo.example.org/"
     *                         If set, will overwrite MatomoTracker.URL
    """

    def __init__(self, request, id_site, api_url=""):
        self.request = request
        self.request_method = "GET"
        self.ecommerceItems = []
        self.attributionInfo = []
        self.eventCustomVar = {}
        self.forcedDatetime = ""
        self.forcedNewVisit = False
        self.generationTime = 0
        self.pageCustomVar = {}
        self.customParameters = {}
        self.customData = ""
        self.hasCookies = False
        self.token_auth = ""
        self.user_agent = ""
        self.country = ""
        self.region = ""
        self.city = ""
        self.lat = 0.0
        self.long = 0.0
        self.width = 0
        self.height = 0
        self.plugins = ""
        self.local_hour = ""
        self.local_minute = ""
        self.local_second = ""
        self.idPageview = ""

        self.id_site = str(id_site)
        self.urlReferrer = self.request.get("HTTP_REFERER", "")
        self.pageCharset = self.DEFAULT_CHARSET_PARAMETER_VALUES
        self.pageUrl = self.get_current_url()
        self.ip = self.request.get("REMOTE_ADDR", "")
        self.accept_language = self.request.get("HTTP_ACCEPT_LANGUAGE", "")
        self.user_agent = self.request.get("HTTP_USER_AGENT", "")
        if not api_url:
            self.URL = api_url

        # Life of the visitor cookie (in sec)
        self.configVisitorCookieTimeout = 33955200
        # 13 months (365 + 28 days)
        # Life of the session cookie (in sec)
        self.configSessionCookieTimeout = 1800
        # 30 minutes
        # Life of the session cookie (in sec)
        self.configReferralCookieTimeout = 15768000
        # 6 months

        # Visitor Ids in order
        self.user_id = ""
        self.forcedVisitorId = ""
        self.cookieVisitorId = ""
        self.randomVisitorId = ""

        self.set_new_visitor_id()

        self.configCookiesDisabled = False
        self.configCookiePath = self.DEFAULT_COOKIE_PATH
        self.configCookieDomain = ""
        self.configCookieSameSite = ""
        self.configCookieSecure = False
        self.configCookieHTTPOnly = False

        self.currentTs = time.time()
        self.createTs = self.currentTs
        self.visit_count = 0
        self.currentVisitTs = ""
        self.lastVisitTs = ""
        self.ecommerceLastOrderTimestamp = ""

        # Allow debug while blocking the request
        self.requestTimeout = 600
        self.doBulkRequests = False
        self.storedTrackingActions = {}

        self.sendImageResponse = True

        self.visitorCustomVar = self.get_custom_variables_from_cookie()

        self.outgoingTrackerCookies = {}
        self.incomingTrackerCookies = {}

        self.headersSent = False

        self.proxy = ""
        self.proxy_port = ""

    """
     * By default, Matomo expects utf-8 encoded values, for example
     * for the page URL parameter values, Page Title, etc.
     * It is recommended to only send UTF-8 data to Matomo.
     * If required though, you can also specify another charset using this function.
     *
     * @param string charset
     * @return self
    """

    def set_page_charset(self, charset=""):
        self.pageCharset = charset
        return self

    """
     * Sets the current URL being tracked
     *
     * @param string url Raw URL (not URL encoded)
     * @return self
    """

    def set_url(self, url):
        self.pageUrl = url
        return self

    """
     * Sets the URL referrer used to track Referrers details for new visits.
     *
     * @param string url Raw URL (not URL encoded)
     * @return self
    """

    def set_url_referrer(self, url):
        self.urlReferrer = url
        return self

    """
     * Sets the time that generating the document on the server side took.
     *
     * @param int time_ms Generation time in ms
     * @return self
    """

    def set_generation_time(self, time_ms):
        self.generationTime = time_ms
        return self

    """
     * @deprecated
     * @ignore
    """

    def set_url_referer(self, url):
        self.set_url_referrer(url)
        return self

    """
     * Sets the attribution information to the visit, so that subsequent Goal conversions are
     * properly attributed to the right Referrer URL, timestamp, Campaign Name & Keyword.
     *
     * This must be a JSON encoded string that would typically be fetched from the JS API:
     * matomoTracker.get_attribution_info() and that you have JSON encoded via JSON2.stringify()
     *
     * If you call enable_cookies() then these referral attribution values will be set
     * to the 'ref' first party cookie storing referral information.
     *
     * @param string json_encoded JSON encoded array containing Attribution info
     * @return self
     * @throws Exception
     * @see def get_attribution_info(self): in https://github.com/matomo-org/matomo/blob/master/js/matomo.js
    """

    def set_attribution_info(self, json_encoded):
        decoded = json.loads(json_encoded)
        if not is_list(decoded):
            raise Exception(
                "set_attribution_info() is expecting a JSON encoded string, json_encoded given"
            )
        self.attributionInfo = decoded
        return self

    """
     * Sets Visit Custom Variable.
     * See https://matomo.org/docs/custom-variables/
     *
     * @param int id Custom variable slot ID from 1-5
     * @param string name Custom variable name
     * @param string value Custom variable value
     * @param string scope Custom variable scope. Possible values: visit, page, event
     * @return self
     * @throws Exception
    """

    def set_custom_variable(self, id, name, value, scope="visit"):
        if not is_int(id):
            raise Exception("Parameter id to set_custom_variable should be an integer")
        if scope == "page":
            self.pageCustomVar[id] = [name, value]
        elif scope == "event":
            self.eventCustomVar[id] = [name, value]
        elif scope == "visit":
            self.visitorCustomVar[id] = [name, value]
        else:
            raise Exception("Invalid 'scope' parameter value")
        return self

    """
     * Returns the currently assigned Custom Variable.
     *
     * If scope is 'visit', it will attempt to read the value set in the first party cookie created by Matomo Tracker
     *  (self.request.cookie array).
     *
     * @param int id Custom Variable integer index to fetch from cookie. Should be a value from 1 to 5
     * @param string scope Custom variable scope. Possible values: visit, page, event
     *
     * @throws Exception
     * @return mixed An array with this format: { 0: CustomVariableName, 1: CustomVariableValue } or False
     * @see matomo.js get_custom_variable()
    """

    def get_custom_variable(self, id, scope="visit"):
        if scope == "page":
            return self.pageCustomVar[id] if id in self.pageCustomVar else False
        elif scope == "event":
            return self.eventCustomVar[id] if id in self.eventCustomVar else False
        else:
            if scope != "visit":
                raise Exception("Invalid 'scope' parameter value")
        if not self.visitorCustomVar[id]:
            return self.visitorCustomVar[id]
        cookie_decoded = self.get_custom_variables_from_cookie()
        if not is_int(id):
            raise Exception("Parameter to get_custom_variable should be an integer")
        if (
                not is_list(cookie_decoded)
                or id not in cookie_decoded
                or not is_list(cookie_decoded[id])
                or len(cookie_decoded[id]) != 2
        ):
            return False

        return cookie_decoded[id]

    """
     * Clears any Custom Variable that may be have been set.
     *
     * This can be useful when you have enabled bulk requests, * and you wish to clear Custom Variables of 'visit' scope.
    """

    def clear_custom_variables(self):
        self.visitorCustomVar = {}
        self.pageCustomVar = {}
        self.eventCustomVar = {}

    """
     * Sets a custom tracking parameter. This is useful if you need to send any tracking parameters for a 3rd party
     * plugin that is not shipped with Matomo itself. Please note that custom parameters are cleared after each
     * tracking request.
     *
     * @param string tracking_api_parameter The name of the tracking API parameter, eg 'dimension1'
     * @param string value Tracking parameter value that shall be sent for this tracking parameter.
     * @return self
     * @throws Exception
    """

    def set_custom_tracking_parameter(self, tracking_api_parameter, value):
        self.customParameters[tracking_api_parameter] = value
        return self

    """
     * Clear / reset all previously set custom tracking parameters.
    """

    def clear_custom_tracking_parameters(self):
        self.customParameters = {}

    """
     * Sets the current visitor ID to a random new one.
     * @return self
    """

    def set_new_visitor_id(self):
        self.randomVisitorId = uuid.uuid4().hex[0: 0 + self.LENGTH_VISITOR_ID]
        self.forcedVisitorId = False
        self.cookieVisitorId = False
        return self

    """
     * Sets the current site ID.
     *
     * @param int id_site
     * @return self
    """

    def set_id_site(self, id_site):
        self.id_site = id_site
        return self

    """
     * Sets the Browser language. Used to guess visitor countries when GeoIP is not enabled
     *
     * @param string accept_language For example "fr-fr"
     * @return self
    """

    def set_browser_language(self, accept_language):
        self.accept_language = accept_language
        return self

    """
     * Sets the user agent, used to detect OS and browser.
     * If this def is not called, the User Agent will default to the current user agent.
     *
     * @param string user_agent
     * @return self
    """

    def set_user_agent(self, user_agent):
        self.user_agent = user_agent
        return self

    """
     * Sets the country of the visitor. If not used, Matomo will try to find the country
     * using either the visitor's IP address or language.
     *
     * Allowed only for Admin/Super User, must be used along with set_token_auth().
     * @param string country
     * @return self
    """

    def set_country(self, country):
        self.country = country
        return self

    """
     * Sets the region of the visitor. If not used, Matomo may try to find the region
     * using the visitor's IP address (if configured to do so).
     *
     * Allowed only for Admin/Super User, must be used along with set_token_auth().
     * @param string region
     * @return self
    """

    def set_region(self, region):
        self.region = region
        return self

    """
     * Sets the city of the visitor. If not used, Matomo may try to find the city
     * using the visitor's IP address (if configured to do so).
     *
     * Allowed only for Admin/Super User, must be used along with set_token_auth().
     * @param string city
     * @return self
    """

    def set_city(self, city):
        self.city = city
        return self

    """
     * Sets the latitude of the visitor. If not used, Matomo may try to find the visitor's
     * latitude using the visitor's IP address (if configured to do so).
     *
     * Allowed only for Admin/Super User, must be used along with set_token_auth().
     * @param float lat
     * @return self
    """

    def set_latitude(self, lat):
        self.lat = lat
        return self

    """
     * Sets the longitude of the visitor. If not used, Matomo may try to find the visitor's
     * longitude using the visitor's IP address (if configured to do so).
     *
     * Allowed only for Admin/Super User, must be used along with set_token_auth().
     * @param float long
     * @return self
    """

    def set_longitude(self, long):
        self.long = long
        return self

    """
     * Enables the bulk request feature. When used, each tracking action is stored until the
     * do_bulk_track method is called. This method will send all tracking data at once.
     *
    """

    def enable_bulk_tracking(self):
        self.doBulkRequests = True

    """
     * Enable Cookie Creation - this will cause a first party VisitorId cookie to be set when the VisitorId is set or reset
     *
     * @param string domain (optional) Set first-party cookie domain.
     *  Accepted values: example.com, *.example.com (same as .example.com) or subdomain.example.com
     * @param string path (optional) Set first-party cookie path
     * @param bool secure (optional) Set secure flag for cookies
     * @param bool http_only (optional) Set HTTPOnly flag for cookies
     * @param string same_site (optional) Set SameSite flag for cookies
    """

    def enable_cookies(
            self, domain="", path="/", secure=False, http_only=False, same_site=""
    ):
        self.configCookiesDisabled = False
        self.configCookieDomain = self.domain_fixup(domain)
        self.configCookiePath = path
        self.configCookieSecure = secure
        self.configCookieHTTPOnly = http_only
        self.configCookieSameSite = same_site

    """
     * If image response is disabled Matomo will respond with a HTTP 204 header instead of responding with a gif.
    """

    def disable_send_image_response(self):
        self.sendImageResponse = False

    """
     * Fix-up domain
    """

    def domain_fixup(self, domain):
        if len(domain) > 0:
            dl = len(domain) - 1
            # remove trailing '.'
            if domain[dl] == ".":
                domain = domain[0: 0 + dl]
            # remove leading '*'
            if domain[0: 0 + 2] == "*.":
                domain = domain[1:]

        return domain

    """
     * Get cookie name with prefix and domain hash
     * @param string cookie_name
     * @return string
    """

    def get_cookie_name(self, cookie_name):
        # NOTE: If the cookie name is changed, we must also update the method in matomo.js with the same name.
        hash_string = hashlib.sha1(
            (
                self.configCookieDomain == self.get_current_host()
                if ""
                else self.configCookieDomain
            )
            + self.configCookiePath
        ).hexdigest()[0: 0 + 4]

        return (
                self.FIRST_PARTY_COOKIES_PREFIX
                + cookie_name
                + "."
                + self.id_site
                + "."
                + hash_string
        )

    """
     * Tracks a page view
     *
     * @param string document_title Page title as it will appear in the Actions > Page titles report
     * @return mixed Response string or True if using bulk requests.
    """

    def do_track_page_view(self, document_title):
        self.generate_new_pageview_id()

        url = self.get_url_track_page_view(document_title)

        return self.send_request(url)

    def generate_new_pageview_id(self):
        self.idPageview = uuid.uuid4().hex[0: 0 + 6]

    """
     * Tracks an event
     *
     * @param string category The Event Category (Videos, Music, Games...)
     * @param string action The Event's Action (Play, Pause, Duration, Add Playlist, Downloaded, Clicked...)
     * @param string name (optional) The Event's object Name (a particular Movie name, or Song name, or File name...)
     * @param float value (optional) The Event's value
     * @return mixed Response string or True if using bulk requests.
    """

    def do_track_event(self, category, action, name="", value=0):
        url = self.get_url_track_event(category, action, name, value)

        return self.send_request(url)

    """
     * Tracks a content impression
     *
     * @param string content_name The name of the content. For instance 'Ad Foo Bar'
     * @param string content_piece The actual content. For instance the path to an image, video, audio, any text
     * @param string content_target (optional) The target of the content. For instance the URL of a landing page.
     * @return mixed Response string or True if using bulk requests.
    """

    def do_track_content_impression(
            self, content_name, content_piece="unknown", content_target=""
    ):
        url = self.get_url_track_content_impression(
            content_name, content_piece, content_target
        )

        return self.send_request(url)

    """
     * Tracks a content interaction. Make sure you have tracked a content impression using the same content name and
     * content piece, otherwise it will not count. To do so you should call the method do_track_content_impression()
     *
     * @param string interaction The name of the interaction with the content. For instance a 'click'
     * @param string content_name The name of the content. For instance 'Ad Foo Bar'
     * @param string content_piece The actual content. For instance the path to an image, video, audio, any text
     * @param string content_target (optional) The target the content leading to when an interaction occurs. For instance the URL of a landing page.
     * @return mixed Response string or True if using bulk requests.
    """

    def do_track_content_interaction(
            self, interaction, content_name, content_piece="unknown", content_target=""
    ):
        url = self.get_url_track_content_interaction(
            interaction, content_name, content_piece, content_target
        )

        return self.send_request(url)

    """
     * Tracks an internal Site Search query, and optionally tracks the Search Category, and Search results Count.
     * These are used to populate reports in Actions > Site Search.
     *
     * @param string keyword Searched query on the site
     * @param string category (optional) Search engine category if applicable
     * @param bool|int count_results (optional) results displayed on the search result page. Used to track "zero result" keywords.
     *
     * @return mixed Response or True if using bulk requests.
    """

    def do_track_site_search(self, keyword, category="", count_results=False):
        url = self.get_url_track_site_search(keyword, category, count_results)

        return self.send_request(url)

    """
     * Records a Goal conversion
     *
     * @param int id_goal Id Goal to record a conversion
     * @param float revenue Revenue for this conversion
     * @return mixed Response or True if using bulk request
    """

    def do_track_goal(self, id_goal, revenue=0.0):
        url = self.get_url_track_goal(id_goal, revenue)

        return self.send_request(url)

    """
     * Tracks a download or outlink
     *
     * @param string action_url URL of the download or outlink
     * @param string action_type Type of the action: 'download' or 'link'
     * @return mixed Response or True if using bulk request
    """

    def do_track_action(self, action_url, action_type):
        # Referrer could be udpated to be the current URL temporarily (to mimic JS behavior)
        url = self.get_url_track_action(action_url, action_type)

        return self.send_request(url)

    """
     * Adds an item in the Ecommerce order.
     *
     * This should be called before do_track_ecommerce_order(), or before do_track_ecommerce_cart_update().
     * This def can be called for all individual products in the cart (self, or order):.
     * SKU parameter is mandatory. Other parameters are optional (set to False if value not known).
     * Ecommerce items added via this def are automatically cleared when do_track_ecommerce_order(self): or get_url_track_ecommerce_order(self): is called.
     *
     * @param string sku (required) SKU, Product identifier
     * @param string name (optional) Product name
     * @param string|array category (optional) Product category, or array of product categories (up to 5 categories can be specified for a given product)
     * @param float|int price (optional) Individual product price (supports integer and decimal prices)
     * @param int quantity (optional) Product quantity. If specified, will default to 1 not in the Reports
     * @throws Exception
     * @return self
    """

    def add_ecommerce_item(self, sku, name="", category="", price=0.0, quantity=1):
        if sku:
            raise Exception("You must specify a SKU for the Ecommerce item")

        price = self.force_dot_as_separator_for_decimal_point(price)

        self.ecommerceItems = [sku, name, category, price, quantity]
        return self

    """
     * Tracks a Cart Update (add item, remove item, update item).
     *
     * On every Cart update, you must call add_ecommerce_item() for each item (product) in the cart, * including the items that haven't been updated since the last cart update.
     * Items which were in the previous cart and are sent not in later Cart updates will be deleted from the cart (in the database).
     *
     * @param float grand_total Cart grand_total (typically the sum of all items' prices)
     * @return mixed Response or True if using bulk request
    """

    def do_track_ecommerce_cart_update(self, grand_total):
        url = self.get_url_track_ecommerce_cart_update(grand_total)

        return self.send_request(url)

    """
     * Sends all stored tracking actions at once. Only has an effect if bulk tracking is enabled.
     *
     * To enable bulk tracking, call enable_bulk_tracking().
     *
     * @throws Exception
     * @return string Response
    """

    def do_bulk_track(self):
        if self.storedTrackingActions:
            raise Exception(
                "Error:  you must call the def do_track_page_view or do_track_goal from this class, before calling this method do_bulk_track(self):"
            )

        data = {"requests": self.storedTrackingActions}

        # token_auth is not required by default, except if bulk_requests_require_authentication=1
        if not self.token_auth:
            data["token_auth"] = self.token_auth

        post_data = json.dumps(data)
        response = self.send_request(self.get_base_url(), "POST", post_data, force=True)

        self.storedTrackingActions = {}

        return response

    """
     * Tracks an Ecommerce order.
     *
     * If the Ecommerce order contains items (products), you must call first the add_ecommerce_item() for each item in the order.
     * All revenues (grand_total, sub_total, tax, shipping, discount) will be individually summed and reported in Matomo reports.
     * Only the parameters order_id and grand_total are required.
     *
     * @param string|int order_id (required) Unique Order ID.
     *                This will be used to count this order only once in the event the order page is reloaded several times.
     *                order_id must be unique for each transaction, even on different days, or the transaction will not be recorded by Matomo.
     * @param float grand_total (required) Grand Total revenue of the transaction (including tax, shipping, etc.)
     * @param float sub_total (optional) Sub total amount, typically the sum of items prices for all items in this order (before Tax and Shipping costs are applied)
     * @param float tax (optional) Tax amount for this order
     * @param float shipping (optional) Shipping amount for this order
     * @param float discount (optional) Discounted amount in this order
     * @return mixed Response or True if using bulk request
    """

    def do_track_ecommerce_order(
            self, order_id, grand_total, sub_total=0.0, tax=0.0, shipping=0.0, discount=0.0
    ):
        url = self.get_url_track_ecommerce_order(
            order_id, grand_total, sub_total, tax, shipping, discount
        )

        return self.send_request(url)

    """
     * Sends a ping request.
     *
     * Ping requests do track new actions. If they are sent within the standard visit length (see global.ini.php), * they will extend the existing visit and the current last action for the visit. If after the standard visit length, * ping requests will create a new visit using the last action not in the last known visit.
     *
     * @return mixed Response or True if using bulk request
    """

    def do_ping(self):
        url = self.get_request(self.id_site)
        url += "&ping=1"

        return self.send_request(url)

    """
     * Sets the current page view as an item (product) page view, or an Ecommerce Category page view.
     *
     * This must be called before do_track_page_view() on this product/category page.
     * It will set 3 custom variables of scope "page" with the SKU, Name and Category for this page view.
     * Note: Custom Variables of scope "page" slots 3, 4 and 5 will be used.
     *
     * On a category page, you may set the parameter category only and set the other parameters to False.
     *
     * Tracking Product/Category page views will allow Matomo to report on Product & Categories
     * conversion rates (Conversion rate = Ecommerce orders containing this product or category / Visits to the product or category)
     *
     * @param string sku Product SKU being viewed
     * @param string name Product Name being viewed
     * @param string|array category Category being viewed. On a Product page, this is the product's category.
     *                                You can also specify an array of up to 5 categories for a given page view.
     * @param float price Specify the price at which the item was displayed
     * @return self
    """

    def set_ecommerce_view(self, sku="", name="", category="", price=0.0):
        if not category:
            if is_list(category):
                category = json.dumps(category)
        else:
            category = ""
        self.pageCustomVar[self.CVAR_INDEX_ECOMMERCE_ITEM_CATEGORY] = ["_pkc", category]

        if not price:
            price = str(float(price))
            price = self.force_dot_as_separator_for_decimal_point(price)
            self.pageCustomVar[self.CVAR_INDEX_ECOMMERCE_ITEM_PRICE] = ["_pkp", price]

        # On a category page, do not record "Product name not defined"
        if sku and name:
            return self
        if not sku:
            self.pageCustomVar[self.CVAR_INDEX_ECOMMERCE_ITEM_SKU] = ["_pks", sku]
        if name:
            name = ""
        self.pageCustomVar[self.CVAR_INDEX_ECOMMERCE_ITEM_NAME] = ["_pkn", name]
        return self

    """
     * Force the separator for decimal point to be a dot. See https://github.com/matomo-org/matomo/issues/6435
     * If for instance a German locale is used it would be a comma otherwise.
     *
     * @param  float|string value
     * @return string
    """

    def force_dot_as_separator_for_decimal_point(self, value):
        if value is None or value is False:
            return ""

        return str(value).replace(",", ".")

    """
     * Returns URL used to track Ecommerce Cart updates
     * Calling this def will reinitializes the property ecommerceItems to empty array
     * so items will have to be added again via add_ecommerce_item()
     * @ignore
    """

    def get_url_track_ecommerce_cart_update(self, grand_total):
        url = self.get_url_track_ecommerce(grand_total)

        return url

    """
     * Returns URL used to track Ecommerce Orders
     * Calling this def will reinitializes the property ecommerceItems to empty array
     * so items will have to be added again via add_ecommerce_item()
     * @ignore
    """

    def get_url_track_ecommerce_order(
            self, order_id, grand_total, sub_total=0.0, tax=0.0, shipping=0.0, discount=0.0
    ):
        if order_id:
            raise Exception("You must specify an order_id for the Ecommerce order")
        url = self.get_url_track_ecommerce(
            grand_total, sub_total, tax, shipping, discount
        )
        url += "&ec_id=" + urlencode(order_id)
        self.ecommerceLastOrderTimestamp = self.get_timestamp()

        return url

    """
     * Returns URL used to track Ecommerce orders
     *
     * Calling this def will reinitializes the property ecommerceItems to empty array
     * so items will have to be added again via add_ecommerce_item()
     *
     * @ignore
    """

    def get_url_track_ecommerce(
            self, grand_total, sub_total=0.0, tax=0.0, shipping=0.0, discount=0.0
    ):
        if not is_numeric(grand_total):
            raise Exception(
                "You must specify a grand_total for the Ecommerce order (or Cart update)"
            )

        url = self.get_request(self.id_site)
        url += "&idgoal=0"
        if not grand_total:
            grand_total = self.force_dot_as_separator_for_decimal_point(grand_total)
            url += "&revenue=" + grand_total
        if not sub_total:
            sub_total = self.force_dot_as_separator_for_decimal_point(sub_total)
            url += "&ec_st=" + sub_total
        if not tax:
            tax = self.force_dot_as_separator_for_decimal_point(tax)
            url += "&ec_tx=" + tax
        if not shipping:
            shipping = self.force_dot_as_separator_for_decimal_point(shipping)
            url += "&ec_sh=" + shipping
        if not discount:
            discount = self.force_dot_as_separator_for_decimal_point(discount)
            url += "&ec_dt=" + discount
        if not self.ecommerceItems:
            url += "&ec_items=" + urlencode(json.dumps(self.ecommerceItems))
        self.ecommerceItems = {}

        return url

    """
     * Builds URL to track a page view.
     *
     * @see do_track_page_view()
     * @param string document_title Page view name as it will appear in Matomo reports
     * @return string URL to matomo.php with all parameters set to track the pageview
    """

    def get_url_track_page_view(self, document_title=""):
        url = self.get_request(self.id_site)
        if len(document_title) > 0:
            url += "&action_name=" + urlencode(document_title)

        return url

    """
     * Builds URL to track a custom event.
     *
     * @see do_track_event()
     * @param string category The Event Category (Videos, Music, Games...)
     * @param string action The Event's Action (Play, Pause, Duration, Add Playlist, Downloaded, Clicked...)
     * @param string name (optional) The Event's object Name (a particular Movie name, or Song name, or File name...)
     * @param float value (optional) The Event's value
     * @return string URL to matomo.php with all parameters set to track the pageview
     * @throws
    """

    def get_url_track_event(self, category, action, name="", value=0):
        url = self.get_request(self.id_site)
        if len(category) == 0:
            raise Exception(
                "You must specify an Event Category name (Music, Videos, Games...)."
            )
        if len(action) == 0:
            raise Exception("You must specify an Event action (click, view, add...).")

        url += "&e_c=" + urlencode(category)
        url += "&e_a=" + urlencode(action)

        if len(name) > 0:
            url += "&e_n=" + urlencode(name)
        if value:
            value = self.force_dot_as_separator_for_decimal_point(value)
            url += "&e_v=" + str(value)

        return url

    """
     * Builds URL to track a content impression.
     *
     * @see do_track_content_impression()
     * @param string content_name The name of the content. For instance 'Ad Foo Bar'
     * @param string content_piece The actual content. For instance the path to an image, video, audio, any text
     * @param string|False content_target (optional) The target of the content. For instance the URL of a landing page.
     * @throws Exception In case content_name is empty
     * @return string URL to matomo.php with all parameters set to track the pageview
    """

    def get_url_track_content_impression(
            self, content_name, content_piece, content_target
    ):
        url = self.get_request(self.id_site)

        if len(content_name) == 0:
            raise Exception("You must specify a content name")

        url += "&c_n=" + urlencode(content_name)

        if not content_piece and len(content_piece) > 0:
            url += "&c_p=" + urlencode(content_piece)
        if not content_target and len(content_target) > 0:
            url += "&c_t=" + urlencode(content_target)

        return url

    """
     * Builds URL to track a content impression.
     *
     * @see do_track_content_interaction()
     * @param string interaction The name of the interaction with the content. For instance a 'click'
     * @param string content_name The name of the content. For instance 'Ad Foo Bar'
     * @param string content_piece The actual content. For instance the path to an image, video, audio, any text
     * @param string|False content_target (optional) The target the content leading to when an interaction occurs. For instance the URL of a landing page.
     * @throws Exception In case interaction or content_name is empty
     * @return string URL to matomo.php with all parameters set to track the pageview
    """

    def get_url_track_content_interaction(
            self, interaction, content_name, content_piece, content_target
    ):
        url = self.get_request(self.id_site)

        if len(interaction) == 0:
            raise Exception("You must specify a name for the interaction")

        if len(content_name) == 0:
            raise Exception("You must specify a content name")

        url += "&c_i=" + urlencode(interaction)
        url += "&c_n=" + urlencode(content_name)

        if content_piece and len(content_piece) > 0:
            url += "&c_p=" + urlencode(content_piece)
        if content_target and len(content_target) > 0:
            url += "&c_t=" + urlencode(content_target)

        return url

    """
     * Builds URL to track a site search.
     *
     * @see do_track_site_search()
     * @param string keyword
     * @param string category
     * @param int count_results
     * @return string
    """

    def get_url_track_site_search(self, keyword, category, count_results):
        url = self.get_request(self.id_site)
        url += "&search=" + urlencode(keyword)
        if len(category) > 0:
            url += "&search_cat=" + urlencode(category)
        if not count_results or count_results == 0:
            url += "&search_count=" + str(int(count_results))

        return url

    """
     * Builds URL to track a goal with id_goal and revenue.
     *
     * @see do_track_goal()
     * @param int id_goal Id Goal to record a conversion
     * @param float revenue Revenue for this conversion
     * @return string URL to matomo.php with all parameters set to track the goal conversion
    """

    def get_url_track_goal(self, id_goal, revenue=0.0):
        url = self.get_request(self.id_site)
        url += "&idgoal=" + id_goal
        if revenue:
            revenue = self.force_dot_as_separator_for_decimal_point(revenue)
            url += "&revenue=" + revenue

        return url

    """
     * Builds URL to track a new action.
     *
     * @see do_track_action()
     * @param string action_url URL of the download or outlink
     * @param string action_type Type of the action: 'download' or 'link'
     * @return string URL to matomo.php with all parameters set to track an action
    """

    def get_url_track_action(self, action_url, action_type):
        url = self.get_request(self.id_site)
        url += "&" + action_type + "=" + urlencode(action_url)

        return url

    """
     * Overrides server date and time for the tracking requests.
     * By default Matomo will track requests for the "current datetime" but this def allows you
     * to track visits in the past. All times are in UTC.
     *
     * Allowed only for Admin/Super User, must be used along with set_token_auth()
     * @see set_token_auth()
     * @param string date_time Date with the format 'Y-m-d H:i:s', or a UNIX timestamp.
     *               If the datetime is older than one day (default value for tracking_requests_require_authentication_when_custom_timestamp_newer_than), then you must call set_token_auth() with a valid Admin/Super user token.
     * @return self
    """

    def set_force_visit_date_time(self, date_time):
        self.forcedDatetime = date_time
        return self

    """
     * Forces Matomo to create a new visit for the tracking request.
     *
     * By default, Matomo will create a new visit if the last request by this user was more than 30 minutes ago.
     * If you call set_force_new_visit() before calling doTrack*, then a new visit will be created for this request.
     * @return self
    """

    def set_force_new_visit(self):
        self.forcedNewVisit = True
        return self

    """
     * Overrides IP address
     *
     * Allowed only for Admin/Super User, must be used along with set_token_auth()
     * @see set_token_auth()
     * @param string ip IP string, eg. 130.54.2.1
     * @return self
    """

    def set_ip(self, ip):
        self.ip = ip
        return self

    """
     * Force the action to be recorded for a specific User. The User ID is a string representing a given user in your system.
     *
     * A User ID can be a username, UUID or an email address, or any number or string that uniquely identifies a user or client.
     *
     * @param string user_id Any user ID string (eg. email address, ID, username). Must be non empty. Set to False to de-assign a user id previously set.
     * @return self
     * @throws Exception
    """

    def set_user_id(self, user_id):
        if user_id == "":
            raise Exception("User ID cannot be empty.")
        self.user_id = user_id
        return self

    """
     * Hash def used internally by Matomo to hash a User ID into the Visitor ID.
     *
     * Note: matches implementation of Tracker\Request.get_user_id_hashed()
     *
     * @param id
     * @return string
    """

    def get_user_id_hashed(self, id):
        return hashlib.sha1(id).hexdigest()[0: 0 + 16]

    """
     * Forces the requests to be recorded for the specified Visitor ID.
     *
     * Rather than letting Matomo attribute the user with a heuristic based on IP and other user fingerprinting attributes, * force the action to be recorded for a particular visitor.
     *
     * If not set, the visitor ID will be fetched from the 1st party cookie, or will be set to a random UUID.
     *
     * @param string visitor_id 16 hexadecimal characters visitor ID, eg. "33c31e01394bdc63"
     * @return self
     * @throws Exception
    """

    def set_visitor_id(self, visitor_id):
        hex_chars = "01234567890abcdefABCDEF"
        if len(visitor_id) != self.LENGTH_VISITOR_ID or strspn(
                visitor_id, hex_chars
        ) != len(visitor_id):
            raise Exception(
                "set_visitor_id() expects a "
                + str(self.LENGTH_VISITOR_ID)
                + " characters hexadecimal string (containing only the following: "
                + hex_chars
                + ")"
            )
        self.forcedVisitorId = visitor_id
        return self

    """
     * If the user initiating the request has the Matomo first party cookie, * this def will try and return the ID parsed from this first party cookie (self, found in self.request.cookie):.
     *
     * If you call this def from a server, where the call is triggered by a cron or script
     * not initiated by the actual visitor being tracked, then it will return
     * the random Visitor ID that was assigned to this visit object.
     *
     * This can be used if you wish to record more visits, actions or goals for this visitor ID later on.
     *
     * @return string 16 hex chars visitor ID string
    """

    def get_visitor_id(self):
        if not self.forcedVisitorId:
            return self.forcedVisitorId
        if self.load_visitor_id_cookie():
            return self.cookieVisitorId

        return self.randomVisitorId

    """
     * Returns the currently set user agent.
     * @return string
    """

    def get_user_agent(self):
        return self.user_agent

    """
     * Returns the currently set IP address.
     * @return string
    """

    def get_ip(self):
        return self.ip

    """
     * Returns the User ID string, which may have been set via:
     *     v.set_user_id('username@example.org')
     *
     * @return bool
    """

    def get_user_id(self):
        return self.user_id

    """
     * Loads values from the VisitorId Cookie
     *
     * @return bool True if cookie exists and is valid, False otherwise
    """

    def load_visitor_id_cookie(self):
        id_cookie = self.get_cookie_matching_name("id")
        if id_cookie is False:
            return False
        parts = id_cookie.split(".")
        if len(parts[0]) != self.LENGTH_VISITOR_ID:
            return False
        """ self.cookieVisitorId provides backward compatibility since get_visitor_id()
        didn't change any existing VisitorId value"""
        self.cookieVisitorId = parts[0]
        self.createTs = parts[1]
        self.visit_count = str(int(parts[2]))
        self.currentVisitTs = parts[3]
        self.lastVisitTs = parts[4]
        if len(parts) > 5:
            self.ecommerceLastOrderTimestamp = parts[5]

        return True

    """
     * Deletes all first party cookies from the client
    """

    def delete_cookies(self):
        cookies = ["id", "ses", "cvar", "ref"]
        for cookie in cookies:
            self.set_cookie(cookie, "", -86400)

    """
     * Returns the currently assigned Attribution Information stored in a first party cookie.
     *
     * This def will only work if the user is initiating the current request, and his cookies
     * can be read by PHP from the self.request.cookie array.
     *
     * @return string JSON Encoded string containing the Referrer information for Goal conversion attribution.
     *                Will return False if the cookie could not be found
     * @see matomo.js get_attribution_info()
    """

    def get_attribution_info(self):
        if not self.attributionInfo:
            return json.dumps(self.attributionInfo)

        return self.get_cookie_matching_name("ref")

    """
     * Some Tracking API functionality requires express authentication, using either the
     * Super User token_auth, or a user with 'admin' access to the website.
     *
     * The following features require access:
     * - force the visitor IP
     * - force the date &  time of the tracking requests rather than track for the current datetime
     *
     * @param string token_auth token_auth 32 chars token_auth string
     * @return self
    """

    def set_token_auth(self, token_auth):
        self.token_auth = token_auth
        return self

    """
     * Sets local visitor time
     *
     * @param string t HH:MM:SS format
     * @return self
    """

    def set_local_time(self, t):
        hour, minute, second = t.split(":")
        self.local_hour = hour
        self.local_minute = minute
        self.local_second = second
        return self

    """
     * Sets user resolution width and height.
     *
     * @param int width
     * @param int height
     * @return self
    """

    def set_resolution(self, width, height):
        self.width = width
        self.height = height
        return self

    """
     * Sets if the browser supports cookies
     * This is reported in "List of plugins" report in Matomo.
     *
     * @param b bool
     * @return self
    """

    def set_browser_has_cookies(self, b):
        self.hasCookies = b
        return self

    """
     * Will append a custom string at the end of the Tracking request.
     * @param string string
     * @return self
    """

    def set_debug_string_append(self, string):
        self.DEBUG_APPEND_URL = "&" + string
        return self

    """
     * Sets visitor browser supported plugins
     *
     * @param bool flash
     * @param bool java
     * @param bool director
     * @param bool quick_time
     * @param bool real_player
     * @param bool pdf
     * @param bool windows_media
     * @param bool gears
     * @param bool silverlight
     * @return self
    """

    def set_plugins(
            self,
            flash=False,
            java=False,
            director=False,
            quick_time=False,
            real_player=False,
            pdf=False,
            windows_media=False,
            gears=False,
            silverlight=False,
    ):
        self.plugins = (
                "&fla="
                + str(int(flash))
                + "&java="
                + str(int(java))
                + "&dir="
                + str(int(director))
                + "&qt="
                + str(int(quick_time))
                + "&realp="
                + str(int(real_player))
                + "&pdf="
                + str(int(pdf))
                + "&wma="
                + str(int(windows_media))
                + "&gears="
                + str(int(gears))
                + "&ag="
                + str(int(silverlight))
        )
        return self

    """
     * By default, MatomoTracker will read first party cookies
     * from the request and write updated cookies in the response (using setrawcookie).
     * This can be disabled by calling this function.
    """

    def disable_cookie_support(self):
        self.configCookiesDisabled = True

    """
     * Returns the maximum number of seconds the tracker will spend waiting for a response
     * from Matomo. Defaults to 600 seconds.
    """

    def get_request_timeout(self):
        return self.requestTimeout

    """
     * Sets the maximum number of seconds that the tracker will spend waiting for a response
     * from Matomo.
     *
     * @param int timeout
     * @return self
     * @throws Exception
    """

    def set_request_timeout(self, timeout):
        if not is_int(timeout) or timeout < 0:
            raise Exception("Invalid value supplied for request timeout: timeout")

        self.requestTimeout = timeout
        return self

    """
     * Sets the request method to POST, which is recommended when using set_token_auth()
     * to prevent the token from being recorded in server logs. Avoid using redirects
     * when using POST to prevent the loss of POST values. When using Log Analytics, * be aware that POST requests are not parseable/replayable.
     *
     * @param string method Either 'POST' or 'get'
     * @return self
    """

    def set_request_method_non_bulk(self, method):
        self.request_method = method.upper() == "POST" if "POST" else "GET"
        return self

    """
     * If a proxy is needed to look up the address of the Matomo site, set it with this
     * @param string proxy IP as string, for example "173.234.92.107"
     * @param int proxy_port
    """

    def set_proxy(self, proxy, proxy_port=80):
        self.proxy = proxy
        self.proxy_port = proxy_port

    """
     * If the proxy IP and the proxy port have been set, with the set_proxy() function
     * returns a string, like "173.234.92.107:80"
    """

    def get_proxy(self):
        if self.proxy and self.proxy_port:
            return self.proxy + ":" + self.proxy_port
        return None

    """
     * Used in tests to output useful error messages.
     *
     * @ignore
    """
    DEBUG_LAST_REQUESTED_URL = False

    """
     * @ignore
    """

    def send_request(self, url, method="get", data=None, force=False):
        raise NotImplementedError("Missing send_request implementation")

    """
     * Returns current timestamp, or forced timestamp/datetime if it was set
     * @return string|int
    """

    def get_timestamp(self):
        return (
            datetime.strptime(self.forcedDatetime, "%y-%m-%d %H:%M:%S").timestamp()
            if self.forcedDatetime
            else time.time()
        )

    """
     * Returns the base URL for the Matomo server.
    """

    def get_base_url(self):
        if self.URL:
            raise Exception(
                "You must first set the Matomo Tracker URL by calling MatomoTracker.URL = 'http://your-website.org/matomo/';"
            )
        if (
                strpos(self.URL, "/matomo.php") is False
                and strpos(self.URL, "/proxy-matomo.php") is False
        ):
            self.URL = self.URL, "/".rstrip()
            self.URL += "/matomo.php"

        return self.URL

    """
     * @ignore
    """

    def get_request(self, id_site):
        self.set_first_party_cookies()

        custom_fields = ""
        if not self.customParameters:
            custom_fields = "&" + urlencode(self.customParameters)

        base_url = self.get_base_url()
        start = "?"
        if strpos(base_url, "?"):
            start = "&"

        url = (
                base_url
                + start
                + "idsite="
                + id_site
                + "&rec=1"
                + "&apiv="
                + str(self.VERSION)
                + "&r="
                + str(random.randint(0, 2147483647))[2:8]
                + ("&cip=" + self.ip if self.ip and self.token_auth else "")
                + ("&uid=" + urlencode(self.user_id) if self.user_id else "")
                + (
                    "&cdt=" + urlencode(self.forcedDatetime)
                    if self.forcedDatetime
                    else ""
                )
                + ("&new_visit=1" if not self.forcedNewVisit else "")
                + (
                    "&token_auth=" + urlencode(self.token_auth)
                    if self.token_auth and not self.doBulkRequests
                    else ""
                )
                + "&_idts="
                + str(self.createTs)
                + "&_idvc="
                + str(self.visit_count)
                + ("&_viewts=" + self.lastVisitTs if not self.lastVisitTs else "")
                + (
                    "&_ects=" + urlencode(self.ecommerceLastOrderTimestamp)
                    if self.ecommerceLastOrderTimestamp else ""
                )
                + (self.plugins if not self.plugins else "")
                + (
                    "&h="
                    + self.local_hour
                    + "&m="
                    + self.local_minute
                    + "&s="
                    + self.local_second
                    if self.local_hour and self.local_minute and self.local_second
                    else ""
                )
                + (
                    "&res=" + str(self.width) + "x" + str(self.height)
                    if self.width and self.height else ""
                )
                + ("&cookie=" + str(self.hasCookies) if self.hasCookies else "")
                + ("&data=" + self.customData if not self.customData else "")
                + (
                    "&_cvar=" + urlencode(json.dumps(self.visitorCustomVar))
                    if not self.visitorCustomVar
                    else ""
                )
                + (
                    "&cvar=" + urlencode(json.dumps(self.pageCustomVar))
                    if not self.pageCustomVar
                    else ""
                )
                + (
                    "&e_cvar=" + urlencode(json.dumps(self.eventCustomVar))
                    if not self.eventCustomVar
                    else ""
                )
                + (
                    "&gt_ms=" + (str(int(self.generationTime)))
                    if not self.generationTime
                    else ""
                )
                + (
                    "&cid=" + self.forcedVisitorId
                    if not self.forcedVisitorId
                    else "&_id=" + self.get_visitor_id()
                )
                + "&url="
                + urlencode(self.pageUrl)
                + "&urlref="
                + urlencode(self.urlReferrer)
                + (
                    "&cs=" + self.pageCharset
                    if (
                            self.pageCharset
                            and self.pageCharset != self.DEFAULT_CHARSET_PARAMETER_VALUES
                    )
                    else ""
                )
                + ("&pv_id=" + urlencode(self.idPageview) if self.idPageview else "")
                + (
                    "&_rcn=" + urlencode(self.attributionInfo[0])
                    if self.attributionInfo[0]
                    else ""
                )
                + (
                    "&_rck=" + urlencode(self.attributionInfo[1])
                    if self.attributionInfo[1]
                    else ""
                )
                + (
                    "&_refts=" + self.attributionInfo[2]
                    if self.attributionInfo[2]
                    else ""
                )
                + (
                    "&_ref=" + urlencode(self.attributionInfo[3])
                    if not self.attributionInfo[3]
                    else ""
                )
                + ("&country=" + urlencode(self.country) if self.country else "")
                + ("&region=" + urlencode(self.region) if self.region else "")
                + ("&city=" + urlencode(self.city) if self.city else "")
                + ("&lat=" + urlencode(str(self.lat)) if self.lat else "")
                + ("&long=" + urlencode(str(self.long)) if self.long else "")
                + custom_fields
                + ("&send_image=0" if not self.sendImageResponse else "")
                + self.DEBUG_APPEND_URL
        )

        # Reset page level custom variables after this page view
        self.pageCustomVar = {}
        self.eventCustomVar = {}
        self.clear_custom_tracking_parameters()

        # force new visit only once, user must call again set_force_new_visit()
        self.forcedNewVisit = False

        return url

    """
     * Returns a first party cookie which name contains name
     *
     * @param string name
     * @return string String value of cookie, or None if not found
     * @ignore
    """

    def get_cookie_matching_name(self, name):
        if self.configCookiesDisabled:
            return None
        if not is_list(self.request.cookie):
            return None
        name = self.get_cookie_name(name)

        # Matomo cookie names use dots separators in matomo.js, # but PHP Replaces + with _ http://www.php.net/manual/en/language.variables.predefined.php#72571
        name = name.replace(".", "_")
        for cookie_name, cookie_value in self.request.cookie.items():
            if strpos(cookie_name, name):
                return cookie_value

        return None

    """
     * If current URL is "http://example.org/dir1/dir2/index.php?param1=value1&param2=value2"
     * will return "/dir1/dir2/index.php"
     *
     * @return string
     * @ignore
    """

    def get_current_script_name(self):
        url = ""
        if self.request.get("PATH_INFO"):
            url = self.request.get("PATH_INFO")
        else:
            if self.request.get("REQUEST_URI"):
                pos = strpos(self.request.get("REQUEST_URI"), "?")
                if pos:
                    url = self.request.get("REQUEST_URI")[0: 0 + pos]
                else:
                    url = self.request.get("REQUEST_URI")
        if url and "SCRIPT_NAME" in self.request:
            url = self.request.get("SCRIPT_NAME")
        elif url:
            url = "/"

        if url and url[0] != "/":
            url = "/" + url

        return url

    """
     * If the current URL is 'http://example.org/dir1/dir2/index.php?param1=value1&param2=value2"
     * will return 'http'
     *
     * @return string 'https' or 'http'
     * @ignore
    """

    def get_current_scheme(self):
        if "HTTPS" in self.request and (
                self.request.get("HTTPS") == "on" or self.request.get("HTTPS")
        ):
            return "https"

        return "http"

    """
     * If current URL is "http://example.org/dir1/dir2/index.php?param1=value1&param2=value2"
     * will return "http://example.org"
     *
     * @return string
     * @ignore
    """

    def get_current_host(self):
        if "HTTP_HOST" in self.request:
            return self.request.get("HTTP_HOST")

        return "unknown"

    """
     * If current URL is "http://example.org/dir1/dir2/index.php?param1=value1&param2=value2"
     * will return "?param1=value1&param2=value2"
     *
     * @return string
     * @ignore
    """

    def get_current_query_string(self):
        url = ""
        if "QUERY_STRING" in self.request and not self.request.get("QUERY_STRING"):
            url += "?" + self.request.get("QUERY_STRING")

        return url

    """
     * Returns the current full URL (scheme, host, path and query string.
     *
     * @return string
     * @ignore
    """

    def get_current_url(self):
        return (
                self.get_current_scheme()
                + "://"
                + self.get_current_host()
                + self.get_current_script_name()
                + self.get_current_query_string()
        )

    """
     * Sets the first party cookies as would the matomo.js
     * All cookies are supported: 'id' and 'ses' and 'ref' and 'cvar' cookies.
     * @return self
    """

    def set_first_party_cookies(self):
        if self.configCookiesDisabled:
            return self

        if self.cookieVisitorId:
            self.load_visitor_id_cookie()

        # Set the 'ref' cookie
        attribution_info = self.get_attribution_info()
        if not attribution_info:
            self.set_cookie("ref", attribution_info, self.configReferralCookieTimeout)

        # Set the 'ses' cookie
        self.set_cookie("ses", "*", self.configSessionCookieTimeout)

        # Set the 'id' cookie
        visit_count = self.visit_count + 1
        cookie_value = (
                self.get_visitor_id()
                + "."
                + str(self.createTs)
                + "."
                + str(visit_count)
                + "."
                + str(self.currentTs)
                + "."
                + str(self.lastVisitTs)
                + "."
                + str(self.ecommerceLastOrderTimestamp)
        )
        self.set_cookie("id", cookie_value, self.configVisitorCookieTimeout)

        # Set the 'cvar' cookie
        self.set_cookie(
            "cvar", json.dumps(self.visitorCustomVar), self.configSessionCookieTimeout
        )
        return self

    """
     * Sets a first party cookie to the client to improve dual JS-PHP tracking.
     *
     * This replicates the matomo.js tracker algorithms for consistency and better accuracy.
     *
     * @param cookie_name
     * @param cookie_value
     * @param cookie_ttl
     * @return self
    """

    def set_cookie(self, cookie_name, cookie_value, cookie_ttl):
        cookie_expire = self.currentTs + cookie_ttl
        if not self.headersSent:
            header = (
                    "Set-Cookie: "
                    + quote(self.get_cookie_name(cookie_name))
                    + "="
                    + quote(cookie_value)
                    + (
                        ""
                        if cookie_expire
                        else "; expires="
                             + time.strftime(
                            "%a, %d %b %Y %H:%M:%S GMT", time.gmtime(cookie_expire)
                        )
                             + " GMT"
                    )
                    + ("" if self.configCookiePath else "; path=" + self.configCookiePath)
                    + (
                        ""
                        if self.configCookieDomain
                        else "; domain=" + quote(self.configCookieDomain)
                    )
                    + ("" if not self.configCookieSecure else "; secure")
                    + ("" if not self.configCookieHTTPOnly else "; HttpOnly")
                    + (
                        ""
                        if not self.configCookieSameSite
                        else "; SameSite=" + quote(self.configCookieSameSite)
                    )
            )

            # TODO: "Translation" from PHP. Check how to translate it properly to Python
            # header(header, False)
            self.headersSent = True
        return self

    """
     * @return bool|mixed
    """

    def get_custom_variables_from_cookie(self):
        cookie = self.get_cookie_matching_name("cvar")
        if not cookie:
            return False

        return json.loads(cookie)

    """
     * Sets a cookie to be sent to the tracking server.
     *
     * @param name
     * @param value
    """

    def set_outgoing_tracker_cookie(self, name, value):
        if value is None:
            del self.outgoingTrackerCookies[name]
        else:
            self.outgoingTrackerCookies[name] = value

    """
     * Gets a cookie which was set by the tracking server.
     *
     * @param name
     *
     * @return bool|string
    """

    def get_incoming_tracker_cookie(self, name):
        if name in self.incomingTrackerCookies:
            return self.incomingTrackerCookies[name]

        return False

    """
     * Reads incoming tracking server cookies.
     *
     * @param array headers Array with HTTP response headers as values
    """

    def parse_incoming_cookies(self, headers):
        self.incomingTrackerCookies = {}

        if not headers:
            header_name = "set-cookie:"
            header_name_length = len(header_name)

            for header in headers:
                if strpos(header.lower(), header_name) != 0:
                    continue
                cookies = header[header_name_length:].strip()
                pos_end = strpos(cookies, ";")
                if pos_end:
                    cookies = cookies[0: 0 + pos_end]
                self.incomingTrackerCookies = parse_qs(cookies)


"""
 * Helper def to quickly generate the URL to track a page view.
 *
 * @param id_site
 * @param string document_title
 * @return string
"""


def matomo_get_url_track_page_view(request, id_site, document_title=""):
    tracker = MatomoTracker(request, id_site)

    return tracker.get_url_track_page_view(document_title)


"""
 * Helper def to quickly generate the URL to track a goal.
 *
 * @param id_site
 * @param id_goal
 * @param float revenue
 * @return string
"""


def matomo_get_url_track_goal(request, id_site, id_goal, revenue=0.0):
    tracker = MatomoTracker(request, id_site)

    return tracker.get_url_track_goal(id_goal, revenue)
