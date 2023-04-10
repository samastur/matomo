import json
import random

import pytest

from matomo import MatomoTracker
from matomo.request import Request


request_data = {
    "HTTP_REFERER": "http://localhost:7000/matomo_test",
    "REMOTE_ADDR": "192.168.0.1",
    "HTTP_HOST": "test.domain.example",
    "REQUEST_URI": "/matomo_test_fake",
    "QUERY_STRING": "test=1",
}


@pytest.fixture
def tracker():
    def send_request(url):
        return url

    req = Request(request_data)
    track = MatomoTracker(req, 1, "https://matomo.domain.example")
    track.real_send_request = track.send_request
    track.send_request = send_request
    return track


def test___init__(tracker):
    assert tracker.id_site == "1"
    assert tracker.urlReferrer == request_data["HTTP_REFERER"]
    assert tracker.ip == request_data["REMOTE_ADDR"]


def test_set_page_charset(tracker):
    assert tracker.pageCharset == "utf-8"
    tracker.set_page_charset("utf-16")
    assert tracker.pageCharset == "utf-16"


def test_set_url(tracker):
    assert tracker.pageUrl == "http://test.domain.example/matomo_test_fake?test=1"
    tracker.set_url("http://test.domain.example/matomo_test_faked")
    assert tracker.pageUrl == "http://test.domain.example/matomo_test_faked"


def test_set_url_referrer(tracker):
    ref_url = "http://localhost:7000/differe-url"
    assert tracker.urlReferrer == request_data["HTTP_REFERER"]
    tracker.set_url_referrer(ref_url)
    assert tracker.urlReferrer == ref_url


def test_set_performance_timings(tracker):
    fields = [
        "networkTime",
        "serverTime",
        "transferTime",
        "domProcessingTime",
        "domCompletionTime",
        "onLoadTime",
    ]
    values = [random.randint(1, 100) for i in range(len(fields))]

    for field in fields:
        assert getattr(tracker, field) == 0

    tracker.set_performance_timings(*values)

    for i, field in enumerate(fields):
        assert getattr(tracker, field) == values[i]


def test_clear_performance_timings(tracker):
    fields = [
        "networkTime",
        "serverTime",
        "transferTime",
        "domProcessingTime",
        "domCompletionTime",
        "onLoadTime",
    ]

    test_set_performance_timings(tracker)

    for field in fields:
        assert getattr(tracker, field) != 0

    tracker.clear_performance_timings()

    for field in fields:
        assert getattr(tracker, field) == 0


def test_set_url_referer(tracker):
    ref_url = "http://localhost:7000/differe-url"
    assert tracker.urlReferrer == request_data["HTTP_REFERER"]
    tracker.set_url_referer(ref_url)
    assert tracker.urlReferrer == ref_url


def test_set_attribution_info(tracker):
    valid = [1, 2, "3", 4]
    invalid = {1: 2}

    assert tracker.attributionInfo is None
    tracker.set_attribution_info(json.dumps(valid))
    assert tracker.attributionInfo == valid

    with pytest.raises(Exception):
        tracker.set_attribution_info(json.dumps(invalid))


def test_set_custom_variable(tracker):
    assert tracker.pageCustomVar == {}
    assert tracker.eventCustomVar == {}
    assert tracker.visitorCustomVar == {}

    # First check error handling
    with pytest.raises(Exception) as exc:
        tracker.set_custom_variable("1", "name", "value")
    exc = exc.value.args[0]
    assert exc == "Parameter id to set_custom_variable should be an integer"

    with pytest.raises(Exception) as exc:
        tracker.set_custom_variable(1, "name", "value", "invalidscope")
    exc = exc.value.args[0]
    assert exc == "Invalid 'scope' parameter value"

    tracker.set_custom_variable(1, "name", "value", "page")
    assert tracker.pageCustomVar[1] == ["name", "value"]

    tracker.set_custom_variable(3, "name", "value", "event")
    assert tracker.eventCustomVar[3] == ["name", "value"]

    tracker.set_custom_variable(2, "name", "value", "visit")
    assert tracker.visitorCustomVar[2] == ["name", "value"]


def test_get_custom_variable(tracker):
    tracker.set_custom_variable(1, "name", "value", "page")
    tracker.set_custom_variable(3, "name", "value2", "event")
    tracker.set_custom_variable(2, "name", "value3", "visit")

    assert tracker.get_custom_variable(1, "page") == ["name", "value"]
    assert tracker.get_custom_variable(3, "event") == ["name", "value2"]
    assert tracker.get_custom_variable(2, "visit") == ["name", "value3"]
    assert tracker.get_custom_variable(2, "page") is False
    assert tracker.get_custom_variable(4, "event") is False
    assert tracker.get_custom_variable(3, "visit") is False


