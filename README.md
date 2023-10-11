# matomo

A Python client for Matomo based on a port of 
[the PHP tracker](https://github.com/matomo-org/matomo-php-tracker) with
an almost 100% compatibility.

The current version should be almost fully compatible with Matomo 5, but it has
not been extensively tested yet. 100% compatibility is not possible because of
differences between PHP running environment and Python's.

Check `/tests` and `/examples` folders for examples on how to use it or `/docs`
to read its API documentation.

API Reference and User Guide available on
[Read the Docs](https://matomo.readthedocs.io/en/latest/).

### Differences with PHP version

* added `_set_cookie` method that returns cookie as string
* added `set_cookie_response` method called with all cookie values that is
  called by `set_cookie`  and needs to be implemented for your framework
  (check `django.py` for an example)
* added `set_response` for adding a response object that methods for cookies can
  use
* changed `set_first_party_cookies` to also do nothing if response object does
  not exist
* added `proxy_type option` to `set_proxy` and `get_proxy` returns full string
  because `requests` library
  [requires](https://docs.python-requests.org/en/master/user/advanced/#proxies)
  proxy to include proxy type)
* added `PATH_TO_CERTIFICATES_FILE` to `Matomo` class for using certificates
  (instead of checking if a constant with that name exists)
* missing support for `doTrackPhpThrowable` and `doTrackCrash` until I figure
  out how to use and test them.

Cookie handling is not yet settled and may change in the future.

## Django

`matomo.django` module contains support for Django. It contains two classes:

* `Matomo` - a Django compatible subclass of the `Matomo` tracker class that 
  correctly reads configuration values from Django's request object.

* `MatomoMixin` - a mixin for class based views that creates and stores `matomo`
  tracker object on the view's instance.

To use either of them you need to configure two variables in your Django's
`settings.py`:

* `MATOMO_SITE_ID` - ID of the sie you want to track
* `MATOMO_TRACKING_API_URL` - your tracking URL

**WARNING**: All calls to Matomo servers are synchronous and will thus impact
the response time of views that make them.
