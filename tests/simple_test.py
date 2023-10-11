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