def test_clear_custom_variable(tracker):
    tracker.set_custom_variable(1, "name", "value", "page")
    tracker.set_custom_variable(3, "name", "value2", "event")
    tracker.set_custom_variable(2, "name", "value3", "visit")

    tracker.clear_custom_variables()

    assert tracker.get_custom_variable(1, "page") is False
    assert tracker.get_custom_variable(3, "event") is False
    assert tracker.get_custom_variable(2, "visit") is False


def test_set_custom_dimension(tracker):
    assert tracker.customDimensions == {}
    tracker.set_custom_dimension("1", "val1")
    assert tracker.customDimensions["dimension1"] == "val1"


def test_clear_custom_dimensions(tracker):
    tracker.set_custom_dimension("1", "val1")
    tracker.set_custom_dimension("2", "val2")
    tracker.clear_custom_dimensions()
    assert tracker.customDimensions == {}


def test_get_custom_dimensions(tracker):
    tracker.set_custom_dimension(1, "val1")
    tracker.set_custom_dimension(2, "val2")
    assert tracker.get_custom_dimension(1) == "val1"
    assert tracker.get_custom_dimension(1) == "val1"
    assert tracker.get_custom_dimension(3) is None


def test_set_custom_tracking_parameter(tracker):
    tracker.set_custom_tracking_parameter("bw_bytes", "value5")
    assert tracker.customParameters["bw_bytes"] == "value5"

    tracker.set_custom_tracking_parameter("dimension1", "value4")
    assert tracker.customParameters.get("dimension1") is None
    assert tracker.get_custom_dimension(1) == "value4"


def test_clear_custom_tracking_parameters(tracker):
    tracker.set_custom_tracking_parameter("bw_bytes", "value5")
    tracker.clear_custom_tracking_parameters()
    assert tracker.customParameters.get("bw_bytes") is None


def test_set_new_visitor_id(tracker):
    tracker.set_new_visitor_id()
    visitor_id = tracker.randomVisitorId

    assert visitor_id is not None
    assert tracker.forcedVisitorId is False
    assert tracker.cookieVisitorId is False

    tracker.set_new_visitor_id()
    assert visitor_id != tracker.randomVisitorId


def test_set_id_site(tracker):
    assert tracker.id_site == "1"
    tracker.set_id_site(2)
    assert tracker.id_site == 2


def test_set_browser_language(tracker):
    assert tracker.accept_language == ""
    tracker.set_browser_language("sl_SI")
    assert tracker.accept_language == "sl_SI"


def test_set_user_agent(tracker):
    """
    Sets the user agent, used to detect OS and browser.
    If this function is not called, the User Agent will default to the current user agent.

    * @param str user_agent
    * @return self
    """
    assert tracker.user_agent == ""
    tracker.set_user_agent("Mozilla 5.0")
    assert tracker.user_agent == "Mozilla 5.0"


def test_set_client_hints(tracker):
    assert tracker.clientHints == {
        "model": "",
        "platform": "",
        "platformVersion": "",
        "uaFullVersion": "",
        "fullVersionList": [],
    }

    tracker.set_client_hints("modelA", "platformB", "1.12", "", "uaC")
    assert tracker.clientHints == {
        "model": "modelA",
        "platform": "platformB",
        "platformVersion": "1.12",
        "uaFullVersion": "uaC",
        "fullVersionList": [],
    }

    full_version_list = '" Not A;Brand";v="99.0.0.0", "Chromium";v="98.0.4750.0", "Google Chrome";v="98.0.4750.0"'
    tracker.set_client_hints("modelA", "platformB", "1.12", full_version_list, "uaC")
    assert tracker.clientHints == {
        "model": "modelA",
        "platform": "platformB",
        "platformVersion": "1.12",
        "uaFullVersion": "uaC",
        "fullVersionList": [
            {"brand": " Not A;Brand", "version": "99.0.0.0"},
            {"brand": "Chromium", "version": "98.0.4750.0"},
            {"brand": "Google Chrome", "version": "98.0.4750.0"},
        ],
    }


def test_set_country(tracker):
    assert tracker.country == ""
    tracker.set_country("Slovenia")
    assert tracker.country == "Slovenia"


def test_set_region(tracker):
    assert tracker.region == ""
    tracker.set_region("Primorska")
    assert tracker.region == "Primorska"


