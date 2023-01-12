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
    req = Request(request_data)
    return MatomoTracker(req, 1)


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
    fields = ["networkTime", "serverTime", "transferTime", "domProcessingTime",
              "domCompletionTime", "onLoadTime"]
    values = [random.randint(1, 100) for i in range(len(fields))]

    for field in fields:
        assert getattr(tracker, field) == 0

    tracker.set_performance_timings(*values)

    for i, field in enumerate(fields):
        assert getattr(tracker, field) == values[i]


def test_clear_performance_timings(tracker):
    fields = ["networkTime", "serverTime", "transferTime", "domProcessingTime",
              "domCompletionTime", "onLoadTime"]

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
    valid = [1,2,"3",4]
    invalid = {1:2}

    assert tracker.attributionInfo == []
    tracker.set_attribution_info(json.dumps(valid))
    assert tracker.attributionInfo == valid

    with pytest.raises(Exception):
        tracker.set_attribution_info(json.dumps(invalid))


def test_set_custom_variable(tracker):
    assert tracker.pageCustomVar == {}
    assert tracker.eventCustomVar == {}
    assert tracker.visitorCustomVar == {}

    # First check error handling
    with pytest.raises(Exception) as excinfo:
        tracker.set_custom_variable("1", "name", "value")
    exc = excinfo.value
    assert exc.args[0] == 'Parameter id to set_custom_variable should be an integer'

    with pytest.raises(Exception) as excinfo:
        tracker.set_custom_variable(1, "name", "value", "invalidscope")
    exc = excinfo.value
    assert exc.args[0] == "Invalid 'scope' parameter value"

    tracker.set_custom_variable(1, "name", "value", "page")
    assert tracker.pageCustomVar[1] == ["name", "value"]

    tracker.set_custom_variable(3, "name", "value", "event")
    assert tracker.eventCustomVar[3] == ["name", "value"]

    tracker.set_custom_variable(2, "name", "value", "visit")
    assert tracker.visitorCustomVar[2] == ["name", "value"]


def test_set_client_hints(tracker):
    assert tracker.clientHints == {
        "model": "",
        "platform": "",
        "platformVersion": "",
        "uaFullVersion": "",
        "fullVersionList": []
    }

    tracker.set_client_hints("modelA", "platformB", "1.12", "", "uaC")
    assert tracker.clientHints == {
        "model": "modelA",
        "platform": "platformB",
        "platformVersion": "1.12",
        "uaFullVersion": "uaC",
        "fullVersionList": []
    }

    fullVersionList = '" Not A;Brand";v="99.0.0.0", "Chromium";v="98.0.4750.0", "Google Chrome";v="98.0.4750.0"'
    tracker.set_client_hints("modelA", "platformB", "1.12", fullVersionList, "uaC")
    assert tracker.clientHints == {
        "model": "modelA",
        "platform": "platformB",
        "platformVersion": "1.12",
        "uaFullVersion": "uaC",
        "fullVersionList": [
            {"brand": " Not A;Brand", "version": "99.0.0.0"},
            {"brand": "Chromium", "version": "98.0.4750.0"},
            {"brand": "Google Chrome", "version": "98.0.4750.0"},
        ]
    }


