# -*- coding: utf-8 -*-
"""
Compatibility imports between py2/py3
"""
# pragma: nocover
try:
    from itertools import zip_longest                   # noqa
except ImportError:
    from itertools import izip_longest as zip_longest   # noqa

try:
    import configparser                                 # noqa
except ImportError:
    import ConfigParser as configparser                 # noqa