def test_set_city(tracker):
    assert tracker.city == ""
    tracker.set_city("Ljubljana")
    assert tracker.city == "Ljubljana"


def test_set_latitude(tracker):
    assert tracker.lat == 0
    tracker.set_latitude(15.34)
    assert tracker.lat == 15.34


def test_set_longitude(tracker):
    assert tracker.long == 0
    tracker.set_longitude(16.34)
    assert tracker.long == 16.34


def test_enable_bulk_tracking(tracker):
    assert tracker.doBulkRequests is False
    tracker.enable_bulk_tracking()
    assert tracker.doBulkRequests is True


def test_disable_bulk_tracking(tracker):
    tracker.enable_bulk_tracking()
    assert tracker.doBulkRequests is True
    tracker.disable_bulk_tracking()
    assert tracker.doBulkRequests is False


def test_enable_cookies(tracker):
    tracker.configCookiesDisabled = True
    tracker.configCookieSecure = False
    tracker.configCookieHTTPOnly = False

    tracker.enable_cookies(
        domain="google.com",
        path="/somepath",
        secure=True,
        http_only=True,
        same_site="1",
    )

    assert tracker.configCookiesDisabled is False
    assert tracker.configCookieDomain == "google.com"
    assert tracker.configCookiePath == "/somepath"
    assert tracker.configCookieSecure is True
    assert tracker.configCookieHTTPOnly is True
    assert tracker.configCookieSameSite == "1"


def test_disable_send_image_response(tracker):
    tracker.sendImageResponse = True
    tracker.disable_send_image_response()
    assert tracker.sendImageResponse is False


def test_domain_fixup(tracker):
    assert tracker.domain_fixup("*.google.com.") == "google.com"


def test_get_cookie_name(tracker):
    name = "bla"
    site_id = 3
    tracker.FIRST_PARTY_COOKIES_PREFIX = "pr_"
    tracker.set_id_site(site_id)

    cookie_name = tracker.get_cookie_name(name)
    assert cookie_name[:-4] == f"pr_{name}.{site_id}."


def test_do_track_page_view(tracker):
    title = "Title with space"
    result = tracker.do_track_page_view(title)
    # Escaped title should be contained in url
    assert "action_name=Title%20with%20space" in result


def test_generate_new_pageview_id(tracker):
    assert tracker.idPageview == ""
    tracker.generate_new_pageview_id()
    assert len(tracker.idPageview) == 6


def test_do_track_event(tracker):
    result = tracker.do_track_event(
        category="music", action="buy", name="rand", value=5
    )

    assert "e_c=music" in result
    assert "e_a=buy" in result
    assert "e_n=rand" in result
    assert "e_v=5" in result


def test_do_track_content_impression(tracker):
    result = tracker.do_track_content_impression(
        "Foo bar", "The real content", "target_label"
    )

    assert "&c_n=Foo%20bar" in result
    assert "&c_p=The%20real%20content" in result
    assert "&c_t=target_label" in result


def test_do_track_content_interaction(tracker):
    result = tracker.do_track_content_interaction(
        "click", "Foo bar", "The real content", "target_label"
    )

    assert "&c_i=click" in result
    assert "&c_n=Foo%20bar" in result
    assert "&c_p=The%20real%20content" in result
    assert "&c_t=target_label" in result


def test_do_track_site_search(tracker):
    result = tracker.do_track_site_search("foo bar", "shoes", 5)

    assert "&search=foo%20bar" in result
    assert "&search_cat=shoes" in result
    assert "&search_count=5" in result


def test_do_track_goal(tracker):
    result = tracker.do_track_goal(4, 45.23)

    assert "&idgoal=4" in result
    assert "&revenue=45.23" in result


def test_do_track_action(tracker):
    result = tracker.do_track_action("https://domain.example/action_url", "download")
    assert "&download=https%3A//domain.example/action_url" in result

    result = tracker.do_track_action("https://domain.example/action_url2", "link")
    assert "&link=https%3A//domain.example/action_url2" in result


def test_add_ecommerce_item(tracker):
    values = ["pk1", "Air 1", "sneakers", 230.99, 1]
    tracker.add_ecommerce_item(*values)

    values[3] = str(values[3])
    assert tracker.ecommerceItems == values

    with pytest.raises(Exception) as exc:
        tracker.add_ecommerce_item("", "Air 1", "sneakers", 230.99, 1)
    assert exc.value.args[0] == "You must specify a SKU for the Ecommerce item"


