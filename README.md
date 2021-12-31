# matomo

A Python client for Matomo based on a port of 
[the PHP tracker](https://github.com/matomo-org/matomo-php-tracker) and aiming
for an almost 100% compatibility.

The current version should be almost fully compatible with Matomo 4, but it has
not been extensively tested yet. Methods for dealing with cookies are especially
suspicious.

100% compatibility is probably not possible because of differences between
PHP running environment and Python's.

Check `/tests` folder for an example on how to use it or `/docs` to read
its API documentation. Better documentation on how to use it is coming soon
(once I fix cookies).

### Differences with PHP version

* added `_set_cookie` method that returns cookie as string
* added `proxy_type option` to `set_proxy` and `get_proxy` returns full string
  because `requests` library
  [requires](https://docs.python-requests.org/en/master/user/advanced/#proxies)
  proxy to include proxy type)
* added `PATH_TO_CERTIFICATES_FILE` to `Matomo` class for using certificates
  (instead of checking if a constant with that name exists)
