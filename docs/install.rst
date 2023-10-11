.. _install:

Install
=======

This part of the documentation covers the installation of Matomo,
a necessary first step for its use.

$ python -m pip install matomo
------------------------------

To install Matomo, simply run this simple command in your terminal of choice::

    $ python -m pip install matomo


Get the Source Code
-------------------

Matomo is actively developed on GitHub, where the code is
`always available <https://github.com/samastur/matomo>`_.

You can clone the public repository::

    $ git clone https://github.com/samastur/matomo.git

Once you have a copy of the source, you can embed it in your own Python
package, or install it into your site-packages easily::

    $ cd matomo
    $ python -m pip install .