def test_do_track_ecommerce_cart_update(tracker):
    result = tracker.do_track_ecommerce_cart_update(133.21)
    assert "&revenue=133.21" in result


def test_do_bulk_track(tracker):
    def post_request(request, method, data, force):
        return request, method, data, force

    tracker.do_track_goal(4, 45.23)
    with pytest.raises(Exception) as exc:
        tracker.do_bulk_track()
    assert exc.value.args[0] == (
        "Error: you must call the function do_track_page_view or do_track_goal"
        " from this class, before calling this method do_bulk_track():"
    )

    # Need to fake part of it because send_request would take care of some of it
    # and is not implemented in the tracker itself
    tracker.storedTrackingActions.append(tracker.do_track_goal(4, 45.23))
    tracker.send_request = post_request
    request, method, data, force = tracker.do_bulk_track()
    data = json.loads(data)

    assert request == "https://matomo.domain.example/matomo.php"
    assert method == "POST"
    assert force is True
    assert len(data["requests"]) == 1
    assert data["requests"][0].startswith(request)
    assert data["requests"][0].endswith("&revenue=45.23")


def test_do_track_ecommerce_order(tracker):
    result = tracker.do_track_ecommerce_order(2012, 345.2, 120, 45.66, 56.6, 10.5)
    assert "&revenue=345.2" in result
    assert "&ec_st=120" in result
    assert "&ec_tx=45.66" in result
    assert "&ec_sh=56.6" in result
    assert "&ec_dt=10.5" in result
    assert "&ec_id=2012" in result


def test_do_ping(tracker):
    result = tracker.do_ping()
    assert result.endswith("&ping=1")


def test_set_ecommerce_view(tracker):
    tracker.set_ecommerce_view(sku="pk1", name="Air 1", category="shoes", price=156.99)

    eview = tracker.ecommerceView
    assert eview["_pks"] == "pk1"
    assert eview["_pkc"] == "shoes"
    assert eview["_pkn"] == "Air 1"
    assert eview["_pkp"] == "156.99"

    tracker.set_ecommerce_view(sku="pk1", name=None, category="shoes", price=156.99)
    eview = tracker.ecommerceView
    assert eview["_pkn"] == ""

    tracker.set_ecommerce_view(
        sku="pk1", name=None, category=["shoes", "sneakers"], price=156.99
    )
    eview = tracker.ecommerceView
    assert json.loads(eview["_pkc"]) == ["shoes", "sneakers"]


def test_force_dot_as_separator_for_decimal_point(tracker):
    assert tracker.force_dot_as_separator_for_decimal_point(None) == ""
    assert tracker.force_dot_as_separator_for_decimal_point(False) == ""
    assert tracker.force_dot_as_separator_for_decimal_point("1345,56") == "1345.56"
    assert tracker.force_dot_as_separator_for_decimal_point("1345.56") == "1345.56"


def test_get_url_track_ecommerce_cart_update(tracker):
    tracker.ecommerceItems.append(1)  # Faulty entry, but will be emptied anyway
    result = tracker.get_url_track_ecommerce_cart_update(789.56)
    assert "&revenue=789.56" in result
    assert tracker.ecommerceItems == []


def test_get_url_track_ecommerce_order(tracker):
    result = tracker.get_url_track_ecommerce_order(
        order_id=345, grand_total=33, sub_total=23, tax=8, shipping=10, discount=5.4
    )

    assert "&ec_st=23" in result
    assert "&ec_tx=8" in result
    assert "&ec_sh=10" in result
    assert "&ec_dt=5.4" in result
    assert "&ec_id=345" in result
    assert "&revenue=33" in result
    assert tracker.ecommerceItems == []

    with pytest.raises(Exception) as exc:
        tracker.get_url_track_ecommerce_order(
            order_id=None,
            grand_total=33,
            sub_total=23,
            tax=8,
            shipping=10,
            discount=5.4,
        )
    assert exc.value.args[0] == "You must specify an order_id for the Ecommerce order"


