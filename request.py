import collections
import requests


class Request(collections.UserDict):
    cookie = requests.cookies.RequestsCookieJar()