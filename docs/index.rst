.. Matomo documentation master file, created by
   sphinx-quickstart on Mon Apr 10 10:53:27 2023.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome to Matomo's documentation!
==================================

A Python client for `Matomo <https://matomo.org/>`_, Google Analytics alternative
that protects your data and your customers' privacy, based on a port of the
`PHP tracker <https://developer.matomo.org/api-reference/PHP-Matomo-Tracker>`_
with an almost 100% compatibility.

The current version should be almost fully compatible with Matomo 5.
100% compatibility is not possible because of differences between PHP running
environment and Python's.


Differences with PHP version
----------------------------
- added _set_cookie method that returns cookie as string
- added set_cookie_response method called with all cookie values that is called by set_cookie and needs to be implemented for your framework (check django.py for an example)
- added set_response for adding a response object that methods for cookies can use
- changed set_first_party_cookies to also do nothing if response object does not exist
- added proxy_type option to set_proxy and get_proxy returns full string because requests library requires proxy to include proxy type)
- added PATH_TO_CERTIFICATES_FILE to Matomo class for using certificates (instead of checking if a constant with that name exists)
- missing support for doTrackPhpThrowable and doTrackCrash until I figure out how to use and test them.


.. toctree::
   :maxdepth: 2
   :caption: Contents:

   install
   usage
   api



Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