def test_get_url_track_ecommerce(tracker):
    result = tracker.get_url_track_ecommerce(
        grand_total=33, sub_total=23, tax=8, shipping=10, discount=5.4
    )

    assert "&ec_st=23" in result
    assert "&ec_tx=8" in result
    assert "&ec_sh=10" in result
    assert "&ec_dt=5.4" in result
    assert "&revenue=33" in result

    result = tracker.get_url_track_ecommerce(
        grand_total=0, sub_total=23, tax=8, shipping=10, discount=5.4
    )
    assert "&revenue=" not in result

    result = tracker.get_url_track_ecommerce(
        grand_total=33, sub_total=0, tax=8, shipping=10, discount=5.4
    )
    assert "&ec_st=" not in result

    result = tracker.get_url_track_ecommerce(
        grand_total=33, sub_total=23, tax=0, shipping=10, discount=5.4
    )
    assert "&ec_tx=" not in result

    result = tracker.get_url_track_ecommerce(
        grand_total=33, sub_total=23, tax=8, shipping=0, discount=5.4
    )
    assert "&ec_sh=" not in result

    result = tracker.get_url_track_ecommerce(
        grand_total=33, sub_total=23, tax=8, shipping=10, discount=0
    )
    assert "&ec_dt=" not in result


def test_get_url_track_page_view(tracker):
    result = tracker.get_url_track_page_view("")
    assert "&action_name=" not in result
    result = tracker.get_url_track_page_view("Title with space")
    assert result.endswith("&action_name=Title%20with%20space")


def test_get_url_track_event(tracker):
    with pytest.raises(Exception) as exc:
        tracker.get_url_track_event("", "click", "Zootopia", 1.3)
    assert (
        exc.value.args[0]
        == "You must specify an Event Category name (Music, Videos, Games...)."
    )

    with pytest.raises(Exception) as exc:
        tracker.get_url_track_event("Videos", "", "Zootopia", 1.3)
        assert (
            exc.value.args[0]
            == "You must specify an Event action (click, view, add...)."
        )

    result = tracker.get_url_track_event("Videos", "click", "Zootopia", 1.3)
    assert "e_c=Video" in result
    assert "e_a=click" in result
    assert "e_n=Zootopia" in result
    assert "e_v=1.3" in result

    result = tracker.get_url_track_event("Videos", "click")
    assert "e_c=Video" in result
    assert "e_a=click" in result
    assert "e_n=" not in result
    assert "e_v=" not in result


def test_get_url_track_content_impression(tracker):
    with pytest.raises(Exception) as exc:
        tracker.get_url_track_content_impression(
            "", "https://domain.example/img.jpg", False
        )
    assert exc.value.args[0] == "You must specify a content name"

    result = tracker.get_url_track_content_impression(
        "Content_title", "https://domain.example/img.jpg", False
    )
    assert "&c_n=Content_title" in result
    assert "&c_p=https%3A//domain.example/img.jpg" in result
    assert "&c_t=" not in result

    result = tracker.get_url_track_content_impression(
        "Content_title", "https://domain.example/img.jpg", "target1"
    )
    assert "&c_t=target1" in result


def test_get_url_track_content_interaction(tracker):
    with pytest.raises(Exception) as exc:
        tracker.get_url_track_content_interaction(
            "", "Foo bar", "The real content", "target_label"
        )
    assert exc.value.args[0] == "You must specify a name for the interaction"

    with pytest.raises(Exception) as exc:
        tracker.get_url_track_content_interaction(
            "click", "", "The real content", "target_label"
        )
    assert exc.value.args[0] == "You must specify a content name"

    result = tracker.get_url_track_content_interaction(
        "click", "Foo bar", "The real content", "target_label"
    )
    assert "&c_i=click" in result
    assert "&c_n=Foo%20bar" in result
    assert "&c_p=The%20real%20content" in result
    assert "&c_t=target_label" in result

    result = tracker.get_url_track_content_interaction("click", "Foo bar", "", "")
    assert "&c_i=click" in result
    assert "&c_n=Foo%20bar" in result
    assert "&c_p=" not in result
    assert "&c_t=" not in result


def test_get_url_track_site_search(tracker):
    result = tracker.get_url_track_site_search("foo bar", "shoes", 5)
    assert "&search=foo%20bar" in result
    assert "&search_cat=shoes" in result
    assert "&search_count=5" in result

    result = tracker.get_url_track_site_search("foo bar", "", "")
    assert "&search=foo%20bar" in result
    assert "&search_cat=" not in result
    assert "&search_count=" not in result


def test_get_url_track_goal(tracker):
    result = tracker.get_url_track_goal(4, 45.23)
    assert "&idgoal=4" in result
    assert "&revenue=45.23" in result

    result = tracker.get_url_track_goal(4)
    assert "&idgoal=4" in result
    assert "&revenue=" not in result


def test_get_url_track_action(tracker):
    result = tracker.get_url_track_action(
        "https://domain.example/action_url", "download"
    )
    assert "&download=https%3A//domain.example/action_url" in result

    result = tracker.get_url_track_action("https://domain.example/action_url2", "link")
    assert "&link=https%3A//domain.example/action_url2" in result


def test_set_force_visit_date_time(tracker):
    assert tracker.forcedDatetime == ""
    tracker.set_force_visit_date_time("2023-01-02 12:00:00")
    assert tracker.forcedDatetime == "2023-01-02 12:00:00"


def test_set_force_new_visit(tracker):
    assert tracker.forcedNewVisit is False
    tracker.set_force_new_visit()
    assert tracker.forcedNewVisit is True


def test_set_ip(tracker):
    assert tracker.ip == "192.168.0.1"
    tracker.set_user_id("1.1.1.1")
    assert tracker.user_id == "1.1.1.1"


def test_set_user_id(tracker):
    assert tracker.user_id == ""
    tracker.set_user_id("jj3")
    assert tracker.user_id == "jj3"

    with pytest.raises(Exception) as exc:
        tracker.set_user_id("")
    assert exc.value.args[0] == "User ID cannot be empty."


def test_set_visitor_id(tracker):
    with pytest.raises(Exception) as exc:
        tracker.set_visitor_id("")
    assert exc.value.args[0] == (
        "set_visitor_id() expects a 16 characters"
        " hexadecimal string (containing only the following: 01234567890abcdefABCDEF)"
    )
    with pytest.raises(Exception) as exc:
        tracker.set_visitor_id("123456789012345Q")
    assert exc.value.args[0] == (
        "set_visitor_id() expects a 16 characters"
        " hexadecimal string (containing only the following: 01234567890abcdefABCDEF)"
    )
    visitor_id = "1234567890abcdef"
    tracker.set_visitor_id(visitor_id)
    assert tracker.forcedVisitorId == visitor_id


def test_get_visitor_id(tracker):
    visitor_id = "1234567890abcdef"
    tracker.set_visitor_id(visitor_id)
    assert tracker.get_visitor_id() == visitor_id

    tracker.load_visitor_id_cookie = lambda: True
    tracker.forcedVisitorId = ""
    tracker.cookieVisitorId = "ble"
    assert tracker.get_visitor_id() == "ble"

    tracker.load_visitor_id_cookie = lambda: False
    tracker.forcedVisitorId = ""
    tracker.randomVisitorId = "bla"
    assert tracker.get_visitor_id() == "bla"


def test_get_user_agent(tracker):
    tracker.set_user_agent("Fake Mozilla")
    assert tracker.get_user_agent() == tracker.user_agent


def test_get_ip(tracker):
    assert tracker.get_ip() == tracker.ip


def test_get_user_id(tracker):
    tracker.set_user_id("bla")
    assert tracker.get_user_id() == tracker.user_id


def test_load_visitor_id_cookie(tracker):
    tracker.get_cookie_matching_name = lambda x: ""
    assert tracker.load_visitor_id_cookie() is False

    tracker.get_cookie_matching_name = lambda x: "1234567890abcdef.194522"
    assert tracker.load_visitor_id_cookie() is True
    assert tracker.cookieVisitorId == "1234567890abcdef"
    assert tracker.createTs == "194522"


def test_delete_cookies(tracker, mocker):
    # Relies on set_cookie method that relied on set_cookie_response which is implementation specific and not implemented
    # in the tracker. Hence we'll just check if set_cookie is called correctly
    tracker.set_cookie = lambda c, i, v: (c, i, v)
    spy = mocker.spy(tracker, "set_cookie")

    tracker.delete_cookies()
    assert spy.call_count == 4
    call_args = {call.args for call in spy.call_args_list}
    assert call_args == {
        ("ref", None, -86400),
        ("id", None, -86400),
        ("cvar", None, -86400),
        ("ses", None, -86400),
    }


def test_get_attribution_info(tracker):
    tracker.get_cookie_matching_name = lambda x: "1234567890abcdef.194522"
    assert tracker.get_attribution_info() == "1234567890abcdef.194522"

    tracker.attributionInfo = {1: 2}
    assert tracker.get_attribution_info() == '{"1": 2}'


def test_set_token_auth(tracker):
    fake_token = "blable"
    tracker.set_token_auth(fake_token)
    assert tracker.token_auth == fake_token


def test_set_local_time(tracker):
    tracker.set_local_time("19:45:22")
    assert tracker.local_hour == "19"
    assert tracker.local_minute == "45"
    assert tracker.local_second == "22"


def test_set_resolution(tracker):
    tracker.set_resolution(800, 600)
    assert tracker.width == 800
    assert tracker.height == 600


def test_set_browser_has_cookies(tracker):
    assert tracker.hasCookies is False
    tracker.set_browser_has_cookies(True)
    assert tracker.hasCookies is True


def test_set_debug_string_append(tracker):
    tracker.set_debug_string_append("dbgstr")
    url = tracker.get_request(tracker.id_site)
    assert "&dbgstr" in url


def test_set_plugins(tracker):
    tracker.set_plugins(
        flash=True,
        java=False,
        quick_time=False,
        real_player=True,
        pdf=False,
        windows_media=False,
        silverlight=True,
    )
    expected = "&fla=1&java=0&qt=0&realp=1&pdf=0&wma=0&ag=1"
    assert tracker.plugins == expected


def test_disable_cookie_support(tracker):
    tracker.configCookiesDisabled = False
    tracker.disable_cookie_support()
    assert tracker.configCookiesDisabled is True


def test_get_request_timeout(tracker):
    assert tracker.get_request_timeout() != 0
    assert tracker.requestTimeout == tracker.get_request_timeout()


def test_set_request_timeout(tracker):
    with pytest.raises(Exception) as exc:
        tracker.set_request_timeout("a")
    exc = exc.value.args[0]
    assert exc == "Invalid value supplied for request timeout: timeout"

    current = tracker.get_request_timeout()
    tracker.set_request_timeout(current + 10)
    assert tracker.get_request_timeout() == current + 10


def test_set_request_method_non_bulk(tracker):
    assert tracker.request_method == "GET"
    tracker.set_request_method_non_bulk("POST")
    assert tracker.request_method == "POST"
    tracker.set_request_method_non_bulk("GET")
    assert tracker.request_method == "GET"


def test_set_proxy(tracker):
    tracker.set_proxy(proxy="domain.example", proxy_port=6667, proxy_type="https")
    assert tracker.proxy == "domain.example"
    assert tracker.proxy_port == 6667
    assert tracker.proxy_type == "https"


def test_get_proxy(tracker):
    tracker.set_proxy(proxy="domain.example", proxy_port=6667, proxy_type="https")
    assert tracker.get_proxy() == "https://domain.example:6667"

    tracker.set_proxy(proxy="", proxy_port=6667, proxy_type="https")
    assert tracker.get_proxy() is None


def test_get_timestamp(tracker):
    import time

    assert time.time() - tracker.get_timestamp() < 1

    tracker.set_force_visit_date_time("2023-01-01 18:45:23")
    assert tracker.get_timestamp() == 1672595123.0


def test_get_base_url(tracker):
    assert tracker.URL == "https://matomo.domain.example"
    assert tracker.get_base_url() == "https://matomo.domain.example/matomo.php"

    tracker.URL = ""
    with pytest.raises(Exception) as exc:
        tracker.get_base_url()
    exc = exc.value.args[0]
    assert exc == (
        "You must first set the Matomo Tracker URL by calling "
        "MatomoTracker.URL = 'http://your-website.org/matomo/'"
    )


def test_get_request(tracker):
    """
    Tricky to test because there are so many components.

    Work in progress
    """
    id_site = tracker.id_site
    assert tracker.get_request(id_site).startswith(
        f"https://matomo.domain.example/matomo.php?idsite={id_site}"
    )


def test_get_cookie_matching_name(tracker, mocker):
    spy = mocker.spy(tracker, "get_cookie_name")

    tracker.disable_cookie_support()
    cookie = tracker.get_cookie_matching_name("id")
    assert spy.call_count == 0
    assert cookie is None

    tracker.configCookiesDisabled = False
    tracker.request.cookie = {"id": "doesntmatter"}

    cookie_value = tracker.get_cookie_matching_name("id")
    assert spy.call_count == 1
    assert cookie_value == "doesntmatter"


def test_get_current_script_name(tracker):
    assert tracker.get_current_script_name() == "/matomo_test_fake"


def test_get_current_scheme(tracker):
    assert tracker.get_current_scheme() == "http"
    tracker.request["HTTPS"] = True
    assert tracker.get_current_scheme() == "https"


def test_get_current_host(tracker):
    assert tracker.get_current_host() == "test.domain.example"


def test_get_current_query_string(tracker):
    assert tracker.get_current_query_string() == "?test=1"
    del tracker.request["QUERY_STRING"]
    assert tracker.get_current_query_string() == ""


def test_get_current_url(tracker):
    assert (
        tracker.get_current_url()
        == "http://test.domain.example/matomo_test_fake?test=1"
    )


def test_set_first_party_cookies(tracker, mocker):
    tracker.set_cookie = mocker.Mock()
    spy = mocker.spy(tracker, "set_cookie")

    tracker.configCookiesDisabled = True
    tracker.set_first_party_cookies()

    assert spy.call_count == 0

    tracker.configCookiesDisabled = False
    tracker.response = True  # Doesn't matter what it is for test as long as it exists
    tracker.set_first_party_cookies()

    calls = {call.args for call in spy.call_args_list}
    id_cookie_value = f"{tracker.get_visitor_id()}.{tracker.createTs}"

    assert spy.call_count == 3  # Everything but ref should be set by default
    assert ("cvar", "{}", 1800) in calls
    assert ("ses", "*", 1800) in calls
    assert ("id", id_cookie_value, tracker.configVisitorCookieTimeout) in calls

    valid = [1, 2, "3", 4]
    tracker.set_attribution_info(json.dumps(valid))
    tracker.set_first_party_cookies()
    calls = {call.args for call in spy.call_args_list}

    assert spy.call_count == 7  # 4 more (count is not resetted)
    assert len(calls) == 4
    assert ("ref", '[1, 2, "3", 4]', tracker.configReferralCookieTimeout) in calls


def test__set_cookie(tracker):
    tracker.currentTs = 1680952180.13168  # Fix for predictable results
    header = tracker._set_cookie("id", "somevalue", 15000)

    assert (
        header
        == "Set-Cookie: id=somevalue; expires='Sat, 08-04-2023 15:19:40 GMT; path=/"
    )

    tracker.enable_cookies(
        domain="test.domain.example",
        path="/somepath",
        secure=True,
        http_only=True,
        same_site="123",
    )
    header = tracker._set_cookie("id", "somevalue", 15000)
    assert (
        header
        == "Set-Cookie: id=somevalue; expires='Sat, 08-04-2023 15:19:40 GMT; path=/somepath; domain=test.domain.example; secure; HttpOnly; SameSite=123"
    )


def test_set_cookie(tracker, mocker):
    # set_cookie_response method is not implemented in tracker (depends on cookie jar implementation)
    params = {
        "cookie_name": "id",
        "cookie_value": "somevalue",
        "cookie_ttl": 15000,
    }
    tracker.set_cookie_response = mocker.Mock()
    spy = mocker.spy(tracker, "set_cookie_response")
    tracker.set_cookie(**params)

    assert spy.call_count == 1
    assert spy.call_args.args == (params["cookie_name"], params["cookie_value"])
    spy_kwargs = spy.call_args.kwargs
    assert spy_kwargs["max_age"] == params["cookie_ttl"] + tracker.currentTs
    assert spy_kwargs["secure"] == tracker.configCookieSecure
    assert spy_kwargs["httponly"] == tracker.configCookieHTTPOnly
    assert spy_kwargs["path"] == tracker.configCookiePath


def test_get_cookies(tracker):
    cookie = {"id": "doesntmatter"}
    tracker.request.cookie = cookie
    assert tracker.get_cookies() == cookie


def test_get_custom_variables_from_cookie(tracker, mocker):
    assert tracker.get_custom_variables_from_cookie() == {}

    tracker.get_cookie_matching_name = mocker.Mock(return_value='{"key1":"val1"}')
    spy = mocker.spy(tracker, "get_cookie_matching_name")
    value = tracker.get_custom_variables_from_cookie()

    assert value == {"key1": "val1"}
    assert spy.call_count == 1
    assert spy.call_args.args == ("cvar",)


def test_set_outgoing_tracker_cookie(tracker):
    assert tracker.outgoingTrackerCookies == {}
    tracker.set_outgoing_tracker_cookie("id", "new_value")
    assert tracker.outgoingTrackerCookies == {"id": "new_value"}
    tracker.set_outgoing_tracker_cookie("id")
    assert tracker.outgoingTrackerCookies == {}


def test_get_incoming_tracker_cookie(tracker):
    tracker.incomingTrackerCookies = {"id": "somevalue"}
    assert tracker.get_incoming_tracker_cookie("id") == "somevalue"
    assert tracker.get_incoming_tracker_cookie("missing") is False


def test_parse_incoming_cookies(tracker):
    headers = [
        "Set-Cookie: id=a3fWa; Expires=Wed, 21 Oct 2015 07:28:00 GMT",
        "Http-Host: test.domain.example",
    ]
    tracker.parse_incoming_cookies(headers)
    assert tracker.incomingTrackerCookies.get("id") == ["a3fWa"]
